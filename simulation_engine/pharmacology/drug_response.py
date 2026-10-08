"""Hypothetical treatment comparison.

Treatment_A and Treatment_B are parameter sets, not real drugs.
Numeric outputs come from the PK/PD equations, the Monte Carlo sampler,
and the sensitivity runner.
"""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import numpy as np

from simulation_engine.biosignals.ecg import bandpass_ecg, ecg_features, synthesize_ecg
from simulation_engine.core.labels import (
    MODEL_PREDICTION,
    SIMPLIFIED_MODEL,
    SIMULATION_BANNER,
    SOFTWARE_VALIDATION,
    SOFTWARE_VERSION,
    SYNTHETIC_DATA,
)
from simulation_engine.core.reproducibility import experiment_record
from simulation_engine.core.sensitivity import one_at_a_time
from simulation_engine.core.uncertainty import percentile_band, sample_lognormal, summarize_samples
from simulation_engine.disease.diabetes_states import label_glucose
from simulation_engine.patients.virtual_patient import generate_population, generate_virtual_patient
from simulation_engine.pharmacology.equations import oral_concentration
from simulation_engine.pharmacology.pkpd import IndirectGlucosePD

MODEL_VERSIONS = {
    "pk_one_compartment_oral": "0.1.0",
    "pkpd_indirect_glucose": "0.1.0",
    "synthetic_ecg": "0.1.0",
    "glucose_state": "0.1.0",
    "virtual_patient": "0.1.0",
}

PD_KEYS = ("kout_per_h", "k_insulin_per_h", "insulin_slope", "insulin_base_mu_l")
PK_SAMPLE_KEYS = ("ka_per_h", "cl_l_per_h", "v_l", "ec50_mg_l")


def default_config() -> dict:
    path = Path(__file__).resolve().parents[2] / "experiments" / "templates" / "drug_response.json"
    return json.loads(path.read_text())


def _drug(ka: float, emax: float, ec50: float, hr_effect: float) -> dict:
    return {
        "dose_mg": 400,
        "ka_per_h": ka,
        "cl_l_per_h": 5,
        "v_l": 22,
        "bioavailability": 1,
        "emax": emax,
        "ec50_mg_l": ec50,
        "hr_effect_bpm": hr_effect,
        "reference_weight_kg": 70,
    }


def time_grid(duration: float, dt: float) -> np.ndarray:
    steps = int(np.floor(duration / dt + 1e-9))
    return np.linspace(0.0, steps * dt, steps + 1)


def scaled_pk(drug: dict, weight_kg: float) -> dict:
    """Allometric scaling around the template's reference weight. An assumption."""

    ratio = float(weight_kg) / float(drug.get("reference_weight_kg", 70))
    scaled = dict(drug)
    scaled["v_l"] = float(drug["v_l"]) * ratio
    scaled["cl_l_per_h"] = float(drug["cl_l_per_h"]) * ratio**0.75
    return scaled


def _as_n(value, n: int) -> np.ndarray:
    array = np.asarray(value, dtype=float)
    if array.ndim == 0:
        return np.full(n, float(array))
    if array.shape != (n,):
        raise ValueError(f"Expected a scalar or length-{n} array, got shape {array.shape}.")
    return array


