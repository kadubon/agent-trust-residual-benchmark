"""Deterministic aggregation for benchmark comparison metrics."""

from __future__ import annotations

from collections import defaultdict
from statistics import mean
from typing import Any

from atrb.config import CONDITIONS
from atrb.models import BenchmarkCase, Decision


def _safe_rate(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 4) if denominator else 0.0


def _first_half_life_steps(
    case: BenchmarkCase,
    decisions_by_key: dict[tuple[str, str], Decision],
) -> int | None:
    expected = set(case.expected_residuals)
    threshold = len(expected) / 2
    for step, condition in enumerate(CONDITIONS):
        observed = set(decisions_by_key[(case.case_id, condition)].residuals)
        untracked = len(expected - observed)
        if untracked <= threshold:
            return step
    return None


def compute_metrics(cases: list[BenchmarkCase], decisions: list[Decision]) -> dict[str, Any]:
    """Compute all required metrics from normalized decisions."""

    grouped: dict[str, list[Decision]] = defaultdict(list)
    decisions_by_key = {(item.case_id, item.condition): item for item in decisions}
    for decision in decisions:
        grouped[decision.condition].append(decision)

    expected_failure_count = sum(len(case.expected_failures) for case in cases)
    rejected_cases = {case.case_id for case in cases if case.expected_decision == "reject"}
    non_independent_cases = {
        case.case_id
        for case in cases
        if "non_independent_consensus_detected" in case.expected_failures
    }
    half_lives = {
        case.case_id: _first_half_life_steps(case, decisions_by_key) for case in cases
    }
    per_condition: dict[str, dict[str, Any]] = {}

    for condition_index, condition in enumerate(CONDITIONS):
        condition_decisions = grouped[condition]
        detected_expected = 0
        false_promotions = 0
        consensus_detected = 0
        review_minutes = 0.0

        for case in cases:
            decision = decisions_by_key[(case.case_id, condition)]
            detected_expected += len(set(decision.detected_failures) & set(case.expected_failures))
            if case.case_id in rejected_cases and (
                decision.accepted or decision.reusable or decision.action_allowed
            ):
                false_promotions += 1
            if (
                case.case_id in non_independent_cases
                and "non_independent_consensus_detected" in decision.detected_failures
            ):
                consensus_detected += 1
            review_minutes += (
                len(decision.detected_failures) * 1.25
                + len(decision.residuals) * 0.75
                + (2.0 if not decision.action_allowed else 0.5)
            )

        available_half_lives = [
            steps
            for steps in half_lives.values()
            if steps is not None and steps <= condition_index
        ]
        per_condition[condition] = {
            "time_to_verified_result_ms": round(
                mean(item.time_to_verified_result_ms for item in condition_decisions), 3
            ),
            "verification_yield": _safe_rate(detected_expected, expected_failure_count),
            "expected_failures_detected_count": detected_expected,
            "expected_failures_total_count": expected_failure_count,
            "residual_half_life_steps": (
                round(mean(available_half_lives), 3) if available_half_lives else None
            ),
            "false_promotion_rate": _safe_rate(false_promotions, len(rejected_cases)),
            "false_promotion_count": false_promotions,
            "expected_reject_case_count": len(rejected_cases),
            "non_independent_consensus_detection_rate": _safe_rate(
                consensus_detected, len(non_independent_cases)
            ),
            "non_independent_consensus_detected_count": consensus_detected,
            "non_independent_consensus_case_count": len(non_independent_cases),
            "estimated_human_review_minutes": round(review_minutes, 2),
            "execution_cost_units": round(
                sum(item.execution_cost_units for item in condition_decisions), 2
            ),
            "reusable_artifact_rate": _safe_rate(
                sum(item.reusable for item in condition_decisions), len(condition_decisions)
            ),
            "reusable_artifact_count": sum(item.reusable for item in condition_decisions),
            "accepted_count": sum(item.accepted for item in condition_decisions),
            "accepted_rate": _safe_rate(
                sum(item.accepted for item in condition_decisions), len(condition_decisions)
            ),
            "action_allowed_count": sum(
                item.action_allowed for item in condition_decisions
            ),
            "action_allowed_rate": _safe_rate(
                sum(item.action_allowed for item in condition_decisions),
                len(condition_decisions),
            ),
            "rejected_count": sum(item.decision == "reject" for item in condition_decisions),
            "parse_failed_count": sum(
                item.decision == "parse_failed" for item in condition_decisions
            ),
            "decision_total_count": len(condition_decisions),
        }

    return {
        "case_count": len(cases),
        "condition_count": len(CONDITIONS),
        "decision_count": len(decisions),
        "metric_semantics": {
            "time_to_verified_result_ms": (
                "Mean measured model time or deterministic validator work estimate."
            ),
            "verification_yield": "Detected expected failures divided by all expected failures.",
            "residual_half_life_steps": (
                "Mean first condition step at which at least half of expected residuals "
                "are tracked."
            ),
            "false_promotion_rate": (
                "Rejected cases promoted by accepted, reusable, or action_allowed status."
            ),
            "non_independent_consensus_detection_rate": (
                "Known non-independent consensus cases correctly detected."
            ),
            "estimated_human_review_minutes": (
                "Deterministic total based on failures, residuals, and denied actions."
            ),
            "execution_cost_units": (
                "Deterministic total based on model calls, validators, ledgers, and workcells."
            ),
            "reusable_artifact_rate": "Decisions with reusable=true divided by all decisions.",
        },
        "conditions": per_condition,
    }
