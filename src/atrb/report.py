"""Human-readable report and demonstration artifact generation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atrb.config import CONDITIONS
from atrb.metrics import compute_metrics
from atrb.models import BenchmarkCase, Decision
from atrb.scientific import build_scientific_summary


def _format_metric(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


def _count_rate(values: dict[str, Any], count_key: str, total_key: str, rate_key: str) -> str:
    count = values[count_key]
    total = values[total_key]
    rate = values[rate_key] * 100
    return f"{count}/{total} ({rate:.1f}%)"


def render_report(
    config: dict[str, Any],
    cases: list[BenchmarkCase],
    metrics: dict[str, Any],
    runtime: dict[str, Any],
    scientific_summary: dict[str, Any],
) -> str:
    """Render a beginner-readable report with explicit validity boundaries."""

    headers = [
        "Condition",
        "Expected failures detected",
        "False promotions",
        "Consensus detection",
        "Reusable",
        "Action allowed",
        "Residual half-life",
        "Review min",
        "Cost units",
        "Time metric (ms)",
    ]
    observed = scientific_summary["observed"]
    integrity = scientific_summary["data_integrity"]
    final_values = metrics["conditions"][CONDITIONS[-1]]
    raw_values = metrics["conditions"][CONDITIONS[0]]
    false_promotion_sequence = ", ".join(
        f"{condition}={metrics['conditions'][condition]['false_promotion_count']}/"
        f"{metrics['conditions'][condition]['expected_reject_case_count']}"
        for condition in CONDITIONS
    )
    parse_counts = runtime["parse_status_counts"]
    mode_note = (
        "The raw mock baseline is deliberately programmed to make unsafe promotions. Its numbers "
        "demonstrate the measurement pipeline; they are not evidence about an LLM."
        if config["mode"] == "mock"
        else "The raw baseline contains one observation per case from the configured local model. "
        "There are no repeated trials, so model-level uncertainty is not estimated."
    )
    raw_inconsistencies = observed["raw_field_permission_inconsistencies"]
    inconsistency_note = (
        "The model set accepted=false for every case, but emitted separate field-level "
        "permissions for "
        + ", ".join(
            (
                f"{item['case_id']} (reusable={str(item['reusable']).lower()}, "
                f"action_allowed={str(item['action_allowed']).lower()})"
            )
            for item in raw_inconsistencies
        )
        + ". The false-promotion metric counts any accepted, reusable, or action-allowed signal."
        if raw_inconsistencies
        else "No raw field-level permission inconsistency was observed in this run."
    )
    lines = [
        "# Agent Trust and Residual Benchmark Report",
        "",
        "## Start here",
        "",
        f"This run evaluated {len(cases)} synthetic failure cases under six comparison conditions. "
        f"The final condition detected {observed['final_expected_failures_detected_count']}/"
        f"{observed['expected_failure_count']} expected failure labels and produced "
        f"{observed['final_false_promotion_count']}/{observed['negative_control_count']} false "
        "promotions.",
        "",
        "The central validity warning is that every included case is expected to be rejected. "
        "There are no positive controls. A system that rejects everything can therefore obtain "
        "zero false promotions on this dataset. This report measures fixture conformance and "
        "failure detection, not general safety, truth, or balanced decision quality.",
        "",
        mode_note,
        "",
        inconsistency_note,
        "",
        "## Run identity",
        "",
        f"- Requested mode: `{config['requested_mode']}`",
        f"- Effective mode: `{config['mode']}`",
        f"- Model: `{config['model']}`",
        f"- Cases: {len(cases)}",
        f"- Evaluation time: `{config['evaluation_time']}`",
        f"- Mock fallback used: `{str(config['mock_fallback_used']).lower()}`",
        "",
        "## Experimental design",
        "",
        f"- Negative-control cases: {observed['negative_control_count']}",
        f"- Positive-control cases: {observed['positive_control_count']}",
        f"- Expected failure labels: {observed['expected_failure_count']}",
        f"- Conditions: {metrics['condition_count']}",
        (
            f"- Decisions expected and observed: {integrity['expected_decision_count']} "
            f"and {integrity['observed_decision_count']}"
        ),
        "- Design: cumulative deterministic compatibility adapters after a separate raw baseline",
        "- Actions: simulated only; no real-world operation is executed",
        "",
        "## Observed results",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for condition in CONDITIONS:
        values = metrics["conditions"][condition]
        lines.append(
            "| "
            + " | ".join(
                [
                    condition,
                    _count_rate(
                        values,
                        "expected_failures_detected_count",
                        "expected_failures_total_count",
                        "verification_yield",
                    ),
                    _count_rate(
                        values,
                        "false_promotion_count",
                        "expected_reject_case_count",
                        "false_promotion_rate",
                    ),
                    _count_rate(
                        values,
                        "non_independent_consensus_detected_count",
                        "non_independent_consensus_case_count",
                        "non_independent_consensus_detection_rate",
                    ),
                    _count_rate(
                        values,
                        "reusable_artifact_count",
                        "decision_total_count",
                        "reusable_artifact_rate",
                    ),
                    _count_rate(
                        values,
                        "action_allowed_count",
                        "decision_total_count",
                        "action_allowed_rate",
                    ),
                    _format_metric(values["residual_half_life_steps"]),
                    _format_metric(values["estimated_human_review_minutes"]),
                    _format_metric(values["execution_cost_units"]),
                    _format_metric(values["time_to_verified_result_ms"]),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "The time column is not a cross-condition latency benchmark. Raw-model time is "
            "measured wall time, while deterministic-condition time is a stable work estimate.",
            "Review minutes and cost units are deterministic heuristic scores, not observed labor "
            "time or monetary cost.",
            "",
            "The conditions do not improve monotonically over the raw baseline. False promotions "
            f"were {false_promotion_sequence}. Intermediate stages intentionally lack checks that "
            "appear only in later stages, so the table measures staged coverage rather than a "
            "universal ranking of methods.",
            "",
            "## Runtime record",
            "",
            f"- Measured benchmark computation time: {runtime['wall_clock_ms'] / 1000:.2f} seconds",
            f"- Model calls: {runtime['model_call_count']}",
            f"- Model-call total: {runtime['model_elapsed_total_ms'] / 1000:.2f} seconds",
            f"- Model-call mean: {_format_metric(runtime['model_elapsed_mean_ms'])} ms",
            f"- Model-call median: {_format_metric(runtime['model_elapsed_median_ms'])} ms",
            f"- Model-call range: {_format_metric(runtime['model_elapsed_min_ms'])}-"
            f"{_format_metric(runtime['model_elapsed_max_ms'])} ms",
            (
                "- Parse status counts: "
                f"valid={parse_counts['valid']}, parse_failed={parse_counts['parse_failed']}, "
                f"request_failed={parse_counts['request_failed']}"
            ),
            "",
            "Runtime values are host-specific observations, not portable performance claims.",
            "",
            "## What the result supports",
            "",
        ]
    )
    for finding in scientific_summary["supported_findings"]:
        lines.append(
            f"- {finding['claim']} Evidence: {finding['evidence']} Scope: {finding['scope']}"
        )
    lines.extend(
        [
            "",
            "## What the result does not support",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in scientific_summary["unsupported_inferences"])
    lines.extend(
        [
            "",
            "## Additional limitations",
            "",
            "- Fixtures and validators were developed together; this is not a blinded evaluation.",
            (
                "- Cases are hand-authored and do not constitute a random sample of "
                "deployed agent work."
            ),
            "- Cumulative conditions do not identify the isolated causal contribution of a layer.",
            (
                "- One model configuration and one response per case do not characterize "
                "model variance."
            ),
            (
                "- The adapters are lightweight compatibility implementations, not the named "
                "external OSS."
            ),
            (
                "- Perfect final fixture yield is a software-conformance result, not external "
                "validation."
            ),
            "",
            "## Integrity checks",
            "",
            f"- Decision matrix complete: `{str(integrity['decision_count_complete']).lower()}`",
            f"- Missed expected failures: {observed['final_expected_failures_missed_count']}",
            f"- Unexpected final failures: {observed['final_unexpected_failure_count']}",
            f"- Raw false promotions: {raw_values['false_promotion_count']}/"
            f"{raw_values['expected_reject_case_count']}",
            f"- Final false promotions: {final_values['false_promotion_count']}/"
            f"{final_values['expected_reject_case_count']}",
            "",
            "## Reproduction",
            "",
            "```bash",
            "uv sync",
            f"uv run atrb run --mode {config['requested_mode']} --model {config['model']} "
            "--think false --out runs/reproduction",
            "uv run atrb report runs/reproduction --out runs/reproduction/report.md",
            "```",
            "",
            "## Included cases",
            "",
        ]
    )
    lines.extend(f"- `{case.case_id}` — {case.title} ({case.category})" for case in cases)
    lines.append("")
    return "\n".join(lines)


def render_failure_log(cases: list[BenchmarkCase], decisions: list[Decision]) -> str:
    """Explain fail-closed behavior for every case and condition."""

    by_key = {(item.case_id, item.condition): item for item in decisions}
    lines = [
        "# Failure Log",
        "",
        "Every action in this benchmark is simulated. Rejections are fail-closed decisions.",
        "",
    ]
    conditions = list(dict.fromkeys(item.condition for item in decisions))
    for case in cases:
        lines.extend(
            [
                f"## {case.case_id}: {case.title}",
                "",
                f"Expected failures: {', '.join(case.expected_failures)}",
                "",
            ]
        )
        for condition in conditions:
            decision = by_key[(case.case_id, condition)]
            failures = ", ".join(decision.detected_failures) or "none"
            lines.append(
                f"- `{condition}`: **{decision.decision}**; detected: {failures}. "
                f"{decision.notes}"
            )
        lines.append("")
    return "\n".join(lines)


def render_demo_script(out_dir: Path, case_count: int) -> str:
    """Create a concise three-minute walkthrough."""

    return f"""# Three-Minute Demo Script

