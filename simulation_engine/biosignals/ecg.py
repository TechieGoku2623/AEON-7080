"""Synthetic ECG built from Gaussian waves.

This is a teaching waveform, not a clinical electrocardiogram.
"""

from __future__ import annotations

import numpy as np

from simulation_engine.core.base import SimulationModel
from simulation_engine.core.labels import SOFTWARE_VALIDATION, SYNTHETIC_DATA
from simulation_engine.core.results import SimulationResult
from simulation_engine.core.specs import ParameterSpec


WAVES = (
    ("P", -0.20, 0.040, 0.15),
    ("Q", -0.045, 0.012, -0.12),
    ("R", 0.0, 0.012, 1.0),
    ("S", 0.035, 0.012, -0.22),
    ("T", 0.24, 0.055, 0.32),
)


def synthesize_ecg(
    duration_s: float,
    heart_rate_bpm: float,
    fs: float = 250.0,
    noise_std: float = 0.0,
    t_wave_scale: float = 1.0,
    seed: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    if heart_rate_bpm <= 0 or fs <= 0 or duration_s <= 0:
        raise ValueError("duration, heart rate, and sampling rate must be positive.")
    n = int(duration_s * fs)
    t = np.arange(n) / fs
    rr = 60.0 / heart_rate_bpm
    signal = np.zeros(n)
    beat = 0
    while True:
        r_time = beat * rr
        if r_time - 0.4 > duration_s:
            break
        for name, center, width, amp in WAVES:
            amplitude = amp * t_wave_scale if name == "T" else amp
            signal += amplitude * np.exp(-0.5 * ((t - (r_time + center)) / width) ** 2)
        beat += 1
    if noise_std > 0:
        rng = np.random.default_rng(seed)
        signal = signal + rng.normal(0.0, noise_std, size=n)
    return t, signal


def detect_r_peaks(signal: np.ndarray, fs: float, threshold: float = 0.5, refractory_s: float = 0.3) -> np.ndarray:
    x = np.asarray(signal, dtype=float)
    if len(x) < 3:
        return np.array([], dtype=int)
    refractory = int(refractory_s * fs)
    peaks = []
    last = -refractory
    for i in range(1, len(x) - 1):
        if x[i] >= threshold and x[i] >= x[i - 1] and x[i] > x[i + 1] and i - last >= refractory:
            peaks.append(i)
            last = i
    return np.asarray(peaks, dtype=int)


def bandpass_ecg(signal: np.ndarray, fs: float, low: float = 0.5, high: float = 40.0) -> np.ndarray:
    from scipy.signal import butter, sosfiltfilt

    x = np.asarray(signal, dtype=float)
    if len(x) < int(fs):
        return x.copy()
    sos = butter(2, [low, high], btype="bandpass", fs=fs, output="sos")
    return sosfiltfilt(sos, x)


def ecg_features(signal: np.ndarray, fs: float, heart_rate_hint: float) -> dict:
    peaks = detect_r_peaks(signal, fs)
    if len(peaks) >= 2:
        rr = np.diff(peaks) / fs
        hr = float(60.0 / np.mean(rr))
        rr_std = float(np.std(rr, ddof=1)) if len(rr) > 1 else 0.0
    else:
        hr = float(heart_rate_hint)
        rr_std = 0.0
    twave = []
    qrs = []
    r_amp = []
    half = int(0.04 * fs)
    t0 = int(0.16 * fs)
    t1 = int(0.32 * fs)
    for peak in peaks:
        r_amp.append(float(signal[peak]))
        left = max(0, peak - half)
        right = min(len(signal), peak + half)
        segment = signal[left:right]
        above = np.where(segment > 0.5 * signal[peak])[0]
        qrs.append(float(len(above) / fs) if len(above) else 0.0)
        a = peak + t0
        b = min(len(signal), peak + t1)
        if b > a:
            twave.append(float(np.mean(signal[a:b])))
    return {
        "n_peaks": int(len(peaks)),
        "heart_rate_bpm": hr,
        "rr_std_s": rr_std,
        "qrs_width_s": float(np.mean(qrs)) if qrs else 0.0,
        "r_amplitude": float(np.mean(r_amp)) if r_amp else 0.0,
        "t_wave_mean": float(np.mean(twave)) if twave else 0.0,
        "peak_indices": peaks,
    }


class SyntheticECG(SimulationModel):
    name = "synthetic_ecg"
    version = "0.1.0"
    solver_name = "sum of Gaussian waves"
    validation_status = SOFTWARE_VALIDATION

    def parameter_specs(self) -> list[ParameterSpec]:
        return [
            ParameterSpec("heart_rate_bpm", "bpm", "Beat rate", 30, 220),
            ParameterSpec("duration_s", "s", "Waveform length", 1, 30, default=10),
            ParameterSpec("fs_hz", "Hz", "Sampling rate", 50, 1000, default=250),
            ParameterSpec("noise_std", "mV scale", "Gaussian noise standard deviation", 0, 0.5, default=0.0),
            ParameterSpec("t_wave_scale", "fraction", "T-wave amplitude multiplier", -2, 2, default=1),
        ]

    def run(self, initial_state, parameters, duration, dt, seed: int = 42) -> SimulationResult:
        # duration/dt are part of the common interface; the waveform uses duration_s and fs.
        self.parameters = self.validate_parameters(parameters)
        p = self.parameters
        t, signal = synthesize_ecg(
            p["duration_s"],
            p["heart_rate_bpm"],
            p["fs_hz"],
            p["noise_std"],
            p["t_wave_scale"],
            seed,
        )
        features = ecg_features(signal, p["fs_hz"], p["heart_rate_bpm"])
        peak_indices = features.pop("peak_indices")
        result = self._pack(
            t,
            {"amplitude": signal, "peaks": peak_indices, "features": features},
            p["duration_s"],
            1.0 / p["fs_hz"],
            seed,
        )
        result.labels.append(SYNTHETIC_DATA)
        result.units["amplitude"] = "illustrative amplitude"
        return result

    def get_observables(self) -> list[str]:
        return ["amplitude"]

    def get_assumptions(self) -> list[str]:
        return [
            "Each beat is a sum of fixed Gaussian P, Q, R, S, and T waves.",
            "The rate is constant.",
        ]

    def get_limitations(self) -> list[str]:
        limits = super().get_limitations()
        limits.append("This waveform is synthetic. It is not an ECG recording and supports no rhythm call.")
        return limits

    def get_equations(self) -> list[dict]:
        return [
            {
                "latex": r"x(t) = \sum_b \sum_w A_w \exp\left(-\frac{(t - t_b - c_w)^2}{2\sigma_w^2}\right)",
                "description": "Gaussian-wave synthetic ECG.",
            }
        ]
