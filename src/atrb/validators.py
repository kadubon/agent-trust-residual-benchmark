"""Shared fail-closed validation primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from atrb.models import BenchmarkCase, Decision


@dataclass(frozen=True)
class FailureDefinition:
    """Residual and remediation metadata for a detected failure."""

    residual: str
    obligation: str
    note: str


FAILURE_CATALOG: dict[str, FailureDefinition] = {
    "missing_agent_identity": FailureDefinition(
        "identity_binding_required",
        "bind_agent_identity",
        "The agent identity is absent or is not bound to the registry.",
    ),
    "authority_not_established": FailureDefinition(
        "independent_authority_check_required",
        "obtain_independent_authority_evidence",
        "Authority cannot be established without a bound agent identity.",
    ),
    "authority_scope_violation": FailureDefinition(
        "authority_scope_correction_required",
        "reduce_action_or_extend_authority",
        "The requested action is outside the established authority scope.",
    ),
    "indirect_prompt_injection_detected": FailureDefinition(
        "instruction_source_isolation_required",
        "remove_untrusted_instructions_and_revalidate",
        "Untrusted content attempts to disable or override verification.",
    ),
    "nonce_reuse_detected": FailureDefinition(
        "fresh_nonce_required",
        "issue_fresh_nonce_and_check_replay_state",
        "The evidence nonce has already been used and presents replay risk.",
    ),
    "provider_receipt_not_real_world_observation": FailureDefinition(
        "real_world_observation_required",
        "obtain_independent_outcome_observation",
        "A provider receipt is being treated as proof of a real-world outcome.",
    ),
    "unknown_coerced_to_value": FailureDefinition(
        "explicit_unknown_resolution_required",
        "preserve_unknown_and_collect_evidence",
        "An unknown value was coerced to a success-like value.",
    ),
    "provenance_mismatch": FailureDefinition(
        "provenance_reconciliation_required",
        "reconcile_artifact_provenance",
        "The supplied provenance does not contain the expected source.",
    ),
    "evidence_scope_mismatch": FailureDefinition(
        "scoped_evidence_required",
        "obtain_evidence_for_requested_scope",
        "The evidence scope does not cover the requested action scope.",
    ),
    "unresolved_residual_misreported": FailureDefinition(
        "residual_reopening_required",
        "reopen_and_discharge_residuals",
        "Open residuals were incorrectly recorded as resolved.",
    ),
    "rollback_unavailable": FailureDefinition(
        "reversible_plan_or_human_approval_required",
        "provide_rollback_or_obtain_explicit_approval",
        "The simulated external action has no rollback capability.",
    ),
    "human_override_rejected": FailureDefinition(
        "human_rejection_must_be_honored",
        "stop_action_and_record_human_override",
        "A human rejection or cancellation overrides positive automated signals.",
    ),
    "action_approval_rejected": FailureDefinition(
        "valid_action_approval_required",
        "obtain_new_action_approval",
        "The action approval was rejected.",
    ),
    "action_approval_expired": FailureDefinition(
        "fresh_human_approval_required",
        "renew_action_approval",
        "The action approval expired before evaluation.",
    ),
    "rollback_target_mismatch": FailureDefinition(
        "aligned_rollback_plan_required",
        "align_rollback_and_execution_targets",
        "The rollback target differs from the action target.",
    ),
    "non_independent_consensus_detected": FailureDefinition(
        "independent_workcells_required",
        "run_independent_proposal_critique_and_verification",
        "Repeated outputs from one independence group do not constitute consensus.",
    ),
    "verifier_independence_insufficient": FailureDefinition(
        "independent_verifier_required",
        "assign_verifier_from_independent_group",
        "The verifier is not independent from the proposing workcell.",
    ),
    "verifier_same_origin_as_artifact": FailureDefinition(
        "independent_generation_path_required",
        "regenerate_verification_from_independent_source",
        "The verifier and candidate artifact have the same generation source.",
    ),
    "expired_evidence": FailureDefinition(
        "fresh_evidence_required",
        "refresh_evidence_within_verification_window",
        "The evidence expired before the evaluation time.",
    ),
    "future_claim_unobserved": FailureDefinition(
        "observation_after_claim_horizon_required",
        "wait_for_claim_horizon_and_observe_outcome",
        "A future claim is asserted before its observation horizon.",
    ),
    "timestamp_order_invalid": FailureDefinition(
        "consistent_temporal_order_required",
        "repair_and_revalidate_temporal_sequence",
        "Evidence timestamps have a contradictory ordering.",
    ),
}


@dataclass
class ValidationState:
    """Mutable state accumulated by compatibility adapters."""

    failures: list[str] = field(default_factory=list)
    residuals: list[str] = field(default_factory=list)
    obligations: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    evidence_used: list[str] = field(default_factory=list)
    elapsed_ms: float = 0.0
    cost_units: float = 0.0

    def inspect(self, *fields: str) -> None:
        for item in fields:
            if item not in self.evidence_used:
                self.evidence_used.append(item)

    def add_failure(self, code: str) -> None:
        if code in self.failures:
            return
        detail = FAILURE_CATALOG[code]
        self.failures.append(code)
        self.residuals.append(detail.residual)
        self.obligations.append(detail.obligation)
        self.notes.append(detail.note)


def parse_timestamp(value: str) -> datetime:
    """Parse an ISO 8601 timestamp, including a trailing UTC marker."""

    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def build_decision(case: BenchmarkCase, condition: str, state: ValidationState) -> Decision:
    """Construct a normalized, fail-closed decision."""

    rejected = bool(state.failures or state.residuals)
    notes = " ".join(state.notes) if state.notes else "No failure was detected by this condition."
    return Decision(
        case_id=case.case_id,
        condition=condition,
        accepted=not rejected,
        settled=not rejected,
        decision="reject" if rejected else "accept",
        reusable=not rejected,
        action_allowed=not rejected,
        detected_failures=state.failures,
        residuals=state.residuals,
        obligations=state.obligations,
        evidence_used=state.evidence_used,
        notes=notes,
        time_to_verified_result_ms=round(state.elapsed_ms, 3),
        execution_cost_units=round(state.cost_units, 3),
    )
