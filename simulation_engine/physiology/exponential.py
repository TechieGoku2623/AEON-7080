"""Analytically solvable decay, used to test the numerical solver.

dC/dt = -k C
C(t) = C0 exp(-k t)
"""

from __future__ import annotations

import numpy as np

from simulation_engine.core.base import SimulationModel
from simulation_engine.core.labels import SOFTWARE_VALIDATION
from simulation_engine.core.results import SimulationResult
from simulation_engine.core.specs import ParameterSpec


def analytical_decay(t, c0: float, k: float) -> np.ndarray:
    t = np.asarray(t, dtype=float)
    return c0 * np.exp(-k * t)


class ExponentialDecay(SimulationModel):
    name = "exponential_decay"
    version = "0.1.0"
    validation_status = SOFTWARE_VALIDATION

    def parameter_specs(self) -> list[ParameterSpec]:
        return [
            ParameterSpec("C0", "concentration", "Initial amount", 0, 1e9),
            ParameterSpec("k", "1/time", "First-order rate constant", 0, 1e3),
        ]

    def state_vector(self, state: dict) -> np.ndarray:
        return np.array([self.parameters["C0"]], dtype=float)

    def derivative(self, t: float, y: np.ndarray) -> np.ndarray:
        return np.array([-self.parameters["k"] * y[0]])

    def step(self, state: dict, dt: float) -> dict:
        self.parameters = self.validate_parameters({**self.parameters, **state.get("parameters", {})})
        c0 = float(state.get("C", self.parameters["C0"]))
        t = float(state.get("t", 0.0))
        y = self.derivative  # noqa: keep interface honest
        from simulation_engine.core.solver import rk4_step

        y2 = rk4_step(lambda _t, yv: np.array([-self.parameters["k"] * yv[0]]), t, np.array([c0]), dt)
        return {"t": t + dt, "C": float(y2[0])}

    def _observe_trajectory(self, state: dict, t: np.ndarray) -> dict:
        # The numerical trajectory is produced by the integrator in run().
        raise NotImplementedError

    def run(self, initial_state, parameters, duration, dt, seed: int = 42) -> SimulationResult:
        self.parameters = self.validate_parameters(parameters)
        from simulation_engine.core.solver import integrate_rk4

        def derivative(_t, y):
            return np.array([-self.parameters["k"] * y[0]])

        t, y = integrate_rk4(derivative, np.array([self.parameters["C0"]]), duration, dt)
        analytical = analytical_decay(t, self.parameters["C0"], self.parameters["k"])
        result = self._pack(
            t,
            {"C": y[:, 0], "C_analytical": analytical},
            duration,
            dt,
            seed,
        )
        result.results["max_abs_error"] = float(np.max(np.abs(y[:, 0] - analytical)))
        return result

    def get_observables(self) -> list[str]:
        return ["C", "C_analytical"]

    def get_assumptions(self) -> list[str]:
        return ["First-order decay with a constant rate.", "No inputs after t = 0."]

    def get_equations(self) -> list[dict]:
        return [
            {
                "latex": r"\frac{dC}{dt} = -k C",
                "description": "First-order decay.",
            },
            {
                "latex": r"C(t) = C_0 e^{-k t}",
                "description": "Analytical solution used for software checks.",
            },
        ]