def simulate_batch(t, drug, weight, glucose0, heart_rate0, pd, n: int = 1) -> dict:
    """Vectorized oral PK plus explicit Euler for the indirect response.

    PK parameters may be scalars or length-n arrays. Clearance and volume are
    scaled by weight unless ``reference_weight_kg`` already equals that weight.
    """

    weight = _as_n(weight, n)
    reference = float(drug.get("reference_weight_kg", 70))
    ratio = weight / reference
    dose = _as_n(drug["dose_mg"], n)
    ka = _as_n(drug["ka_per_h"], n)
    cl = _as_n(drug["cl_l_per_h"], n) * ratio**0.75
    volume = _as_n(drug["v_l"], n) * ratio
    f = _as_n(drug["bioavailability"], n)
    emax = _as_n(drug["emax"], n)
    ec50 = _as_n(drug["ec50_mg_l"], n)
    conc = oral_concentration(t, dose, ka, cl, volume, f)
    g0 = np.full(n, glucose0, dtype=float) if np.ndim(glucose0) == 0 else np.asarray(glucose0, dtype=float)
    i0 = np.full(n, pd["insulin_base_mu_l"], dtype=float)
    kout = float(pd["kout_per_h"])
    ki = float(pd["k_insulin_per_h"])
    slope = float(pd["insulin_slope"])
    kin = kout * g0
    glucose = np.empty_like(conc)
    insulin = np.empty_like(conc)
    glucose[:, 0] = g0
    insulin[:, 0] = i0
    for k in range(len(t) - 1):
        h = float(t[k + 1] - t[k])
        c = conc[:, k]
        effect = emax * c / (ec50 + c)
        glucose[:, k + 1] = glucose[:, k] + h * (kin * (1.0 - effect) - kout * glucose[:, k])
        insulin[:, k + 1] = insulin[:, k] + h * (
            -ki * (insulin[:, k] - i0) + slope * np.maximum(glucose[:, k] - g0, 0.0)
        )
    cmax = np.max(conc, axis=1)
    hr0 = _as_n(heart_rate0, n)
    hr_effect = _as_n(drug["hr_effect_bpm"], n)
    heart = hr0[:, None] + hr_effect[:, None] * np.divide(conc, cmax[:, None], out=np.zeros_like(conc), where=cmax[:, None] > 1e-12)
    return {
        "concentration": conc,
        "glucose": glucose,
        "insulin": insulin,
        "heart_rate": heart,
    }


def _index_at(t: np.ndarray, hour: float) -> int:
    return int(np.argmin(np.abs(t - hour)))


def _endpoints(t: np.ndarray, batch: dict, glucose0: float) -> dict:
    idx = _index_at(t, 12.0)
    conc = batch["concentration"]
    # single trajectory
    c = conc[0]
    cmax = float(np.max(c))
    tmax = float(t[int(np.argmax(c))])
    g12 = float(batch["glucose"][0, idx])
    nadir = float(np.min(batch["glucose"][0]))
    trap = np.trapezoid if hasattr(np, "trapezoid") else np.trapz
    return {
        "cmax_mg_l": cmax,
        "tmax_h": tmax,
        "auc_mg_h_l": float(trap(c, t)),
        "glucose_12h_mg_dl": g12,
        "glucose_delta_12h_mg_dl": g12 - float(glucose0),
        "glucose_nadir_mg_dl": nadir,
        "glucose_nadir_delta_mg_dl": nadir - float(glucose0),
        "heart_rate_at_tmax_bpm": float(batch["heart_rate"][0, int(np.argmax(c))]),
    }


def _series_payload(t, batch, stride_samples: int = 1) -> dict:
    sl = slice(None, None, stride_samples)
    return {
        "time_h": t[sl],
        "concentration_mg_l": batch["concentration"][0, sl],
        "glucose_mg_dl": batch["glucose"][0, sl],
        "insulin_mu_l": batch["insulin"][0, sl],
        "heart_rate_bpm": batch["heart_rate"][0, sl],
    }


