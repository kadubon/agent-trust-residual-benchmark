"""Command-line interface for local benchmark operation."""

from __future__ import annotations

import json
import platform
import shutil
import tempfile
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal

import jsonschema
import typer
from rich.console import Console
from rich.table import Table

from atrb.benchmark import run_benchmark
from atrb.config import (
    DEFAULT_BASE_URL,
    DEFAULT_CASES_PATH,
    DEFAULT_MODEL,
    DEFAULT_V02_CASES_PATH,
    DEFAULT_V02_EVALUATION_TIME,
    PROJECT_ROOT,
    RunConfig,
)
from atrb.mock_llm import MockLLM
from atrb.ollama_client import OllamaClient, OllamaError
from atrb.publication import (
    PublicationSafetyError,
    prepare_publication_bundle,
    scan_directory,
    verify_publication_bundle,
)
from atrb.report import regenerate_report
from atrb.runtime import estimate_from_run_directory, render_runtime_estimate
from atrb.v02_coding import export_rationale_coding, import_rationale_coding
from atrb.v02_mock import V02_MOCK_MODEL
from atrb.v02_models import V02RunConfig
from atrb.v02_publication import sanitize_v02_run, verify_v02_bundle
from atrb.v02_report import regenerate_v02_report
from atrb.v02_runner import run_v02_benchmark

app = typer.Typer(
    name="atrb",
    help="Run the Agent Trust and Residual Benchmark locally.",
    no_args_is_help=True,
)
console = Console()
v02_app = typer.Typer(
    name="v02",
    help="Run the additive balanced-control ATRB v0.2 experiment.",
    no_args_is_help=True,
)
app.add_typer(v02_app, name="v02")


class Mode(StrEnum):
    """Supported model execution modes."""

    mock = "mock"
    ollama = "ollama"


class V02Profile(StrEnum):
    """Recommended v0.2 replication profiles."""

    quick = "quick"
    full = "full"


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "on"}:
        return True
    if normalized in {"false", "0", "no", "off"}:
        return False
    raise typer.BadParameter("Expected true or false.")


def _validate_cases_schema() -> tuple[bool, str]:
    try:
        schema_path = DEFAULT_CASES_PATH.parent / "schemas" / "case.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        data = json.loads(DEFAULT_CASES_PATH.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()
        )
        errors = sorted(error.message for item in data for error in validator.iter_errors(item))
        if errors:
            return False, errors[0]
        return True, f"{len(data)} cases valid"
    except (OSError, ValueError, jsonschema.SchemaError) as exc:
        return False, str(exc)


def _validate_v02_cases_schema() -> tuple[bool, str]:
    try:
        schema_path = DEFAULT_V02_CASES_PATH.parent / "schemas" / "case_v02.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        data = json.loads(DEFAULT_V02_CASES_PATH.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()
        )
        errors = sorted(error.message for item in data for error in validator.iter_errors(item))
        if errors:
            return False, errors[0]
        positive = sum(item.get("control_type") == "positive" for item in data)
        negative = sum(item.get("control_type") == "negative" for item in data)
        near_miss = sum(bool(item.get("near_miss")) for item in data)
        return (
            True,
            f"{len(data)} cases; {positive} positive, {negative} negative, "
            f"{near_miss} near misses",
        )
    except (OSError, ValueError, jsonschema.SchemaError) as exc:
        return False, str(exc)


def _writable_output() -> tuple[bool, str]:
    try:
        output_dir = PROJECT_ROOT / "runs"
        output_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=output_dir, prefix="atrb-doctor-", delete=True):
            pass
        return True, str(output_dir)
    except OSError as exc:
        return False, str(exc)


