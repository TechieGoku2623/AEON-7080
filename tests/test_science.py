"""Software-correctness checks for the simplified models."""

from __future__ import annotations

import numpy as np
import pytest
import sympy as sp

from ai_scientist.critic.critic import critique_config
from ai_scientist.planner.planner import plan_question
from ai_scientist.report_generator.report import render_report
from ai_scientist.tools.registry import FORBIDDEN, TOOL_NAMES
from data.schemas.mapping import apply_mapping, suggest_mapping
from data.transformation.units import convert
from data.privacy.identifiers import scan_table
from ml.training.logistic import train_morphology_classifier
from simulation_engine.biosignals.ecg import detect_r_peaks, synthesize_ecg
from simulation_engine.core.reproducibility import fingerprint
from simulation_engine.core.uncertainty import sample_lognormal, summarize_samples
from simulation_engine.epidemiology.sir import SIRModel
from simulation_engine.patients.virtual_patient import bmi, generate_virtual_patient
from simulation_engine.pharmacology.equations import iv_bolus_concentration, oral_concentration
from simulation_engine.pharmacology.pk_one_compartment import OneCompartmentIV, OneCompartmentOral
from simulation_engine.pharmacology.pk_two_compartment import TwoCompartmentIV
from simulation_engine.pharmacology.pkpd import analytical_constant_concentration
from simulation_engine.pharmacology.drug_response import default_config, run_drug_response
from simulation_engine.physiology.exponential import ExponentialDecay, analytical_decay
from simulation_engine.core.solver import integrate_rk4


def test_exponential_matches_analytical_solution():
    result = ExponentialDecay().run(None, {"C0": 10, "k": 0.2}, 5, 0.01, seed=1)
    assert result.results["max_abs_error"] < 1e-6
    expected = analytical_decay(5, 10, 0.2)
    assert expected == pytest.approx(10 * np.exp(-1))


def test_sympy_confirms_decay_solution():
    t, k, c0 = sp.symbols("t k C0", positive=True)
    c = sp.Function("C")
    equation = sp.diff(c(t), t) + k * c(t)
    solution = sp.dsolve(equation, c(t), ics={c(0): c0})
    assert sp.simplify(solution.rhs - c0 * sp.exp(-k * t)) == 0


def test_iv_bolus_matches_closed_form():
    result = OneCompartmentIV().run(None, {"dose_mg": 100, "cl_l_per_h": 2, "v_l": 10}, 5, 0.01)
    assert result.results["max_abs_error"] < 1e-4
    at_five = iv_bolus_concentration(5, 100, 2, 10)
    assert float(at_five) == pytest.approx(10 * np.exp(-1))


def test_oral_starts_at_zero_and_matches_limit_when_rates_equal():
    oral = OneCompartmentOral().run(
        None,
        {"dose_mg": 100, "ka_per_h": 0.5, "cl_l_per_h": 5, "v_l": 10, "bioavailability": 1},
        1,
        0.05,
    )
    assert oral.results["concentration_mg_l"][0] == pytest.approx(0, abs=1e-12)
    # ka = CL/V = 0.5
    t = np.linspace(0, 4, 9)
    closed = oral_concentration(t, 100, 0.5, 5, 10, 1)
    limit = (100 * 0.5 * t / 10) * np.exp(-0.5 * t)
    assert np.allclose(closed, limit, atol=1e-8)


def test_constant_effect_glucose_matches_analytical():
    g0, kout, effect = 150.0, 0.45, 0.4
    t = np.linspace(0, 8, 161)
    analytical = analytical_constant_concentration(t, g0, kout, effect)

    def derivative(_t, y):
        kin = kout * g0
        return np.array([kin * (1 - effect) - kout * y[0]])

    _time, numeric = integrate_rk4(derivative, np.array([g0]), 8, 0.05)
    assert np.max(np.abs(numeric[:, 0] - analytical)) < 1e-3


