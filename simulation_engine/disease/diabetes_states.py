"""Map a simulated glucose trajectory to computational state labels.

The cut-points are parameters of this teaching model. They are not a diagnosis
and they are not a clinical staging system.
"""

from __future__ import annotations

import numpy as np

from simulation_engine.core.base import SimulationModel
from simulation_engine.core.labels import SOFTWARE_VALIDATION
from simulation_engine.core.results import SimulationResult
from simulation_engine.core.specs import ParameterSpec

STATE_ORDER = (
    "model_state_low",
    "model_state_baseline",
    "model_state_intermediate",
    "model_state_elevated",
)


def label_glucose(value: float, low: float, intermediate: float, elevated: float) -> str:
    if value < low:
        return "model_state_low"
    if value < intermediate:
        return "model_state_baseline"
    if value < elevated:
        return "model_state_intermediate"
    return "model_state_elevated"


class GlucoseStateModel(SimulationModel):
    name = "glucose_state"
    version = "0.1.0"
    solver_name = "threshold labeling of an input series"
    validation_status = SOFTWARE_VALIDATION

    def parameter_specs(self) -> list[ParameterSpec]:
        return [
            ParameterSpec("low_mg_dl", "mg/dL", "Lower teaching cut-point", 40, 120, default=70),
            ParameterSpec("intermediate_mg_dl", "mg/dL", "Intermediate teaching cut-point", 80, 180, default=110),
            ParameterSpec("elevated_mg_dl", "mg/dL", "Upper teaching cut-point", 100, 300, default=140),
        ]

    def validate_parameters(self, parameters: dict) -> dict:
        cleaned = super().validate_parameters(parameters)
        if not (
            cleaned["low_mg_dl"] < cleaned["intermediate_mg_dl"] < cleaned["elevated_mg_dl"]
        ):
            raise ValueError("Cut-points must increase: low < intermediate < elevated.")
        return cleaned

    def run(self, initial_state, parameters, duration, dt, seed: int = 42) -> SimulationResult:
        self.parameters = self.validate_parameters(parameters)
        series = (initial_state or {}).get("glucose_mg_dl")
        if series is None:
            raise ValueError("glucose_state requires initial_state.glucose_mg_dl.")
        glucose = np.asarray(series, dtype=float)
        p = self.parameters
        labels = [
            label_glucose(float(g), p["low_mg_dl"], p["intermediate_mg_dl"], p["elevated_mg_dl"])
            for g in glucose
        ]
        t = np.arange(len(glucose)) * dt
        result = self._pack(t, {"state": labels, "glucose_mg_dl": glucose}, duration, dt, seed)
        result.results["state_note"] = (
            "Computational state labels for a simplified model. Not a diagnosis or clinical stage."
        )
        return result

    def get_observables(self) -> list[str]:
        return ["state"]

    def get_assumptions(self) -> list[str]:
        return ["Labels depend only on the supplied glucose series and the three cut-points."]

    def get_limitations(self) -> list[str]:
        limits = super().get_limitations()
        limits.append("State names are not clinical stages and must not be read as a diagnosis.")
        return limits

    def get_equations(self) -> list[dict]:
        return [
            {
                "latex": r"s(G) = \mathrm{label}(G; \theta_{low}, \theta_{mid}, \theta_{high})",
                "description": "Piecewise labeling of simulated glucose.",
            }
        ]
