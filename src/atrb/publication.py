"""Fail-closed preparation and privacy scanning for public result bundles."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from atrb.report import render_demo_script

PUBLISHABLE_ARTIFACTS = (
    "config.json",
    "cases.normalized.json",
    "raw_outputs.jsonl",
    "decisions.jsonl",
    "residuals.jsonl",
    "ledgers.jsonl",
    "metrics.json",
    "runtime.json",
    "result_summary.json",
    "report.md",
    "failure_log.md",
    "demo_script.md",
)

SENSITIVE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "windows_user_path",
        re.compile(
            r"(?i)\b[A-Z]:[\\/]+(?:Users|Documents and Settings)[\\/]+[^\\/\s\"']+"
        ),
    ),
    ("posix_home_path", re.compile(r"/(?:home|Users)/[^/\s\"']+")),
    ("file_uri", re.compile(r"(?i)file://[^\s\"']+")),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("openai_style_key", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    (
        "assigned_secret",
        re.compile(
            r"(?i)(?:api[_-]?key|password|secret|access[_-]?token)\s*[:=]\s*"
            r"[\"'][^\"']{8,}[\"']"
        ),
    ),
    (
        "email_address",
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    ),
    (
        "private_network_address",
        re.compile(
            r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|"
            r"172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"
        ),
    ),
)


class PublicationSafetyError(RuntimeError):
    """Raised when a publication candidate contains blocking local information."""


def _finding(relative_path: Path, line_number: int, code: str) -> dict[str, Any]:
    return {
        "severity": "blocking",
        "code": code,
        "file": relative_path.as_posix(),
        "line": line_number,
        "matched_text": "<redacted>",
    }


def scan_text(
    text: str,
    *,
    relative_path: Path,
    local_username: str | None = None,
) -> list[dict[str, Any]]:
    """Find likely local identifiers and secrets without retaining matched values."""

    findings: list[dict[str, Any]] = []
    username_pattern = (
        re.compile(re.escape(local_username), re.IGNORECASE)
        if local_username and len(local_username) >= 3
        else None
    )
    for line_number, line in enumerate(text.splitlines(), start=1):
        for code, pattern in SENSITIVE_PATTERNS:
            if pattern.search(line):
                findings.append(_finding(relative_path, line_number, code))
        if username_pattern and username_pattern.search(line):
            findings.append(_finding(relative_path, line_number, "local_username"))
    return findings


def scan_directory(
    directory: Path,
    *,
    filenames: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Scan text artifacts and return a machine-readable fail-closed audit."""

    directory = directory.resolve()
    paths = (
        [directory / name for name in filenames]
        if filenames is not None
        else sorted(path for path in directory.rglob("*") if path.is_file())
    )
    local_username = Path.home().name
    findings: list[dict[str, Any]] = []
    scanned = 0
    for path in paths:
        if not path.is_file() or path.suffix.lower() not in {
            ".json",
            ".jsonl",
            ".md",
            ".txt",
            ".toml",
            ".yaml",
            ".yml",
        }:
            continue
        scanned += 1
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(_finding(path.relative_to(directory), 0, "non_utf8_text"))
            continue
        findings.extend(
            scan_text(
                text,
                relative_path=path.relative_to(directory),
                local_username=local_username,
            )
        )
    return {
        "audit_version": "1.0",
        "status": "pass" if not findings else "fail",
        "scanned_file_count": scanned,
        "blocking_finding_count": len(findings),
        "blocking_findings": findings,
        "allowed_disclosures": [
            {
                "field": "localhost Ollama endpoint",
                "reason": (
                    "Loopback configuration is required for reproducibility and is not "
                    "remote access."
                ),
            },
            {
                "field": "coarse OS, architecture, and Python version",
                "reason": "Non-hostname environment metadata supports runtime interpretation.",
            },
            {
                "field": "UTC run timestamps and model identifier",
                "reason": "Experimental provenance without a personal identifier.",
            },
            {
                "field": "synthetic prompt-injection text",
                "reason": "An inert benchmark fixture, not an executed instruction.",
            },
        ],
        "not_scanned": [
            "Binary files",
            "Repository history and remote hosting metadata",
            "Semantic re-identification beyond the configured patterns",
        ],
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65_536), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def prepare_publication_bundle(source_run: Path, out_dir: Path) -> dict[str, Any]:
    """Copy only allowlisted artifacts, remove local paths, scan, and hash the bundle."""

    source_run = source_run.resolve()
    out_dir = out_dir.resolve()
    if source_run == out_dir:
        raise ValueError("Publication output must differ from the source run directory.")
    missing = [name for name in PUBLISHABLE_ARTIFACTS if not (source_run / name).is_file()]
    if missing:
        raise ValueError(f"Source run is missing artifacts: {', '.join(missing)}")

    out_dir.mkdir(parents=True, exist_ok=True)
    for name in PUBLISHABLE_ARTIFACTS:
        source = source_run / name
        destination = out_dir / name
        if name == "config.json":
            config = json.loads(source.read_text(encoding="utf-8"))
            config["cases_path"] = "data/cases.json"
            _write_json(destination, config)
        elif name == "demo_script.md":
            cases = json.loads(
                (source_run / "cases.normalized.json").read_text(encoding="utf-8")
            )
            destination.write_text(
                render_demo_script(Path("runs/demo"), len(cases)),
                encoding="utf-8",
            )
        else:
            destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

    audit = scan_directory(out_dir, filenames=PUBLISHABLE_ARTIFACTS)
    _write_json(out_dir / "safety_audit.json", audit)
    if audit["status"] != "pass":
        raise PublicationSafetyError(
            f"Publication audit failed with {audit['blocking_finding_count']} finding(s)."
        )

    config = json.loads((out_dir / "config.json").read_text(encoding="utf-8"))
    summary = json.loads((out_dir / "result_summary.json").read_text(encoding="utf-8"))
    hashed_files = [*PUBLISHABLE_ARTIFACTS, "safety_audit.json"]
    manifest = {
        "bundle_version": "0.1",
        "generated_at": datetime.now(UTC).isoformat(),
        "source_run_label": source_run.name,
        "mode": config["mode"],
        "model": config["model"],
        "case_count": summary["observed"]["case_count"],
        "condition_count": summary["observed"]["condition_count"],
        "safety_audit_status": audit["status"],
        "sanitization_actions": [
            "Replaced the absolute cases path with data/cases.json.",
            "Regenerated demo commands with repository-relative paths.",
            "Copied only allowlisted experiment artifacts.",
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
    _write_json(out_dir / "publication_manifest.json", manifest)
    return manifest


def verify_publication_bundle(bundle_dir: Path) -> dict[str, Any]:
    """Verify hashes, allowlisted content, and the recorded safety status without mutation."""

    bundle_dir = bundle_dir.resolve()
    manifest_path = bundle_dir / "publication_manifest.json"
    if not manifest_path.is_file():
        raise ValueError("publication_manifest.json is missing.")
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
        if path.is_file()
        and path.name
        not in {*PUBLISHABLE_ARTIFACTS, "safety_audit.json", "publication_manifest.json"}
    )
    rescan = scan_directory(
        bundle_dir,
        filenames=(
            *PUBLISHABLE_ARTIFACTS,
            "safety_audit.json",
            "publication_manifest.json",
        ),
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
        "content_rescan_file_count": rescan["scanned_file_count"],
        "recorded_safety_audit_status": recorded_audit.get("status"),
    }
