"""Execute a validated plan. One cycle. No autonomous loop."""

from __future__ import annotations

MAX_AUTONOMOUS_CYCLES = 1

from ai_scientist.planner.planner import plan_question
from ai_scientist.providers.base import configured_provider
from ai_scientist.researcher.researcher import retrieve
from ai_scientist.tools.registry import assert_allowed
from simulation_engine.pharmacology.drug_response import default_config, run_drug_response


def answer_question(question: str, config: dict | None = None) -> dict:
    plan = plan_question(question)
    if not plan["supported"]:
        return {
            "plan": plan,
            "executed": False,
            "result": None,
            "narrative": None,
            "references": retrieve(question, external_enabled=False),
            "cycles": 0,
        }
    result = execute_plan(plan, config)
    evidence = result.get("explanation", "")
    narrative = configured_provider().narrate(evidence)
    return {
        "plan": plan,
        "executed": True,
        "result": result,
        "narrative": narrative,
        "references": retrieve(question, external_enabled=False),
        "cycles": MAX_AUTONOMOUS_CYCLES,
        "loop": "Stopped after one cycle. A follow-up runs only when the user asks.",
    }


def execute_plan(plan: dict, config: dict | None = None) -> dict:
    if not plan.get("supported"):
        raise ValueError(plan.get("reason") or "Plan is not supported.")
    tools = list(plan.get("tools", []))
    for tool in tools:
        assert_allowed(tool)
    if tools == ["analyze_dataset"]:
        raise ValueError("Dataset questions run through the data analyst with a loaded table.")
    if tools == ["create_virtual_patient"]:
        from simulation_engine.patients.virtual_patient import generate_virtual_patient

        patient = generate_virtual_patient(int((config or {}).get("seed", 42)), "unspecified")
        return {
            "patient": patient,
            "explanation": (
                f"Generated one synthetic record, seed {patient['seed']}, "
                f"age {patient['age']}, glucose {patient['glucose_mg_dl']} mg/dL."
            ),
            "tools": [{"name": "create_virtual_patient", "status": "called"}],
            "labels": ["SYNTHETIC DATA", "SIMULATION RESULT — NOT CLINICAL EVIDENCE, DIAGNOSIS, OR MEDICAL ADVICE."],
        }
    if "run_pkpd_simulation" not in tools and "generate_ecg" in tools:
        from simulation_engine.biosignals.ecg import SyntheticECG

        result = SyntheticECG().run(None, {"heart_rate_bpm": 72, "noise_std": 0.01}, 10, 0.004, seed=42)
        return {
            "ecg": result.to_dict(),
            "explanation": "Generated a synthetic Gaussian-wave ECG at 72 bpm. It is not a rhythm interpretation.",
            "tools": [{"name": tool, "status": "called"} for tool in tools],
            "labels": result.labels,
        }
    if tools == ["run_physiology_simulation"]:
        from simulation_engine.epidemiology.sir import SIRModel

        result = SIRModel().run(
            None,
            {"beta_per_day": 0.5, "gamma_per_day": 0.2, "s0": 0.99, "i0": 0.01, "r0": 0.0},
            80,
            0.1,
            seed=42,
        )
        peak = max(result.results["infectious"])
        return {
            "simulation": result.to_dict(),
            "explanation": (
                f"Abstract SIR peak infectious fraction was {peak:.4f}. "
                "This is not a forecast for a named organism."
            ),
            "tools": [{"name": "run_physiology_simulation", "status": "called"}],
            "labels": result.labels,
        }
    cfg = default_config()
    if config:
        cfg.update({k: v for k, v in config.items() if k != "interventions"})
        if "interventions" in config:
            cfg["interventions"] = config["interventions"]
    if plan.get("mode") == "population":
        cfg["mode"] = "population"
        cfg["population_size"] = int(plan["population"]["size"])
        cfg["condition"] = plan["population"]["condition"]
        cfg["monte_carlo"] = {"n": min(1000, int(plan["population"]["size"])), "cv": 0.2}
    elif plan.get("population", {}).get("condition"):
        cfg["condition"] = plan["population"]["condition"]
    # Interactive default stays smaller when the caller did not ask for a population.
    if plan.get("mode") == "patient" and "monte_carlo" not in (config or {}):
        cfg["monte_carlo"] = {"n": 200, "cv": 0.2}
    result = run_drug_response(cfg, include_waveforms=cfg["mode"] == "patient")
    result["tools"] = [
        {"name": tool, "status": "called" if _tool_used(tool, result) else "covered_by_drug_response"}
        for tool in plan["tools"]
    ]
    return result


def _tool_used(tool: str, result: dict) -> bool:
    if tool in {"run_pkpd_simulation", "compare_experiments", "generate_report"}:
        return True
    if tool in {"create_virtual_patient", "generate_population"}:
        return bool(result.get("patient") or result.get("population"))
    if tool == "run_monte_carlo":
        return True
    if tool == "sensitivity_analysis":
        return any((drug.get("sensitivity") or {}).get("bars") for drug in result.get("drugs", {}).values())
    if tool in {"generate_ecg", "analyze_signal"}:
        return "baseline" in (result.get("ecg") or {})
    if tool == "run_ml_model":
        return "metrics" in (result.get("ml") or {})
    return False
