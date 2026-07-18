"""Validated data models for cases, decisions, and ledgers."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class HumanOverride(BaseModel):
    """A human decision that dominates automated positive signals."""

    status: Literal["none", "approved", "rejected", "cancelled"] = "none"
    reason: str | None = None


class EvidencePacket(BaseModel):
    """Evidence supplied with candidate agent work.

    Extra fields are allowed so future fixtures can extend the benchmark without
    weakening validation of the common fields.
    """

    model_config = ConfigDict(extra="allow")

    agent_id: str | None = None
    agent_registry_bound: bool = True
    authority_scope: list[str] = Field(default_factory=list)
    requested_action: str
    action_scope: str = "simulation"
    evidence_scope: list[str] = Field(default_factory=list)
    nonce: str
    nonce_reused: bool = False
    issued_at: str
    expires_at: str
    provider_receipt: str | None = None
    real_world_observation: str | None = None
    provenance: list[str] = Field(default_factory=list)
    expected_provenance: str | None = None
    external_action: bool = False
    rollback_supported: bool = True
    action_target: str | None = None
    rollback_target: str | None = None
    claimed_outcome_from_receipt: bool = False
    unknown_fields: list[str] = Field(default_factory=list)
    unknown_coerced_to_value: bool = False
    open_residuals: list[str] = Field(default_factory=list)
    residual_status: Literal["open", "resolved", "none"] = "none"
    action_approval_status: Literal["not_required", "approved", "rejected"] = "not_required"
    action_approval_expires_at: str | None = None
    workcells: list[dict[str, Any]] = Field(default_factory=list)
    verifier_independence_required: bool = False
    verifier_source: str | None = None
    artifact_source: str | None = None
    observation_time: str | None = None
    claim_horizon: str | None = None
    verification_window_start: str | None = None
    verification_window_end: str | None = None


class BenchmarkCase(BaseModel):
    """One safe, simulated failure case."""

    case_id: str = Field(pattern=r"^C\d{3}$")
    title: str
    category: str
    scenario: str
    user_task: str
    agent_output: str
    evidence_packet: EvidencePacket
    human_override: HumanOverride
    expected_failures: list[str] = Field(min_length=1)
    expected_decision: Literal["accept", "reject"]
    expected_residuals: list[str] = Field(min_length=1)
    expected_reusable: bool


class RawJudgment(BaseModel):
    """Strict schema for untrusted model output."""

    model_config = ConfigDict(extra="forbid")

    accepted: bool
    reusable: bool
    action_allowed: bool
    rationale: str


class Decision(BaseModel):
    """Normalized output from every comparison condition."""

    case_id: str
    condition: str
    accepted: bool
    settled: bool
    decision: Literal["accept", "reject", "parse_failed"]
    reusable: bool
    action_allowed: bool
    detected_failures: list[str]
    residuals: list[str]
    obligations: list[str]
    evidence_used: list[str]
    notes: str
    time_to_verified_result_ms: float = Field(ge=0)
    execution_cost_units: float = Field(ge=0)


class Ledger(BaseModel):
    """Finite FOST-compatible claim ledger emitted by layered conditions."""

    case_id: str
    condition: str
    claims: list[str]
    support: list[str]
    unknowns: list[str]
    obligations: list[str]
    residuals: list[str]
    environment_assumptions: list[str]


class RawOutput(BaseModel):
    """Captured response or failure from a model client."""

    case_id: str
    mode: str
    model: str
    raw_text: str
    parse_status: Literal["valid", "parse_failed", "request_failed"]
    error: str | None = None
    elapsed_ms: float = Field(ge=0)
