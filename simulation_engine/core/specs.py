"""Parameter specifications and range checks."""

from __future__ import annotations

from dataclasses import dataclass


class ParameterError(ValueError):
    """Raised when parameters are missing, mistyped, or outside range.

    Callers must surface this. Nothing here rewrites the user's values.
    """


@dataclass(frozen=True)
class ParameterSpec:
    name: str
    unit: str
    description: str
    minimum: float | None = None
    maximum: float | None = None
    default: float | None = None
    required: bool = True


def validate_parameters(
    parameters: dict,
    specs: list[ParameterSpec],
    *,
    allow_extra: bool = False,
) -> dict:
    if not isinstance(parameters, dict):
        raise ParameterError("Parameters must be an object.")
    unknown = set(parameters) - {spec.name for spec in specs}
    if unknown and not allow_extra:
        raise ParameterError(f"Unknown parameters: {sorted(unknown)}")
    cleaned: dict = {}
    for spec in specs:
        if spec.name not in parameters:
            if spec.required and spec.default is None:
                raise ParameterError(f"Missing parameter: {spec.name}")
            if spec.default is not None and spec.name not in parameters:
                cleaned[spec.name] = spec.default
            continue
        value = parameters[spec.name]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ParameterError(f"{spec.name} must be a number.")
        numeric = float(value)
        if spec.minimum is not None and numeric < spec.minimum:
            raise ParameterError(
                f"{spec.name}={numeric} is below the allowed minimum {spec.minimum} {spec.unit}."
            )
        if spec.maximum is not None and numeric > spec.maximum:
            raise ParameterError(
                f"{spec.name}={numeric} is above the allowed maximum {spec.maximum} {spec.unit}."
            )
        cleaned[spec.name] = numeric
    if allow_extra:
        for key in unknown:
            cleaned[key] = parameters[key]
    return cleaned


def units_map(specs: list[ParameterSpec]) -> dict[str, str]:
    return {spec.name: spec.unit for spec in specs}
