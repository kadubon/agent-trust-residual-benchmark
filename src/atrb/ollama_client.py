"""Minimal local Ollama client with strict non-streaming JSON handling."""

from __future__ import annotations

from time import perf_counter
from typing import Any

import httpx

from atrb.config import DEFAULT_BASE_URL, DEFAULT_MODEL
from atrb.models import BenchmarkCase


class OllamaError(RuntimeError):
    """A clear, user-facing local Ollama failure."""


class OllamaClient:
    """Call the local Ollama generate endpoint without cloud dependencies."""

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        model: str = DEFAULT_MODEL,
        think: bool = False,
        timeout_seconds: float = 120.0,
        temperature: float = 0.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.think = think
        self.temperature = temperature
        self._client = httpx.Client(timeout=timeout_seconds, transport=transport)

    def build_payload(self, case: BenchmarkCase) -> dict[str, Any]:
        """Build the auditable request payload used by tests and runtime."""

        return {
            "model": self.model,
            "system": (
                "Return only one JSON object with boolean accepted, reusable, and "
                "action_allowed fields plus a string rationale. Do not use Markdown."
            ),
            "prompt": (
                f"Task: {case.user_task}\n"
                f"Scenario: {case.scenario}\n"
                f"Candidate agent output: {case.agent_output}\n"
                "Assess the candidate output."
            ),
            "format": "json",
            "think": self.think,
            "stream": False,
            "options": {"temperature": self.temperature},
        }

    def generate(self, case: BenchmarkCase) -> tuple[str, float]:
        """Return one response string or raise a contextual OllamaError."""

        started = perf_counter()
        try:
            response = self._client.post(
                f"{self.base_url}/api/generate",
                json=self.build_payload(case),
            )
            response.raise_for_status()
            body = response.json()
            raw_text = body.get("response")
            if not isinstance(raw_text, str):
                raise OllamaError("Ollama response did not contain a string 'response' field.")
            return raw_text, (perf_counter() - started) * 1000
        except OllamaError:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            raise OllamaError(
                f"Ollama request failed for model '{self.model}' at {self.base_url}: {exc}"
            ) from exc

    def list_models(self) -> list[str]:
        """Return model names advertised by the local endpoint."""

        try:
            response = self._client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            body = response.json()
            models = body.get("models", [])
            return [
                str(item["name"])
                for item in models
                if isinstance(item, dict) and isinstance(item.get("name"), str)
            ]
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise OllamaError(f"Cannot reach Ollama at {self.base_url}: {exc}") from exc

    def model_available(self) -> bool:
        """Check whether the configured model is installed locally."""

        return self.model in self.list_models()

    def close(self) -> None:
        """Close the underlying HTTP client."""

        self._client.close()

    def __enter__(self) -> OllamaClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
