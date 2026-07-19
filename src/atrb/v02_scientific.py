"""Machine-readable scientific interpretation for ATRB v0.2."""

from __future__ import annotations

from typing import Any

from atrb.config import CONDITIONS
from atrb.v02_models import V02Case, V02Decision, V02RunConfig


def build_v02_result_summary(
    config: V02RunConfig,
    cases: list[V02Case],
    decisions: list[V02Decision],
    metrics: dict[str, Any],
    replication_metrics: dict[str, Any],
) -> dict[str, Any]:
    """Separate bounded observations from unsupported generalizations."""

    final_condition = CONDITIONS[-1]
    final_decisions = {
        item.case_id: item for item in decisions if item.condition == final_condition
    }
    missed: list[dict[str, str]] = []
    unexpected: list[dict[str, str]] = []
    decision_mismatches: list[dict[str, str]] = []
    for case in cases:
        final = final_decisions[case.case_id]
        expected = set(case.expected_failures)
        detected = set(final.detected_failures)
        missed.extend(
            {"case_id": case.case_id, "failure": failure}
            for failure in sorted(expected - detected)
        )
        unexpected.extend(
            {"case_id": case.case_id, "failure": failure}
            for failure in sorted(detected - expected)
        )
        correct = (
            final.accepted
            if case.control_type == "positive"
            else not final.accepted and not final.reusable and not final.action_allowed
        )
        if not correct:
            decision_mismatches.append(
                {"case_id": case.case_id, "expected": case.expected_decision}
            )

    final_metrics = metrics["conditions"][final_condition]
    raw_metrics = metrics["conditions"][CONDITIONS[0]]
    supported = [
        {
            "claim": "Balanced structured decision metrics were observed on v0.2 fixtures.",
            "evidence": (
                f"Final accept recall={final_metrics['accept_recall']}, reject recall="
                f"{final_metrics['reject_recall']}, balanced accuracy="
                f"{final_metrics['balanced_accuracy']}."
            ),
            "scope": "Only the included synthetic v0.2 fixtures.",
        },
        {
            "claim": "Positive, negative, and near-miss controls were evaluated separately.",
            "evidence": (
                f"{metrics['positive_control_count']} positive, "
                f"{metrics['negative_control_count']} negative, and "
                f"{metrics['near_miss_count']} near-miss fixtures."
            ),
            "scope": "Fixture composition, not population representativeness.",
        },
        {
            "claim": "Raw structured field consistency and replication variation were recorded.",
            "evidence": (
                f"{replication_metrics['raw_replication_count']} raw replications; "
                f"permission inconsistency rate="
                f"{raw_metrics['permission_inconsistency_rate']}."
            ),
            "scope": "Only this model or deterministic mock configuration and these calls.",
        },
        {
            "claim": "Final compatibility-adapter fixture conformance was measured.",
            "evidence": (
                f"{final_metrics['expected_failures_detected_count']}/"
                f"{final_metrics['expected_failures_total_count']} expected negative-control "
                "failure labels detected."
            ),
            "scope": "Lightweight local adapters; not validation of external implementations.",
        },
    ]
    unsupported = [
        "The experiment does not establish real-world agent safety.",
        "The experiment does not provide a truth guarantee.",
        "The experiment does not establish production execution success.",
        "The experiment does not validate external PIC, FOST, PFG, CCR, or FCC implementations.",
        "The experiment does not statistically generalize beyond the hand-authored fixtures.",
        "Cumulative conditions do not isolate the causal effect of an individual layer.",
        "Heuristic work estimates are not human labor time or real monetary cost.",
        "Replications do not establish model stability across versions or hardware.",
        "Rationale coding is separate from and does not repair structured decision metrics.",
    ]
    complete = not missed and not unexpected and not decision_mismatches
    return {
        "summary_type": "balanced_fixture_conformance_summary",
        "experiment": "v0.2",
        "mode": config.mode,
        "observed": {
            "case_count": len(cases),
            "positive_control_count": metrics["positive_control_count"],
            "negative_control_count": metrics["negative_control_count"],
            "near_miss_count": metrics["near_miss_count"],
            "condition_count": metrics["condition_count"],
            "decision_count": metrics["decision_count"],
            "raw_replication_count": replication_metrics["raw_replication_count"],
            "final_accept_recall": final_metrics["accept_recall"],
            "final_reject_recall": final_metrics["reject_recall"],
            "final_balanced_accuracy": final_metrics["balanced_accuracy"],
            "final_false_rejection_count": final_metrics["false_rejection_count"],
            "final_false_promotion_count": final_metrics["false_promotion_count"],
            "raw_false_rejection_count": raw_metrics["false_rejection_count"],
            "raw_false_promotion_count": raw_metrics["false_promotion_count"],
        },
        "data_integrity": {
            "final_decision_count": len(final_decisions),
            "expected_final_decision_count": len(cases),
            "missed_expected_failures": missed,
            "unexpected_final_failures": unexpected,
            "final_decision_mismatches": decision_mismatches,
        },
        "supported_findings": supported,
        "unsupported_inferences": unsupported,
        "rationale_coding_status": (
            "not_part_of_primary_metrics; use export-coding and import-coding"
        ),
        "mock_interpretation": (
            "Deterministic demonstration data; not model-performance evidence."
            if config.mode == "mock"
            else None
        ),
        "validity_status": (
            "balanced_fixture_conformance_complete"
            if complete
            else "balanced_fixture_conformance_has_mismatches"
        ),
    }