@app.command()
def doctor(
    model: Annotated[
        str, typer.Option("--model", help="Expected local Ollama model.")
    ] = DEFAULT_MODEL,
    base_url: Annotated[
        str, typer.Option("--base-url", help="Local Ollama base URL.")
    ] = DEFAULT_BASE_URL,
) -> None:
    """Check core project readiness and optional local Ollama availability."""

    schema_ok, schema_detail = _validate_cases_schema()
    v02_schema_ok, v02_schema_detail = _validate_v02_cases_schema()
    writable_ok, writable_detail = _writable_output()
    project_ok = (PROJECT_ROOT / "pyproject.toml").is_file() and (
        PROJECT_ROOT / "uv.lock"
    ).is_file()
    uv_path = shutil.which("uv")

    ollama_ok = False
    model_ok = False
    ollama_detail = "not checked"
    try:
        with OllamaClient(base_url=base_url, model=model, timeout_seconds=3.0) as client:
            models = client.list_models()
            ollama_ok = True
            model_ok = model in models
            ollama_detail = f"reachable; {len(models)} model(s) installed"
    except OllamaError as exc:
        ollama_detail = str(exc)

    table = Table(title="ATRB Doctor")
    table.add_column("Check")
    table.add_column("Status")
    table.add_column("Details")

    def add(name: str, ok: bool, detail: str) -> None:
        table.add_row(name, "PASS" if ok else "WARN", detail)

    python_ok = tuple(int(part) for part in platform.python_version_tuple()[:2]) >= (3, 11)
    add("Python >= 3.11", python_ok, platform.python_version())
    add("uv executable", uv_path is not None, uv_path or "not found")
    add("uv project", project_ok, str(PROJECT_ROOT))
    add("Ollama endpoint", ollama_ok, ollama_detail)
    add("Ollama model", model_ok, model if model_ok else f"missing: {model}")
    add("mock mode", True, "deterministic mock available")
    add("case schema", schema_ok, schema_detail)
    add("v0.2 case schema", v02_schema_ok, v02_schema_detail)
    add("output writable", writable_ok, writable_detail)
    console.print(table)
    if not (
        python_ok
        and uv_path
        and project_ok
        and schema_ok
        and v02_schema_ok
        and writable_ok
    ):
        raise typer.Exit(code=1)


def _build_client(config: RunConfig, allow_mock_fallback: bool) -> MockLLM | OllamaClient:
    if config.mode == "mock":
        return MockLLM()

    client = OllamaClient(
        base_url=config.base_url,
        model=config.model,
        think=config.think,
        timeout_seconds=config.timeout_seconds,
        temperature=config.temperature,
    )
    try:
        if not client.model_available():
            raise OllamaError(
                f"Ollama is reachable, but model '{config.model}' is not installed. "
                f"Run: ollama pull {config.model}"
            )
        return client
    except OllamaError as exc:
        client.close()
        if not allow_mock_fallback:
            raise
        config.mode = "mock"
        config.mock_fallback_used = True
        console.print(
            "[yellow]Ollama unavailable; using deterministic mock fallback: "
            f"{exc}[/yellow]"
        )
        return MockLLM()


def _execute(
    *,
    mode: Mode,
    out: Path,
    model: str,
    base_url: str,
    think: str,
    timeout: float,
    cases: Path,
    case_ids: list[str] | None,
    allow_mock_fallback: bool,
) -> None:
    requested_mode: Literal["mock", "ollama"] = (
        "mock" if mode is Mode.mock else "ollama"
    )
    config = RunConfig(
        mode=requested_mode,
        requested_mode=requested_mode,
        model=model,
        base_url=base_url,
        think=_parse_bool(think),
        timeout_seconds=timeout,
        cases_path=str(cases.resolve()),
        case_ids=case_ids,
    )
    client: MockLLM | OllamaClient | None = None
    try:
        client = _build_client(config, allow_mock_fallback)
        metrics = run_benchmark(
            config,
            out.resolve(),
            client,
            allow_mock_fallback=allow_mock_fallback,
        )
    except (OllamaError, OSError, ValueError, json.JSONDecodeError) as exc:
        console.print(f"[red]Benchmark failed: {exc}[/red]")
        if mode is Mode.ollama and not allow_mock_fallback:
            console.print(
                "Use --allow-mock-fallback to complete the run in deterministic mock mode."
            )
        raise typer.Exit(code=2) from exc
    finally:
        if isinstance(client, OllamaClient):
            client.close()
    console.print(
        f"[green]Completed[/green] {metrics['case_count']} cases x "
        f"{metrics['condition_count']} conditions in {out.resolve()}"
    )


