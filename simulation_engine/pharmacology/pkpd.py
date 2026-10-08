"""Oral one-compartment PK coupled to an indirect glucose response.

For a constant concentration the glucose solution is analytical:

G(t) = G_inf + (G0 - G_inf) exp(-k_out t)
G_inf = G0 * (1 - E)
E = Emax * C / (EC50 + C)

Time-varying concentration uses fixed-step RK4.
"""

from __future__ import annotations

import numpy as np

from simulation_engine.core.base import SimulationModel
from simulation_engine.core.labels import SOFTWARE_VALIDATION
from simulation_engine.core.results import SimulationResult
from simulation_engine.core.solver import integrate_rk4
from simulation_engine.core.specs import ParameterSpec
from simulation_engine.pharmacology.equations import oral_concentration


def effect_fraction(concentration, emax, ec50) -> np.ndarray:
    concentration = np.asarray(concentration, dtype=float)
    return emax * concentration / (ec50 + concentration)


def analytical_constant_concentration(t, g0: float, kout: float, effect: float) -> np.ndarray:
    t = np.asarray(t, dtype=float)
    g_inf = g0 * (1.0 - effect)
    return g_inf + (g0 - g_inf) * np.exp(-kout * t)


class IndirectGlucosePD(SimulationModel):
    name = "pkpd_indirect_glucose"
    version = "0.1.0"
    solver_name = "analytical PK + fixed-step RK4 for glucose and insulin"
    validation_status = SOFTWARE_VALIDATION

    def parameter_specs(self) -> list[ParameterSpec]:
        return [
            ParameterSpec("dose_mg", "mg", "Extravascular dose", 0, 1e6),
            ParameterSpec("ka_per_h", "1/h", "Absorption rate", 1e-4, 20),
            ParameterSpec("cl_l_per_h", "L/h", "Clearance", 1e-6, 500),
            ParameterSpec("v_l", "L", "Volume", 1e-3, 500),
            ParameterSpec("bioavailability", "fraction", "Bioavailability", 0, 1, default=1),
            ParameterSpec("glucose_mg_dl", "mg/dL", "Baseline glucose", 40, 400),
            ParameterSpec("emax", "fraction", "Maximum inhibition of production", 0, 0.95),
            ParameterSpec("ec50_mg_l", "mg/L", "Concentration at half-maximum effect", 1e-4, 1e4),
            ParameterSpec("kout_per_h", "1/h", "Glucose loss rate", 1e-3, 5, default=0.45),
            ParameterSpec("insulin_mu_l", "illustrative mU/L", "Baseline insulin scale", 0, 200, default=8),
            ParameterSpec("k_insulin_per_h", "1/h", "Insulin return rate", 1e-3, 5, default=0.35),
            ParameterSpec("insulin_slope", "illustrative", "Glucose-driven insulin term", 0, 2, default=0.04),
            ParameterSpec("heart_rate_bpm", "bpm", "Baseline heart rate", 30, 220, default=72),
            ParameterSpec("hr_effect_bpm", "bpm", "Hypothetical added bpm at Cmax", -40, 40, default=0),
        ]

    def concentration(self, t: np.ndarray) -> np.ndarray:
        p = self.parameters
        return oral_concentration(
            t, p["dose_mg"], p["ka_per_h"], p["cl_l_per_h"], p["v_l"], p["bioavailability"]
        )

    def derivative(self, t: float, y: np.ndarray) -> np.ndarray:
        p = self.parameters
        conc = float(self.concentration(np.array([t]))[0])
        e = float(effect_fraction(conc, p["emax"], p["ec50_mg_l"]))
        kin = p["kout_per_h"] * p["glucose_mg_dl"]
        dg = kin * (1.0 - e) - p["kout_per_h"] * y[0]
        di = -p["k_insulin_per_h"] * (y[1] - p["insulin_mu_l"]) + p["insulin_slope"] * max(
            y[0] - p["glucose_mg_dl"], 0.0
        )
        return np.array([dg, di])

    def run(self, initial_state, parameters, duration, dt, seed: int = 42) -> SimulationResult:
        self.parameters = self.validate_parameters(parameters)
        p = self.parameters
        t, y = integrate_rk4(
            self.derivative,
            np.array([p["glucose_mg_dl"], p["insulin_mu_l"]]),
            duration,
            dt,
        )
        conc = self.concentration(t)
        cmax = float(np.max(conc)) if len(conc) else 0.0
        if cmax <= 1e-12:
            hr = np.full_like(t, p["heart_rate_bpm"])
        else:
            hr = p["heart_rate_bpm"] + p["hr_effect_bpm"] * (conc / cmax)
        result = self._pack(
            t,
            {
                "concentration_mg_l": conc,
                "glucose_mg_dl": y[:, 0],
                "insulin_mu_l": y[:, 1],
                "heart_rate_bpm": hr,
                "effect_fraction": effect_fraction(conc, p["emax"], p["ec50_mg_l"]),
            },
            duration,
            dt,
            seed,
        )
        result.units.update(
            {
                "concentration_mg_l": "mg/L",
                "glucose_mg_dl": "mg/dL",
                "insulin_mu_l": "illustrative mU/L",
                "heart_rate_bpm": "bpm",
                "effect_fraction": "fraction",
            }
        )
        return result

    def get_observables(self) -> list[str]:
        return ["concentration_mg_l", "glucose_mg_dl", "insulin_mu_l", "heart_rate_bpm"]

    def get_assumptions(self) -> list[str]:
        return [
            "The drug effect inhibits glucose production through an Emax function of concentration.",
            "Baseline production equals kout × baseline glucose, so glucose is steady when concentration is zero.",
            "Heart-rate change is an optional hypothetical parameter, not a predicted property of a real drug.",
            "PD constants are illustrative.",
        ]

    def get_equations(self) -> list[dict]:
        return [
            {
                "latex": r"E(C) = \frac{E_{max} C}{EC_{50} + C}",
                "description": "Fractional inhibition.",
            },
            {
                "latex": r"\frac{dG}{dt} = k_{in}(1-E(C)) - k_{out} G",
                "description": "Indirect response. kin = kout × G_baseline.",
            },
            {
                "latex": r"\frac{dI}{dt} = -k_i(I-I_{base}) + s \max(G-G_{base},0)",
                "description": "Illustrative insulin scale.",
            },
            {
                "latex": r"HR(t) = HR_0 + \Delta HR \cdot C(t)/C_{max}",
                "description": "Hypothetical rate shift supplied by the user.",
            },
        ]
