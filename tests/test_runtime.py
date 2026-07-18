from __future__ import annotations

from atrb.models import RawOutput
from atrb.runtime import estimate_full_runtime, render_runtime_estimate


def _observation(case_id: str, elapsed_ms: float) -> RawOutput:
    return RawOutput(
        case_id=case_id,
        mode="ollama",
        model="local-model",
        raw_text="{}",
        parse_status="valid",
        elapsed_ms=elapsed_ms,
    )


def test_runtime_estimate_exposes_assumptions_instead_of_confidence_claim() -> None:
    observations = [
        _observation("C001", 10_000),
        _observation("C002", 20_000),
        _observation("C003", 30_000),
    ]
    estimate = estimate_full_runtime(
        observations,
        target_case_count=18,
        observed_wall_clock_ms=65_000,
        startup_observation_seconds=60.0,
    )

    assert estimate["warm_central_minutes"] == 6.5
    assert estimate["startup_adjusted_minutes"] == 7.17
    assert estimate["recommended_planning_budget_minutes"] == 12
    assert estimate["is_confidence_interval"] is False
    assert "not a statistical confidence" in " ".join(estimate["limitations"])
    assert "not a confidence interval" in render_runtime_estimate(estimate)
