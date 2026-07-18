from __future__ import annotations

from pathlib import Path

from atrb.benchmark import run_benchmark
from atrb.config import DEFAULT_CASES_PATH, RunConfig
from atrb.mock_llm import MockLLM


def test_metrics_show_progressive_detection(tmp_path: Path) -> None:
    config = RunConfig(
        mode="mock",
        requested_mode="mock",
        cases_path=str(DEFAULT_CASES_PATH),
    )
    metrics = run_benchmark(config, tmp_path, MockLLM())
    conditions = metrics["conditions"]
    assert conditions["raw_model_output"]["verification_yield"] == 0.0
    assert conditions["raw_model_output"]["false_promotion_rate"] == 0.9444
    assert conditions["fcc_temporal_claims"]["verification_yield"] == 1.0
    assert conditions["fcc_temporal_claims"]["false_promotion_rate"] == 0.0
    assert (
        conditions["ccr_independent_workcells"][
            "non_independent_consensus_detection_rate"
        ]
        == 1.0
    )
