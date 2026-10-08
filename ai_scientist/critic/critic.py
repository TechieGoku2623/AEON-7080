"""Scientific critic.

Flags problems and does not rewrite parameters.
"""

from __future__ import annotations

import re


class CritiqueError(ValueError):
    pass


def critique_config(config: dict) -> dict:
    flags = []
    for name, drug in config.get("interventions", {}).items():
        for key in ("dose_mg", "ka_per_h", "cl_l_per_h", "v_l", "ec50_mg_l"):
            if key in drug and float(drug[key]) < 0:
                flags.append(f"{name}.{key} is negative ({drug[key]}). The value was not changed.")
        if "emax" in drug and not 0 <= float(drug["emax"]) <= 0.95:
            flags.append(f"{name}.emax={drug['emax']} is outside [0, 0.95]. The value was not changed.")
        if "bioavailability" in drug and not 0 <= float(drug["bioavailability"]) <= 1:
            flags.append(f"{name}.bioavailability is outside [0, 1]. The value was not changed.")
    if int(config.get("seed", 0)) == 0 and "seed" not in config:
        flags.append("No random seed was set.")
    n = int(config.get("monte_carlo", {}).get("n", 1))
    if n > 10000:
        flags.append(f"Monte Carlo n={n} exceeds the limit of 10000.")
    status = "fail" if flags else "pass"
    return {"status": status, "flags": flags, "changed_parameters": False}


def critique_result(config: dict, payload: dict, explanation: str) -> dict:
    flags = list(critique_config(config)["flags"])
    if "reproducibility" not in payload:
        flags.append("The result has no reproducibility record.")
    for drug in payload.get("drugs", {}).values():
        if "monte_carlo" not in drug:
            flags.append("A drug result is missing an uncertainty summary.")
    if _claims_clinical_effect(explanation):
        flags.append("The explanation used clinical-effect language. Treat it as unsupported.")
    if payload.get("labels") and not any("NOT CLINICAL" in label for label in payload["labels"]):
        flags.append("The clinical-evidence banner is missing.")
    status = "fail" if any("negative" in flag or "exceeds" in flag for flag in flags) else ("warn" if flags else "pass")
    return {
        "status": status,
        "flags": flags,
        "changed_parameters": False,
        "checked": [
            "parameter ranges",
            "seed",
            "uncertainty",
            "clinical-claim language",
            "disclaimer banner",
        ],
    }


def critique_narrative(narrative: str, evidence_text: str) -> list[str]:
    """Flag numbers in an optional narration that never appear in the evidence."""

    flags = []
    evidence_numbers = set(re.findall(r"\d+(?:\.\d+)?", evidence_text))
    for number in re.findall(r"\d+(?:\.\d+)?", narrative):
        if number not in evidence_numbers and number not in {"0", "1", "12", "24"}:
            flags.append(f"Narration contains {number}, which is not in the tool evidence.")
            break
    return flags


def _claims_clinical_effect(text: str) -> bool:
    lowered = text.lower()
    banned = ("clinically effective", "safe and effective", "patients improved", "recommended dose")
    return any(phrase in lowered for phrase in banned)
