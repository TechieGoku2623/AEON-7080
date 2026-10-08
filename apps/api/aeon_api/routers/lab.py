"""Simulations, patients, and classical ML."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from aeon_api.db import get_session
from aeon_api.models import (
    ModelVersion,
    SimulationRun,
    StoredModel,
    User,
    VirtualPatient,
    VirtualPopulation,
    Workspace,
)
from aeon_api.security import current_user, current_workspace, new_id
from ml.training.logistic import train_morphology_classifier
from simulation_engine.core.registry import EXTENSION_POINTS, build_default_registry
from simulation_engine.patients.virtual_patient import generate_population, generate_virtual_patient

router = APIRouter(tags=["lab"])
REGISTRY = build_default_registry()


class SimulationRequest(BaseModel):
    model: str
    parameters: dict
    initial_state: dict | None = None
    duration: float = 24
    dt: float = 0.05
    seed: int = 42


class PatientRequest(BaseModel):
    seed: int = 42
    condition: str = "synthetic_diabetes"


class PopulationRequest(BaseModel):
    seed: int = 42
    size: int = Field(default=50, ge=1, le=5000)
    condition: str = "synthetic_diabetes"


class TrainRequest(BaseModel):
    seed: int = 42
    name: str = "synthetic-morphology-logistic"


def _guard(exc: Exception) -> HTTPException:
    return HTTPException(status_code=400, detail=str(exc))


@router.get("/api/simulations/models")
def models() -> dict:
    return {"models": REGISTRY.metadata(), "extensions": EXTENSION_POINTS}


@router.post("/api/simulations/run")
def run_simulation(
    body: SimulationRequest,
    user: User = Depends(current_user),
    session: Session = Depends(get_session),
) -> dict:
    try:
        model = REGISTRY.get(body.model)
        result = model.run(body.initial_state, body.parameters, body.duration, body.dt, body.seed)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ValueError, TypeError) as exc:
        raise _guard(exc) from exc
    payload = result.to_dict()
    session.add(
        SimulationRun(
            id=new_id(),
            model_name=result.model_name,
            model_version=result.model_version,
            seed=body.seed,
            result_json={"summary": _shrink(payload)},
        )
    )
    session.commit()
    return payload


@router.post("/api/patients/generate")
def patients(
    body: PatientRequest,
    user: User = Depends(current_user),
    workspace: Workspace = Depends(current_workspace),
    session: Session = Depends(get_session),
) -> dict:
    try:
        record = generate_virtual_patient(body.seed, body.condition)
    except ValueError as exc:
        raise _guard(exc) from exc
    session.add(VirtualPatient(id=new_id(), workspace_id=workspace.id, seed=body.seed, record_json=record))
    session.commit()
    return record


@router.post("/api/populations/generate")
def populations(
    body: PopulationRequest,
    workspace: Workspace = Depends(current_workspace),
    session: Session = Depends(get_session),
) -> dict:
    try:
        record = generate_population(body.seed, body.size, body.condition)
    except ValueError as exc:
        raise _guard(exc) from exc
    summary = {
        "label": record["label"],
        "disclaimer": record["disclaimer"],
        "seed": record["seed"],
        "size": record["size"],
        "condition": record["condition"],
        "summary": record["summary"],
        "sample": record["patients"][:12],
    }
    session.add(
        VirtualPopulation(
            id=new_id(),
            workspace_id=workspace.id,
            seed=body.seed,
            size=body.size,
            summary_json=record["summary"],
        )
    )
    session.commit()
    return summary


@router.post("/api/ml/train")
def train(
    body: TrainRequest,
    workspace: Workspace = Depends(current_workspace),
    session: Session = Depends(get_session),
) -> dict:
    trained = train_morphology_classifier(body.seed)
    trained.pop("predict", None)
    model = StoredModel(id=new_id(), workspace_id=workspace.id, name=body.name, framework="numpy")
    session.add(model)
    session.add(
        ModelVersion(
            id=new_id(),
            model_id=model.id,
            version="0.1.0",
            features_json={"inputs": ["t_wave_mean"]},
            config_json={"epochs": 200, "seed": body.seed},
            metrics_json=trained["metrics"],
            seed=body.seed,
        )
    )
    session.commit()
    return {"model_id": model.id, "label": "MODEL PREDICTION", "training_data": "SYNTHETIC DATA", **trained}


@router.get("/api/ml/models")
def list_models(workspace: Workspace = Depends(current_workspace), session: Session = Depends(get_session)) -> dict:
    rows = session.query(StoredModel).filter(StoredModel.workspace_id == workspace.id).all()
    return {"models": [{"id": row.id, "name": row.name, "framework": row.framework} for row in rows]}


@router.post("/api/ml/predict")
def predict(body: dict, user: User = Depends(current_user)) -> dict:
    feature = body.get("t_wave_mean")
    if not isinstance(feature, (int, float)):
        raise HTTPException(status_code=400, detail="t_wave_mean is required.")
    trained = train_morphology_classifier(int(body.get("seed", 42)))
    prediction = trained["predict"](float(feature))
    return {"prediction": prediction, "metrics": trained["metrics"], "label": "MODEL PREDICTION"}


def _shrink(payload: dict) -> dict:
    results = payload.get("results", {})
    return {
        "model_name": payload.get("model_name"),
        "observables": payload.get("observables"),
        "n_timepoints": len(results.get("time", [])),
        "validation": payload.get("validation"),
    }
