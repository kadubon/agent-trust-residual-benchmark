from __future__ import annotations

from pathlib import Path

from atrb.config import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    DEFAULT_V02_CASES_PATH,
    DEFAULT_V02_EVALUATION_TIME,
)
from atrb.v02_models import V02RunConfig
from atrb.v02_runner import run_v02_benchmark


def test_v02_metrics_include_false_rejection_and_balanced_accuracy(tmp_path: Path) -> None:
    config = V02RunConfig(
        mode="mock",
        requested_mode="mock",
        model=DEFAULT_MODEL,
        base_url=DEFAULT_BASE_URL,
        evaluation_time=DEFAULT_V02_EVALUATION_TIME,
        replications=3,
        cases_path=str(DEFAULT_V02_CASES_PATH),
    )
    result = run_v02_benchmark(config, tmp_path)
    metrics = result["metrics"]
    raw = metrics["conditions"]["raw_model_output"]
    final = metrics["conditions"]["fcc_temporal_claims"]
    assert raw["false_rejection_count"] == 2
    assert raw["false_rejection_rate"] > 0
    assert 0 <= raw["balanced_accuracy"] <= 1
    assert final["accept_recall"] == 1
    assert final["reject_recall"] == 1
    assert final["balanced_accuracy"] == 1
    assert final["safe_action_allowance_accuracy"] == 1
    assert final["safe_reuse_accuracy"] == 1
