from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from atrb.benchmark import run_benchmark
from atrb.config import DEFAULT_CASES_PATH, PROJECT_ROOT, RunConfig
from atrb.mock_llm import MockLLM


def test_mock_run_writes_complete_artifact_set(tmp_path: Path) -> None:
    config = RunConfig(
        mode="mock",
        requested_mode="mock",
        cases_path=str(DEFAULT_CASES_PATH),
    )
    run_benchmark(config, tmp_path, MockLLM())
    expected = {
        "config.json",
        "cases.normalized.json",
        "raw_outputs.jsonl",
        "decisions.jsonl",
        "residuals.jsonl",
        "ledgers.jsonl",
        "metrics.json",
        "runtime.json",
        "result_summary.json",
        "report.md",
        "failure_log.md",
        "demo_script.md",
    }
    assert expected <= {path.name for path in tmp_path.iterdir()}
    decisions = (tmp_path / "decisions.jsonl").read_text(encoding="utf-8").splitlines()
    ledgers = (tmp_path / "ledgers.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(decisions) == 18 * 6
    assert len(ledgers) == 18 * 4

    decision_schema = json.loads(
        (PROJECT_ROOT / "data" / "schemas" / "decision.schema.json").read_text(
            encoding="utf-8"
        )
    )
    decision_validator = jsonschema.Draft202012Validator(decision_schema)
    for line in decisions:
        decision_validator.validate(json.loads(line))

    metrics_schema = json.loads(
        (PROJECT_ROOT / "data" / "schemas" / "metrics.schema.json").read_text(
            encoding="utf-8"
        )
    )
    metrics = json.loads((tmp_path / "metrics.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(metrics_schema).validate(metrics)

    runtime_schema = json.loads(
        (PROJECT_ROOT / "data" / "schemas" / "runtime.schema.json").read_text(
            encoding="utf-8"
        )
    )
    runtime = json.loads((tmp_path / "runtime.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(
        runtime_schema, format_checker=jsonschema.FormatChecker()
    ).validate(runtime)

    result_schema = json.loads(
        (PROJECT_ROOT / "data" / "schemas" / "result_summary.schema.json").read_text(
            encoding="utf-8"
        )
    )
    result_summary = json.loads(
        (tmp_path / "result_summary.json").read_text(encoding="utf-8")
    )
    jsonschema.Draft202012Validator(result_schema).validate(result_summary)
    assert result_summary["observed"]["positive_control_count"] == 0
    assert result_summary["validity_status"] == "fixture_conformance_complete"

    report = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "There are no positive controls" in report
    assert "not general safety, truth, or balanced decision quality" in report
