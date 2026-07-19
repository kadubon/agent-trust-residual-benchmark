"""Replicated balanced-control orchestration for ATRB v0.2."""

from __future__ import annotations

import hashlib
import json
import platform
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean, median
from time import perf_counter
from typing import Any

from pydantic import ValidationError

from atrb.config import CONDITIONS
from atrb.ollama_client import OllamaClient, OllamaError
from atrb.v02_metrics import compute_replication_metrics, compute_v02_metrics
from atrb.v02_mock import generate_v02_mock
from atrb.v02_models import (
    V02Case,
    V02Decision,
    V02RawJudgment,
    V02RawReplication,
    V02RunConfig,
)
from atrb.v02_report import (
    render_field_inconsistency_log,
    render_near_miss_log,
    render_positive_control_log,
    render_v02_demo_script,
    render_v02_failure_log,
    render_v02_report,
)
from atrb.v02_scientific import build_v02_result_summary
from atrb.v02_validators import (
    build_deterministic_decision,
    build_ledger,
    inspect_case,
    permission_inconsistency_reasons,
)


def load_v02_cases(path: Path, case_ids: list[str] | None = None) -> list[V02Case]:
    """Load and validate the dedicated v0.2 fixture set."""

    data = json.loads(path.read_text(encoding="utf-8"))
    cases = [V02Case.model_validate(item) for item in data]
    if case_ids is None:
        return cases
    selected = set(case_ids)
    filtered = [case for case in cases if case.case_id in selected]
    missing = selected - {case.case_id for case in filtered}
    if missing:
        raise ValueError(f"Unknown v0.2 case IDs: {', '.join(sorted(missing))}")
    return filtered


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, values: list[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(item, sort_keys=True) + "\n" for item in values),
        encoding="utf-8",
    )


def _capture_raw_replication(
    case: V02Case,
    replication_id: int,
    config: V02RunConfig,
    ollama_client: OllamaClient | None,
) -> V02RawReplication:
    error: str | None = None
    if config.mode == "mock":
        raw_text, elapsed_ms = generate_v02_mock(case, replication_id)
        request_status = "ok"
    else:
        if ollama_client is None:
            raise ValueError("Ollama mode requires an initialized local client.")
        try:
            raw_text, elapsed_ms = ollama_client.generate(case)
            request_status = "ok"
        except OllamaError as exc:
            raw_text = ""
            elapsed_ms = 0.0
            request_status = "failed"
            error = str(exc)

    response_hash = hashlib.sha256(raw_text.encode("utf-8")).hexdigest()
    if request_status == "failed":
        return V02RawReplication(
            case_id=case.case_id,
            replication_id=replication_id,
            mode=config.mode,
            model=config.model,
            raw_text=raw_text,
            parse_status="request_failed",
            request_status="failed",
            error=error,
            elapsed_ms=elapsed_ms,
            response_hash=response_hash,
            field_consistent=True,
        )

    try:
        parsed = V02RawJudgment.model_validate_json(raw_text)
    except (ValidationError, ValueError):
        return V02RawReplication(
            case_id=case.case_id,
            replication_id=replication_id,
            mode=config.mode,
            model=config.model,
            raw_text=raw_text,
            parse_status="parse_failed",
            request_status="ok",
            error="Raw response did not satisfy the strict v0.2 judgment schema.",
            elapsed_ms=elapsed_ms,
            response_hash=response_hash,
            field_consistent=True,
        )

    reasons = permission_inconsistency_reasons(
        case,
        accepted=parsed.accepted,
        reusable=parsed.reusable,
        action_allowed=parsed.action_allowed,
        rationale=parsed.rationale,
        evaluation_time=config.evaluation_time,
    )
    return V02RawReplication(
        case_id=case.case_id,
        replication_id=replication_id,
        mode=config.mode,
        model=config.model,
        raw_text=raw_text,
        parse_status="valid",
        request_status="ok",
        elapsed_ms=elapsed_ms,
        response_hash=response_hash,
        accepted=parsed.accepted,
        reusable=parsed.reusable,
        action_allowed=parsed.action_allowed,
        rationale=parsed.rationale,
        field_consistent=not reasons,
        field_inconsistency_reasons=reasons,
    )


def _raw_decision(case: V02Case, replication: V02RawReplication) -> V02Decision:
    if replication.parse_status != "valid":
        return V02Decision(
            case_id=case.case_id,
            replication_id=replication.replication_id,
            condition=CONDITIONS[0],
            accepted=False,
            settled=False,
            decision=replication.parse_status,
            reusable=False,
            action_allowed=False,
            detected_failures=[replication.parse_status],
            residuals=[f"{replication.parse_status}_raw_output"],
            obligations=["obtain_schema_valid_raw_model_output"],
            evidence_used=[],
            notes=replication.error or "Raw output was unavailable.",
            rationale=replication.rationale,
            field_consistent=True,
            permission_inconsistency_reasons=[],
            time_to_verified_result_ms=replication.elapsed_ms,
            execution_cost_units=10.0,
        )
    assert replication.accepted is not None
    assert replication.reusable is not None
    assert replication.action_allowed is not None
    return V02Decision(
        case_id=case.case_id,
        replication_id=replication.replication_id,
        condition=CONDITIONS[0],
        accepted=replication.accepted,
        settled=replication.accepted,
        decision="accept" if replication.accepted else "reject",
        reusable=replication.reusable,
        action_allowed=replication.action_allowed,
        detected_failures=[],
        residuals=[],
        obligations=[],
        evidence_used=[],
        notes=replication.rationale,
        rationale=replication.rationale,
        field_consistent=replication.field_consistent,
        permission_inconsistency_reasons=replication.field_inconsistency_reasons,
        time_to_verified_result_ms=replication.elapsed_ms,
        execution_cost_units=10.0,
    )


