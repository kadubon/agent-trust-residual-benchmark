"""Human-readable reporting and log generation for ATRB v0.2."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atrb.config import CONDITIONS
from atrb.v02_metrics import compute_replication_metrics, compute_v02_metrics
from atrb.v02_models import V02Case, V02Decision, V02RawReplication, V02RunConfig
from atrb.v02_scientific import build_v02_result_summary


def _percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def render_v02_report(
    config: V02RunConfig,
    cases: list[V02Case],
    metrics: dict[str, Any],
    replication_metrics: dict[str, Any],
    runtime: dict[str, Any],
    result_summary: dict[str, Any],
) -> str:
    """Render all required report sections with explicit scientific boundaries."""

    final = metrics["conditions"][CONDITIONS[-1]]
    raw = metrics["conditions"][CONDITIONS[0]]
    successful_sensitivity = replication_metrics["successful_response_sensitivity"]
    successful_variation = replication_metrics["successful_response_variation"]
    positives = [case for case in cases if case.control_type == "positive"]
    negatives = [case for case in cases if case.control_type == "negative"]
    near_misses = [case for case in cases if case.near_miss]
    lines = [
        "# Agent Trust and Residual Benchmark v0.2 Report",
        "",
        "## 1. Start here",
        "",
        (
            f"This run evaluated {len(cases)} synthetic fixtures: {len(positives)} positive "
            f"controls, {len(negatives)} negative controls, and {len(near_misses)} near misses."
        ),
        (
            "Positive controls make decision quality more measurable than in v0.1 because "
            "reject-all behavior now produces false rejections."
        ),
        "",
        "## 2. Central validity warning",
        "",
        (
            "ATRB v0.2 does not prove real-world safety, truth, or successful execution. The "
            "fixtures are synthetic and hand-authored, so external validity remains limited."
        ),
        (
            "The deterministic conditions are lightweight compatibility adapters. They do not "
            "claim API compatibility or equivalence with external PIC, FOST, PFG, CCR, or FCC "
            "implementations."
        ),
        (
            "Raw rationale coding is separate from structured decision metrics. Repeated calls "
            "describe within-run variation and are not a deployment guarantee."
        ),
        "",
        "## 3. Run identity",
        "",
        f"- Experiment: `{config.experiment}`",
        f"- Mode: `{config.mode}`",
        f"- Profile: `{config.profile}`",
        f"- Model: `{config.model}`",
        f"- Replications per case: {config.replications}",
        f"- Evaluation time: `{config.evaluation_time}`",
        f"- think: `{str(config.think).lower()}`",
        f"- stream: `{str(config.stream).lower()}`",
        f"- temperature: {config.temperature}",
        "",
        "## 4. Dataset composition",
        "",
        f"- Positive controls: {len(positives)}",
        f"- Negative controls: {len(negatives)}",
        f"- Near-miss controls: {len(near_misses)}",
        f"- Near-miss positive controls: {sum(case.near_miss for case in positives)}",
        f"- Near-miss negative controls: {sum(case.near_miss for case in negatives)}",
        "- Every action and outcome reference is a simulation.",
        "",
        "## 5. Main decision metrics",
        "",
        (
            "Primary metrics use structured booleans only. Rationale coding is not included in "
            "this table. Raw-model denominators include replications; deterministic denominators "
            "include one decision per case."
        ),
        "",
        (
            "| Condition | Accept recall | Reject recall | Balanced accuracy | "
            "False rejection | False promotion | Field consistency |"
        ),
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for condition in CONDITIONS:
        values = metrics["conditions"][condition]
        lines.append(
            f"| `{condition}` | {_percent(values['accept_recall'])} | "
            f"{_percent(values['reject_recall'])} | "
            f"{_percent(values['balanced_accuracy'])} | "
            f"{values['false_rejection_count']}/{values['expected_accept_count']} | "
            f"{values['false_promotion_count']}/{values['expected_reject_count']} | "
            f"{_percent(values['field_consistency_rate'])} |"
        )
    lines.extend(
        [
            "",
            (
                "The raw operational row retains request and parse failures as fail-closed "
                "decisions and reports those failures separately. Restricting the calculation "
                "to successful structured responses gives reject recall "
                f"{successful_sensitivity['true_reject_count']}/"
                f"{successful_sensitivity['expected_reject_count']} "
                f"({_percent(successful_sensitivity['reject_recall'])}) and balanced accuracy "
                f"{_percent(successful_sensitivity['balanced_accuracy'])}."
            ),
            "",
            "## 6. Positive control results",
            "",
            (
                f"The final condition accepted {final['true_accept_count']}/"
                f"{final['expected_accept_count']} positive-control decisions. "
                f"Safe reuse accuracy was {_percent(final['safe_reuse_accuracy'])}; safe action "
                f"allowance accuracy was {_percent(final['safe_action_allowance_accuracy'])}."
            ),
            (
                "Positive does not mean every permission is true: P017 is the one fixture where "
                "action_allowed=true is expected, and P018 is accepted but explicitly non-reusable."
            ),
            "",
            "## 7. Negative control results",
            "",
            (
                f"The final condition fail-closed rejected {final['true_reject_count']}/"
                f"{final['expected_reject_count']} negative-control decisions and detected "
                f"{final['expected_failures_detected_count']}/"
                f"{final['expected_failures_total_count']} expected failure labels."
            ),
            "",
            "## 8. Near-miss results",
            "",
            (
                f"Final near-miss accuracy was {_percent(final['near_miss_accuracy'])} "
                f"({final['near_miss_correct_count']}/{final['near_miss_count']})."
            ),
            (
                "Near misses include one-minute temporal boundaries, plausible receipts with "
                "bounded meanings, scope mismatches, close rollback targets, and declared "
                "independence-group boundaries."
            ),
            "",
            "## 9. Field-level inconsistency analysis",
            "",
            (
                f"Raw structured decisions had permission inconsistency rate "
                f"{_percent(raw['permission_inconsistency_rate'])}. False promotion counts any "
                "expected-reject replication with accepted, reusable, or action_allowed true."
            ),
            "See `field_inconsistency_log.md` for replication-level reasons.",
            "",
            "## 10. Replication analysis",
            "",
            f"- Raw replications: {replication_metrics['raw_replication_count']}",
            (
                "- Replication-level false promotion rate: "
                f"{_percent(replication_metrics['replication_level_false_promotion_rate'])}"
            ),
            (
                "- Replication-level false rejection rate: "
                f"{_percent(replication_metrics['replication_level_false_rejection_rate'])}"
            ),
            f"- Parse failure rate: {_percent(replication_metrics['parse_failure_rate'])}",
            f"- Request failure rate: {_percent(replication_metrics['request_failure_rate'])}",
            (
                "- Response hash uniqueness rate: "
                f"{_percent(replication_metrics['response_hash_uniqueness_rate'])}"
            ),
            (
                "- Cases with multiple successful response hashes: "
                f"{successful_variation['cases_with_multiple_successful_response_hashes']}/"
                f"{successful_variation['case_count_with_successful_response']}"
            ),
            (
                "- Cases with multiple successful acceptance values: "
                f"{successful_variation['cases_with_multiple_successful_acceptance_values']}/"
                f"{successful_variation['case_count_with_successful_response']}"
            ),
            (
                "The global hash-uniqueness rate includes expected differences between cases; "
                "the within-case successful-response counts are the relevant repeatability view."
            ),
            "",
            "## 11. Runtime analysis",
            "",
            f"- Wall-clock time: {runtime['wall_clock_ms'] / 1000:.3f} seconds",
            f"- Raw model calls attempted: {runtime['model_call_count']}",
            f"- Successful calls: {runtime['successful_model_call_count']}",
            f"- Request failures: {runtime['request_failure_count']}",
            (
                "- Successful-call latency mean/median: "
                f"{replication_metrics['latency_ms']['mean']}/"
                f"{replication_metrics['latency_ms']['median']} ms"
            ),
            "Runtime is host-specific and is not a portable performance claim.",
            "",
            "## 12. What this run supports",
            "",
        ]
    )
    for finding in result_summary["supported_findings"]:
        lines.append(
            f"- {finding['claim']} Evidence: {finding['evidence']} Scope: {finding['scope']}"
        )
    lines.extend(["", "## 13. What this run does not support", ""])
    lines.extend(f"- {item}" for item in result_summary["unsupported_inferences"])
    lines.extend(
        [
            "",
            "## 14. Threats to validity",
            "",
            "- Fixtures and deterministic validators were developed together.",
            "- Cases are purposive and synthetic rather than sampled from deployment traffic.",
            "- Conditions are cumulative, so individual-layer causal effects are not isolated.",
            "- Mock output is deterministic demonstration data, not model-performance evidence.",
            "- Ollama replications do not cover other versions, prompts, hardware, or seeds.",
            "- The model tag is recorded, but an immutable model-weight digest is not.",
            "- Single-coder rationale coding is supported; inter-rater reliability is future work.",
            "",
            "## 15. Reproduction commands",
            "",
            "```bash",
            "uv sync",
            "uv run atrb v02 run --mode mock --out runs/v02-mock",
            "uv run atrb v02 report runs/v02-mock --out runs/v02-mock/report.md",
            (
                "uv run atrb v02 export-coding runs/v02-mock --out "
                "runs/v02-mock/blinded_rationales.jsonl"
            ),
            "uv run atrb v02 demo --mode mock --out runs/v02-demo",
            "```",
            "",
            "## 16. Included cases",
            "",
        ]
    )
    lines.extend(
        f"- `{case.case_id}` — {case.title} ({case.control_type}, {case.difficulty})"
        for case in cases
    )
    lines.append("")
    return "\n".join(lines)


def _decision_map(decisions: list[V02Decision], condition: str) -> dict[str, V02Decision]:
    return {item.case_id: item for item in decisions if item.condition == condition}


def render_v02_failure_log(cases: list[V02Case], decisions: list[V02Decision]) -> str:
    """Render final negative-control failure conformance."""

    final = _decision_map(decisions, CONDITIONS[-1])
    lines = [
        "# v0.2 Negative-Control Failure Log",
        "",
        "All cases and actions are synthetic simulations.",
        "",
    ]
    for case in cases:
        if case.control_type != "negative":
            continue
        decision = final[case.case_id]
        lines.extend(
            [
                f"## {case.case_id}: {case.title}",
                "",
                f"- Expected: {', '.join(case.expected_failures)}",
                f"- Detected: {', '.join(decision.detected_failures) or 'none'}",
                f"- Decision: {decision.decision}",
                "",
            ]
        )
    return "\n".join(lines)


def render_positive_control_log(
    cases: list[V02Case], decisions: list[V02Decision]
) -> str:
    """Render final permissions for positive controls."""

    final = _decision_map(decisions, CONDITIONS[-1])
    lines = ["# v0.2 Positive-Control Log", ""]
    for case in cases:
        if case.control_type != "positive":
            continue
        decision = final[case.case_id]
        lines.append(
            f"- `{case.case_id}` {case.title}: accepted={str(decision.accepted).lower()}, "
            f"reusable={str(decision.reusable).lower()}, "
            f"action_allowed={str(decision.action_allowed).lower()}, "
            f"settled={str(decision.settled).lower()}; scope: {case.acceptance_scope}."
        )
    lines.append("")
    return "\n".join(lines)


def render_near_miss_log(cases: list[V02Case], decisions: list[V02Decision]) -> str:
    """Render final outcomes for boundary-focused fixtures."""

    final = _decision_map(decisions, CONDITIONS[-1])
    lines = ["# v0.2 Near-Miss Log", ""]
    for case in cases:
        if not case.near_miss:
            continue
        decision = final[case.case_id]
        lines.append(
            f"- `{case.case_id}` ({case.control_type}): expected={case.expected_decision}, "
            f"observed={decision.decision}; detected="
            f"{', '.join(decision.detected_failures) or 'none'}."
        )
    lines.append("")
    return "\n".join(lines)


def render_field_inconsistency_log(
    raw_replications: list[V02RawReplication],
) -> str:
    """Render only raw replications with annotated field-level conflicts."""

    lines = [
        "# v0.2 Raw Field-Inconsistency Log",
        "",
        "This log describes structured raw-model fields; it is separate from rationale coding.",
        "",
    ]
    inconsistent = [item for item in raw_replications if not item.field_consistent]
    if not inconsistent:
        lines.append("No field-level inconsistency was observed.")
    for item in inconsistent:
        lines.append(
            f"- `{item.case_id}` replication {item.replication_id}: "
            f"{', '.join(item.field_inconsistency_reasons)}."
        )
    lines.append("")
    return "\n".join(lines)


def render_v02_demo_script(out_dir: Path) -> str:
    """Create a short balanced-control walkthrough."""

    path = out_dir.as_posix()
    return f"""# ATRB v0.2 Three-Minute Demo

