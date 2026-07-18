"""Dangerous raw-model baseline retained for comparative measurement."""

from __future__ import annotations

from pydantic import ValidationError

from atrb.models import BenchmarkCase, Decision, RawJudgment, RawOutput


def evaluate(case: BenchmarkCase, raw_output: RawOutput) -> Decision:
    """Trust a strict model JSON response without evidence validation.

    Invalid JSON is the only fail-closed behavior in this intentionally unsafe
    condition.
    """

    try:
        judgment = RawJudgment.model_validate_json(raw_output.raw_text)
    except (ValidationError, ValueError):
        return Decision(
            case_id=case.case_id,
            condition="raw_model_output",
            accepted=False,
            settled=False,
            decision="parse_failed",
            reusable=False,
            action_allowed=False,
            detected_failures=["parse_failed"],
            residuals=["unparseable_model_output"],
            obligations=["regenerate_schema_valid_model_output"],
            evidence_used=[],
            notes="The raw model output did not satisfy the strict JSON schema.",
            time_to_verified_result_ms=raw_output.elapsed_ms,
            execution_cost_units=10.0,
        )

    return Decision(
        case_id=case.case_id,
        condition="raw_model_output",
        accepted=judgment.accepted,
        settled=judgment.accepted,
        decision="accept" if judgment.accepted else "reject",
        reusable=judgment.reusable,
        action_allowed=judgment.action_allowed,
        detected_failures=[],
        residuals=[],
        obligations=[],
        evidence_used=[],
        notes=judgment.rationale,
        time_to_verified_result_ms=raw_output.elapsed_ms,
        execution_cost_units=10.0,
    )
