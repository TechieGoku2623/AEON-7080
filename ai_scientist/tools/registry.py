"""Allowlisted tools. There is no shell, filesystem, or Python tool."""

from __future__ import annotations

TOOL_NAMES = (
    "create_virtual_patient",
    "generate_population",
    "run_physiology_simulation",
    "run_pkpd_simulation",
    "run_disease_model",
    "run_monte_carlo",
    "generate_ecg",
    "analyze_signal",
    "run_ml_model",
    "analyze_dataset",
    "run_statistical_summary",
    "compare_experiments",
    "sensitivity_analysis",
    "generate_report",
)

FORBIDDEN = {"python", "shell", "bash", "sql", "exec", "eval", "filesystem"}


def assert_allowed(name: str) -> None:
    if name in FORBIDDEN or name not in TOOL_NAMES:
        raise PermissionError(f"Tool '{name}' is not allowlisted.")
