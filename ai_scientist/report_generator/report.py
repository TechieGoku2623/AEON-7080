"""Reports quote stored results. They do not invent citations."""

from __future__ import annotations


def render_report(config: dict, payload: dict) -> str:
    drugs = payload.get("drugs", {})
    lines = [
        "# AEON 7080 computational report",
        "",
        "SIMULATION RESULT — NOT CLINICAL EVIDENCE, DIAGNOSIS, OR MEDICAL ADVICE.",
        "",
        "## 1. Title",
        config.get("title") or "Hypothetical computational comparison",
        "",
        "## 2. Research question",
        "How do two hypothetical parameter sets differ inside the simplified PK/PD model?",
        "",
        "## 3. Hypothesis",
        payload.get("hypothesis", {}).get("hypothesis", ""),
        "",
        "## 4. Data",
        _data_section(payload),
        "",
        "## 5. Virtual population",
        _population_section(payload),
        "",
        "## 6. Methods",
        "Oral one-compartment pharmacokinetics, an indirect glucose response, "
        "optional heart-rate scaling, Monte Carlo or population spread, and one-at-a-time sensitivity.",
        "",
        "## 7. Models",
        ", ".join(f"{name} {version}" for name, version in payload.get("model_versions", {}).items()),
        "",
        "## 8. Equations",
    ]
    for equation in payload.get("equations", []):
        lines.append(f"- {equation.get('latex')} — {equation.get('description')}")
    lines.extend(["", "## 9. Parameters"])
    for name, drug in drugs.items():
        lines.append(f"- {name}: `{drug.get('parameters')}`")
    lines.extend(
        [
            "",
            "## 10. Simulation configuration",
            f"Seed {payload.get('seed')}. Mode {payload.get('mode')}. Software {payload.get('software_version')}.",
            "",
            "## 11. Results",
        ]
    )
    for name, drug in drugs.items():
        endpoints = drug.get("endpoints", {})
        lines.append(
            f"- {name}: glucose nadir change = {endpoints.get('glucose_nadir_delta_mg_dl')} mg/dL; "
            f"12 h change = {endpoints.get('glucose_delta_12h_mg_dl')} mg/dL; "
            f"Cmax = {endpoints.get('cmax_mg_l')} mg/L."
        )
    lines.extend(["", "## 12. Uncertainty"])
    for name, drug in drugs.items():
        summary = (drug.get("monte_carlo") or {}).get("endpoint_summary") or {}
        if summary:
            lines.append(
                f"- {name} {drug['monte_carlo'].get('endpoint')}: "
                f"mean {summary.get('mean')}, p05 {summary.get('p05')}, p95 {summary.get('p95')}, n {summary.get('n')}."
            )
        note = (drug.get("monte_carlo") or {}).get("interpretation")
        if note:
            lines.append(f"  {note}")
    lines.extend(["", "## 13. Sensitivity analysis"])
    for name, drug in drugs.items():
        bars = (drug.get("sensitivity") or {}).get("bars") or []
        if not bars:
            lines.append(f"- {name}: not run in this mode.")
            continue
        top = bars[0]
        lines.append(
            f"- {name}: largest OAT swing was {top['parameter']} "
            f"({top['low_output']:.3f} to {top['high_output']:.3f})."
        )
    lines.extend(
        [
            "",
            "## 14. Interpretation",
            payload.get("explanation", ""),
            "",
            "## 15. Limitations",
        ]
    )
    for item in payload.get("limitations", []):
        lines.append(f"- {item}")
    repro = payload.get("reproducibility") or {}
    lines.extend(
        [
            "",
            "## 16. Reproducibility",
            f"Fingerprint {repro.get('config_fingerprint')}.",
            repro.get("replay", ""),
            "",
            "## 17. References",
            "No external citations were retrieved. This report does not fabricate references.",
            "",
            "## 18. Safety disclaimer",
            "SIMULATION RESULT — NOT CLINICAL EVIDENCE, DIAGNOSIS, OR MEDICAL ADVICE.",
            "MODEL PREDICTION labels apply only to the synthetic morphology classifier.",
            "SYNTHETIC DATA labels apply to generated patients, waveforms, and training rows.",
            "SIMPLIFIED COMPUTATIONAL MODEL: equations and constants are illustrative.",
        ]
    )
    return "\n".join(lines) + "\n"


def _data_section(payload: dict) -> str:
    if payload.get("dataset"):
        return f"User dataset {payload['dataset']} was used where a confirmed mapping supplied parameters."
    return "No user dataset. Inputs are synthetic or user-entered parameters."


def _population_section(payload: dict) -> str:
    population = payload.get("population")
    if not population:
        patient = payload.get("patient") or {}
        if not patient:
            return "No population was generated."
        return (
            f"One synthetic record, seed {patient.get('seed')}, "
            f"age {patient.get('age')}, glucose {patient.get('glucose_mg_dl')} mg/dL. SYNTHETIC DATA."
        )
    summary = population["summary"]
    return (
        f"SYNTHETIC DATA. n={population['size']}, condition={population['condition']}, "
        f"mean glucose {summary['glucose_mg_dl_mean']:.2f} mg/dL."
    )
