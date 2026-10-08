"""Unit conversions. Original and converted values are both returned."""

from __future__ import annotations

GLUCOSE_MGDL_PER_MMOLL = 18.0182

CONVERSIONS = {
    ("mg", "g"): 0.001,
    ("g", "mg"): 1000.0,
    ("g", "kg"): 0.001,
    ("kg", "g"): 1000.0,
    ("mg", "kg"): 1e-6,
    ("kg", "mg"): 1e6,
    ("mL", "L"): 0.001,
    ("L", "mL"): 1000.0,
    ("seconds", "minutes"): 1 / 60,
    ("minutes", "seconds"): 60,
    ("minutes", "hours"): 1 / 60,
    ("hours", "minutes"): 60,
    ("seconds", "hours"): 1 / 3600,
    ("hours", "seconds"): 3600,
    ("mg/dL", "mmol/L"): 1 / GLUCOSE_MGDL_PER_MMOLL,
    ("mmol/L", "mg/dL"): GLUCOSE_MGDL_PER_MMOLL,
}


def convert(value: float, from_unit: str, to_unit: str) -> dict:
    if from_unit == to_unit:
        factor = 1.0
    else:
        try:
            factor = CONVERSIONS[(from_unit, to_unit)]
        except KeyError as exc:
            raise ValueError(f"No conversion from {from_unit} to {to_unit}.") from exc
    original = float(value)
    return {
        "original": original,
        "original_unit": from_unit,
        "converted": original * factor,
        "converted_unit": to_unit,
        "factor": factor,
        "note": "Glucose mg/dL ↔ mmol/L uses 18.0182, the conventional factor for glucose.",
    }
