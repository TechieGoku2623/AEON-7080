"""Closed-form pharmacokinetic expressions."""

from __future__ import annotations

import numpy as np


def iv_bolus_concentration(t, dose, cl, volume) -> np.ndarray:
    """One-compartment IV bolus. C(t) = (Dose/V) exp(-(CL/V) t)."""

    t = np.asarray(t, dtype=float)
    dose = np.asarray(dose, dtype=float)
    cl = np.asarray(cl, dtype=float)
    volume = np.asarray(volume, dtype=float)
    kel = cl / volume
    return (dose / volume) * np.exp(-kel * t)


def oral_concentration(t, dose, ka, cl, volume, bioavailability=1.0) -> np.ndarray:
    """One-compartment first-order absorption.

    Supports scalar or batched parameters of shape (n,) with t shaped (T,).
    Returns shape (T,) or (n, T).
    """

    t = np.asarray(t, dtype=float)
    scalar = np.ndim(ka) == 0 and np.ndim(cl) == 0 and np.ndim(volume) == 0 and np.ndim(dose) == 0
    ka = np.atleast_1d(np.asarray(ka, dtype=float))
    cl = np.atleast_1d(np.asarray(cl, dtype=float))
    volume = np.atleast_1d(np.asarray(volume, dtype=float))
    dose = np.atleast_1d(np.asarray(dose, dtype=float))
    bioavailability = np.atleast_1d(np.asarray(bioavailability, dtype=float))
    kel = cl / volume
    ka_ = ka[:, None]
    kel_ = kel[:, None]
    vol_ = volume[:, None]
    dose_ = dose[:, None]
    f_ = bioavailability[:, None]
    tt = t[None, :]
    close = np.isclose(ka_, kel_, rtol=1e-5, atol=1e-8)
    denom = np.where(close, 1.0, ka_ - kel_)
    standard = (f_ * dose_ * ka_ / (vol_ * denom)) * (np.exp(-kel_ * tt) - np.exp(-ka_ * tt))
    limit = (f_ * dose_ * ka_ * tt / vol_) * np.exp(-ka_ * tt)
    out = np.where(close, limit, standard)
    if scalar:
        return out[0]
    return out
