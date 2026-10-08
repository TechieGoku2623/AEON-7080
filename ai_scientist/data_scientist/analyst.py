"""Computed answers about a table. Unimplemented questions are refused."""

from __future__ import annotations

import pandas as pd


def analyze_question(frame: pd.DataFrame, question: str) -> dict:
    text = " ".join(question.lower().split())
    if not text:
        return _refuse("The question is empty.")
    if "missing" in text:
        missing = {str(col): float(frame[col].isna().mean()) for col in frame.columns}
        return _answer(
            "missingness",
            "Computed the fraction of missing values in each column.",
            {"missing_fraction_by_column": missing},
        )
    if "correlat" in text or "associated" in text:
        numeric = frame.select_dtypes(include="number")
        if numeric.shape[1] < 2:
            return _refuse("At least two numeric columns are required for a correlation.")
        target = _pick_target(numeric.columns, text) or str(numeric.columns[0])
        corr = numeric.corr(numeric_only=True)[target].drop(labels=[target]).sort_values(key=lambda s: s.abs(), ascending=False)
        top = {str(k): float(v) for k, v in corr.head(8).items() if v == v}
        regression = _ols(numeric, target)
        return _answer(
            "association",
            f"Computed Pearson correlations with {target}.",
            {"target": target, "pearson": top, "regression": regression},
        )
    if "trend" in text or "heart" in text:
        column = _pick_target(frame.columns, text) or _first_numeric(frame)
        if column is None:
            return _refuse("No numeric column is available for a trend.")
        series = pd.to_numeric(frame[column], errors="coerce").dropna()
        if series.empty:
            return _refuse(f"{column} has no numeric values.")
        return _answer(
            "trend",
            f"Computed the order of values in {column}. This is not a time-series model unless that column is time.",
            {
                "column": column,
                "count": int(series.shape[0]),
                "first": float(series.iloc[0]),
                "last": float(series.iloc[-1]),
                "mean": float(series.mean()),
                "change_last_minus_first": float(series.iloc[-1] - series.iloc[0]),
            },
        )
    if "summar" in text or "describe" in text or "what can i do" in text:
        numeric = frame.select_dtypes(include="number")
        summary = {}
        for column in numeric.columns:
            summary[str(column)] = {
                "mean": float(numeric[column].mean()),
                "min": float(numeric[column].min()),
                "max": float(numeric[column].max()),
            }
        workflows = []
        names = {c.lower() for c in frame.columns}
        if names & {"glucose", "glucose_mg_dl", "fasting_glucose"}:
            workflows.append("Map glucose, age, and weight into the PK/PD experiment after you confirm the mapping.")
        if names & {"heart_rate", "hr", "heart_rate_bpm"}:
            workflows.append("Use the heart-rate column as the cardiovascular initial condition after confirmation.")
        if not workflows:
            workflows.append("Profile the table, then confirm a mapping before any simulation.")
        return _answer("summary", "Computed numeric summaries.", {"summary": summary, "workflows": workflows})
    return _refuse(
        "This data analyst can compute missingness, Pearson associations, a simple trend, or a summary. "
        "It will not guess an answer."
    )


def _ols(frame: pd.DataFrame, target: str) -> dict | None:
    predictors = [c for c in frame.columns if c != target]
    if not predictors:
        return None
    try:
        import statsmodels.api as sm
    except ImportError:
        return {"available": False, "note": "statsmodels is not installed. Pearson correlations are the computed result."}
    subset = frame[[target, *predictors]].dropna()
    if len(subset) < len(predictors) + 2:
        return {"available": False, "note": "Not enough complete rows for a regression."}
    y = subset[target].to_numpy(dtype=float)
    x = sm.add_constant(subset[predictors].to_numpy(dtype=float), has_constant="add")
    try:
        fit = sm.OLS(y, x).fit()
    except Exception as exc:  # noqa: BLE001 — return the failure instead of a fake fit
        return {"available": False, "note": f"Regression did not run: {exc}"}
    names = ["intercept", *[str(c) for c in predictors]]
    return {
        "available": True,
        "n": int(len(subset)),
        "rsquared": float(fit.rsquared),
        "coefficients": {name: float(coef) for name, coef in zip(names, fit.params)},
        "note": "Ordinary least squares on the complete rows. Not a causal estimate.",
    }


def _pick_target(columns, text: str) -> str | None:
    for column in columns:
        if str(column).lower() in text:
            return str(column)
    for column in columns:
        token = str(column).lower().replace("_", " ")
        if token in text:
            return str(column)
    return None


def _first_numeric(frame: pd.DataFrame) -> str | None:
    numeric = frame.select_dtypes(include="number")
    if numeric.shape[1] == 0:
        return None
    return str(numeric.columns[0])


def _answer(kind: str, method: str, result: dict) -> dict:
    return {
        "supported": True,
        "kind": kind,
        "method": method,
        "result": result,
        "disclaimer": "Computed from the loaded table. Not medical advice.",
    }


def _refuse(reason: str) -> dict:
    return {"supported": False, "reason": reason, "result": None}