This run contains {case_count} safe simulation cases.

1. Start with `report.md` and read the validity warning: all fixtures are expected rejects.
2. Compare raw and final counts, including the denominators rather than rates alone.
3. Show `result_summary.json` to separate supported findings from unsupported inferences.
4. Show `runtime.json` and explain that timing is local and host-specific.
5. Open `failure_log.md`, then inspect one finite record in `ledgers.jsonl`.

Reproduce this demo from the project root:

```bash
uv run atrb demo --mode mock --out {out_dir.as_posix()}
uv run atrb report {out_dir.as_posix()} --out {out_dir.as_posix()}/report.md
```

Closing statement: accepted candidate work is not a truth guarantee, and a provider receipt is not
a real-world outcome observation.
"""


def regenerate_report(run_dir: Path, out_path: Path) -> None:
    """Regenerate a report using existing machine-readable artifacts."""

    config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    case_data = json.loads((run_dir / "cases.normalized.json").read_text(encoding="utf-8"))
    runtime = json.loads((run_dir / "runtime.json").read_text(encoding="utf-8"))
    decisions = [
        Decision.model_validate_json(line)
        for line in (run_dir / "decisions.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    cases = [BenchmarkCase.model_validate(item) for item in case_data]
    metrics = compute_metrics(cases, decisions)
    scientific_summary = build_scientific_summary(cases, decisions, metrics)
    (run_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (run_dir / "result_summary.json").write_text(
        json.dumps(scientific_summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        render_report(config, cases, metrics, runtime, scientific_summary),
        encoding="utf-8",
    )
