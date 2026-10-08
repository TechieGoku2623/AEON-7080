"""Experiments, replay, comparison, and reports."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from aeon_api.db import get_session
from aeon_api.models import AuditLog, Experiment, ExperimentResult, Report, User, Workspace
from aeon_api.security import current_user, current_workspace, new_id
from data.lineage.lineage import experiment_lineage
from simulation_engine.pharmacology.drug_response import default_config, run_drug_response

router = APIRouter(prefix="/api", tags=["experiments"])


class ExperimentCreate(BaseModel):
    title: str | None = None
    template_id: str | None = "drug-response"
    config: dict | None = None


def _owned(session: Session, workspace: Workspace, experiment_id: str) -> Experiment:
    experiment = session.get(Experiment, experiment_id)
    if experiment is None or experiment.workspace_id != workspace.id:
        raise HTTPException(status_code=404, detail="Experiment not found.")
    return experiment


def _latest(session: Session, experiment_id: str) -> ExperimentResult | None:
    return session.scalar(
        select(ExperimentResult)
        .where(ExperimentResult.experiment_id == experiment_id)
        .order_by(ExperimentResult.created_at.desc())
    )


@router.post("/experiments")
def create_experiment(
    body: ExperimentCreate,
    user: User = Depends(current_user),
    workspace: Workspace = Depends(current_workspace),
    session: Session = Depends(get_session),
) -> dict:
    config = default_config()
    if body.config:
        config.update(body.config)
    if body.template_id:
        config["template_id"] = body.template_id
    experiment = Experiment(
        id=new_id(),
        workspace_id=workspace.id,
        title=body.title or config.get("title") or "Computational experiment",
        template_id=config.get("template_id") or "",
        seed=int(config.get("seed", 42)),
        config_json=config,
        status="created",
    )
    session.add(experiment)
    session.add(AuditLog(id=new_id(), user_id=user.id, action="experiment.create", target=experiment.id))
    session.commit()
    return {"id": experiment.id, "status": experiment.status, "config": config}


@router.get("/experiments")
def list_experiments(workspace: Workspace = Depends(current_workspace), session: Session = Depends(get_session)) -> dict:
    rows = session.scalars(
        select(Experiment).where(Experiment.workspace_id == workspace.id).order_by(Experiment.created_at.desc())
    ).all()
    return {
        "experiments": [
            {
                "id": row.id,
                "title": row.title,
                "status": row.status,
                "seed": row.seed,
                "template_id": row.template_id,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
    }


@router.get("/experiments/compare")
def compare(
    ids: str,
    workspace: Workspace = Depends(current_workspace),
    session: Session = Depends(get_session),
) -> dict:
    selected = [part for part in ids.split(",") if part]
    if len(selected) < 2:
        raise HTTPException(status_code=400, detail="Provide at least two experiment ids.")
    rows = []
    for experiment_id in selected:
        experiment = _owned(session, workspace, experiment_id)
        result = _latest(session, experiment.id)
        if result is None:
            raise HTTPException(status_code=400, detail=f"{experiment_id} has no result.")
        drugs = {}
        for name, drug in result.payload_json.get("drugs", {}).items():
            drugs[name] = {
                "parameters": drug.get("parameters"),
                "endpoints": drug.get("endpoints"),
                "uncertainty": (drug.get("monte_carlo") or {}).get("endpoint_summary"),
            }
        rows.append(
            {
                "id": experiment.id,
                "title": experiment.title,
                "seed": experiment.seed,
                "model_versions": result.payload_json.get("model_versions"),
                "assumptions": result.payload_json.get("assumptions"),
                "drugs": drugs,
            }
        )
    return {"comparison": rows, "note": "Differences are between stored computational runs."}


@router.get("/experiments/{experiment_id}")
def get_experiment(
    experiment_id: str,
    workspace: Workspace = Depends(current_workspace),
    session: Session = Depends(get_session),
) -> dict:
    experiment = _owned(session, workspace, experiment_id)
    result = _latest(session, experiment.id)
    report = session.scalar(select(Report).where(Report.experiment_id == experiment.id))
    return {
        "id": experiment.id,
        "title": experiment.title,
        "status": experiment.status,
        "config": experiment.config_json,
        "result": result.payload_json if result else None,
        "report_id": report.id if report else None,
        "lineage": experiment_lineage(),
    }


@router.post("/experiments/{experiment_id}/run")
def run_experiment(
    experiment_id: str,
    user: User = Depends(current_user),
    workspace: Workspace = Depends(current_workspace),
    session: Session = Depends(get_session),
) -> dict:
    experiment = _owned(session, workspace, experiment_id)
    try:
        payload = run_drug_response(experiment.config_json)
    except (ValueError, PermissionError) as exc:
        experiment.status = "failed"
        session.commit()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    payload["experiment_id"] = experiment.id
    stored = ExperimentResult(id=new_id(), experiment_id=experiment.id, payload_json=payload)
    report = Report(id=new_id(), experiment_id=experiment.id, markdown=payload["report_markdown"])
    experiment.status = "completed"
    session.add(stored)
    session.add(report)
    session.add(
        AuditLog(
            id=new_id(),
            user_id=user.id,
            action="experiment.run",
            target=experiment.id,
            detail_json={"fingerprint": payload["reproducibility"]["config_fingerprint"]},
        )
    )
    session.commit()
    return {"experiment_id": experiment.id, "report_id": report.id, "result": payload}


@router.post("/experiments/{experiment_id}/replay")
def replay(
    experiment_id: str,
    user: User = Depends(current_user),
    workspace: Workspace = Depends(current_workspace),
    session: Session = Depends(get_session),
) -> dict:
    experiment = _owned(session, workspace, experiment_id)
    previous = _latest(session, experiment.id)
    payload = run_drug_response(experiment.config_json, include_waveforms=experiment.config_json.get("mode", "patient") == "patient")
    payload["experiment_id"] = experiment.id
    same = False
    if previous:
        same = previous.payload_json["reproducibility"]["config_fingerprint"] == payload["reproducibility"]["config_fingerprint"]
        old = previous.payload_json["drugs"]
        new = payload["drugs"]
        same = same and _endpoints_match(old, new)
    stored = ExperimentResult(id=new_id(), experiment_id=experiment.id, payload_json=payload, replay_of=previous.id if previous else None)
    session.add(stored)
    session.add(AuditLog(id=new_id(), user_id=user.id, action="experiment.replay", target=experiment.id))
    session.commit()
    return {"experiment_id": experiment.id, "matched_previous": same, "result": payload}


@router.post("/reports/generate")
def generate_report(body: dict, workspace: Workspace = Depends(current_workspace), session: Session = Depends(get_session)) -> dict:
    experiment = _owned(session, workspace, body.get("experiment_id", ""))
    result = _latest(session, experiment.id)
    if result is None:
        raise HTTPException(status_code=400, detail="Run the experiment before generating a report.")
    report = Report(id=new_id(), experiment_id=experiment.id, markdown=result.payload_json["report_markdown"])
    session.add(report)
    session.commit()
    return {"id": report.id, "markdown": report.markdown}


@router.get("/reports/{report_id}")
def get_report(report_id: str, workspace: Workspace = Depends(current_workspace), session: Session = Depends(get_session)) -> dict:
    report = session.get(Report, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    _owned(session, workspace, report.experiment_id)
    return {"id": report.id, "experiment_id": report.experiment_id, "markdown": report.markdown}


def _endpoints_match(old: dict, new: dict) -> bool:
    for name, drug in old.items():
        if name not in new:
            return False
        a = drug["endpoints"]["glucose_nadir_delta_mg_dl"]
        b = new[name]["endpoints"]["glucose_nadir_delta_mg_dl"]
        if abs(float(a) - float(b)) > 1e-6:
            return False
    return True
