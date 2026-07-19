from __future__ import annotations

import json
from pathlib import Path

import pytest

from atrb.config import (
    DEFAULT_BASE_URL,
    DEFAULT_V02_CASES_PATH,
    DEFAULT_V02_EVALUATION_TIME,
)
from atrb.publication import PublicationSafetyError, scan_text
from atrb.v02_mock import V02_MOCK_MODEL
from atrb.v02_models import V02RunConfig
from atrb.v02_publication import (
    V02_BUNDLE_FILES,
    sanitize_v02_run,
    verify_v02_bundle,
)
from atrb.v02_runner import run_v02_benchmark


def _make_run(run_dir: Path) -> None:
    config = V02RunConfig(
        mode="mock",
        requested_mode="mock",
        model=V02_MOCK_MODEL,
        base_url=DEFAULT_BASE_URL,
        evaluation_time=DEFAULT_V02_EVALUATION_TIME,
        replications=1,
        cases_path=str(DEFAULT_V02_CASES_PATH),
    )
    run_v02_benchmark(config, run_dir)


def test_v02_sanitize_is_allowlisted_hashed_and_verifiable(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "public"
    _make_run(source)
    manifest = sanitize_v02_run(source, destination)
    names = {path.name for path in destination.iterdir() if path.is_file()}
    assert names == V02_BUNDLE_FILES
    assert len(manifest["files"]) == 16
    public_config = json.loads((destination / "config.json").read_text(encoding="utf-8"))
    assert public_config["cases_path"] == "data/cases_v02.json"
    assert "coding_blind_map.json" not in names
    assert verify_v02_bundle(destination)["status"] == "pass"
    for item in manifest["files"]:
        assert b"\r\n" not in (destination / item["path"]).read_bytes()


def test_v02_safety_scan_blocks_local_identifiers_and_sanitize_fails(
    tmp_path: Path,
) -> None:
    local_path = "C:" + "\\" + "Users" + "\\" + "release-person" + "\\run"
    findings = scan_text(
        f"source={local_path}\n\"hostname\": \"workstation-17\"",
        relative_path=Path("report.md"),
        local_username="release-person",
    )
    assert {item["code"] for item in findings} >= {
        "windows_user_path",
        "local_username",
        "recorded_hostname",
    }

    source = tmp_path / "source"
    destination = tmp_path / "public"
    _make_run(source)
    with (source / "report.md").open("a", encoding="utf-8") as handle:
        handle.write(f"\nUnsafe test path: {local_path}\n")
    with pytest.raises(PublicationSafetyError):
        sanitize_v02_run(source, destination)
