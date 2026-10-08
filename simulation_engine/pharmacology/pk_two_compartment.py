"""Two-compartment IV bolus integrated with fixed-step RK4.

dA1/dt = -(CL/V1 + Q/V1) A1 + (Q/V2) A2
dA2/dt = (Q/V1) A1 - (Q/V2) A2
C = A1 / V1
"""

from __future__ import annotations

import numpy as np

from simulation_engine.core.base import SimulationModel
from simulation_engine.core.labels import SOFTWARE_VALIDATION
from simulation_engine.core.results import SimulationResult
from simulation_engine.core.solver import integrate_rk4, integrate_scipy
from simulation_engine.core.specs import ParameterSpec


class TwoCompartmentIV(SimulationModel):
    name = "pk_two_compartment_iv"
    version = "0.1.0"
    solver_name = "fixed-step RK4 (SciPy solve_ivp available for checks)"
    validation_status = SOFTWARE_VALIDATION

    def parameter_specs(self) -> list[ParameterSpec]:
        return [
            ParameterSpec("dose_mg", "mg", "IV bolus into the central compartment", 0, 1e6),
            ParameterSpec("cl_l_per_h", "L/h", "Elimination clearance", 1e-6, 500),
            ParameterSpec("v1_l", "L", "Central volume", 1e-3, 500),
            ParameterSpec("v2_l", "L", "Peripheral volume", 1e-3, 500),
            ParameterSpec("q_l_per_h", "L/h", "Intercompartmental clearance", 1e-6, 500),
        ]

    def derivative(self, t: float, y: np.ndarray) -> np.ndarray:
        p = self.parameters
        a1, a2 = y
        k10 = p["cl_l_per_h"] / p["v1_l"]
        k12 = p["q_l_per_h"] / p["v1_l"]
        k21 = p["q_l_per_h"] / p["v2_l"]
        return np.array([-(k10 + k12) * a1 + k21 * a2, k12 * a1 - k21 * a2])

    def run(self, initial_state, parameters, duration, dt, seed: int = 42) -> SimulationResult:
        self.parameters = self.validate_parameters(parameters)
        t, y = integrate_rk4(self.derivative, np.array([self.parameters["dose_mg"], 0.0]), duration, dt)
        conc = y[:, 0] / self.parameters["v1_l"]
        result = self._pack(
            t,
            {
                "concentration_mg_l": conc,
                "central_amount_mg": y[:, 0],
                "peripheral_amount_mg": y[:, 1],
            },
            duration,
            dt,
            seed,
        )
        result.units["concentration_mg_l"] = "mg/L"
        return result

    def scipy_concentration(self, parameters, duration: float, dt: float) -> tuple[np.ndarray, np.ndarray]:
        self.parameters = self.validate_parameters(parameters)
        steps = int(np.floor(duration / dt + 1e-9))
        t = np.linspace(0.0, steps * dt, steps + 1)
        y = integrate_scipy(self.derivative, np.array([self.parameters["dose_mg"], 0.0]), t)
        return t, y[:, 0] / self.parameters["v1_l"]

    def get_observables(self) -> list[str]:
        return ["concentration_mg_l", "central_amount_mg", "peripheral_amount_mg"]

    def get_assumptions(self) -> list[str]:
        return [
            "Linear two-compartment mammillary model.",
            "Bolus enters only the central compartment.",
            "Elimination occurs only from the central compartment.",
        ]

    def get_equations(self) -> list[dict]:
        return [
            {
                "latex": r"\frac{dA_1}{dt} = -(CL/V_1 + Q/V_1) A_1 + (Q/V_2) A_2",
                "description": "Central amount.",
            },
            {
                "latex": r"\frac{dA_2}{dt} = (Q/V_1) A_1 - (Q/V_2) A_2",
                "description": "Peripheral amount.",
            },
            {"latex": r"C = A_1 / V_1", "description": "Observed central concentration."},
        ]
