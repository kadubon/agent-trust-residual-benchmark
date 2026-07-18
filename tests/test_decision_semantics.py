from __future__ import annotations

import json
from pathlib import Path

from atrb.benchmark import run_benchmark
from atrb.config import DEFAULT_CASES_PATH, RunConfig
from atrb.mock_llm import MockLLM


def _run(tmp_path: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    config = RunConfig(
        mode="mock",
        requested_mode="mock",
        cases_path=str(DEFAULT_CASES_PATH),
    )
    run_benchmark(config, tmp_path, MockLLM())
    decisions = [
        json.loads(line)
        for line in (tmp_path / "decisions.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    cases = json.loads((tmp_path / "cases.normalized.json").read_text(encoding="utf-8"))
    return decisions, cases


def test_final_condition_detects_every_expected_failure(tmp_path: Path) -> None:
    decisions, cases = _run(tmp_path)
    final = {
        item["case_id"]: item
        for item in decisions
        if item["condition"] == "fcc_temporal_claims"
    }
    for case in cases:
        decision = final[case["case_id"]]
        assert set(case["expected_failures"]) <= set(decision["detected_failures"])
        assert set(case["expected_residuals"]) <= set(decision["residuals"])
        assert decision["accepted"] is False
        assert decision["settled"] is False
        assert decision["reusable"] is False
        assert decision["action_allowed"] is False


def test_human_rejection_dominates_positive_signals(tmp_path: Path) -> None:
    decisions, _ = _run(tmp_path)
    decision = next(
        item
        for item in decisions
        if item["case_id"] == "C012" and item["condition"] == "pic_fost_pfg"
    )
    assert "human_override_rejected" in decision["detected_failures"]
    assert decision["action_allowed"] is False
