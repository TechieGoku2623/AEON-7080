"""Canonical simulation result records."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

import numpy as np

from simulation_engine.core.labels import (
    SIMPLIFIED_MODEL,
    SIMULATION_BANNER,
    SOFTWARE_VERSION,
)


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    if isinstance(value, np.ndarray):
        return jsonable(value.tolist())
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, float):
        if np.isnan(value) or np.isinf(value):
            raise ValueError("Non-finite numeric result.")
        return value
    return value


@dataclass
class SimulationResult:
    model_name: str
    model_version: str
    parameters: dict
    units: dict
    duration: float
    time_step: float
    random_seed: int
    assumptions: list[str]
    limitations: list[str]
    results: dict
    uncertainty: dict = field(default_factory=dict)
    created_at: str = ""
    equations: list[dict] = field(default_factory=list)
    solver: str = ""
    validation: str = ""
    labels: list[str] = field(default_factory=lambda: [SIMULATION_BANNER, SIMPLIFIED_MODEL])
    software_version: str = SOFTWARE_VERSION
    observables: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return jsonable(asdict(self))