def test_two_compartment_mass_leaves_the_system():
    result = TwoCompartmentIV().run(
        None,
        {"dose_mg": 100, "cl_l_per_h": 4, "v1_l": 10, "v2_l": 20, "q_l_per_h": 3},
        80,
        0.05,
    )
    remaining = result.results["central_amount_mg"][-1] + result.results["peripheral_amount_mg"][-1]
    assert remaining < 1.0
    t, scipy_c = TwoCompartmentIV().scipy_concentration(
        {"dose_mg": 100, "cl_l_per_h": 4, "v1_l": 10, "v2_l": 20, "q_l_per_h": 3},
        4,
        0.02,
    )
    rk = TwoCompartmentIV().run(
        None,
        {"dose_mg": 100, "cl_l_per_h": 4, "v1_l": 10, "v2_l": 20, "q_l_per_h": 3},
        4,
        0.02,
    )
    assert np.max(np.abs(rk.results["concentration_mg_l"] - scipy_c)) < 1e-2


def test_sir_conserves_people():
    result = SIRModel().run(None, {"beta_per_day": 0.4, "gamma_per_day": 0.2, "s0": 0.99, "i0": 0.01, "r0": 0}, 40, 0.05)
    assert result.results["compartment_sum_error"] < 1e-6
    assert result.results["basic_reproduction_number"] == pytest.approx(2)


def test_negative_clearance_is_flagged_not_rewritten():
    config = default_config()
    config["interventions"]["Treatment_A"]["cl_l_per_h"] = -2
    critique = critique_config(config)
    assert critique["changed_parameters"] is False
    assert critique["status"] == "fail"
    assert any("not changed" in flag for flag in critique["flags"])
    assert config["interventions"]["Treatment_A"]["cl_l_per_h"] == -2


def test_treatment_b_lowers_simulated_glucose_more():
    config = default_config()
    config["monte_carlo"] = {"n": 25, "cv": 0.0}
    config["duration_h"] = 12
    config["dt_h"] = 0.1
    result = run_drug_response(config, include_waveforms=False)
    delta_a = result["drugs"]["Treatment_A"]["endpoints"]["glucose_nadir_delta_mg_dl"]
    delta_b = result["drugs"]["Treatment_B"]["endpoints"]["glucose_nadir_delta_mg_dl"]
    assert delta_b < delta_a
    summary = result["drugs"]["Treatment_A"]["monte_carlo"]["endpoint_summary"]
    assert summary["p05"] <= summary["p50"] <= summary["p95"]
    assert result["critic"]["status"] == "pass"
    assert result["critic"]["flags"] == []
    assert "NOT CLINICAL" in result["labels"][0]
    assert "et al" not in result["report_markdown"].lower()
    assert "No external citations" in result["report_markdown"]
    replay = run_drug_response(config, include_waveforms=False)
    assert replay["reproducibility"]["config_fingerprint"] == result["reproducibility"]["config_fingerprint"]
    assert replay["drugs"]["Treatment_A"]["endpoints"]["glucose_nadir_delta_mg_dl"] == pytest.approx(delta_a)


def test_zero_cv_monte_carlo_matches_itself():
    rng = np.random.default_rng(1)
    drawn = sample_lognormal(rng, np.array([2.0, 3.0]), 0)
    assert np.allclose(drawn, [2.0, 3.0])
    summary = summarize_samples(np.array([1.0, 2.0, 3.0, 4.0]))
    assert summary["p50"] == pytest.approx(2.5)


def test_patient_is_deterministic_and_synthetic():
    first = generate_virtual_patient(42, "synthetic_diabetes")
    second = generate_virtual_patient(42, "synthetic_diabetes")
    assert first == second
    assert first["label"] == "SYNTHETIC DATA"
    assert first["bmi"] == pytest.approx(bmi(first["weight_kg"], first["height_cm"]), abs=0.02)
    assert first["blood_pressure_mmhg"]["systolic"] > first["blood_pressure_mmhg"]["diastolic"]


