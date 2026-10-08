"""Common simulation interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from simulation_engine.core.results import SimulationResult
from simulation_engine.core.solver import integrate_rk4
from simulation_engine.core.specs import ParameterSpec, units_map, validate_parameters


class SimulationModel(ABC):
    name: str = "unnamed"
    version: str = "0.1.0"
    solver_name: str = "fixed-step RK4"
    validation_status: str = ""

    def __init__(self) -> None:
        self.parameters: dict = {}

    @abstractmethod
    def parameter_specs(self) -> list[ParameterSpec]:
        raise NotImplementedError

    def validate_parameters(self, parameters: dict) -> dict:
        return validate_parameters(parameters or {}, self.parameter_specs())

    def initialize(self, state: dict | None, parameters: dict) -> dict:
        self.parameters = self.validate_parameters(parameters)
        return dict(state or {})

    def step(self, state: dict, dt: float) -> dict:
        raise NotImplementedError(f"{self.name} does not implement step().")

    def run(
        self,
        initial_state: dict | None,
        parameters: dict,
        duration: float,
        dt: float,
        seed: int = 42,
    ) -> SimulationResult:
        state = self.initialize(initial_state, parameters)
        if duration < 0 or dt <= 0:
            raise ValueError("duration must be >= 0 and dt must be > 0.")
        if duration > 24 * 30:
            raise ValueError("duration exceeds the 30-day limit for this build.")
        t, _y = self._integrate(state, duration, dt)
        observables = self._observe_trajectory(state, t)
        return self._pack(t, observables, duration, dt, seed)

    def _integrate(self, state: dict, duration: float, dt: float):
        y0 = self.state_vector(state)

        def derivative(t, y):
            return self.derivative(t, y)

        return integrate_rk4(derivative, y0, duration, dt)

    def state_vector(self, state: dict) -> np.ndarray:
        raise NotImplementedError

    def derivative(self, t: float, y: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def _observe_trajectory(self, state: dict, t: np.ndarray) -> dict:
        raise NotImplementedError

    def _pack(self, t, observables: dict, duration: float, dt: float, seed: int) -> SimulationResult:
        specs = self.parameter_specs()
        results = {"time": np.asarray(t, dtype=float), **observables}
        return SimulationResult(
            model_name=self.name,
            model_version=self.version,
            parameters=dict(self.parameters),
            units=units_map(specs),
            duration=float(duration),
            time_step=float(dt),
            random_seed=int(seed),
            assumptions=self.get_assumptions(),
            limitations=self.get_limitations(),
            results=results,
            equations=self.get_equations(),
            solver=self.solver_name,
            validation=self.validation_status,
            observables=self.get_observables(),
        )

    def get_observables(self) -> list[str]:
        return []

    def get_assumptions(self) -> list[str]:
        return []

    def get_limitations(self) -> list[str]:
        return [
            "This is a simplified computational model.",
            "It is not clinically validated.",
            "It must not be used for diagnosis, treatment, or dosing decisions.",
        ]

    def get_equations(self) -> list[dict]:
        return []

    def get_metadata(self) -> dict:
        specs = self.parameter_specs()
        return {
            "name": self.name,
            "version": self.version,
            "solver": self.solver_name,
            "validation": self.validation_status,
            "implemented": True,
            "parameters": [
                {
                    "name": spec.name,
                    "unit": spec.unit,
                    "description": spec.description,
                    "minimum": spec.minimum,
                    "maximum": spec.maximum,
                    "default": spec.default,
                }
                for spec in specs
            ],
            "observables": self.get_observables(),
            "assumptions": self.get_assumptions(),
            "limitations": self.get_limitations(),
            "equations": self.get_equations(),
            "labels": ["SIMPLIFIED COMPUTATIONAL MODEL"],
        }
