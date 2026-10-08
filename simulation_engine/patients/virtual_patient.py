"""Seeded synthetic patient generator.

Every record is labeled synthetic. Nothing here is a real person.
"""

from __future__ import annotations

import math
import uuid

import numpy as np

from simulation_engine.core.labels import SIMULATION_BANNER, SYNTHETIC_DATA


def _clip(rng_value: float, low: float, high: float) -> float:
    return float(min(max(rng_value, low), high))


def generate_virtual_patient(seed: int, condition: str = "unspecified") -> dict:
    if condition not in {"unspecified", "synthetic_diabetes"}:
        raise ValueError("condition must be 'unspecified' or 'synthetic_diabetes'.")
    rng = np.random.default_rng(int(seed))
    sex = str(rng.choice(["female", "male", "unspecified"]))
    age = int(rng.integers(18, 86))
    height = _clip(float(rng.normal(170, 8)), 150, 200)
    weight = _clip(float(rng.normal(78, 12)), 48, 140)
    bmi = weight / (height / 100.0) ** 2
    if condition == "synthetic_diabetes":
        glucose = _clip(float(rng.normal(158, 18)), 110, 280)
    else:
        glucose = _clip(float(rng.normal(92, 8)), 70, 140)
    heart_rate = _clip(float(rng.normal(74, 8)), 52, 110)
    systolic = _clip(float(rng.normal(126, 10)), 100, 170)
    diastolic = _clip(float(rng.normal(78, 6)), 60, min(100, systolic - 20))
    stroke_volume = _clip(70.0 * (weight / 70.0) ** 0.5 + float(rng.normal(0, 3)), 45, 120)
    respiratory_rate = _clip(float(rng.normal(14, 1.5)), 10, 22)
    return {
        "id": f"pt_{uuid.uuid5(uuid.NAMESPACE_URL, f'aeon7080:{seed}:{condition}').hex[:12]}",
        "label": SYNTHETIC_DATA,
        "disclaimer": SIMULATION_BANNER,
        "seed": int(seed),
        "condition": condition,
        "age": age,
        "sex": sex,
        "height_cm": round(height, 1),
        "weight_kg": round(weight, 1),
        "bmi": round(bmi, 2),
        "glucose_mg_dl": round(glucose, 1),
        "heart_rate_bpm": round(heart_rate, 1),
        "blood_pressure_mmhg": {
            "systolic": round(systolic, 1),
            "diastolic": round(diastolic, 1),
        },
        "stroke_volume_ml": round(stroke_volume, 1),
        "respiratory_rate_per_min": round(respiratory_rate, 1),
        "note": "Synthetic record generated from a seeded random draw. Not a patient.",
    }


def generate_population(seed: int, size: int, condition: str = "unspecified") -> dict:
    if not 1 <= size <= 5000:
        raise ValueError("population size must be from 1 to 5000.")
    rng = np.random.default_rng(int(seed))
    child_seeds = rng.integers(0, 2**31 - 1, size=size)
    patients = [generate_virtual_patient(int(s), condition) for s in child_seeds]
    glucose = np.array([p["glucose_mg_dl"] for p in patients])
    hr = np.array([p["heart_rate_bpm"] for p in patients])
    return {
        "label": SYNTHETIC_DATA,
        "disclaimer": SIMULATION_BANNER,
        "seed": int(seed),
        "size": size,
        "condition": condition,
        "patients": patients,
        "summary": {
            "glucose_mg_dl_mean": float(np.mean(glucose)),
            "glucose_mg_dl_std": float(np.std(glucose, ddof=1)) if size > 1 else 0.0,
            "heart_rate_bpm_mean": float(np.mean(hr)),
            "age_mean": float(np.mean([p["age"] for p in patients])),
            "bmi_mean": float(np.mean([p["bmi"] for p in patients])),
        },
    }


def bmi(weight_kg: float, height_cm: float) -> float:
    if height_cm <= 0 or weight_kg <= 0:
        raise ValueError("height and weight must be positive.")
    return weight_kg / (height_cm / 100.0) ** 2


def assert_finite_patient(patient: dict) -> None:
    if not math.isfinite(patient["bmi"]):
        raise ValueError("BMI is not finite.")
