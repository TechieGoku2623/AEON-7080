"""One-at-a-time sensitivity. Does not change the caller's parameters."""

from __future__ import annotations

from collections.abc import Callable


def one_at_a_time(
    baseline: dict[str, float],
    names: list[str],
    evaluate: Callable[[dict[str, float]], float],
    fraction: float = 0.2,
) -> dict:
    if not 0 < fraction < 1:
        raise ValueError("fraction must be between 0 and 1.")
    base_value = float(evaluate(dict(baseline)))
    rows = []
    for name in names:
        low = dict(baseline)
        high = dict(baseline)
        low[name] = float(baseline[name]) * (1.0 - fraction)
        high[name] = float(baseline[name]) * (1.0 + fraction)
        low_value = float(evaluate(low))
        high_value = float(evaluate(high))
        rows.append(
            {
                "parameter": name,
                "baseline_parameter": float(baseline[name]),
                "low_parameter": low[name],
                "high_parameter": high[name],
                "baseline_output": base_value,
                "low_output": low_value,
                "high_output": high_value,
                "swing": abs(high_value - low_value),
            }
        )
    rows.sort(key=lambda row: row["swing"], reverse=True)
    return {
        "method": "one-at-a-time",
        "fraction": fraction,
        "baseline_output": base_value,
        "bars": rows,
        "note": (
            "Each parameter is moved alone by the stated fraction. "
            "Interactions are not estimated."
        ),
    }
