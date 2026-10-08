"""One-compartment pharmacokinetic models with analytical solutions."""

from __future__ import annotations

import numpy as np

from simulation_engine.core.base import SimulationModel
from simulation_engine.core.labels import SOFTWARE_VALIDATION
from simulation_engine.core.results import SimulationResult
from simulation_engine.core.solver import integrate_rk4
from simulation_engine.core.specs import ParameterSpec
from simulation_engine.pharmacology.equations import iv_bolus_concentration, oral_concentration


class OneCompartmentIV(SimulationModel):
    name = "pk_one_compartment_iv"
    version = "0.1.0"
    solver_name = "analytical solution; RK4 also implemented for checks"
    validation_status = SOFTWARE_VALIDATION

    def parameter_specs(self) -> list[ParameterSpec]:
        return [
            ParameterSpec("dose_mg", "mg", "IV bolus dose", 0, 1e6),
            ParameterSpec("cl_l_per_h", "L/h", "Clearance", 1e-6, 500),
            ParameterSpec("v_l", "L", "Volume", 1e-3, 500),
        ]

    def derivative(self, t: float, y: np.ndarray) -> np.ndarray:
        kel = self.parameters["cl_l_per_h"] / self.parameters["v_l"]
        return np.array([-kel * y[0]])

    def run(self, initial_state, parameters, duration, dt, seed: int = 42) -> SimulationResult:
        self.parameters = self.validate_parameters(parameters)
        p = self.parameters
        steps = int(np.floor(duration / dt + 1e-9))
        t = np.linspace(0.0, steps * dt, steps + 1)
        c0 = p["dose_mg"] / p["v_l"]
        _tn, y = integrate_rk4(self.derivative, np.array([c0]), duration, dt)
        analytical = iv_bolus_concentration(t, p["dose_mg"], p["cl_l_per_h"], p["v_l"])
        result = self._pack(
            t,
            {
                "concentration_mg_l": analytical,
                "concentration_rk4_mg_l": y[:, 0],
            },
            duration,
            dt,
            seed,
        )
        result.results["max_abs_error"] = float(np.max(np.abs(y[:, 0] - analytical)))
        result.units["concentration_mg_l"] = "mg/L"
        return result

    def get_observables(self) -> list[str]:
        return ["concentration_mg_l"]

    def get_assumptions(self) -> list[str]:
        return [
            "Instantaneous bolus into a single well-mixed compartment.",
            "First-order elimination with constant clearance and volume.",
        ]

    def get_equations(self) -> list[dict]:
        return [
            {"latex": r"\frac{dC}{dt} = -\frac{CL}{V} C", "description": "One-compartment IV."},
            {"latex": r"C(t) = \frac{Dose}{V} e^{-(CL/V) t}", "description": "Analytical solution."},
        ]


class OneCompartmentOral(SimulationModel):
    name = "pk_one_compartment_oral"
    version = "0.1.0"
    solver_name = "analytical solution"
    validation_status = SOFTWARE_VALIDATION

    def parameter_specs(self) -> list[ParameterSpec]:
        return [
            ParameterSpec("dose_mg", "mg", "Extravascular dose", 0, 1e6),
            ParameterSpec("ka_per_h", "1/h", "Absorption rate constant", 1e-4, 20),
            ParameterSpec("cl_l_per_h", "L/h", "Clearance", 1e-6, 500),
            ParameterSpec("v_l", "L", "Volume", 1e-3, 500),
            ParameterSpec("bioavailability", "fraction", "Bioavailability", 0, 1, default=1),
        ]

    def run(self, initial_state, parameters, duration, dt, seed: int = 42) -> SimulationResult:
        self.parameters = self.validate_parameters(parameters)
        p = self.parameters
        steps = int(np.floor(duration / dt + 1e-9))
        t = np.linspace(0.0, steps * dt, steps + 1)
        conc = oral_concentration(
            t, p["dose_mg"], p["ka_per_h"], p["cl_l_per_h"], p["v_l"], p["bioavailability"]
        )
        amount_gut = p["bioavailability"] * p["dose_mg"] * np.exp(-p["ka_per_h"] * t)
        result = self._pack(
            t,
            {"concentration_mg_l": conc, "gut_amount_mg": amount_gut},
            duration,
            dt,
            seed,
        )
        result.units["concentration_mg_l"] = "mg/L"
        result.units["gut_amount_mg"] = "mg"
        return result

    def get_observables(self) -> list[str]:
        return ["concentration_mg_l", "gut_amount_mg"]

    def get_assumptions(self) -> list[str]:
        return [
            "First-order absorption into one well-mixed compartment.",
            "No lag time and no saturable absorption.",
            "Constant clearance and volume.",
        ]

    def get_equations(self) -> list[dict]:
        return [
            {"latex": r"\frac{dA_g}{dt} = -k_a A_g", "description": "Gut amount."},
            {
                "latex": r"\frac{dA_c}{dt} = k_a A_g - \frac{CL}{V} A_c",
                "description": "Central amount.",
            },
            {
                "latex": r"C(t) = \frac{F \cdot Dose \cdot k_a}{V(k_a-k_{el})}(e^{-k_{el}t}-e^{-k_a t})",
                "description": "Analytical concentration when ka ≠ kel. The kel limit is used when they match.",
            },
        ]
