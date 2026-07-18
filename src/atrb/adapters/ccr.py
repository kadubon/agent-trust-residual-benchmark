"""CCR-compatible independent workcell simulation."""

from __future__ import annotations

from typing import Any

from atrb.models import BenchmarkCase
from atrb.validators import ValidationState

REQUIRED_WORKCELL_FIELDS = {
    "agent_family",
    "model_id",
    "prompt_hash",
    "seed",
    "verifier_id",
    "independence_group",
}


def _default_workcells(case: BenchmarkCase) -> list[dict[str, Any]]:
    """Create deterministic independent workcells for ordinary fixtures."""

    return [
        {
            "role": "proposal",
            "agent_family": "rules-a",
            "model_id": "deterministic-proposer-v1",
            "prompt_hash": f"{case.case_id}-proposal",
            "seed": 11,
            "verifier_id": "verifier-a",
            "independence_group": "group-a",
        },
        {
            "role": "critique",
            "agent_family": "rules-b",
            "model_id": "deterministic-critic-v1",
            "prompt_hash": f"{case.case_id}-critique",
            "seed": 23,
            "verifier_id": "verifier-b",
            "independence_group": "group-b",
        },
        {
            "role": "verification",
            "agent_family": "rules-c",
            "model_id": "deterministic-verifier-v1",
            "prompt_hash": f"{case.case_id}-verify",
            "seed": 37,
            "verifier_id": "verifier-c",
            "independence_group": "group-c",
        },
        {
            "role": "integration",
            "agent_family": "rules-d",
            "model_id": "deterministic-integrator-v1",
            "prompt_hash": f"{case.case_id}-integrate",
            "seed": 41,
            "verifier_id": "verifier-d",
            "independence_group": "group-d",
        },
    ]


def apply(case: BenchmarkCase, state: ValidationState) -> None:
    """Reject repeated same-origin outputs masquerading as independent consensus."""

    evidence = case.evidence_packet
    workcells = evidence.workcells or _default_workcells(case)
    state.elapsed_ms += 4.0 + len(workcells) * 1.5
    state.cost_units += 3.0 + len(workcells) * 2.0
    state.inspect("workcells", "verifier_source", "artifact_source")

    complete = all(set(workcell) >= REQUIRED_WORKCELL_FIELDS for workcell in workcells)
    signatures = {
        tuple(workcell.get(field) for field in sorted(REQUIRED_WORKCELL_FIELDS))
        for workcell in workcells
    }
    groups = {str(workcell.get("independence_group")) for workcell in workcells}
    if not complete or len(signatures) < 2 or len(groups) < 2:
        state.add_failure("non_independent_consensus_detected")

    if evidence.verifier_independence_required:
        proposal_groups = {
            workcell.get("independence_group")
            for workcell in workcells
            if workcell.get("role") == "proposal"
        }
        independent_verifiers = [
            workcell
            for workcell in workcells
            if workcell.get("role") == "verification"
            and workcell.get("independence_group") not in proposal_groups
        ]
        if not independent_verifiers:
            state.add_failure("verifier_independence_insufficient")

    if (
        evidence.verifier_source
        and evidence.artifact_source
        and evidence.verifier_source == evidence.artifact_source
    ):
        state.add_failure("verifier_same_origin_as_artifact")
