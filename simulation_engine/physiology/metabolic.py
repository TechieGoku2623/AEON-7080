"""Simplified glucose-insulin bookkeeping without a drug input.

dG/dt = -k_g (G - G_base)
dI/dt = -k_i (I - I_base) + s * max(G - G_base, 0)

Steady state is the supplied baseline. This is not the Bergman minimal model
and the constants are illustrative.
"""

from __future__ import annotations

import numpy as np

from simulation_engine.core.base import SimulationModel
from simulation_engine.core.labels import SOFTWARE_VALIDATION
from simulation_engine.core.results import SimulationResult
from simulation_engine.core.solver import integrate_rk4
from simulation_engine.core.specs import ParameterSpec


class GlucoseInsulinModel(SimulationModel):
    name = "glucose_insulin"
    version = "0.1.0"
    validation_status = SOFTWARE_VALIDATION

    def parameter_specs(self) -> list[ParameterSpec]:
        return [
            ParameterSpec("glucose_mg_dl", "mg/dL", "Baseline glucose", 40, 400),
            ParameterSpec("insulin_mu_l", "illustrative mU/L", "Baseline insulin scale", 0, 200, default=8),
            ParameterSpec("k_glucose_per_h", "1/h", "Glucose return rate", 1e-4, 5, default=0.4),
            ParameterSpec("k_insulin_per_h", "1/h", "Insulin return rate", 1e-4, 5, default=0.35),
            ParameterSpec("insulin_slope", "mU/L per mg/dL per h", "Illustrative glucose-driven insulin term", 0, 2, default=0.04),
        ]

    def derivative(self, t: float, y: np.ndarray) -> np.ndarray:
        p = self.parameters
        g, i = y
        dg = -p["k_glucose_per_h"] * (g - p["glucose_mg_dl"])
        di = -p["k_insulin_per_h"] * (i - p["insulin_mu_l"]) + p["insulin_slope"] * max(g - p["glucose_mg_dl"], 0.0)
        return np.array([dg, di])

    def run(self, initial_state, parameters, duration, dt, seed: int = 42) -> SimulationResult:
        self.parameters = self.validate_parameters(parameters)
        state = initial_state or {}
        g0 = float(state.get("glucose_mg_dl", self.parameters["glucose_mg_dl"]))
        i0 = float(state.get("insulin_mu_l", self.parameters["insulin_mu_l"]))
        t, y = integrate_rk4(self.derivative, np.array([g0, i0]), duration, dt)
        return self._pack(
            t,
            {"glucose_mg_dl": y[:, 0], "insulin_mu_l": y[:, 1]},
            duration,
            dt,
            seed,
        )

    def get_observables(self) -> list[str]:
        return ["glucose_mg_dl", "insulin_mu_l"]

    def get_assumptions(self) -> list[str]:
        return [
            "No meal, drug, or hormone input unless the initial state differs from baseline.",
            "Rates are illustrative constants, not fitted human parameters.",
        ]

    def get_equations(self) -> list[dict]:
        return [
            {
                "latex": r"\frac{dG}{dt} = -k_g (G - G_{base})",
                "description": "Glucose relaxes toward the supplied baseline.",
            },
            {
                "latex": r"\frac{dI}{dt} = -k_i (I - I_{base}) + s \max(G - G_{base}, 0)",
                "description": "Illustrative insulin scale.",
            },
        ]