@app.command("run")
def run_command(
    mode: Annotated[Mode, typer.Option("--mode", case_sensitive=False)] = Mode.mock,
    out: Annotated[Path, typer.Option("--out")] = Path("runs/mock"),
    model: Annotated[str, typer.Option("--model")] = DEFAULT_MODEL,
    base_url: Annotated[str, typer.Option("--base-url")] = DEFAULT_BASE_URL,
    think: Annotated[
        str, typer.Option("--think", help="Pass true or false explicitly.")
    ] = "false",
    timeout: Annotated[float, typer.Option("--timeout", min=0.1)] = 120.0,
    cases: Annotated[
        Path, typer.Option("--cases", exists=True, dir_okay=False)
    ] = DEFAULT_CASES_PATH,
    allow_mock_fallback: Annotated[
        bool, typer.Option("--allow-mock-fallback")
    ] = False,
) -> None:
    """Run all cases across all six comparison conditions."""

    _execute(
        mode=mode,
        out=out,
        model=model,
        base_url=base_url,
        think=think,
        timeout=timeout,
        cases=cases,
        case_ids=None,
        allow_mock_fallback=allow_mock_fallback,
    )


@app.command()
def report(
    run_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False)],
    out: Annotated[Path | None, typer.Option("--out")] = None,
) -> None:
    """Regenerate the Markdown report from an existing run directory."""

    destination = out or run_dir / "report.md"
    try:
        regenerate_report(run_dir.resolve(), destination.resolve())
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        console.print(f"[red]Report generation failed: {exc}[/red]")
        raise typer.Exit(code=2) from exc
    console.print(f"[green]Report written[/green] {destination.resolve()}")


@app.command()
def demo(
    mode: Annotated[Mode, typer.Option("--mode", case_sensitive=False)] = Mode.mock,
    out: Annotated[Path, typer.Option("--out")] = Path("runs/demo"),
    model: Annotated[str, typer.Option("--model")] = DEFAULT_MODEL,
    base_url: Annotated[str, typer.Option("--base-url")] = DEFAULT_BASE_URL,
    think: Annotated[str, typer.Option("--think")] = "false",
    timeout: Annotated[float, typer.Option("--timeout", min=0.1)] = 120.0,
    allow_mock_fallback: Annotated[
        bool, typer.Option("--allow-mock-fallback")
    ] = False,
) -> None:
    """Generate a representative three-case, three-minute demo run."""

    _execute(
        mode=mode,
        out=out,
        model=model,
        base_url=base_url,
        think=think,
        timeout=timeout,
        cases=DEFAULT_CASES_PATH,
        case_ids=["C001", "C006", "C004"],
        allow_mock_fallback=allow_mock_fallback,
    )


