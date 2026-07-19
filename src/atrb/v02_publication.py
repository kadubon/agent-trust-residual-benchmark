"""Allowlisted sanitization and verification for ATRB v0.2 result bundles."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from atrb.publication import PublicationSafetyError, scan_directory
from atrb.v02_report import render_v02_demo_script

V02_PUBLISHABLE_ARTIFACTS = (
    "config.json",
    "cases.normalized.json",
    "raw_outputs.jsonl",
    "raw_replications.jsonl",
    "decisions.jsonl",
    "metrics.json",
    "replication_metrics.json",
    "result_summary.json",
    "report.md",
    "failure_log.md",
    "positive_control_log.md",
    "near_miss_log.md",
    "field_inconsistency_log.md",
    "runtime.json",
    "demo_script.md",
)
V02_BUNDLE_FILES = {*V02_PUBLISHABLE_ARTIFACTS, "safety_audit.json", "manifest.json"}


def _write_json(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65_536), b""):
            digest.update(block)
    return digest.hexdigest()


def sanitize_v02_run(source_run: Path, out_dir: Path) -> dict[str, Any]:
    """Copy only the declared v0.2 public artifacts and remove local path metadata."""

    source_run = source_run.resolve()
    out_dir = out_dir.resolve()
    if source_run == out_dir:
        raise ValueError("Sanitized output must differ from the source run directory.")
    missing = [name for name in V02_PUBLISHABLE_ARTIFACTS if not (source_run / name).is_file()]
    if missing:
        raise ValueError(f"Source v0.2 run is missing: {', '.join(missing)}")
    if out_dir.exists():
        unexpected_existing = sorted(
            path.relative_to(out_dir).as_posix()
            for path in out_dir.rglob("*")
            if path.is_file() and path.name not in V02_BUNDLE_FILES
        )
        if unexpected_existing:
            raise ValueError(
                "Sanitized output contains non-allowlisted files: "
                + ", ".join(unexpected_existing)
            )
    out_dir.mkdir(parents=True, exist_ok=True)

    for name in V02_PUBLISHABLE_ARTIFACTS:
        source = source_run / name
        destination = out_dir / name
        if name == "config.json":
            config = json.loads(source.read_text(encoding="utf-8"))
            config["cases_path"] = "data/cases_v02.json"
            _write_json(destination, config)
        elif name == "demo_script.md":
            destination.write_text(
                render_v02_demo_script(Path("runs/v02-demo")),
                encoding="utf-8",
                newline="\n",
            )
        else:
            destination.write_text(
                source.read_text(encoding="utf-8"),
                encoding="utf-8",
                newline="\n",
            )

    audit = scan_directory(out_dir, filenames=V02_PUBLISHABLE_ARTIFACTS)
    _write_json(out_dir / "safety_audit.json", audit)
    if audit["status"] != "pass":
        raise PublicationSafetyError(
            f"v0.2 publication audit found {audit['blocking_finding_count']} blocking item(s)."
        )

    config = json.loads((out_dir / "config.json").read_text(encoding="utf-8"))
    summary = json.loads((out_dir / "result_summary.json").read_text(encoding="utf-8"))
    hashed_files = [*V02_PUBLISHABLE_ARTIFACTS, "safety_audit.json"]
    manifest = {
        "bundle_version": "0.2",
        "generated_at": datetime.now(UTC).isoformat(),
        "source_run_label": source_run.name,
        "mode": config["mode"],
        "model": config["model"],
        "case_count": summary["observed"]["case_count"],
        "positive_control_count": summary["observed"]["positive_control_count"],
        "negative_control_count": summary["observed"]["negative_control_count"],
        "near_miss_count": summary["observed"]["near_miss_count"],
        "safety_audit_status": audit["status"],
        "sanitization_actions": [
            "Replaced the absolute cases path with data/cases_v02.json.",
            "Regenerated demo commands with repository-relative paths.",
            "Excluded coding blind maps, human coding inputs, residual ledgers, and all "
            "non-allowlisted files.",
        ],
        "files": [
            {
                "path": name,
                "bytes": (out_dir / name).stat().st_size,
                "sha256": _sha256(out_dir / name),
            }
            for name in hashed_files
        ],
    }
    _write_json(out_dir / "manifest.json", manifest)
    return manifest


def verify_v02_bundle(bundle_dir: Path) -> dict[str, Any]:
    """Verify the v0.2 allowlist, hashes, and safety scan without mutation."""

    bundle_dir = bundle_dir.resolve()
    manifest_path = bundle_dir / "manifest.json"
    if not manifest_path.is_file():
        raise ValueError("manifest.json is missing.")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    missing: list[str] = []
    mismatched: list[str] = []
    for item in manifest.get("files", []):
        relative = str(item["path"])
        path = bundle_dir / relative
        if not path.is_file():
            missing.append(relative)
        elif _sha256(path) != item["sha256"]:
            mismatched.append(relative)
    unexpected = sorted(
        path.relative_to(bundle_dir).as_posix()
        for path in bundle_dir.rglob("*")
        if path.is_file() and path.name not in V02_BUNDLE_FILES
    )
    rescan = scan_directory(
        bundle_dir,
        filenames=(*V02_PUBLISHABLE_ARTIFACTS, "safety_audit.json", "manifest.json"),
    )
    recorded_audit = json.loads(
        (bundle_dir / "safety_audit.json").read_text(encoding="utf-8")
    )
    passed = (
        not missing
        and not mismatched
        and not unexpected
        and rescan["status"] == "pass"
        and recorded_audit.get("status") == "pass"
    )
    return {
        "status": "pass" if passed else "fail",
        "manifest_hash_count": len(manifest.get("files", [])),
        "missing_files": missing,
        "hash_mismatches": mismatched,
        "unexpected_files": unexpected,
        "content_rescan_status": rescan["status"],
        "recorded_safety_audit_status": recorded_audit.get("status"),
    }