def run_drug_response(config: dict | None = None, include_waveforms: bool = True) -> dict:
    cfg = _merge(config)
    _validate_config(cfg)
    mode = cfg["mode"]
    seed = int(cfg["seed"])
    t = time_grid(float(cfg["duration_h"]), float(cfg["dt_h"]))
    if mode == "patient":
        patient = cfg.get("patient") or generate_virtual_patient(seed, cfg["condition"])
        payload, stages = _run_patient(cfg, patient, t, include_waveforms)
    elif mode == "population":
        payload, stages = _run_population(cfg, t)
        patient = None
    else:
        raise ValueError("mode must be 'patient' or 'population'.")
    record = experiment_record(
        config=_public_config(cfg),
        seed=seed,
        model_versions=MODEL_VERSIONS,
        software_version=SOFTWARE_VERSION,
    )
    explanation = explain(payload)
    hypothesis = build_hypothesis(payload)
    from ai_scientist.critic.critic import critique_result
    from ai_scientist.report_generator.report import render_report

    payload.update(
        {
            "labels": [SIMULATION_BANNER, SIMPLIFIED_MODEL, SYNTHETIC_DATA],
            "patient": patient,
            "mode": mode,
            "seed": seed,
            "time_h": t[:: max(1, len(t) // 500)],
            "explanation": explanation,
            "hypothesis": hypothesis,
            "reproducibility": record,
            "software_version": SOFTWARE_VERSION,
            "model_versions": MODEL_VERSIONS,
            "validation": SOFTWARE_VALIDATION,
            "stages": stages,
            "assumptions": _assumptions(),
            "limitations": _limitations(),
            "equations": IndirectGlucosePD().get_equations(),
        }
    )
    payload["critic"] = critique_result(cfg, payload, explanation)
    payload["report_markdown"] = render_report(cfg, payload)
    return _json(payload)


def _run_patient(cfg, patient, t, include_waveforms: bool):
    drugs = {}
    stages = [
        {
            "id": "patient",
            "status": "complete",
            "summary": f"Synthetic patient seed {patient['seed']}, age {patient['age']}.",
        }
    ]
    baseline_glucose = float(patient["glucose_mg_dl"])
    for name, drug in cfg["interventions"].items():
        point = _point_drug(drug, patient["weight_kg"])
        batch = simulate_batch(
            t,
            point,
            patient["weight_kg"],
            baseline_glucose,
            patient["heart_rate_bpm"],
            cfg["pd"],
            n=1,
        )
        # simulate_batch scales again if reference weight is 70. _point_drug sets
        # reference_weight to the patient weight and already-scaled CL/V, so the
        # ratio is 1. See _point_drug.
        endpoints = _endpoints(t, batch, baseline_glucose)
        stride = max(1, len(t) // 300)
        mc = _monte_carlo(cfg, patient, t, drug, stride)
        sensitivity = _sensitivity(cfg, patient, drug)
        state = label_glucose(endpoints["glucose_12h_mg_dl"], 70, 110, 140)
        drugs[name] = {
            "parameters": drug,
            "scaled_parameters": {k: point[k] for k in ("cl_l_per_h", "v_l", "ka_per_h", "dose_mg", "emax", "ec50_mg_l")},
            "series": _series_payload(t, batch, stride_samples=stride),
            "endpoints": endpoints,
            "monte_carlo": mc,
            "sensitivity": sensitivity,
            "glucose_state_12h": state,
            "glucose_state_note": "Computational label only. Not a diagnosis.",
        }
        stages.append(
            {
                "id": name,
                "status": "complete",
                "summary": (
                    f"{name} simulated glucose nadir change: "
                    f"{endpoints['glucose_nadir_delta_mg_dl']:.2f} mg/dL."
                ),
            }
        )
    ecg = _ecg_bundle(patient, drugs, int(cfg["seed"])) if include_waveforms else {"label": SYNTHETIC_DATA}
    ml = _morphology_model(int(cfg["seed"]), ecg)
    stages.append({"id": "monte_carlo", "status": "complete", "summary": "Parameter uncertainty bands computed."})
    stages.append({"id": "ecg", "status": "complete", "summary": "Synthetic waveforms generated."})
    stages.append(
        {
            "id": "ml",
            "status": "complete",
            "summary": f"Synthetic morphology model held-out accuracy {ml['metrics']['accuracy']:.2f}.",
        }
    )
    return {"drugs": drugs, "ecg": ecg, "ml": ml}, stages


def _point_drug(drug: dict, weight_kg: float) -> dict:
    scaled = scaled_pk(drug, weight_kg)
    scaled["reference_weight_kg"] = float(weight_kg)
    return scaled


def _monte_carlo(cfg, patient, t, drug, stride: int = 1) -> dict:
    n = int(cfg["monte_carlo"]["n"])
    cv = float(cfg["monte_carlo"]["cv"])
    if not 1 <= n <= 10000:
        raise ValueError("Monte Carlo n must be from 1 to 10000.")
    rng = np.random.default_rng(int(cfg["seed"]) + 17)
    base = _point_drug(drug, patient["weight_kg"])
    means = np.array([base[key] for key in PK_SAMPLE_KEYS], dtype=float)
    tiled = np.tile(means, (n, 1))
    drawn = sample_lognormal(rng, tiled, cv)
    emax = np.clip(base["emax"] * sample_lognormal(rng, np.full(n, 1.0), cv), 0.0, 0.95)
    sampled = dict(base)
    sampled["ka_per_h"] = drawn[:, 0]
    sampled["cl_l_per_h"] = drawn[:, 1]
    sampled["v_l"] = drawn[:, 2]
    sampled["ec50_mg_l"] = drawn[:, 3]
    sampled["emax"] = emax
    sampled["reference_weight_kg"] = float(patient["weight_kg"])
    batch = simulate_batch(
        t,
        sampled,
        np.full(n, patient["weight_kg"]),
        patient["glucose_mg_dl"],
        patient["heart_rate_bpm"],
        cfg["pd"],
        n=n,
    )
    endpoint = np.min(batch["glucose"], axis=1) - patient["glucose_mg_dl"]
    band = percentile_band(batch["glucose"])
    return {
        "n": n,
        "cv": cv,
        "distribution": "lognormal multipliers on ka, CL, V, EC50; Emax clipped to [0, 0.95]",
        "endpoint": "glucose_nadir_delta_mg_dl",
        "endpoint_summary": summarize_samples(endpoint),
        "glucose_p05": band["p05"][::stride],
        "glucose_p50": band["p50"][::stride],
        "glucose_p95": band["p95"][::stride],
        "time_h": t[::stride],
        "interpretation": (
            "Bands are parameter uncertainty around one synthetic patient. "
            "They are not a confidence interval from a clinical sample."
        ),
    }


def _sensitivity(cfg, patient, drug) -> dict:
    base = _point_drug(drug, patient["weight_kg"])

    def evaluate(params: dict) -> float:
        trial = dict(base)
        trial.update(params)
        trial["reference_weight_kg"] = float(patient["weight_kg"])
        t = time_grid(float(cfg["duration_h"]), float(cfg["dt_h"]))
        batch = simulate_batch(
            t,
            trial,
            patient["weight_kg"],
            patient["glucose_mg_dl"],
            patient["heart_rate_bpm"],
            cfg["pd"],
            n=1,
        )
        return _endpoints(t, batch, patient["glucose_mg_dl"])["glucose_nadir_delta_mg_dl"]

    names = ["ka_per_h", "cl_l_per_h", "v_l", "emax", "ec50_mg_l"]
    baseline = {name: float(base[name]) for name in names}
    result = one_at_a_time(baseline, names, evaluate, fraction=0.2)
    result["endpoint"] = "glucose_nadir_delta_mg_dl"
    if result["bars"]:
        top = result["bars"][0]["parameter"]
        result["most_influential"] = top
    return result


def _run_population(cfg, t):
    size = int(cfg.get("population_size", cfg["monte_carlo"]["n"]))
    if not 1 <= size <= 5000:
        raise ValueError("population size must be from 1 to 5000.")
    population = generate_population(int(cfg["seed"]), size, cfg["condition"])
    patients = population["patients"]
    weight = np.array([p["weight_kg"] for p in patients])
    glucose0 = np.array([p["glucose_mg_dl"] for p in patients])
    hr0 = np.array([p["heart_rate_bpm"] for p in patients])
    drugs = {}
    for name, drug in cfg["interventions"].items():
        sampled = dict(drug)
        sampled["reference_weight_kg"] = 70
        batch = simulate_batch(t, sampled, weight, glucose0, hr0, cfg["pd"], n=size)
        idx = _index_at(t, 12.0)
        delta = np.min(batch["glucose"], axis=1) - glucose0
        band = percentile_band(batch["glucose"])
        stride = max(1, len(t) // 240)
        drugs[name] = {
            "parameters": drug,
            "series": {
                "time_h": t[::stride],
                "glucose_mg_dl": band["mean"][::stride],
                "concentration_mg_l": np.mean(batch["concentration"], axis=0)[::stride],
                "insulin_mu_l": np.mean(batch["insulin"], axis=0)[::stride],
                "heart_rate_bpm": np.mean(batch["heart_rate"], axis=0)[::stride],
            },
            "endpoints": {
                "glucose_delta_12h_mg_dl": float(np.mean(batch["glucose"][:, idx] - glucose0)),
                "glucose_nadir_delta_mg_dl": float(np.mean(delta)),
                "glucose_12h_mg_dl": float(np.mean(batch["glucose"][:, idx])),
                "cmax_mg_l": float(np.mean(np.max(batch["concentration"], axis=1))),
                "tmax_h": None,
                "auc_mg_h_l": None,
                "heart_rate_at_tmax_bpm": None,
            },
            "monte_carlo": {
                "n": size,
                "cv": None,
                "distribution": "cross-patient spread from the synthetic population and allometric scaling",
                "endpoint": "glucose_nadir_delta_mg_dl",
                "endpoint_summary": summarize_samples(delta),
                "glucose_p05": band["p05"][::stride],
                "glucose_p50": band["p50"][::stride],
                "glucose_p95": band["p95"][::stride],
                "time_h": t[::stride],
                "interpretation": (
                    "Bands are spread across synthetic patients. "
                    "They are not a clinical confidence interval."
                ),
            },
            "sensitivity": {"bars": [], "note": "OAT sensitivity is run in patient mode."},
            "glucose_state_12h": label_glucose(float(np.mean(batch["glucose"][:, idx])), 70, 110, 140),
            "glucose_state_note": "Computational label of the mean simulated glucose. Not a diagnosis.",
        }
    stages = [
        {"id": "population", "status": "complete", "summary": f"{size} synthetic records."},
        {"id": "comparison", "status": "complete", "summary": "Population means computed."},
    ]
    return {
        "drugs": drugs,
        "population": {
            "size": size,
            "condition": cfg["condition"],
            "summary": population["summary"],
            "label": SYNTHETIC_DATA,
        },
        "ecg": {"note": "ECG is generated in patient mode."},
        "ml": {"note": "The morphology model runs in patient mode.", "label": MODEL_PREDICTION},
    }, stages


def _ecg_bundle(patient, drugs, seed: int) -> dict:
    fs = 250.0
    duration = 8.0
    baseline_t, baseline = synthesize_ecg(duration, patient["heart_rate_bpm"], fs, noise_std=0.01, seed=seed)
    filtered = bandpass_ecg(baseline, fs)
    features = ecg_features(filtered, fs, patient["heart_rate_bpm"])
    features.pop("peak_indices", None)
    bundle = {
        "label": SYNTHETIC_DATA,
        "fs_hz": fs,
        "baseline": _downsample(baseline_t, baseline, 800),
        "baseline_features": features,
        "treatments": {},
    }
    for name, drug in drugs.items():
        hr = drug["endpoints"]["heart_rate_at_tmax_bpm"] or patient["heart_rate_bpm"]
        tt, sig = synthesize_ecg(duration, hr, fs, noise_std=0.01, seed=seed + 3)
        feat = ecg_features(sig, fs, hr)
        feat.pop("peak_indices", None)
        bundle["treatments"][name] = {**_downsample(tt, sig, 800), "features": feat}
    return bundle


def _downsample(t, signal, max_points: int) -> dict:
    stride = max(1, int(np.ceil(len(signal) / max_points)))
    return {"time_s": np.asarray(t)[::stride], "amplitude": np.asarray(signal)[::stride]}


def _morphology_model(seed: int, ecg: dict) -> dict:
    from ml.training.logistic import train_morphology_classifier

    trained = train_morphology_classifier(seed)
    features = ecg.get("baseline_features") or {}
    prediction = None
    if features:
        prediction = trained["predict"](features["t_wave_mean"])
    trained.pop("predict", None)
    return {
        "label": MODEL_PREDICTION,
        "task": "Separate two synthetic T-wave morphologies. Not a rhythm or diagnosis model.",
        "training_data": SYNTHETIC_DATA,
        "metrics": trained["metrics"],
        "loss_curve": trained["loss_curve"],
        "confusion_matrix": trained["metrics"]["confusion_matrix"],
        "architecture": trained["architecture"],
        "prediction": prediction,
        "frameworks": trained["frameworks"],
    }


def explain(payload: dict) -> str:
    drugs = payload["drugs"]
    names = list(drugs)
    if len(names) < 2:
        only = names[0]
        delta = drugs[only]["endpoints"]["glucose_nadir_delta_mg_dl"]
        return (
            f"Under the stated parameters, {only} changed simulated glucose at its lowest point "
            f"by {delta:.2f} mg/dL from the synthetic baseline. "
            "This is a simulation result, not evidence of effect in people."
        )
    a, b = names[0], names[1]
    da = drugs[a]["endpoints"]["glucose_nadir_delta_mg_dl"]
    db = drugs[b]["endpoints"]["glucose_nadir_delta_mg_dl"]
    summary_a = drugs[a]["monte_carlo"]["endpoint_summary"]
    summary_b = drugs[b]["monte_carlo"]["endpoint_summary"]
    relation = "lower" if db < da else "higher" if db > da else "the same"
    return (
        f"The lowest simulated glucose change was {da:.2f} mg/dL for {a} and {db:.2f} mg/dL for {b}. "
        f"{b} was {relation} than {a} on this point estimate. "
        f"The {a} uncertainty summary for that endpoint has mean {summary_a['mean']:.2f} "
        f"and a 5th–95th percentile span of {summary_a['p05']:.2f} to {summary_a['p95']:.2f}. "
        f"The {b} span is {summary_b['p05']:.2f} to {summary_b['p95']:.2f}. "
        "These spans describe the computational experiment, not a clinical trial."
    )


def build_hypothesis(payload: dict) -> dict:
    drugs = payload["drugs"]
    names = list(drugs)
    if len(names) < 2:
        return {
            "observation": "Only one intervention was simulated.",
            "hypothesis": "No comparison hypothesis is offered.",
            "suggested_experiment": "Add a second parameter set and rerun.",
            "run_available": False,
        }
    a, b = names[0], names[1]
    da = drugs[a]["endpoints"]["glucose_nadir_delta_mg_dl"]
    db = drugs[b]["endpoints"]["glucose_nadir_delta_mg_dl"]
    influential = []
    for name in names:
        top = (drugs[name].get("sensitivity") or {}).get("most_influential")
        if top:
            influential.append(f"{name}: {top}")
    direction = f"{b} minus {a} is {db - da:.2f} mg/dL"
    return {
        "observation": f"Simulated glucose nadir change: {direction}.",
        "hypothesis": (
            "Any difference is produced by the parameter values assigned to the two hypothetical "
            "interventions (absorption rate, Emax, EC50, clearance, volume) and, in population mode, "
            "by synthetic covariate spread. It is not evidence about a real treatment."
        ),
        "influential_parameters": influential,
        "suggested_experiment": "Run one-at-a-time sensitivity on ka, CL, V, Emax, and EC50.",
        "run_available": True,
    }


def _assumptions() -> list[str]:
    return [
        "Treatment_A and Treatment_B are hypothetical parameter sets.",
        "Volume scales with weight/70 and clearance with (weight/70)^0.75.",
        "The glucose equation is an illustrative indirect response, not a fitted human model.",
        "Heart-rate change occurs only through the user-supplied hr_effect_bpm parameter.",
    ]


def _limitations() -> list[str]:
    return [
        "Not clinically validated.",
        "Not a dosing, efficacy, or safety assessment.",
        "Monte Carlo bands are computational uncertainty, not clinical confidence intervals.",
        "The morphology classifier is trained and tested on synthetic waveforms only.",
    ]


def _merge(config: dict | None) -> dict:
    base = default_config()
    if not config:
        return base
    merged = deepcopy(base)
    for key, value in config.items():
        if key == "interventions" and isinstance(value, dict):
            for name, drug in value.items():
                current = dict(merged["interventions"].get(name, _drug(1.0, 0.3, 8, 0)))
                current.update(drug)
                merged["interventions"][name] = current
        elif key == "pd" and isinstance(value, dict):
            merged["pd"].update(value)
        elif key == "monte_carlo" and isinstance(value, dict):
            merged["monte_carlo"].update(value)
        else:
            merged[key] = value
    return merged


def _public_config(cfg: dict) -> dict:
    public = deepcopy(cfg)
    public.pop("patient", None)
    return public


def _validate_config(cfg: dict) -> None:
    if cfg["mode"] not in {"patient", "population"}:
        raise ValueError("mode must be patient or population.")
    if float(cfg["dt_h"]) <= 0 or float(cfg["duration_h"]) <= 0:
        raise ValueError("duration and dt must be positive.")
    if float(cfg["duration_h"]) > 168:
        raise ValueError("duration exceeds 168 hours.")
    if len(cfg["interventions"]) < 1:
        raise ValueError("At least one intervention is required.")
    model = IndirectGlucosePD()
    for name, drug in cfg["interventions"].items():
        model.validate_parameters(
            {
                "dose_mg": drug["dose_mg"],
                "ka_per_h": drug["ka_per_h"],
                "cl_l_per_h": drug["cl_l_per_h"],
                "v_l": drug["v_l"],
                "bioavailability": drug["bioavailability"],
                "glucose_mg_dl": 100,
                "emax": drug["emax"],
                "ec50_mg_l": drug["ec50_mg_l"],
                "hr_effect_bpm": drug["hr_effect_bpm"],
                **{k: cfg["pd"][k] for k in ("kout_per_h", "k_insulin_per_h", "insulin_slope")},
                "insulin_mu_l": cfg["pd"]["insulin_base_mu_l"],
            }
        )


def _json(value):
    from simulation_engine.core.results import jsonable

    return jsonable(value)
