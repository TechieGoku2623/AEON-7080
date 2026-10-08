"""Heuristic data-quality score.

The score is not a clinical-quality certification.
"""

from __future__ import annotations

import pandas as pd


IMPOSSIBLE = {
    "age": (0, 120),
    "heart_rate": (20, 240),
    "hr": (20, 240),
    "glucose": (20, 800),
    "glucose_mg_dl": (20, 800),
    "weight": (1, 400),
    "weight_kg": (1, 400),
    "height": (30, 250),
    "height_cm": (30, 250),
    "systolic": (40, 300),
    "diastolic": (20, 200),
}


def quality_report(frame: pd.DataFrame, profile: dict) -> dict:
    deductions = []
    score = 100.0
    missing = float(profile["missing_fraction"])
    if missing:
        penalty = min(40.0, missing * 100)
        score -= penalty
        deductions.append(f"Missing values reduced the score by {penalty:.1f}.")
    if profile["rows"]:
        dup_rate = profile["duplicate_rows"] / profile["rows"]
        if dup_rate:
            penalty = min(20.0, dup_rate * 40)
            score -= penalty
            deductions.append(f"Duplicate rows reduced the score by {penalty:.1f}.")
    impossible = 0
    checked = 0
    for column in frame.columns:
        key = str(column).strip().lower()
        if key not in IMPOSSIBLE or not pd.api.types.is_numeric_dtype(frame[column]):
            continue
        low, high = IMPOSSIBLE[key]
        series = pd.to_numeric(frame[column], errors="coerce")
        checked += int(series.notna().sum())
        impossible += int(((series < low) | (series > high)).sum())
    if impossible:
        penalty = min(25.0, 25.0 * impossible / max(checked, 1))
        score -= penalty
        deductions.append(
            f"{impossible} values fell outside broad physiological bookkeeping bounds (-{penalty:.1f})."
        )
    score = max(0.0, min(100.0, score))
    return {
        "score": round(score, 1),
        "label": "Heuristic data-quality score. Not a clinical-quality certification.",
        "deductions": deductions or ["No deductions from the implemented checks."],
        "impossible_value_count": impossible,
    }