def _runtime_record(
    *,
    started_at: str,
    finished_at: str,
    wall_clock_ms: float,
    raw_replications: list[V02RawReplication],
) -> dict[str, Any]:
    successful = [
        item.elapsed_ms for item in raw_replications if item.request_status == "ok"
    ]
    return {
        "experiment": "v0.2",
        "started_at": started_at,
        "finished_at": finished_at,
        "wall_clock_ms": round(wall_clock_ms, 3),
        "model_call_count": len(raw_replications),
        "successful_model_call_count": len(successful),
        "request_failure_count": sum(
            item.request_status == "failed" for item in raw_replications
        ),
        "parse_failure_count": sum(
            item.parse_status == "parse_failed" for item in raw_replications
        ),
        "model_elapsed_total_ms": round(sum(successful), 3),
        "model_elapsed_mean_ms": round(mean(successful), 3) if successful else None,
        "model_elapsed_median_ms": round(median(successful), 3) if successful else None,
        "environment": {
            "python_version": platform.python_version(),
            "operating_system": platform.system(),
            "operating_system_release": platform.release(),
            "machine": platform.machine(),
            "hostname_recorded": False,
        },
        "measurement_note": (
            "Runtime is host-specific. Mock timing is deterministic demonstration data."
        ),
    }


def run_v02_benchmark(
    config: V02RunConfig,
    out_dir: Path,
    ollama_client: OllamaClient | None = None,
) -> dict[str, Any]:
    """Run v0.2, recording call failures per case instead of discarding the run."""

    started_at = datetime.now(UTC).isoformat()
    started_counter = perf_counter()
    cases = load_v02_cases(Path(config.cases_path), config.case_ids)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_replications: list[V02RawReplication] = []
    decisions: list[V02Decision] = []
    ledgers: list[dict[str, Any]] = []

    for case in cases:
        for replication_id in range(config.replications):
            replication = _capture_raw_replication(
                case, replication_id, config, ollama_client
            )
            raw_replications.append(replication)
            decisions.append(_raw_decision(case, replication))

        state = inspect_case(case, config.evaluation_time)
        for condition in CONDITIONS[1:]:
            decision = build_deterministic_decision(
                case, condition, state, config.evaluation_time
            )
            decisions.append(decision)
            if condition != "pic_only":
                ledgers.append(build_ledger(case, condition, decision).model_dump(mode="json"))

    raw_count = len(cases) * config.replications
    deterministic_count = len(cases) * (len(CONDITIONS) - 1)
    if len(raw_replications) != raw_count:
        raise RuntimeError("Raw replication matrix is incomplete.")
    if len(decisions) != raw_count + deterministic_count:
        raise RuntimeError("v0.2 decision matrix is incomplete.")

    metrics = compute_v02_metrics(cases, decisions)
    raw_decisions = [item for item in decisions if item.condition == CONDITIONS[0]]
    replication_metrics = compute_replication_metrics(
        cases, raw_replications, raw_decisions
    )
    finished_at = datetime.now(UTC).isoformat()
    runtime = _runtime_record(
        started_at=started_at,
        finished_at=finished_at,
        wall_clock_ms=(perf_counter() - started_counter) * 1000,
        raw_replications=raw_replications,
    )
    result_summary = build_v02_result_summary(
        config, cases, decisions, metrics, replication_metrics
    )
    case_data = [case.model_dump(mode="json") for case in cases]
    raw_data = [item.model_dump(mode="json") for item in raw_replications]
    decision_data = [item.model_dump(mode="json") for item in decisions]
    residual_data = [
        {
            "case_id": item.case_id,
            "replication_id": item.replication_id,
            "condition": item.condition,
            "residuals": item.residuals,
            "obligations": item.obligations,
        }
        for item in decisions
    ]

    _write_json(out_dir / "config.json", config.model_dump(mode="json"))
    _write_json(out_dir / "cases.normalized.json", case_data)
    _write_jsonl(out_dir / "raw_outputs.jsonl", raw_data)
    _write_jsonl(out_dir / "raw_replications.jsonl", raw_data)
    _write_jsonl(out_dir / "decisions.jsonl", decision_data)
    _write_jsonl(out_dir / "residuals.jsonl", residual_data)
    _write_jsonl(out_dir / "ledgers.jsonl", ledgers)
    _write_json(out_dir / "metrics.json", metrics)
    _write_json(out_dir / "replication_metrics.json", replication_metrics)
    _write_json(out_dir / "result_summary.json", result_summary)
    _write_json(out_dir / "runtime.json", runtime)
    (out_dir / "report.md").write_text(
        render_v02_report(
            config, cases, metrics, replication_metrics, runtime, result_summary
        ),
        encoding="utf-8",
    )
    (out_dir / "failure_log.md").write_text(
        render_v02_failure_log(cases, decisions), encoding="utf-8"
    )
    (out_dir / "positive_control_log.md").write_text(
        render_positive_control_log(cases, decisions), encoding="utf-8"
    )
    (out_dir / "near_miss_log.md").write_text(
        render_near_miss_log(cases, decisions), encoding="utf-8"
    )
    (out_dir / "field_inconsistency_log.md").write_text(
        render_field_inconsistency_log(raw_replications), encoding="utf-8"
    )
    (out_dir / "demo_script.md").write_text(
        render_v02_demo_script(out_dir), encoding="utf-8"
    )
    return {
        "metrics": metrics,
        "replication_metrics": replication_metrics,
        "result_summary": result_summary,
        "runtime": runtime,
    }
