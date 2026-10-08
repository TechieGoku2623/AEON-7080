"""Fixed-step RK4 and a SciPy solve_ivp wrapper."""

from __future__ import annotations

import numpy as np


def rk4_step(derivative, t: float, y: np.ndarray, dt: float) -> np.ndarray:
    y = np.asarray(y, dtype=float)
    k1 = np.asarray(derivative(t, y), dtype=float)
    k2 = np.asarray(derivative(t + dt / 2.0, y + dt * k1 / 2.0), dtype=float)
    k3 = np.asarray(derivative(t + dt / 2.0, y + dt * k2 / 2.0), dtype=float)
    k4 = np.asarray(derivative(t + dt, y + dt * k3), dtype=float)
    return y + (dt / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)


def integrate_rk4(derivative, y0, duration: float, dt: float) -> tuple[np.ndarray, np.ndarray]:
    if dt <= 0:
        raise ValueError("dt must be positive.")
    if duration < 0:
        raise ValueError("duration must be non-negative.")
    steps = int(np.floor(duration / dt + 1e-9))
    t = np.linspace(0.0, steps * dt, steps + 1)
    y = np.zeros((len(t), len(np.asarray(y0, dtype=float))))
    y[0] = np.asarray(y0, dtype=float)
    for i in range(steps):
        y[i + 1] = rk4_step(derivative, float(t[i]), y[i], dt)
    return t, y


def integrate_scipy(derivative, y0, t_eval: np.ndarray) -> np.ndarray:
    """Return states shaped (T, dim). Raises if SciPy reports failure."""

    from scipy.integrate import solve_ivp

    t_eval = np.asarray(t_eval, dtype=float)
    sol = solve_ivp(
        fun=lambda t, y: np.asarray(derivative(t, y), dtype=float),
        t_span=(float(t_eval[0]), float(t_eval[-1])),
        y0=np.asarray(y0, dtype=float),
        t_eval=t_eval,
        rtol=1e-7,
        atol=1e-9,
        dense_output=False,
    )
    if not sol.success:
        raise RuntimeError(sol.message)
    return sol.y.T
