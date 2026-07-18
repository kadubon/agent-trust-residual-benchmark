"""Runtime provenance and transparent planning estimates."""

from __future__ import annotations

import json
import math
import platform
from pathlib import Path
from statistics import mean, median, stdev
from typing import Any

from atrb.models import RawOutput


def build_runtime_record(
    *,
    started_at: str,
    finished_at: str,
    wall_clock_ms: float,
    raw_outputs: list[RawOutput],
) -> dict[str, Any]:
    """Record observed runtime separately from deterministic metric estimates."""

    elapsed = [item.elapsed_ms for item in raw_outputs]
    model_elapsed_total = sum(elapsed)
    return {
        "started_at": started_at,
        "finished_at": finished_at,
        "measurement_scope": (
            "Case loading through decision and metric aggregation; excludes final artifact writes."
        ),
        "wall_clock_ms": round(wall_clock_ms, 3),
        "model_call_count": len(raw_outputs),
        "model_elapsed_total_ms": round(model_elapsed_total, 3),
        "model_elapsed_mean_ms": round(mean(elapsed), 3) if elapsed else None,
        "model_elapsed_median_ms": round(median(elapsed), 3) if elapsed else None,
        "model_elapsed_min_ms": round(min(elapsed), 3) if elapsed else None,
        "model_elapsed_max_ms": round(max(elapsed), 3) if elapsed else None,
        "non_model_overhead_ms": round(max(0.0, wall_clock_ms - model_elapsed_total), 3),
        "parse_status_counts": {
            status: sum(item.parse_status == status for item in raw_outputs)
            for status in ("valid", "parse_failed", "request_failed")
        },
        "environment": {
            "python_version": platform.python_version(),
            "operating_system": platform.system(),
            "operating_system_release": platform.release(),
            "machine": platform.machine(),
            "hostname_recorded": False,
        },
        "reproducibility_note": (
            "Runtime metadata varies by host and run; deterministic mock decisions and metrics "
            "remain reproducible."
        ),
    }


def estimate_full_runtime(
    raw_outputs: list[RawOutput],
    *,
    target_case_count: int,
    observed_wall_clock_ms: float | None = None,
    startup_observation_seconds: float | None = None,
    warmup_call_count: int = 0,
    timeout_seconds: float = 120.0,
) -> dict[str, Any]:
    """Extrapolate a serial full run without presenting a confidence interval."""

    if target_case_count < 1:
        raise ValueError("target_case_count must be at least 1.")
    all_observations = [
        item.elapsed_ms / 1000
        for item in raw_outputs
        if item.mode == "ollama" and item.error is None
    ]
    if not all_observations:
        raise ValueError("No successful Ollama timing observations were found.")
    if warmup_call_count < 0 or warmup_call_count >= len(all_observations):
        raise ValueError("warmup_call_count must leave at least one timing observation.")

    excluded_observations = all_observations[:warmup_call_count]
    observations = all_observations[warmup_call_count:]
    if startup_observation_seconds is None and excluded_observations:
        startup_observation_seconds = max(excluded_observations)
        startup_source = "excluded calibration call"
    elif startup_observation_seconds is not None:
        startup_source = "operator-provided uncontrolled observation"
    else:
        startup_source = None

    sample_count = len(observations)
    sample_mean = mean(observations)
    sample_median = median(observations)
    per_case_overhead = 0.0
    if observed_wall_clock_ms is not None:
        overhead_seconds = max(
            0.0, observed_wall_clock_ms / 1000 - sum(all_observations)
        )
        per_case_overhead = overhead_seconds / len(all_observations)

    warm_central = (sample_mean + per_case_overhead) * target_case_count
    warm_lower = (min(observations) + per_case_overhead) * target_case_count
    warm_upper = (max(observations) + per_case_overhead) * target_case_count
    startup_adjusted = None
    if startup_observation_seconds is not None:
        startup_adjusted = (
            startup_observation_seconds
            + sample_mean * max(0, target_case_count - 1)
            + per_case_overhead * target_case_count
        )
    planning_base = max(warm_upper, startup_adjusted or 0.0)
    recommended_budget_minutes = math.ceil(planning_base * 1.25 / 60)

    return {
        "estimate_type": "empirical_serial_extrapolation",
        "target_case_count": target_case_count,
        "model_call_count_expected": target_case_count,
        "raw_sample_count": len(all_observations),
        "warm_sample_count": sample_count,
        "warmup_call_count": warmup_call_count,
        "excluded_startup_samples_seconds": [
            round(value, 3) for value in excluded_observations
        ],
        "sample_seconds": [round(value, 3) for value in observations],
        "sample_mean_seconds": round(sample_mean, 3),
        "sample_median_seconds": round(sample_median, 3),
        "sample_min_seconds": round(min(observations), 3),
        "sample_max_seconds": round(max(observations), 3),
        "sample_standard_deviation_seconds": (
            round(stdev(observations), 3) if sample_count >= 2 else None
        ),
        "observed_non_model_overhead_seconds_per_case": round(per_case_overhead, 3),
        "warm_central_minutes": round(warm_central / 60, 2),
        "warm_empirical_range_minutes": [
            round(warm_lower / 60, 2),
            round(warm_upper / 60, 2),
        ],
        "startup_observation_seconds": startup_observation_seconds,
        "startup_observation_source": startup_source,
        "startup_adjusted_minutes": (
            round(startup_adjusted / 60, 2) if startup_adjusted is not None else None
        ),
        "recommended_planning_budget_minutes": recommended_budget_minutes,
        "configured_timeout_ceiling_minutes": round(
            target_case_count * timeout_seconds / 60, 2
        ),
        "is_confidence_interval": False,
        "assumptions": [
            "Ollama calls run serially and each benchmark case makes one model call.",
            "Calibration cases approximate the prompt lengths of the complete fixture set.",
            "The host, model, Ollama settings, and competing workload remain similar.",
            "The startup observation is operational context, not a controlled cold-start sample.",
        ],
        "limitations": [
            "The calibration sample is small and purposively selected, not random.",
            "The empirical range is not a statistical confidence or prediction interval.",
            (
                "Model loading, thermal limits, memory pressure, and other workloads can "
                "dominate runtime."
            ),
            "The timeout ceiling is a failure bound, not an expected duration.",
        ],
    }


