"""Map dataset columns onto computational parameters.

Suggestions are not applied unless the caller sets confirmed=True.
"""

from __future__ import annotations

SYNONYMS = {
    "patient.age": ["age", "years", "patient_age"],
    "patient.weight_kg": ["weight", "wt", "body_weight", "weight_kg"],
    "patient.height_cm": ["height", "ht", "height_cm"],
    "physiology.glucose_mg_dl": ["glucose", "fasting_glucose", "glu", "fpg", "glucose_mg_dl"],
    "cardiovascular.heart_rate_bpm": ["heart_rate", "hr", "pulse", "bpm", "heart_rate_bpm"],
    "cardiovascular.systolic_mmhg": ["sbp", "systolic", "systolic_bp", "systolic_mmhg"],
    "cardiovascular.diastolic_mmhg": ["dbp", "diastolic", "diastolic_bp", "diastolic_mmhg"],
}


def suggest_mapping(columns: list[str]) -> list[dict]:
    lookup = {column.lower(): column for column in columns}
    suggestions = []
    for target, names in SYNONYMS.items():
        for name in names:
            if name in lookup:
                suggestions.append(
                    {
                        "column": lookup[name],
                        "parameter": target,
                        "confidence": "name_match",
                        "confirmed": False,
                    }
                )
                break
    return suggestions


def apply_mapping(row: dict, mapping: list[dict], confirmed: bool) -> dict:
    if not confirmed:
        raise PermissionError("Mapping was not confirmed. AEON 7080 does not map data silently.")
    if not mapping:
        raise ValueError("No mapping was provided.")
    extracted = {}
    for item in mapping:
        if not item.get("confirmed", confirmed):
            continue
        column = item["column"]
        if column not in row:
            raise KeyError(f"Column '{column}' is not in the row.")
        extracted[item["parameter"]] = row[column]
    if not extracted:
        raise ValueError("No confirmed column mappings were applied.")
    return {
        "label": "DATA-CONDITIONED COMPUTATIONAL MODEL",
        "parameters": extracted,
        "note": "Values were copied from the confirmed mapping. They are not a diagnosis.",
    }
