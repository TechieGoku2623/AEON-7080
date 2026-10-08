"""Language-model providers may narrate tool evidence. They do not compute it."""

from __future__ import annotations

import os

from ai_scientist.critic.critic import critique_narrative


class DeterministicProvider:
    name = "deterministic"

    def narrate(self, evidence: str) -> str | None:
        return None


class OpenAICompatibleProvider:
    name = "openai-compatible"

    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    def narrate(self, evidence: str) -> str | None:
        import httpx

        prompt = (
            "Rewrite the evidence in plain language. Use only numbers that already appear. "
            "Do not add citations, doses for real patients, or claims of clinical effect.\n\n"
            + evidence
        )
        try:
            response = httpx.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0,
                },
                timeout=20,
            )
            response.raise_for_status()
            text = response.json()["choices"][0]["message"]["content"]
        except Exception:
            return None
        flags = critique_narrative(text, evidence)
        if flags:
            return None
        return text


def configured_provider():
    base = os.environ.get("AEON_LLM_BASE_URL")
    key = os.environ.get("AEON_LLM_API_KEY")
    model = os.environ.get("AEON_LLM_MODEL", "local")
    if base and key:
        return OpenAICompatibleProvider(base, key, model)
    return DeterministicProvider()
