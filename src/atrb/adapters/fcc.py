"""Future Claim Certifier-compatible temporal checks."""

from __future__ import annotations

from atrb.models import BenchmarkCase
from atrb.validators import ValidationState, parse_timestamp


def apply(case: BenchmarkCase, state: ValidationState, evaluation_time: str) -> None:
    """Fail closed on stale, contradictory, or not-yet-observable claims."""

    evidence = case.evidence_packet
    state.elapsed_ms += 3.0
    state.cost_units += 4.0
    state.inspect(
        "issued_at",
        "expires_at",
        "observation_time",
        "claim_horizon",
        "verification_window_start",
        "verification_window_end",
    )
    try:
        evaluated_at = parse_timestamp(evaluation_time)
        issued_at = parse_timestamp(evidence.issued_at)
        expires_at = parse_timestamp(evidence.expires_at)
        invalid_order = issued_at >= expires_at

        if evidence.observation_time:
            invalid_order = invalid_order or parse_timestamp(evidence.observation_time) < issued_at
        if evidence.verification_window_start and evidence.verification_window_end:
            invalid_order = invalid_order or parse_timestamp(
                evidence.verification_window_start
            ) > parse_timestamp(evidence.verification_window_end)
        if invalid_order:
            state.add_failure("timestamp_order_invalid")
        if evaluated_at > expires_at:
            state.add_failure("expired_evidence")
        if (
            evidence.claim_horizon
            and parse_timestamp(evidence.claim_horizon) > evaluated_at
            and evidence.real_world_observation is None
        ):
            state.add_failure("future_claim_unobserved")
    except ValueError:
        state.add_failure("timestamp_order_invalid")
