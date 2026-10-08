"""Monte Carlo parameter uncertainty for batch simulators."""

from __future__ import annotations

import numpy as np


def lognormal_sigma(cv: float) -> float:
    if cv < 0:
        raise ValueError("cv must be non-negative.")
    if cv == 0:
        return 0.0
    return float(np.sqrt(np.log(1.0 + cv**2)))


def sample_lognormal(rng: np.random.Generator, mean: np.ndarray, cv: float) -> np.ndarray:
    """Sample positive multipliers around each mean. cv=0 returns the means."""

    mean = np.asarray(mean, dtype=float)
    if cv == 0:
        return mean.copy()
    sigma = lognormal_sigma(cv)
    return mean * rng.lognormal(mean=0.0, sigma=sigma, size=mean.shape)


def summarize_samples(samples: np.ndarray) -> dict:
    values = np.asarray(samples, dtype=float)
    return {
        "n": int(values.shape[0]),
        "mean": float(np.mean(values)),
        "variance": float(np.var(values, ddof=1)) if values.shape[0] > 1 else 0.0,
        "std": float(np.std(values, ddof=1)) if values.shape[0] > 1 else 0.0,
        "p05": float(np.percentile(values, 5)),
        "p50": float(np.percentile(values, 50)),
        "p95": float(np.percentile(values, 95)),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
    }


def percentile_band(trajectories: np.ndarray) -> dict[str, list[float]]:
    """trajectories shaped (n, T) -> percentile curves."""

    data = np.asarray(trajectories, dtype=float)
    return {
        "p05": np.percentile(data, 5, axis=0),
        "p50": np.percentile(data, 50, axis=0),
        "p95": np.percentile(data, 95, axis=0),
        "mean": np.mean(data, axis=0),
    }
