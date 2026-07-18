"""Benchmark orchestration and artifact persistence."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any, Literal, Protocol

from pydantic import ValidationError

from atrb.adapters import ccr, fcc, fost, pfg, pic, raw
from atrb.config import CONDITIONS, RunConfig
from atrb.metrics import compute_metrics
from atrb.mock_llm import MockLLM
from atrb.models import BenchmarkCase, Decision, Ledger, RawJudgment, RawOutput
from atrb.ollama_client import OllamaError
from atrb.report import render_demo_script, render_failure_log, render_report
from atrb.runtime import build_runtime_record
from atrb.scientific import build_scientific_summary
from atrb.validators import ValidationState, build_decision


class ModelClient(Protocol):
    """Small interface shared by mock and Ollama clients."""

    model: str

    def generate(self, case: BenchmarkCase) -> tuple[str, float]: ...


def load_cases(path: Path, case_ids: list[str] | None = None) -> list[BenchmarkCase]:
    """Load and validate benchmark fixtures."""

    data = json.loads(path.read_text(encoding="utf-8"))
    cases = [BenchmarkCase.model_validate(item) for item in data]
    if case_ids is not None:
        selected = set(case_ids)
        cases = [case for case in cases if case.case_id in selected]
        missing = selected - {case.case_id for case in cases}
        if missing:
            raise ValueError(f"Unknown case IDs: {', '.join(sorted(missing))}")
    return cases


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, values: list[dict[str, Any]]) -> None:
    text = "".join(json.dumps(value, sort_keys=True) + "\n" for value in values)
    path.write_text(text, encoding="utf-8")


def _raw_output(
    case: BenchmarkCase,
    config: RunConfig,
    client: ModelClient,
    allow_mock_fallback: bool,
) -> tuple[RawOutput, ModelClient]:
    try:
        text, elapsed_ms = client.generate(case)
        status: Literal["valid", "parse_failed", "request_failed"]
        try:
            RawJudgment.model_validate_json(text)
            status = "valid"
        except (ValidationError, ValueError):
            status = "parse_failed"
        return (
            RawOutput(
                case_id=case.case_id,
                mode=config.mode,
                model=client.model,
                raw_text=text,
                parse_status=status,
                elapsed_ms=elapsed_ms,
            ),
            client,
        )
    except OllamaError as exc:
        if not allow_mock_fallback:
            raise
        fallback = MockLLM()
        text, elapsed_ms = fallback.generate(case)
        config.mode = "mock"
        config.mock_fallback_used = True
        status = "valid"
        try:
            RawJudgment.model_validate_json(text)
            status = "valid"
        except (ValidationError, ValueError):
            status = "parse_failed"
        return (
            RawOutput(
                case_id=case.case_id,
                mode="mock",
                model=fallback.model,
                raw_text=text,
                parse_status=status,
                error=f"Mock fallback after Ollama failure: {exc}",
                elapsed_ms=elapsed_ms,
            ),
            fallback,
        )


def _layered_decisions(
    case: BenchmarkCase, evaluation_time: str
) -> tuple[list[Decision], list[Ledger]]:
    decisions: list[Decision] = []
    ledgers: list[Ledger] = []
    state = ValidationState()
    pic.apply(case, state)
    decisions.append(build_decision(case, "pic_only", state))

    fost.apply(case, state)
    decisions.append(build_decision(case, "pic_fost", state))
    ledgers.append(fost.build_ledger(case, "pic_fost", state))

    pfg.apply(case, state, evaluation_time)
    decisions.append(build_decision(case, "pic_fost_pfg", state))
    ledgers.append(fost.build_ledger(case, "pic_fost_pfg", state))

    ccr.apply(case, state)
    decisions.append(build_decision(case, "ccr_independent_workcells", state))
    ledgers.append(fost.build_ledger(case, "ccr_independent_workcells", state))

    fcc.apply(case, state, evaluation_time)
    decisions.append(build_decision(case, "fcc_temporal_claims", state))
    ledgers.append(fost.build_ledger(case, "fcc_temporal_claims", state))
    return decisions, ledgers


def run_benchmark(
    config: RunConfig,
    out_dir: Path,
    client: ModelClient,
    *,
    allow_mock_fallback: bool = False,
) -> dict[str, Any]:
    """Run every selected case and persist all required artifacts."""

    started_at = datetime.now(UTC).isoformat()
    started_counter = perf_counter()
    cases = load_cases(Path(config.cases_path), config.case_ids)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_outputs: list[RawOutput] = []
    decisions: list[Decision] = []
    ledgers: list[Ledger] = []
    active_client = client

    for case in cases:
        captured, active_client = _raw_output(
            case, config, active_client, allow_mock_fallback
        )
        raw_outputs.append(captured)
        decisions.append(raw.evaluate(case, captured))
        layered, case_ledgers = _layered_decisions(case, config.evaluation_time)
        decisions.extend(layered)
        ledgers.extend(case_ledgers)

    expected_count = len(cases) * len(CONDITIONS)
    if len(decisions) != expected_count:
        raise RuntimeError(f"Expected {expected_count} decisions, produced {len(decisions)}.")

    metrics = compute_metrics(cases, decisions)
    finished_at = datetime.now(UTC).isoformat()
    runtime = build_runtime_record(
        started_at=started_at,
        finished_at=finished_at,
        wall_clock_ms=(perf_counter() - started_counter) * 1000,
        raw_outputs=raw_outputs,
    )
    scientific_summary = build_scientific_summary(cases, decisions, metrics)
    config_data = config.model_dump(mode="json")
    normalized = [case.model_dump(mode="json") for case in cases]
    decision_data = [item.model_dump(mode="json") for item in decisions]
    residual_data = [
        {
            "case_id": item.case_id,
            "condition": item.condition,
            "residuals": item.residuals,
            "obligations": item.obligations,
        }
        for item in decisions
    ]

    _write_json(out_dir / "config.json", config_data)
    _write_json(out_dir / "cases.normalized.json", normalized)
    _write_jsonl(
        out_dir / "raw_outputs.jsonl",
        [item.model_dump(mode="json") for item in raw_outputs],
    )
    _write_jsonl(out_dir / "decisions.jsonl", decision_data)
    _write_jsonl(out_dir / "residuals.jsonl", residual_data)
    _write_jsonl(out_dir / "ledgers.jsonl", [item.model_dump(mode="json") for item in ledgers])
    _write_json(out_dir / "metrics.json", metrics)
    _write_json(out_dir / "runtime.json", runtime)
    _write_json(out_dir / "result_summary.json", scientific_summary)
    (out_dir / "report.md").write_text(
        render_report(config_data, cases, metrics, runtime, scientific_summary),
        encoding="utf-8",
    )
    (out_dir / "failure_log.md").write_text(
        render_failure_log(cases, decisions), encoding="utf-8"
    )
    (out_dir / "demo_script.md").write_text(
        render_demo_script(out_dir, len(cases)), encoding="utf-8"
    )
    return metrics
