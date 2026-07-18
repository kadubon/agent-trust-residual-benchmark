"""Problem Frame Gate-compatible action checks."""

from __future__ import annotations

from atrb.models import BenchmarkCase
from atrb.validators import ValidationState, parse_timestamp


def apply(case: BenchmarkCase, state: ValidationState, evaluation_time: str) -> None:
    """Gate simulated actions using rollback, approval, and override state."""

    evidence = case.evidence_packet
    state.elapsed_ms += 3.0
    state.cost_units += 4.0
    state.inspect(
        "external_action",
        "rollback_supported",
        "action_target",
        "rollback_target",
        "action_approval_status",
        "action_approval_expires_at",
        "human_override",
    )

    if evidence.external_action and not evidence.rollback_supported:
        state.add_failure("rollback_unavailable")
    if case.human_override.status in {"rejected", "cancelled"}:
        state.add_failure("human_override_rejected")
    if evidence.action_approval_status == "rejected":
        state.add_failure("action_approval_rejected")
    if evidence.action_approval_expires_at:
        try:
            if parse_timestamp(evaluation_time) > parse_timestamp(
                evidence.action_approval_expires_at
            ):
                state.add_failure("action_approval_expired")
        except ValueError:
            state.add_failure("timestamp_order_invalid")
    if (
        evidence.action_target
        and evidence.rollback_target
        and evidence.action_target != evidence.rollback_target
    ):
        state.add_failure("rollback_target_mismatch")
