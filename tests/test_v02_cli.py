from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from atrb.cli import app

runner = CliRunner()


def test_v02_cli_run_report_export_and_demo(tmp_path: Path) -> None:
    run_dir = tmp_path / "v02-run"
    result = runner.invoke(
        app, ["v02", "run", "--mode", "mock", "--out", str(run_dir)]
    )
    assert result.exit_code == 0, result.output
    config = json.loads((run_dir / "config.json").read_text(encoding="utf-8"))
    assert config["experiment"] == "v0.2"
    assert config["replications"] == 3
    assert config["think"] is False
    assert config["stream"] is False
    assert config["temperature"] == 0

    report_path = run_dir / "rebuilt.md"
    result = runner.invoke(
        app, ["v02", "report", str(run_dir), "--out", str(report_path)]
    )
    assert result.exit_code == 0, result.output
    assert report_path.is_file()

    blind_path = run_dir / "blinded.jsonl"
    result = runner.invoke(
        app,
        ["v02", "export-coding", str(run_dir), "--out", str(blind_path)],
    )
    assert result.exit_code == 0, result.output
    assert blind_path.is_file()

    demo_dir = tmp_path / "demo"
    result = runner.invoke(
        app, ["v02", "demo", "--mode", "mock", "--out", str(demo_dir)]
    )
    assert result.exit_code == 0, result.output
    assert "4 cases" in result.output


def test_v01_cli_remains_backward_compatible(tmp_path: Path) -> None:
    run_dir = tmp_path / "v01"
    result = runner.invoke(app, ["run", "--mode", "mock", "--out", str(run_dir)])
    assert result.exit_code == 0, result.output
    metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["case_count"] == 18
    assert metrics["decision_count"] == 18 * 6