def render_runtime_estimate(estimate: dict[str, Any]) -> str:
    """Render a beginner-readable planning note."""

    warm_range = estimate["warm_empirical_range_minutes"]
    startup_line = (
        f"- Startup-adjusted estimate: {estimate['startup_adjusted_minutes']} minutes\n"
        if estimate["startup_adjusted_minutes"] is not None
        else ""
    )
    return (
        "# Full Ollama Run Time Estimate\n\n"
        f"- Target: {estimate['target_case_count']} cases, one serial model call per case\n"
        f"- Raw calibration calls: {estimate['raw_sample_count']}\n"
        f"- Warm timing samples used: {estimate['warm_sample_count']}\n"
        f"- Excluded startup samples: {estimate['excluded_startup_samples_seconds']} seconds\n"
        f"- Observed call times: {estimate['sample_seconds']} seconds\n"
        f"- Warm central estimate: {estimate['warm_central_minutes']} minutes\n"
        f"- Warm empirical range: {warm_range[0]}-{warm_range[1]} minutes\n"
        f"{startup_line}"
        "- Recommended planning budget: "
        f"{estimate['recommended_planning_budget_minutes']} minutes\n"
        "- Configured timeout ceiling: "
        f"{estimate['configured_timeout_ceiling_minutes']} minutes\n\n"
        "The empirical range is a planning range, not a confidence interval. The calibration "
        "sample is small and comes from the same local host. Startup state, model loading, "
        "memory pressure, "
        "and competing workloads can materially change the result.\n"
    )


def estimate_from_run_directory(
    run_dir: Path,
    *,
    target_case_count: int,
    startup_observation_seconds: float | None,
    warmup_call_count: int,
    target_timeout_seconds: float | None,
) -> dict[str, Any]:
    """Load calibration artifacts and produce a runtime estimate."""

    raw_outputs = [
        RawOutput.model_validate_json(line)
        for line in (run_dir / "raw_outputs.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    runtime_path = run_dir / "runtime.json"
    runtime = (
        json.loads(runtime_path.read_text(encoding="utf-8"))
        if runtime_path.exists()
        else {}
    )
    return estimate_full_runtime(
        raw_outputs,
        target_case_count=target_case_count,
        observed_wall_clock_ms=runtime.get("wall_clock_ms"),
        startup_observation_seconds=startup_observation_seconds,
        warmup_call_count=warmup_call_count,
        timeout_seconds=(
            target_timeout_seconds
            if target_timeout_seconds is not None
            else float(config.get("timeout_seconds", 120.0))
        ),
    )