@app.command()
def estimate(
    run_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False)],
    case_count: Annotated[int, typer.Option("--case-count", min=1)] = 18,
    startup_observation_seconds: Annotated[
        float | None,
        typer.Option(
            "--startup-observation-seconds",
            min=0.0,
            help="Optional uncontrolled startup-sensitive observation for planning.",
        ),
    ] = None,
    warmup_calls: Annotated[
        int,
        typer.Option(
            "--warmup-calls",
            min=0,
            help="Exclude this many leading calls from the warm per-call estimate.",
        ),
    ] = 0,
    target_timeout_seconds: Annotated[
        float | None,
        typer.Option(
            "--target-timeout-seconds",
            min=0.1,
            help="Override the calibration timeout when computing the target-run ceiling.",
        ),
    ] = None,
    out: Annotated[Path | None, typer.Option("--out")] = None,
) -> None:
    """Estimate a full serial Ollama run from calibration artifacts."""

    destination = out or run_dir / "runtime_estimate.md"
    try:
        estimate_data = estimate_from_run_directory(
            run_dir.resolve(),
            target_case_count=case_count,
            startup_observation_seconds=startup_observation_seconds,
            warmup_call_count=warmup_calls,
            target_timeout_seconds=target_timeout_seconds,
        )
        destination = destination.resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(render_runtime_estimate(estimate_data), encoding="utf-8")
        json_path = destination.with_suffix(".json")
        json_path.write_text(
            json.dumps(estimate_data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        console.print(f"[red]Runtime estimation failed: {exc}[/red]")
        raise typer.Exit(code=2) from exc
    console.print(f"[green]Runtime estimate written[/green] {destination}")
    console.print(f"[green]Machine-readable estimate written[/green] {json_path}")


@app.command("safety-audit")
def safety_audit(
    candidate_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False)],
    out: Annotated[Path | None, typer.Option("--out")] = None,
) -> None:
    """Scan a publication candidate for local identifiers and common secret formats."""

    destination = (
        out
        or candidate_dir.with_name(f"{candidate_dir.name}-safety-audit.json")
    ).resolve()
    try:
        audit = scan_directory(candidate_dir.resolve())
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(audit, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    except (OSError, ValueError) as exc:
        console.print(f"[red]Safety audit failed to run: {exc}[/red]")
        raise typer.Exit(code=2) from exc
    if audit["status"] != "pass":
        console.print(
            f"[red]Safety audit blocked publication: "
            f"{audit['blocking_finding_count']} finding(s).[/red]"
        )
        raise typer.Exit(code=3)
    console.print(f"[green]Safety audit passed[/green] {destination}")


@app.command("prepare-publication")
def prepare_publication(
    run_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False)],
    out: Annotated[Path, typer.Option("--out")] = Path("public-results/ollama-v0.1"),
) -> None:
    """Create a sanitized, allowlisted, hashed public experiment bundle."""

    try:
        manifest = prepare_publication_bundle(run_dir.resolve(), out.resolve())
    except (OSError, ValueError, PublicationSafetyError, json.JSONDecodeError) as exc:
        console.print(f"[red]Publication preparation failed: {exc}[/red]")
        raise typer.Exit(code=3) from exc
    console.print(
        f"[green]Publication bundle ready[/green] {out.resolve()} "
        f"({len(manifest['files'])} hashed artifacts)"
    )


@app.command("verify-publication")
def verify_publication(
    bundle_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False)],
) -> None:
    """Verify publication hashes, allowlist, and sanitized content without writing."""

    try:
        verification = verify_publication_bundle(bundle_dir.resolve())
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        console.print(f"[red]Publication verification failed to run: {exc}[/red]")
        raise typer.Exit(code=2) from exc
    if verification["status"] != "pass":
        console.print(f"[red]Publication verification failed:[/red] {verification}")
        raise typer.Exit(code=3)
    console.print(
        "[green]Publication verification passed[/green] "
        f"{verification['manifest_hash_count']} hashes checked"
    )


