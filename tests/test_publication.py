from __future__ import annotations

import json
from pathlib import Path

from atrb.benchmark import run_benchmark
from atrb.config import DEFAULT_CASES_PATH, RunConfig
from atrb.mock_llm import MockLLM
from atrb.publication import (
    prepare_publication_bundle,
    scan_text,
    verify_publication_bundle,
)


def test_safety_scan_redacts_sensitive_matches() -> None:
    windows_path = "C:" + "\\" + "Users" + "\\" + "local-person" + "\\project"
    email = "person" + "@" + "example.com"
    token = "ghp_" + "abcdefghijklmnopqrstuvwxyz123456"
    text = f"path={windows_path}\nemail={email}\ntoken={token}\n"
    findings = scan_text(
        text,
        relative_path=Path("candidate.txt"),
        local_username="local-person",
    )
    codes = {item["code"] for item in findings}
    assert {"windows_user_path", "local_username", "email_address", "github_token"} <= codes
    assert all(item["matched_text"] == "<redacted>" for item in findings)
    assert "local-person" not in json.dumps(findings)


def test_publication_bundle_removes_local_paths_and_hashes_artifacts(tmp_path: Path) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "public"
    config = RunConfig(
        mode="mock",
        requested_mode="mock",
        cases_path=str(DEFAULT_CASES_PATH),
    )
    run_benchmark(config, source, MockLLM())
    manifest = prepare_publication_bundle(source, destination)

    public_config = json.loads((destination / "config.json").read_text(encoding="utf-8"))
    demo = (destination / "demo_script.md").read_text(encoding="utf-8")
    audit = json.loads((destination / "safety_audit.json").read_text(encoding="utf-8"))
    assert public_config["cases_path"] == "data/cases.json"
    assert str(Path.home()) not in demo
    assert audit["status"] == "pass"
    assert audit["blocking_finding_count"] == 0
    assert manifest["safety_audit_status"] == "pass"
    assert len(manifest["files"]) == 13
    assert (destination / "publication_manifest.json").is_file()
    verification = verify_publication_bundle(destination)
    assert verification["status"] == "pass"
    assert verification["hash_mismatches"] == []
