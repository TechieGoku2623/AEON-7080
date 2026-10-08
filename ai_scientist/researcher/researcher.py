"""Reference retrieval.

No provider is configured. The researcher returns no citations rather than inventing them.
"""

from __future__ import annotations


def retrieve(query: str, external_enabled: bool = False) -> dict:
    if not external_enabled:
        return {
            "query": query,
            "references": [],
            "note": "External research is disabled. No citations were generated.",
        }
    return {
        "query": query,
        "references": [],
        "note": "No retrieval provider is configured. Refusing to invent citations.",
    }
