"""Heuristic flags for possibly sensitive fields.

This is not de-identification and does not claim to find every identifier.
"""

from __future__ import annotations

import re

EMAIL = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PHONE = re.compile(r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{3}\)?[\s-]?)\d{3}[\s-]?\d{4}")
SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
LONG_ID = re.compile(r"\b\d{9,}\b")

NAME_HINTS = {
    "name",
    "first_name",
    "last_name",
    "patient_name",
    "email",
    "e-mail",
    "phone",
    "telephone",
    "address",
    "ssn",
    "social_security",
    "mrn",
    "medical_record",
    "dob",
    "date_of_birth",
    "national_id",
}


def scan_table(columns: list[str], rows: list[dict], sample_limit: int = 200) -> dict:
    flags = []
    for column in columns:
        if column.strip().lower() in NAME_HINTS:
            flags.append(
                {
                    "column": column,
                    "kind": "column_name",
                    "detail": f"Column name '{column}' looks like an identifier.",
                }
            )
    for row in rows[:sample_limit]:
        for column, value in row.items():
            if not isinstance(value, str):
                continue
            kind = None
            if EMAIL.search(value):
                kind = "email"
            elif SSN.search(value):
                kind = "ssn_like"
            elif PHONE.search(value):
                kind = "phone_like"
            elif LONG_ID.search(value):
                kind = "long_numeric_id"
            if kind:
                flags.append({"column": column, "kind": kind, "detail": "A sampled value matched a heuristic."})
                break
    unique = []
    seen = set()
    for flag in flags:
        key = (flag["column"], flag["kind"])
        if key not in seen:
            seen.add(key)
            unique.append(flag)
    return {
        "potentially_sensitive": bool(unique),
        "flags": unique,
        "guarantee": "This scan does not guarantee de-identification or find every identifier.",
        "warning": (
            "POTENTIALLY SENSITIVE DATA. This dataset may contain identifiers or sensitive information. "
            "Verify that you are authorized to use this data. Remove unnecessary identifiers where appropriate. "
            "Follow applicable privacy and security requirements."
        )
        if unique
        else None,
    }
