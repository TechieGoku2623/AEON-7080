"""Canonical experiment fingerprints."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=_default)


def _default(value: Any) -> Any:
    if isinstance(value, set):
        return sorted(value)
    raise TypeError(f"Cannot fingerprint {type(value).__name__}")


def fingerprint(payload: Any) -> str:
    digest = hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
    return digest


def experiment_record(
    *,
    config: dict,
    seed: int,
    model_versions: dict[str, str],
    software_version: str,
) -> dict:
    body = {
        "config": config,
        "seed": seed,
        "model_versions": model_versions,
        "software_version": software_version,
    }
    return {
        "seed": seed,
        "software_version": software_version,
        "model_versions": model_versions,
        "config_fingerprint": fingerprint(body),
        "replay": (
            "Replay re-executes this configuration with the same seed. "
            "It does not reuse stored numeric outputs as a substitute for the solver."
        ),
    }