def _execute_v02(
    *,
    mode: Mode,
    profile: V02Profile,
    replications: int | None,
    out: Path,
    model: str,
    base_url: str,
    think: str,
    stream: str,
    timeout: float,
    cases: Path,
    case_ids: list[str] | None,
    continue_on_error: bool,
) -> None:
    """Build a v0.2 config, run it, and apply CLI-level failure policy."""

    requested_mode: Literal["mock", "ollama"] = (
        "mock" if mode is Mode.mock else "ollama"
    )
    replication_count = replications or (5 if profile is V02Profile.full else 3)
    config = V02RunConfig(
        mode=requested_mode,
        requested_mode=requested_mode,
        profile=profile.value,
        model=V02_MOCK_MODEL if mode is Mode.mock else model,
        base_url=base_url,
        think=_parse_bool(think),
        stream=_parse_bool(stream),
        timeout_seconds=timeout,
        temperature=0.0,
        evaluation_time=DEFAULT_V02_EVALUATION_TIME,
        replications=replication_count,
        continue_on_error=continue_on_error,
        cases_path=str(cases.resolve()),
        case_ids=case_ids,
    )
    if config.stream:
        console.print("[red]v0.2 requires non-streaming raw responses.[/red]")
        raise typer.Exit(code=2)

    client: OllamaClient | None = None
    try:
        if mode is Mode.ollama:
            client = OllamaClient(
                base_url=base_url,
                model=model,
                think=config.think,
                timeout_seconds=timeout,
                temperature=0.0,
            )
            if not client.model_available():
                raise OllamaError(
                    f"Ollama is reachable, but model '{model}' is not installed. "
                    f"Run: ollama pull {model}"
                )
        result = run_v02_benchmark(config, out.resolve(), client)
    except (OllamaError, OSError, ValueError, json.JSONDecodeError) as exc:
        console.print(f"[red]v0.2 benchmark failed: {exc}[/red]")
        raise typer.Exit(code=2) from exc
    finally:
        if client is not None:
            client.close()

    metrics = result["metrics"]
    replication_metrics = result["replication_metrics"]
    console.print(
        f"[green]Completed v0.2[/green] {metrics['case_count']} cases, "
        f"{replication_metrics['raw_replication_count']} raw replications, and "
        f"{metrics['decision_count']} normalized decisions in {out.resolve()}"
    )
    request_failures = int(replication_metrics["request_failure_count"])
    if request_failures and not continue_on_error:
        console.print(
            f"[red]{request_failures} request failure(s) were recorded. "
            "Use --continue-on-error to accept a completed run with case-level failures.[/red]"
        )
        raise typer.Exit(code=4)


@v02_app.command("run")
def v02_run_command(
    mode: Annotated[Mode, typer.Option("--mode", case_sensitive=False)] = Mode.mock,
    out: Annotated[Path, typer.Option("--out")] = Path("runs/v02-mock"),
    profile: Annotated[
        V02Profile, typer.Option("--profile", case_sensitive=False)
    ] = V02Profile.quick,
    replications: Annotated[
        int | None,
        typer.Option(
            "--replications",
            min=1,
            help="Override quick=3 or full=5 raw replications per case.",
        ),
    ] = None,
    model: Annotated[str, typer.Option("--model")] = DEFAULT_MODEL,
    base_url: Annotated[str, typer.Option("--base-url")] = DEFAULT_BASE_URL,
    think: Annotated[str, typer.Option("--think")] = "false",
    stream: Annotated[str, typer.Option("--stream")] = "false",
    timeout: Annotated[float, typer.Option("--timeout", min=0.1)] = 120.0,
    cases: Annotated[
        Path, typer.Option("--cases", exists=True, dir_okay=False)
    ] = DEFAULT_V02_CASES_PATH,
    continue_on_error: Annotated[
        bool,
        typer.Option(
            "--continue-on-error",
            help="Complete with zero exit status when case-level requests fail.",
        ),
    ] = False,
) -> None:
    """Run balanced controls and replicated raw judgments across six conditions."""

    _execute_v02(
        mode=mode,
        profile=profile,
        replications=replications,
        out=out,
        model=model,
        base_url=base_url,
        think=think,
        stream=stream,
        timeout=timeout,
        cases=cases,
        case_ids=None,
        continue_on_error=continue_on_error,
    )


@v02_app.command("report")
def v02_report_command(
    run_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False)],
    out: Annotated[Path | None, typer.Option("--out")] = None,
) -> None:
    """Regenerate v0.2 metrics, summary, and report from recorded artifacts."""

    destination = (out or run_dir / "report.md").resolve()
    try:
        regenerate_v02_report(run_dir.resolve(), destination)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        console.print(f"[red]v0.2 report generation failed: {exc}[/red]")
        raise typer.Exit(code=2) from exc
    console.print(f"[green]v0.2 report written[/green] {destination}")


