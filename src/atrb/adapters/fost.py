"""FOST Agent Ledger-compatible residual and obligation checks."""

from __future__ import annotations

from atrb.models import BenchmarkCase, Ledger
from atrb.validators import ValidationState


def apply(case: BenchmarkCase, state: ValidationState) -> None:
    """Detect residual closure claims that conflict with the finite ledger."""

    evidence = case.evidence_packet
    state.elapsed_ms += 2.0
    state.cost_units += 2.0
    state.inspect("open_residuals", "residual_status")
    if evidence.residual_status == "resolved" and evidence.open_residuals:
        state.add_failure("unresolved_residual_misreported")


def build_ledger(case: BenchmarkCase, condition: str, state: ValidationState) -> Ledger:
    """Build a finite, machine-readable claim ledger."""

    evidence = case.evidence_packet
    support = list(evidence.provenance)
    if evidence.real_world_observation:
        support.append("real_world_observation")
    return Ledger(
        case_id=case.case_id,
        condition=condition,
        claims=[case.agent_output],
        support=support,
        unknowns=list(evidence.unknown_fields),
        obligations=list(state.obligations),
        residuals=list(state.residuals),
        environment_assumptions=[
            "All actions are simulations.",
            "Provider receipts are not outcome observations.",
            "Evaluation time is fixed by the run configuration.",
        ],
    )