def test_ecg_peak_count():
    _t, signal = synthesize_ecg(10, 60, 250, noise_std=0)
    peaks = detect_r_peaks(signal, 250)
    assert 9 <= len(peaks) <= 11


def test_planner_structures_the_diabetic_comparison():
    plan = plan_question("Compare two hypothetical treatments in a virtual diabetic population.")
    assert plan["supported"] is True
    assert plan["objective"] == "compare simulated treatment response"
    assert plan["population"]["condition"] == "synthetic diabetes" or plan["population"]["condition"] == "synthetic_diabetes"
    assert plan["interventions"] == ["Treatment_A", "Treatment_B"]
    assert "run_pkpd_simulation" in plan["tools"]
    assert "python" not in TOOL_NAMES
    assert FORBIDDEN.isdisjoint(TOOL_NAMES)


def test_planner_refuses_medical_advice():
    plan = plan_question("What dose should I take for my diabetes?")
    assert plan["supported"] is False


def test_mapping_requires_confirmation_and_units_keep_both_values():
    suggestions = suggest_mapping(["age", "glucose", "heart_rate"])
    assert any(item["parameter"] == "physiology.glucose_mg_dl" for item in suggestions)
    with pytest.raises(PermissionError):
        apply_mapping({"glucose": 140}, [{"column": "glucose", "parameter": "physiology.glucose_mg_dl"}], False)
    applied = apply_mapping(
        {"glucose": 140},
        [{"column": "glucose", "parameter": "physiology.glucose_mg_dl", "confirmed": True}],
        True,
    )
    assert applied["parameters"]["physiology.glucose_mg_dl"] == 140
    converted = convert(180.182, "mg/dL", "mmol/L")
    assert converted["original"] == pytest.approx(180.182)
    assert converted["converted"] == pytest.approx(10, rel=1e-4)


def test_identifier_scan_flags_email_without_claiming_completeness():
    report = scan_table(["note"], [{"note": "write a@example.com"}])
    assert report["potentially_sensitive"] is True
    assert "does not guarantee" in report["guarantee"]


def test_morphology_model_learns_the_synthetic_rule():
    trained = train_morphology_classifier(3)
    assert trained["metrics"]["accuracy"] >= 0.85
    assert trained["metrics"]["label"] == "MODEL PREDICTION"


def test_fingerprint_ignores_key_order():
    assert fingerprint({"b": 1, "a": {"d": 2, "c": 3}}) == fingerprint({"a": {"c": 3, "d": 2}, "b": 1})


def test_report_quotes_only_supplied_numbers():
    payload = {
        "drugs": {
            "Treatment_A": {
                "parameters": {"dose_mg": 10},
                "endpoints": {"glucose_delta_12h_mg_dl": -3.5, "cmax_mg_l": 1.2},
                "monte_carlo": {"endpoint": "glucose_delta_12h_mg_dl", "endpoint_summary": {"mean": -3.5, "p05": -4, "p95": -3, "n": 5}, "interpretation": "computational"},
                "sensitivity": {"bars": []},
            }
        },
        "explanation": "Simulated change was -3.5 mg/dL.",
        "hypothesis": {"hypothesis": "parameter difference"},
        "model_versions": {"pkpd_indirect_glucose": "0.1.0"},
        "equations": [],
        "limitations": ["Not clinically validated."],
        "seed": 1,
        "mode": "patient",
        "software_version": "0.1.0",
        "reproducibility": {"config_fingerprint": "abc", "replay": "re-executes"},
        "labels": [],
        "patient": {"seed": 1, "age": 40, "glucose_mg_dl": 150},
    }
    markdown = render_report({"title": "T"}, payload)
    assert "NOT CLINICAL EVIDENCE" in markdown
    assert "-3.5" in markdown
    assert "No external citations" in markdown
