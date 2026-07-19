"""Validated models for the additive ATRB v0.2 experiment."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class V02Approval(BaseModel):
    """Scoped simulated approval state."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["not_required", "approved", "rejected"] = "not_required"
    approved_by: str | None = None
    expires_at: str | None = None
    scope: str | None = None


class V02Verifier(BaseModel):
    """Finite verifier identity and independence metadata."""

    model_config = ConfigDict(extra="forbid")

    verifier_id: str | None = None
    independence_group: str | None = None
    artifact_source: str | None = None
    verifier_source: str | None = None


class V02HumanOverride(BaseModel):
    """A human record that dominates automated action approval."""

    model_config = ConfigDict(extra="forbid")

    status: Literal["none", "approved", "rejected", "cancelled"] = "none"
    reason: str | None = None


class V02EvidencePacket(BaseModel):
    """Evidence and policy facts supplied to one synthetic fixture."""

    model_config = ConfigDict(extra="forbid")

    agent_id: str | None
    agent_registry_bound: bool
    authority_scope: list[str]
    requested_action: str
    action_scope: str
    evidence_scope: str
    nonce: str
    nonce_status: Literal["unused", "consumed"]
    issued_at: str
    expires_at: str
    observation_time: str | None = None
    claim_horizon: str | None = None
    provider_receipt: str | None = None
    receipt_role: Literal["none", "dispatch_only", "outcome_evidence"] = "none"
    real_world_observation: str | None = None
    provenance: list[str]
    expected_source: str | None
    prompt_injection_present: bool = False
    unknown_fields: list[str] = Field(default_factory=list)
    unknown_preserved: bool = True
    external_action: bool = False
    rollback_required: bool = False
    rollback_available: bool = True
    action_target: str | None = None
    rollback_target: str | None = None
    reuse_allowed: bool = True
    open_residuals: list[str] = Field(default_factory=list)
    residual_status: Literal["none", "open", "resolved"] = "none"
    approval: V02Approval = Field(default_factory=V02Approval)
    proposer_independence_group: str | None = None
    verifier: V02Verifier = Field(default_factory=V02Verifier)
    workcells: list[dict[str, Any]] = Field(default_factory=list)


class V02Case(BaseModel):
    """One balanced-control v0.2 synthetic benchmark case."""

    model_config = ConfigDict(extra="forbid")

    case_id: str = Field(pattern=r"^[NP]\d{3}$")
    title: str
    category: str
    control_type: Literal["positive", "negative"]
    difficulty: Literal["simple", "near_miss"]
    near_miss: bool
    scenario: str
    user_task: str
    agent_output: str
    evidence_packet: V02EvidencePacket
    human_override: V02HumanOverride
    expected_decision: Literal["accept", "reject"]
    expected_reusable: bool
    expected_action_allowed: bool
    expected_failures: list[str]
    expected_residuals: list[str]
    expected_obligations: list[str]
    acceptance_scope: str

    @model_validator(mode="after")
    def validate_control_contract(self) -> V02Case:
        """Keep identifiers, labels, and difficulty mutually consistent."""

        expected_prefix = "P" if self.control_type == "positive" else "N"
        expected_decision = "accept" if self.control_type == "positive" else "reject"
        expected_difficulty = "near_miss" if self.near_miss else "simple"
        if not self.case_id.startswith(expected_prefix):
            raise ValueError("case_id prefix does not match control_type")
        if self.expected_decision != expected_decision:
            raise ValueError("expected_decision does not match control_type")
        if self.difficulty != expected_difficulty:
            raise ValueError("difficulty does not match near_miss")
        if self.control_type == "negative" and not self.expected_failures:
            raise ValueError("negative controls require at least one expected failure")
        if self.control_type == "positive" and self.expected_failures:
            raise ValueError("positive controls must not declare blocking failures")
        return self


class V02RawJudgment(BaseModel):
    """Strict structured fields requested from the raw model."""

    model_config = ConfigDict(extra="forbid")

    accepted: bool
    reusable: bool
    action_allowed: bool
    rationale: str


class V02RawReplication(BaseModel):
    """One captured raw-model call and its parsing/consistency annotations."""

    case_id: str
    replication_id: int = Field(ge=0)
    mode: Literal["mock", "ollama"]
    model: str
    raw_text: str
    parse_status: Literal["valid", "parse_failed", "request_failed"]
    request_status: Literal["ok", "failed"]
    error: str | None = None
    elapsed_ms: float = Field(ge=0)
    response_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    accepted: bool | None = None
    reusable: bool | None = None
    action_allowed: bool | None = None
    rationale: str = ""
    field_consistent: bool
    field_inconsistency_reasons: list[str] = Field(default_factory=list)


class V02Decision(BaseModel):
    """Normalized v0.2 output for a raw replication or deterministic condition."""

    case_id: str
    replication_id: int = Field(ge=0)
    condition: str
    accepted: bool
    settled: bool
    decision: Literal["accept", "reject", "parse_failed", "request_failed"]
    reusable: bool
    action_allowed: bool
    detected_failures: list[str]
    residuals: list[str]
    obligations: list[str]
    evidence_used: list[str]
    notes: str
    rationale: str
    field_consistent: bool
    permission_inconsistency_reasons: list[str]
    time_to_verified_result_ms: float = Field(ge=0)
    execution_cost_units: float = Field(ge=0)


class V02Ledger(BaseModel):
    """Finite ledger emitted by each deterministic layer after FOST."""

    case_id: str
    condition: str
    claims: list[str]
    support: list[str]
    unknowns: list[str]
    obligations: list[str]
    residuals: list[str]
    environment_assumptions: list[str]


class V02RunConfig(BaseModel):
    """Serializable settings for one v0.2 run."""

    experiment: Literal["v0.2"] = "v0.2"
    mode: Literal["mock", "ollama"]
    requested_mode: Literal["mock", "ollama"]
    profile: Literal["quick", "full"] = "quick"
    model: str
    base_url: str
    think: bool = False
    stream: bool = False
    timeout_seconds: float = Field(default=120.0, gt=0)
    temperature: float = 0.0
    evaluation_time: str
    replications: int = Field(default=3, ge=1)
    continue_on_error: bool = False
    cases_path: str
    case_ids: list[str] | None = None


class V02CodingRecord(BaseModel):
    """One blinded human rationale-coding record."""

    model_config = ConfigDict(extra="forbid")

    blind_id: str
    coder_id: str
    recognized_hazards: list[str]
    rationale_supports_reject: bool
    rationale_permission_inconsistent: bool
    confidence: float = Field(ge=0.0, le=1.0)
    notes: str = ""
