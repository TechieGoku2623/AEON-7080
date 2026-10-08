"""Textbook SIR and SEIR models on an abstract population.

These are not forecasts for a named pathogen.
"""

from __future__ import annotations

import numpy as np

from simulation_engine.core.base import SimulationModel
from simulation_engine.core.labels import SOFTWARE_VALIDATION
from simulation_engine.core.results import SimulationResult
from simulation_engine.core.solver import integrate_rk4
from simulation_engine.core.specs import ParameterSpec


class SIRModel(SimulationModel):
    name = "sir"
    version = "0.1.0"
    validation_status = SOFTWARE_VALIDATION

    def parameter_specs(self) -> list[ParameterSpec]:
        return [
            ParameterSpec("beta_per_day", "1/day", "Transmission coefficient", 0, 5),
            ParameterSpec("gamma_per_day", "1/day", "Recovery coefficient", 1e-4, 5),
            ParameterSpec("s0", "fraction", "Initial susceptible fraction", 0, 1),
            ParameterSpec("i0", "fraction", "Initial infectious fraction", 0, 1),
            ParameterSpec("r0", "fraction", "Initial removed fraction", 0, 1, default=0),
        ]

    def validate_parameters(self, parameters: dict) -> dict:
        cleaned = super().validate_parameters(parameters)
        total = cleaned["s0"] + cleaned["i0"] + cleaned["r0"]
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"s0 + i0 + r0 must equal 1 (got {total}).")
        return cleaned

    def derivative(self, t: float, y: np.ndarray) -> np.ndarray:
        s, i, r = y
        beta = self.parameters["beta_per_day"]
        gamma = self.parameters["gamma_per_day"]
        return np.array([-beta * s * i, beta * s * i - gamma * i, gamma * i])

    def run(self, initial_state, parameters, duration, dt, seed: int = 42) -> SimulationResult:
        self.parameters = self.validate_parameters(parameters)
        p = self.parameters
        t, y = integrate_rk4(self.derivative, np.array([p["s0"], p["i0"], p["r0"]]), duration, dt)
        result = self._pack(
            t,
            {"susceptible": y[:, 0], "infectious": y[:, 1], "removed": y[:, 2]},
            duration,
            dt,
            seed,
        )
        result.results["compartment_sum_error"] = float(np.max(np.abs(y.sum(axis=1) - 1.0)))
        result.results["basic_reproduction_number"] = float(p["beta_per_day"] / p["gamma_per_day"])
        return result

    def get_observables(self) -> list[str]:
        return ["susceptible", "infectious", "removed"]

    def get_assumptions(self) -> list[str]:
        return [
            "Closed, well-mixed abstract population.",
            "Constant transmission and recovery coefficients.",
            "No births, deaths, or interventions unless the coefficients are edited by the user.",
        ]

    def get_limitations(self) -> list[str]:
        limits = super().get_limitations()
        limits.append("This is not a forecast and is not tied to a named organism.")
        return limits

    def get_equations(self) -> list[dict]:
        return [
            {"latex": r"\frac{dS}{dt} = -\beta S I", "description": "Susceptible."},
            {"latex": r"\frac{dI}{dt} = \beta S I - \gamma I", "description": "Infectious."},
            {"latex": r"\frac{dR}{dt} = \gamma I", "description": "Removed."},
            {"latex": r"R_0 = \beta / \gamma", "description": "Basic reproduction number of this model."},
        ]


class SEIRModel(SimulationModel):
    name = "seir"
    version = "0.1.0"
    validation_status = SOFTWARE_VALIDATION

    def parameter_specs(self) -> list[ParameterSpec]:
        return [
            ParameterSpec("beta_per_day", "1/day", "Transmission coefficient", 0, 5),
            ParameterSpec("sigma_per_day", "1/day", "Progression from exposed", 1e-4, 5),
            ParameterSpec("gamma_per_day", "1/day", "Recovery coefficient", 1e-4, 5),
            ParameterSpec("s0", "fraction", "Initial susceptible fraction", 0, 1),
            ParameterSpec("e0", "fraction", "Initial exposed fraction", 0, 1),
            ParameterSpec("i0", "fraction", "Initial infectious fraction", 0, 1),
            ParameterSpec("r0", "fraction", "Initial removed fraction", 0, 1, default=0),
        ]

    def validate_parameters(self, parameters: dict) -> dict:
        cleaned = super().validate_parameters(parameters)
        total = cleaned["s0"] + cleaned["e0"] + cleaned["i0"] + cleaned["r0"]
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"compartment fractions must sum to 1 (got {total}).")
        return cleaned

    def derivative(self, t: float, y: np.ndarray) -> np.ndarray:
        s, e, i, _r = y
        beta = self.parameters["beta_per_day"]
        sigma = self.parameters["sigma_per_day"]
        gamma = self.parameters["gamma_per_day"]
        return np.array(
            [-beta * s * i, beta * s * i - sigma * e, sigma * e - gamma * i, gamma * i]
        )

    def run(self, initial_state, parameters, duration, dt, seed: int = 42) -> SimulationResult:
        self.parameters = self.validate_parameters(parameters)
        p = self.parameters
        t, y = integrate_rk4(
            self.derivative, np.array([p["s0"], p["e0"], p["i0"], p["r0"]]), duration, dt
        )
        result = self._pack(
            t,
            {
                "susceptible": y[:, 0],
                "exposed": y[:, 1],
                "infectious": y[:, 2],
                "removed": y[:, 3],
            },
            duration,
            dt,
            seed,
        )
        result.results["compartment_sum_error"] = float(np.max(np.abs(y.sum(axis=1) - 1.0)))
        return result

    def get_observables(self) -> list[str]:
        return ["susceptible", "exposed", "infectious", "removed"]

    def get_assumptions(self) -> list[str]:
        return [
            "Closed, well-mixed abstract population with a latent exposed compartment.",
            "Constant coefficients.",
        ]

    def get_limitations(self) -> list[str]:
        limits = super().get_limitations()
        limits.append("This is not a forecast and is not tied to a named organism.")
        return limits

    def get_equations(self) -> list[dict]:
        return [
            {"latex": r"\frac{dS}{dt}=-\beta S I", "description": "Susceptible."},
            {"latex": r"\frac{dE}{dt}=\beta S I - \sigma E", "description": "Exposed."},
            {"latex": r"\frac{dI}{dt}=\sigma E - \gamma I", "description": "Infectious."},
            {"latex": r"\frac{dR}{dt}=\gamma I", "description": "Removed."},
        ]