1. Read `report.md` and its central validity warning.
2. Compare positive acceptance, negative rejection, and balanced accuracy.
3. Inspect `near_miss_log.md` and `field_inconsistency_log.md`.
4. Open `replication_metrics.json`; repeated calls are not a deployment guarantee.
5. Keep rationale coding separate from primary structured metrics.

```bash
uv run atrb v02 demo --mode mock --out {path}
uv run atrb v02 report {path} --out {path}/report.md
```

Mock output is deterministic demonstration data, not model-performance evidence.
"""


def regenerate_v02_report(run_dir: Path, out_path: Path) -> None:
    """Regenerate v0.2 metrics, summary, and report from raw artifacts."""

    config = V02RunConfig.model_validate_json(
        (run_dir / "config.json").read_text(encoding="utf-8")
    )
    cases = [
        V02Case.model_validate(item)
        for item in json.loads(
            (run_dir / "cases.normalized.json").read_text(encoding="utf-8")
        )
    ]
    decisions = [
        V02Decision.model_validate_json(line)
        for line in (run_dir / "decisions.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    raw_replications = [
        V02RawReplication.model_validate_json(line)
        for line in (run_dir / "raw_replications.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    runtime = json.loads((run_dir / "runtime.json").read_text(encoding="utf-8"))
    metrics = compute_v02_metrics(cases, decisions)
    raw_decisions = [item for item in decisions if item.condition == CONDITIONS[0]]
    replication_metrics = compute_replication_metrics(
        cases, raw_replications, raw_decisions
    )
    summary = build_v02_result_summary(
        config, cases, decisions, metrics, replication_metrics
    )
    (run_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (run_dir / "replication_metrics.json").write_text(
        json.dumps(replication_metrics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (run_dir / "result_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        render_v02_report(config, cases, metrics, replication_metrics, runtime, summary),
        encoding="utf-8",
    )
