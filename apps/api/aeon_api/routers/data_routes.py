"""Upload, profile, map, and ask a table."""

from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from aeon_api.config import STORAGE
from aeon_api.db import get_session
from aeon_api.models import (
    AuditLog,
    DataLineage,
    DataTransformation,
    Dataset,
    DatasetPermission,
    DatasetVersion,
    User,
    Workspace,
)
from aeon_api.security import current_user, current_workspace, new_id
from ai_scientist.data_scientist.analyst import analyze_question
from data.ingestion.profiler import profile_frame, read_table
from data.lineage.lineage import experiment_lineage
from data.schemas.mapping import apply_mapping, suggest_mapping
from data.transformation.units import convert
from data.validation.quality import quality_report

router = APIRouter(prefix="/api/data", tags=["data"])


class MapRequest(BaseModel):
    mapping: list[dict]
    confirmed: bool = False
    row_index: int = 0


class AnalyzeRequest(BaseModel):
    question: str


class ConvertRequest(BaseModel):
    value: float
    from_unit: str
    to_unit: str


def _flag(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _dataset(session: Session, workspace: Workspace, dataset_id: str) -> Dataset:
    dataset = session.get(Dataset, dataset_id)
    if dataset is None or dataset.workspace_id != workspace.id:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    return dataset


def _latest_version(session: Session, dataset_id: str) -> DatasetVersion:
    version = session.scalar(
        select(DatasetVersion)
        .where(DatasetVersion.dataset_id == dataset_id)
        .order_by(DatasetVersion.version_number.desc())
    )
    if version is None:
        raise HTTPException(status_code=404, detail="Dataset has no version.")
    return version


@router.get("")
def list_datasets(workspace: Workspace = Depends(current_workspace), session: Session = Depends(get_session)) -> dict:
    rows = session.scalars(select(Dataset).where(Dataset.workspace_id == workspace.id)).all()
    payload = []
    for row in rows:
        version = _latest_version(session, row.id)
        payload.append(
            {
                "id": row.id,
                "name": row.name,
                "kind": row.kind,
                "rows": version.row_count,
                "version": version.version_number,
                "label": "SYNTHETIC DATA" if version.source.startswith("synthetic") else "USER DATA",
                "created_at": row.created_at.isoformat(),
            }
        )
    return {"datasets": payload}


@router.post("/upload")
def upload(
    file: UploadFile = File(...),
    name: str = Form(""),
    use_in_experiments: str = Form("true"),
    allow_training: str = Form("false"),
    allow_analytics: str = Form("false"),
    user: User = Depends(current_user),
    workspace: Workspace = Depends(current_workspace),
    session: Session = Depends(get_session),
) -> dict:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".csv", ".tsv", ".json", ".txt"}:
        raise HTTPException(
            status_code=400,
            detail="This build accepts CSV, TSV, and JSON tables. Other formats are extension points.",
        )
    dataset_id = new_id()
    folder = STORAGE / "datasets" / workspace.id / dataset_id / "v1"
    folder.mkdir(parents=True, exist_ok=False)
    destination = folder / f"original{suffix}"
    with destination.open("wb") as handle:
        shutil.copyfileobj(file.file, handle)
    os.chmod(destination, 0o600)
    try:
        frame = read_table(destination)
        profile = profile_frame(frame)
        quality = quality_report(frame, profile)
    except Exception as exc:  # noqa: BLE001
        shutil.rmtree(folder.parent, ignore_errors=True)
        raise HTTPException(status_code=400, detail=f"Could not read the table: {exc}") from exc
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    version_id = new_id()
    session.add(Dataset(id=dataset_id, workspace_id=workspace.id, name=name or file.filename or "dataset", kind="tabular"))
    session.add(
        DatasetVersion(
            id=version_id,
            dataset_id=dataset_id,
            version_number=1,
            storage_path=str(destination),
            content_hash=digest,
            schema_json={"columns": profile["column_names"]},
            profile_json=profile,
            quality_json=quality,
            source="upload",
            notes="Original upload. Not overwritten by later versions.",
            row_count=profile["rows"],
        )
    )
    session.add(
        DatasetPermission(
            id=new_id(),
            dataset_id=dataset_id,
            use_in_experiments=_flag(use_in_experiments),
            allow_training=_flag(allow_training),
            allow_analytics=_flag(allow_analytics),
        )
    )
    session.add(DataTransformation(id=new_id(), dataset_version_id=version_id, step="upload", parameters_json={"filename": file.filename}))
    session.add(AuditLog(id=new_id(), user_id=user.id, action="dataset.upload", target=dataset_id, detail_json={"allow_training": allow_training}))
    session.commit()
    return {"id": dataset_id, "version": 1, "profile": profile, "quality": quality}


@router.get("/{dataset_id}")
def get_dataset(dataset_id: str, workspace: Workspace = Depends(current_workspace), session: Session = Depends(get_session)) -> dict:
    dataset = _dataset(session, workspace, dataset_id)
    version = _latest_version(session, dataset.id)
    if not (version.profile_json or {}).get("column_names"):
        frame = read_table(Path(version.storage_path))
        version.profile_json = profile_frame(frame)
        version.quality_json = quality_report(frame, version.profile_json)
        version.row_count = version.profile_json["rows"]
        version.schema_json = {"columns": version.profile_json["column_names"]}
        session.commit()
    permission = session.scalar(select(DatasetPermission).where(DatasetPermission.dataset_id == dataset.id))
    versions = session.scalars(select(DatasetVersion).where(DatasetVersion.dataset_id == dataset.id)).all()
    return {
        "id": dataset.id,
        "name": dataset.name,
        "version": version.version_number,
        "profile": version.profile_json,
        "quality": version.quality_json,
        "permission": {
            "use_in_experiments": permission.use_in_experiments,
            "allow_training": permission.allow_training,
            "allow_analytics": permission.allow_analytics,
            "acknowledge_sensitive": permission.acknowledge_sensitive,
        }
        if permission
        else None,
        "versions": [
            {"version": item.version_number, "source": item.source, "rows": item.row_count, "created_at": item.created_at.isoformat()}
            for item in versions
        ],
        "suggestions": suggest_mapping(version.profile_json.get("column_names", [])),
    }


