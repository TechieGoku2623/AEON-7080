"""Simplified cardiovascular bookkeeping.

CO = HR * SV
MAP = CO * SVR + CVP

Optional first-order heart-rate lag toward a commanded rate.
Not a circulatory or clinical blood-pressure model.
"""

from __future__ import annotations

import numpy as np

from simulation_engine.core.base import SimulationModel
from simulation_engine.core.labels import SOFTWARE_VALIDATION
from simulation_engine.core.results import SimulationResult
from simulation_engine.core.solver import integrate_rk4
from simulation_engine.core.specs import ParameterSpec


class CardiovascularModel(SimulationModel):
    name = "cardiovascular"
    version = "0.1.0"
    validation_status = SOFTWARE_VALIDATION

    def parameter_specs(self) -> list[ParameterSpec]:
        return [
            ParameterSpec("heart_rate_bpm", "bpm", "Initial heart rate", 30, 220),
            ParameterSpec("stroke_volume_ml", "mL", "Stroke volume, held constant", 20, 200),
            ParameterSpec("systolic_mmhg", "mmHg", "Used only to set the initial mean pressure", 70, 220),
            ParameterSpec("diastolic_mmhg", "mmHg", "Used only to set the initial mean pressure", 40, 140),
            ParameterSpec("hr_command_bpm", "bpm", "Heart rate the lag relaxes toward", 30, 220),
            ParameterSpec("tau_h", "h", "Heart-rate time constant", 1e-4, 10, default=0.01),
            ParameterSpec("cvp_mmhg", "mmHg", "Central venous pressure constant", 0, 20, default=5),
        ]

    def validate_parameters(self, parameters: dict) -> dict:
        cleaned = super().validate_parameters(parameters)
        if cleaned["systolic_mmhg"] <= cleaned["diastolic_mmhg"]:
            raise ValueError("systolic_mmhg must be greater than diastolic_mmhg.")
        return cleaned

    def derivative(self, t: float, y: np.ndarray) -> np.ndarray:
        tau = self.parameters["tau_h"]
        return np.array([(self.parameters["hr_command_bpm"] - y[0]) / tau])

    def run(self, initial_state, parameters, duration, dt, seed: int = 42) -> SimulationResult:
        self.parameters = self.validate_parameters(parameters)
        p = self.parameters
        t, y = integrate_rk4(self.derivative, np.array([p["heart_rate_bpm"]]), duration, dt)
        hr = y[:, 0]
        co_l_min = hr * p["stroke_volume_ml"] / 1000.0
        map0 = (p["systolic_mmhg"] + 2.0 * p["diastolic_mmhg"]) / 3.0
        co0 = p["heart_rate_bpm"] * p["stroke_volume_ml"] / 1000.0
        svr = (map0 - p["cvp_mmhg"]) / co0
        mean_pressure = co_l_min * svr + p["cvp_mmhg"]
        result = self._pack(
            t,
            {
                "heart_rate_bpm": hr,
                "cardiac_output_l_min": co_l_min,
                "mean_pressure_mmhg": mean_pressure,
                "svr_mmhg_min_l": np.full_like(hr, svr),
            },
            duration,
            dt,
            seed,
        )
        result.units.update(
            {
                "heart_rate_bpm": "bpm",
                "cardiac_output_l_min": "L/min",
                "mean_pressure_mmhg": "mmHg",
                "svr_mmhg_min_l": "mmHg·min/L",
            }
        )
        return result

    def get_observables(self) -> list[str]:
        return ["heart_rate_bpm", "cardiac_output_l_min", "mean_pressure_mmhg"]

    def get_assumptions(self) -> list[str]:
        return [
            "Stroke volume is constant.",
            "Vascular resistance is constant and set from the initial pressures.",
            "There is no baroreflex.",
            "Mean pressure uses MAP ≈ (SBP + 2·DBP) / 3 only to initialize resistance.",
        ]

    def get_equations(self) -> list[dict]:
        return [
            {"latex": r"CO = HR \times SV", "description": "Cardiac output from rate and stroke volume."},
            {"latex": r"MAP = CO \times SVR + CVP", "description": "Algebraic pressure with fixed resistance."},
            {
                "latex": r"\frac{dHR}{dt} = \frac{HR_{cmd} - HR}{\tau}",
                "description": "First-order lag toward the commanded rate.",
            },
        ]
