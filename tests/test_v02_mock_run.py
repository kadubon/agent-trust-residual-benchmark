from __future__ import annotations

import json
from pathlib import Path

from atrb.config import (
    DEFAULT_BASE_URL,
    DEFAULT_V02_CASES_PATH,
    DEFAULT_V02_EVALUATION_TIME,
)
from atrb.v02_mock import V02_MOCK_MODEL
from atrb.v02_models import V02RunConfig
from atrb.v02_runner import run_v02_benchmark


def test_v02_mock_run_writes_complete_artifact_set(tmp_path: Path) -> None:
    config = V02RunConfig(
        mode="mock",
        requested_mode="mock",
        model=V02_MOCK_MODEL,
        base_url=DEFAULT_BASE_URL,
        evaluation_time=DEFAULT_V02_EVALUATION_TIME,
        replications=3,
        cases_path=str(DEFAULT_V02_CASES_PATH),
    )
    result = run_v02_benchmark(config, tmp_path)
    expected = {
        "config.json",
        "cases.normalized.json",
        "raw_outputs.jsonl",
        "raw_replications.jsonl",
        "decisions.jsonl",
        "residuals.jsonl",
        "ledgers.jsonl",
        "metrics.json",
        "replication_metrics.json",
        "result_summary.json",
        "report.md",
        "failure_log.md",
        "positive_control_log.md",
        "near_miss_log.md",
        "field_inconsistency_log.md",
        "runtime.json",
        "demo_script.md",
    }
    assert expected <= {path.name for path in tmp_path.iterdir()}
    assert len((tmp_path / "raw_replications.jsonl").read_text().splitlines()) == 108
    assert len((tmp_path / "decisions.jsonl").read_text().splitlines()) == 288
    summary = json.loads((tmp_path / "result_summary.json").read_text(encoding="utf-8"))
    assert summary["validity_status"] == "balanced_fixture_conformance_complete"
    assert result["metrics"]["positive_control_count"] == 18
    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "does not prove real-world safety" in report
    assert "Raw rationale coding is separate" in report