@router.post("/{dataset_id}/profile")
def profile(dataset_id: str, workspace: Workspace = Depends(current_workspace), session: Session = Depends(get_session)) -> dict:
    dataset = _dataset(session, workspace, dataset_id)
    version = _latest_version(session, dataset.id)
    frame = read_table(Path(version.storage_path))
    profile_json = profile_frame(frame)
    quality = quality_report(frame, profile_json)
    version.profile_json = profile_json
    version.quality_json = quality
    version.row_count = profile_json["rows"]
    session.commit()
    return {"profile": profile_json, "quality": quality}


@router.post("/{dataset_id}/map")
def map_data(
    dataset_id: str,
    body: MapRequest,
    workspace: Workspace = Depends(current_workspace),
    session: Session = Depends(get_session),
) -> dict:
    dataset = _dataset(session, workspace, dataset_id)
    version = _latest_version(session, dataset.id)
    permission = session.scalar(select(DatasetPermission).where(DatasetPermission.dataset_id == dataset.id))
    if permission and not permission.use_in_experiments:
        raise HTTPException(status_code=403, detail="This dataset is not marked for use in experiments.")
    frame = read_table(Path(version.storage_path))
    profile_json = version.profile_json or profile_frame(frame)
    if profile_json.get("sensitive", {}).get("potentially_sensitive") and not (permission and permission.acknowledge_sensitive):
        raise HTTPException(
            status_code=409,
            detail=profile_json["sensitive"]["warning"],
        )
    if body.row_index < 0 or body.row_index >= len(frame):
        raise HTTPException(status_code=400, detail="row_index is outside the table.")
    row = frame.iloc[body.row_index].where(pd.notna(frame.iloc[body.row_index]), None).to_dict()
    try:
        extracted = apply_mapping(row, body.mapping, body.confirmed)
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (KeyError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    session.add(
        DataTransformation(
            id=new_id(),
            dataset_version_id=version.id,
            step="map",
            parameters_json={"mapping": body.mapping, "confirmed": body.confirmed, "row_index": body.row_index},
        )
    )
    session.commit()
    return extracted


@router.post("/{dataset_id}/analyze")
def analyze(
    dataset_id: str,
    body: AnalyzeRequest,
    workspace: Workspace = Depends(current_workspace),
    session: Session = Depends(get_session),
) -> dict:
    dataset = _dataset(session, workspace, dataset_id)
    version = _latest_version(session, dataset.id)
    frame = read_table(Path(version.storage_path))
    answer = analyze_question(frame, body.question)
    return answer


@router.get("/{dataset_id}/lineage")
def lineage(dataset_id: str, workspace: Workspace = Depends(current_workspace), session: Session = Depends(get_session)) -> dict:
    dataset = _dataset(session, workspace, dataset_id)
    graph = experiment_lineage(dataset.name)
    session.add(DataLineage(id=new_id(), dataset_id=dataset.id, graph_json=graph))
    session.commit()
    return graph


@router.delete("/{dataset_id}")
def delete_dataset(
    dataset_id: str,
    user: User = Depends(current_user),
    workspace: Workspace = Depends(current_workspace),
    session: Session = Depends(get_session),
) -> dict:
    dataset = _dataset(session, workspace, dataset_id)
    versions = session.scalars(select(DatasetVersion).where(DatasetVersion.dataset_id == dataset.id)).all()
    for version in versions:
        for step in session.scalars(select(DataTransformation).where(DataTransformation.dataset_version_id == version.id)).all():
            session.delete(step)
        path = Path(version.storage_path)
        if path.exists():
            shutil.rmtree(path.parent, ignore_errors=True)
        session.delete(version)
    for item in session.scalars(select(DataLineage).where(DataLineage.dataset_id == dataset.id)).all():
        session.delete(item)
    permission = session.scalar(select(DatasetPermission).where(DatasetPermission.dataset_id == dataset.id))
    if permission:
        session.delete(permission)
    session.delete(dataset)
    session.add(AuditLog(id=new_id(), user_id=user.id, action="dataset.delete", target=dataset_id))
    session.commit()
    return {"deleted": dataset_id}


@router.post("/convert")
def convert_units(body: ConvertRequest, user: User = Depends(current_user)) -> dict:
    try:
        return convert(body.value, body.from_unit, body.to_unit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{dataset_id}/acknowledge")
def acknowledge(dataset_id: str, workspace: Workspace = Depends(current_workspace), session: Session = Depends(get_session)) -> dict:
    _dataset(session, workspace, dataset_id)
    permission = session.scalar(select(DatasetPermission).where(DatasetPermission.dataset_id == dataset_id))
    if permission is None:
        raise HTTPException(status_code=404, detail="No permission record.")
    permission.acknowledge_sensitive = True
    session.commit()
    return {"acknowledge_sensitive": True, "note": "Acknowledgement is not de-identification."}
