from __future__ import annotations

import json

import httpx

from atrb.benchmark import load_cases
from atrb.config import DEFAULT_CASES_PATH
from atrb.ollama_client import OllamaClient


def test_ollama_payload_is_non_streaming_and_disables_thinking() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured.update(json.loads(request.content))
        return httpx.Response(200, json={"response": "{}"})

    case = load_cases(DEFAULT_CASES_PATH, ["C001"])[0]
    with OllamaClient(transport=httpx.MockTransport(handler)) as client:
        client.generate(case)

    assert captured["model"] == "qwen3.6:35b-a3b"
    assert captured["think"] is False
    assert captured["stream"] is False
    assert captured["format"] == "json"
    assert captured["options"] == {"temperature": 0.0}
