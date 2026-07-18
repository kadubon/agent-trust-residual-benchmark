from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from atrb.cli import app

runner = CliRunner()


def test_run_and_report_commands(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    result = runner.invoke(app, ["run", "--mode", "mock", "--out", str(run_dir)])
    assert result.exit_code == 0, result.output
    assert (run_dir / "metrics.json").is_file()

    report_path = run_dir / "rebuilt.md"
    result = runner.invoke(
        app, ["report", str(run_dir), "--out", str(report_path)]
    )
    assert result.exit_code == 0, result.output
    assert report_path.is_file()


def test_demo_selects_three_representative_cases(tmp_path: Path) -> None:
    run_dir = tmp_path / "demo"
    result = runner.invoke(app, ["demo", "--mode", "mock", "--out", str(run_dir)])
    assert result.exit_code == 0, result.output
    assert "3 cases x 6 conditions" in result.output
    assert (run_dir / "demo_script.md").is_file()


def test_ollama_failure_uses_mock_only_when_explicitly_allowed(tmp_path: Path) -> None:
    failed_dir = tmp_path / "no-fallback"
    result = runner.invoke(
        app,
        [
            "run",
            "--mode",
            "ollama",
            "--base-url",
            "http://127.0.0.1:1",
            "--timeout",
            "0.1",
            "--out",
            str(failed_dir),
        ],
    )
    assert result.exit_code == 2
    assert not (failed_dir / "metrics.json").exists()

    fallback_dir = tmp_path / "fallback"
    result = runner.invoke(
        app,
        [
            "run",
            "--mode",
            "ollama",
            "--base-url",
            "http://127.0.0.1:1",
            "--timeout",
            "0.1",
            "--allow-mock-fallback",
            "--out",
            str(fallback_dir),
        ],
    )
    assert result.exit_code == 0, result.output
    config = json.loads((fallback_dir / "config.json").read_text(encoding="utf-8"))
    assert config["requested_mode"] == "ollama"
    assert config["mode"] == "mock"
    assert config["mock_fallback_used"] is True


def test_estimate_command_writes_human_and_machine_readable_outputs(tmp_path: Path) -> None:
    calibration_dir = tmp_path / "calibration"
    calibration_dir.mkdir()
    observations = [
        {
            "case_id": f"C00{index}",
            "mode": "ollama",
            "model": "local-model",
            "raw_text": "{}",
            "parse_status": "valid",
            "error": None,
            "elapsed_ms": elapsed_ms,
        }
        for index, elapsed_ms in enumerate([10_000, 20_000, 30_000], start=1)
    ]
    (calibration_dir / "raw_outputs.jsonl").write_text(
        "".join(json.dumps(item) + "\n" for item in observations),
        encoding="utf-8",
    )
    (calibration_dir / "config.json").write_text(
        json.dumps({"timeout_seconds": 120.0}), encoding="utf-8"
    )
    (calibration_dir / "runtime.json").write_text(
        json.dumps({"wall_clock_ms": 65_000}), encoding="utf-8"
    )

    output_path = tmp_path / "estimate.md"
    result = runner.invoke(
        app,
        [
            "estimate",
            str(calibration_dir),
            "--case-count",
            "18",
            "--startup-observation-seconds",
            "60",
            "--warmup-calls",
            "1",
            "--target-timeout-seconds",
            "120",
            "--out",
            str(output_path),
        ],
    )
    assert result.exit_code == 0, result.output
    assert output_path.is_file()
    assert output_path.with_suffix(".json").is_file()
