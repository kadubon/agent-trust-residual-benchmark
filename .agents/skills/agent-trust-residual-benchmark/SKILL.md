---
name: agent-trust-residual-benchmark
description: "Run and interpret the local Agent Trust and Residual Benchmark for AI-agent authority, provenance, residual-risk, permission, evidence-scope, temporal, verifier-independence, safe-reuse, and receipt-versus-outcome failure modes. Use for deterministic mock checks, explicit local Ollama experiments, or structured result interpretation. Do not use for generic LLM accuracy evaluation, production security certification, real-action execution, or claims of universal real-world agent safety."
license: Apache-2.0
metadata:
  author: K. Takahashi
  repository: https://github.com/kadubon/agent-trust-residual-benchmark
  version: "1.0"
---

# Agent Trust and Residual Benchmark

Measure declared fixture conformance while retaining false promotion, false rejection, and permission distinctions.

## Fast path

1. Select Fast deterministic check, Local model experiment, or Interpret existing results.
2. Use mock mode for installation, smoke testing, and deterministic reproduction.
3. Use Ollama only when the user explicitly requests model evaluation and it is available.
4. Read existing structured artifacts before rerunning an expensive experiment.
5. Interpret acceptance, reuse, and simulated action permission as separate fields.
6. Report metric denominators, fixture scope, residuals, and non-claims.

## Select a mode

### Fast deterministic check

```text
uv run atrb doctor
uv run atrb v02 run --mode mock --out runs/v02-mock
uv run atrb v02 report runs/v02-mock --out runs/v02-mock/report.md
```

Use a fresh ignored `runs/` path; do not add raw run directories to Git.

### Local model experiment

Use only after explicit user direction and a local Ollama/model availability check. The quick profile is `uv run atrb v02 run --mode ollama --model qwen3.6:35b-a3b --think false --replications 3 --profile quick --out runs/v02-ollama-quick`. Treat request failures as recorded data, not successful responses. Do not start the full profile merely to validate this skill.

### Interpret existing results

Prefer `metrics.json`, `replication_metrics.json`, `result_summary.json`, and reports in an existing run or the sanitized public bundle. Read [metric semantics](references/metric-semantics.md) before making comparisons.

## When to use

Use for trust/residual benchmark fixtures: authority or evidence scope, provenance mismatch, temporal claims, verifier independence, safe reuse/action allowance, false promotion/rejection, receipt-versus-outcome confusion, prompt injection controls, or local Ollama evaluation. For an individual agent-output protocol use PIC; for evidence packets use VEK; for persistent memory use CMGL; for adaptive science use Audit-Closed.

## Do not use

- Generic LLM benchmarking or generic accuracy evaluation.
- Production security certification, real action execution, or claims of real-world agent safety.
- An Ollama run unless model evaluation is explicitly requested.

## Evidence and result semantics

False promotion and false rejection are distinct errors. Balanced accuracy, field consistency, near-miss accuracy, safe action allowance, and safe reuse measure declared fixtures with stated denominators; no single headline replaces them. The final deterministic fixture conformance score does not establish universal safety or validate named external projects.

## Retrieve only what is needed

- Read [mode selection](references/mode-selection.md) for command choice.
- Read [metric semantics](references/metric-semantics.md) for results interpretation.
- Read [publication boundary](references/publication-boundary.md) only when preparing public artifacts.
- Read `docs/V02_EXPERIMENT.md` for the full protocol and `docs/SAFETY_AND_PRIVACY.md` before distribution.

## Validate

```text
uv run pytest
uv run atrb doctor
uv run atrb v02 run --mode mock --out runs/v02-mock
```

## Report

State outcome; mode and fixtures; metric values with denominators; false promotions and false rejections; residuals/request failures; scope; non-claims; and the next safe action.

## Required non-claims

- Fixture conformance is not universal real-world agent safety.
- A receipt is not a real-world outcome.
- Benchmark execution never authorizes an external action.