@v02_app.command("export-coding")
def v02_export_coding_command(
    run_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False)],
    out: Annotated[Path, typer.Option("--out")],
) -> None:
    """Export blinded raw rationales and a separate coding protocol."""

    try:
        result = export_rationale_coding(run_dir.resolve(), out.resolve())
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        console.print(f"[red]v0.2 coding export failed: {exc}[/red]")
        raise typer.Exit(code=2) from exc
    console.print(
        f"[green]Blinded coding export written[/green] {result['output']} "
        f"({result['blinded_record_count']} records)"
    )


@v02_app.command("import-coding")
def v02_import_coding_command(
    run_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False)],
    coding: Annotated[
        Path, typer.Option("--coding", exists=True, dir_okay=False)
    ],
) -> None:
    """Import one or more coders without changing primary decision metrics."""

    try:
        metrics = import_rationale_coding(run_dir.resolve(), coding.resolve())
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        console.print(f"[red]v0.2 coding import failed: {exc}[/red]")
        raise typer.Exit(code=2) from exc
    console.print(
        f"[green]Rationale coding imported[/green] "
        f"{metrics['aggregate']['coded_record_count']} records"
    )


@v02_app.command("sanitize")
def v02_sanitize_command(
    run_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False)],
    out: Annotated[Path, typer.Option("--out")] = Path(
        "public-results/ollama-v0.2"
    ),
) -> None:
    """Create an allowlisted, sanitized, hashed v0.2 result bundle."""

    try:
        manifest = sanitize_v02_run(run_dir.resolve(), out.resolve())
    except (OSError, ValueError, PublicationSafetyError, json.JSONDecodeError) as exc:
        console.print(f"[red]v0.2 sanitization failed: {exc}[/red]")
        raise typer.Exit(code=3) from exc
    console.print(
        f"[green]v0.2 sanitized bundle ready[/green] {out.resolve()} "
        f"({len(manifest['files'])} hashed artifacts)"
    )


@v02_app.command("verify-sanitize")
def v02_verify_sanitize_command(
    bundle_dir: Annotated[Path, typer.Argument(exists=True, file_okay=False)],
) -> None:
    """Verify v0.2 allowlist, hashes, and sanitized content without mutation."""

    try:
        verification = verify_v02_bundle(bundle_dir.resolve())
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        console.print(f"[red]v0.2 bundle verification failed: {exc}[/red]")
        raise typer.Exit(code=2) from exc
    if verification["status"] != "pass":
        console.print(f"[red]v0.2 bundle verification failed:[/red] {verification}")
        raise typer.Exit(code=3)
    console.print(
        f"[green]v0.2 bundle verification passed[/green] "
        f"{verification['manifest_hash_count']} hashes checked"
    )


@v02_app.command("demo")
def v02_demo_command(
    mode: Annotated[Mode, typer.Option("--mode", case_sensitive=False)] = Mode.mock,
    out: Annotated[Path, typer.Option("--out")] = Path("runs/v02-demo"),
    model: Annotated[str, typer.Option("--model")] = DEFAULT_MODEL,
    base_url: Annotated[str, typer.Option("--base-url")] = DEFAULT_BASE_URL,
    think: Annotated[str, typer.Option("--think")] = "false",
    timeout: Annotated[float, typer.Option("--timeout", min=0.1)] = 120.0,
    continue_on_error: Annotated[
        bool, typer.Option("--continue-on-error")
    ] = False,
) -> None:
    """Run four representative balanced and near-miss fixtures."""

    _execute_v02(
        mode=mode,
        profile=V02Profile.quick,
        replications=3,
        out=out,
        model=model,
        base_url=base_url,
        think=think,
        stream="false",
        timeout=timeout,
        cases=DEFAULT_V02_CASES_PATH,
        case_ids=["N007", "N015", "P001", "P017"],
        continue_on_error=continue_on_error,
    )


if __name__ == "__main__":
    app()
