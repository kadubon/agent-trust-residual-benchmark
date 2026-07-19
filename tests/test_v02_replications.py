from __future__ import annotations

from pathlib import Path

import httpx

from atrb.config import (
    DEFAULT_BASE_URL,
    DEFAULT_V02_CASES_PATH,
    DEFAULT_V02_EVALUATION_TIME,
)
from atrb.ollama_client import OllamaClient
from atrb.v02_mock import V02_MOCK_MODEL
from atrb.v02_models import V02RunConfig
from atrb.v02_runner import run_v02_benchmark


def _config() -> V02RunConfig:
    return V02RunConfig(
        mode="mock",
        requested_mode="mock",
        model=V02_MOCK_MODEL,
        base_url=DEFAULT_BASE_URL,
        evaluation_time=DEFAULT_V02_EVALUATION_TIME,
        replications=3,
        cases_path=str(DEFAULT_V02_CASES_PATH),
    )


def test_v02_mock_replications_are_reproducible_and_record_variation(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first_result = run_v02_benchmark(_config(), first)
    second_result = run_v02_benchmark(_config(), second)
    assert (first / "raw_replications.jsonl").read_bytes() == (
        second / "raw_replications.jsonl"
    ).read_bytes()
    metrics = first_result["replication_metrics"]
    assert metrics == second_result["replication_metrics"]
    assert metrics["raw_replication_count"] == 36 * 3
    assert metrics["per_case"]["N005"]["acceptance_variance"] > 0
    assert metrics["per_case"]["N007"]["permission_inconsistency_frequency"] > 0
    assert metrics["replication_level_false_rejection_count"] > 0
    assert metrics["parse_failure_count"] == 1
    assert metrics["successful_response_sensitivity"]["decision_count"] == 107
    assert "cases_with_multiple_successful_response_hashes" in metrics[
        "successful_response_variation"
    ]


def test_v02_ollama_request_failures_are_recorded_per_replication(
    tmp_path: Path,
) -> None:
    def fail_request(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, request=request, json={"error": "simulated unavailable"})

    config = V02RunConfig(
        mode="ollama",
        requested_mode="ollama",
        model="local-test-model",
        base_url="http://localhost:11434",
        evaluation_time=DEFAULT_V02_EVALUATION_TIME,
        replications=2,
        continue_on_error=True,
        cases_path=str(DEFAULT_V02_CASES_PATH),
        case_ids=["N001"],
    )
    with OllamaClient(
        model=config.model,
        transport=httpx.MockTransport(fail_request),
    ) as client:
        result = run_v02_benchmark(config, tmp_path, client)
    replication_metrics = result["replication_metrics"]
    assert replication_metrics["raw_replication_count"] == 2
    assert replication_metrics["request_failure_count"] == 2
    assert replication_metrics["successful_response_sensitivity"]["decision_count"] == 0
    assert replication_metrics["successful_response_variation"][
        "case_count_with_successful_response"
    ] == 0
    assert (tmp_path / "report.md").is_file()
