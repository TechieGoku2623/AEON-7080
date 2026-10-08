"""Simplified respiratory bookkeeping.

Minute ventilation is RR × tidal volume.
The saturation index is an illustrative curve of ventilation, not SpO2.
"""

from __future__ import annotations

import numpy as np

from simulation_engine.core.base import SimulationModel
from simulation_engine.core.labels import SOFTWARE_VALIDATION
from simulation_engine.core.results import SimulationResult
from simulation_engine.core.specs import ParameterSpec


class RespiratoryModel(SimulationModel):
    name = "respiratory"
    version = "0.1.0"
    validation_status = SOFTWARE_VALIDATION
    solver_name = "algebraic evaluation on the time grid"

    def parameter_specs(self) -> list[ParameterSpec]:
        return [
            ParameterSpec("respiratory_rate_per_min", "1/min", "Respiratory rate", 4, 60),
            ParameterSpec("tidal_volume_l", "L", "Tidal volume", 0.1, 3),
            ParameterSpec("dead_space_l", "L", "Anatomical dead-space constant", 0.05, 0.5, default=0.15),
            ParameterSpec("reference_alveolar_l_min", "L/min", "Scale of the illustrative index", 0.5, 30, default=5),
        ]

    def run(self, initial_state, parameters, duration, dt, seed: int = 42) -> SimulationResult:
        self.parameters = self.validate_parameters(parameters)
        p = self.parameters
        steps = int(np.floor(duration / dt + 1e-9))
        t = np.linspace(0.0, steps * dt, steps + 1)
        rr = np.full_like(t, p["respiratory_rate_per_min"])
        ve = rr * p["tidal_volume_l"]
        va = np.maximum(rr * (p["tidal_volume_l"] - p["dead_space_l"]), 0.0)
        index = 1.0 - np.exp(-va / p["reference_alveolar_l_min"])
        result = self._pack(
            t,
            {
                "respiratory_rate_per_min": rr,
                "minute_ventilation_l_min": ve,
                "alveolar_ventilation_l_min": va,
                "illustrative_saturation_index": index,
            },
            duration,
            dt,
            seed,
        )
        result.units.update(
            {
                "minute_ventilation_l_min": "L/min",
                "alveolar_ventilation_l_min": "L/min",
                "illustrative_saturation_index": "dimensionless (not SpO2)",
            }
        )
        return result

    def get_observables(self) -> list[str]:
        return [
            "minute_ventilation_l_min",
            "alveolar_ventilation_l_min",
            "illustrative_saturation_index",
        ]

    def get_assumptions(self) -> list[str]:
        return [
            "Rate and tidal volume are constant.",
            "Dead space is a constant volume subtracted from each breath.",
        ]

    def get_limitations(self) -> list[str]:
        limits = super().get_limitations()
        limits.append(
            "illustrative_saturation_index is not an oxygen saturation, PaO2, or pulse-oximeter estimate."
        )
        return limits

    def get_equations(self) -> list[dict]:
        return [
            {"latex": r"V_E = RR \times V_T", "description": "Minute ventilation."},
            {
                "latex": r"V_A = RR \times \max(V_T - V_D, 0)",
                "description": "Alveolar ventilation with constant dead space.",
            },
            {
                "latex": r"I = 1 - e^{-V_A / V_{A,ref}}",
                "description": "Illustrative index only. Not SpO2.",
            },
        ]
