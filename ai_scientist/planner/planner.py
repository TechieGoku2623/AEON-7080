"""Deterministic scientific planner.

Unsupported requests are rejected. The planner does not invent a study.
"""

from __future__ import annotations

from ai_scientist.tools.registry import TOOL_NAMES, assert_allowed


def plan_question(question: str) -> dict:
    text = " ".join(question.lower().split())
    if not text:
        return _unsupported("The question is empty.")
    if _wants_clinical_advice(text):
        return _unsupported(
            "AEON 7080 does not provide medical advice, diagnosis, or treatment recommendations."
        )
    if "compare" in text and any(word in text for word in ("treatment", "drug", "intervention")):
        condition = "synthetic_diabetes" if "diabet" in text else "unspecified"
        size = 1000 if any(word in text for word in ("population", "cohort", "patients")) else 1
        mode = "population" if size > 1 else "patient"
        steps = [
            "create_virtual_patient" if mode == "patient" else "generate_population",
            "run_pkpd_simulation",
            "run_monte_carlo",
            "sensitivity_analysis",
            "generate_ecg" if mode == "patient" else "run_statistical_summary",
            "run_ml_model" if mode == "patient" else "compare_experiments",
            "generate_report",
        ]
        for step in steps:
            assert_allowed(step)
        return {
            "supported": True,
            "objective": "compare simulated treatment response",
            "population": {"size": 1000 if mode == "population" else 1, "condition": condition},
            "interventions": ["Treatment_A", "Treatment_B"],
            "simulation": ["glucose", "insulin", "pkpd"],
            "analysis": ["mean_change", "variance", "monte_carlo", "sensitivity_analysis"],
            "mode": mode,
            "tools": steps,
            "notes": [
                "Treatment_A and Treatment_B are hypothetical parameter sets.",
                "The planner selected only allowlisted tools.",
            ],
        }
    if "virtual patient" in text or "synthetic patient" in text:
        return _simple("create_virtual_patient", "generate a synthetic patient", mode="patient")
    if "ecg" in text or "biosignal" in text:
        return _simple("generate_ecg", "generate a synthetic ECG", tools=["generate_ecg", "analyze_signal", "run_ml_model"])
    if "sir" in text or "seir" in text or "epidemi" in text:
        return _simple("run_physiology_simulation", "run an abstract SIR/SEIR model", tools=["run_physiology_simulation"])
    if "missing" in text or "correlat" in text or "dataset" in text or "glucose" in text and "variable" in text:
        return _simple("analyze_dataset", "analyze a user dataset with computed summaries", tools=["analyze_dataset"])
    if any(word in text for word in ("pk", "pharmaco", "glucose", "heart", "simulation")):
        return _simple("run_pkpd_simulation", "run a simplified physiological or PK/PD model")
    return _unsupported(
        "This build can compare hypothetical treatments, generate a synthetic patient, "
        "run PK/PD, ECG, SIR/SEIR, or analyze a loaded table. The question did not match those tools."
    )


def _simple(tool: str, objective: str, mode: str = "patient", tools: list[str] | None = None) -> dict:
    selected = tools or [tool]
    for name in selected:
        assert_allowed(name)
    return {
        "supported": True,
        "objective": objective,
        "population": {"size": 1, "condition": "unspecified"},
        "interventions": ["Treatment_A", "Treatment_B"] if tool == "run_pkpd_simulation" else [],
        "simulation": [tool],
        "analysis": [],
        "mode": mode,
        "tools": selected,
        "notes": ["Allowlisted tools only."],
    }


def _unsupported(reason: str) -> dict:
    return {
        "supported": False,
        "objective": None,
        "reason": reason,
        "tools": [],
        "notes": ["No simulation was run."],
    }


def _wants_clinical_advice(text: str) -> bool:
    phrases = (
        "should i take",
        "what dose should",
        "diagnose",
        "do i have",
        "prescribe",
        "medical advice",
        "is this cancer",
        "am i sick",
    )
    return any(phrase in text for phrase in phrases)


def supported_tools() -> list[str]:
    return list(TOOL_NAMES)
