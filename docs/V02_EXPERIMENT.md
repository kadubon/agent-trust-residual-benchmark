# ATRB v0.2 Experiment Protocol

## Status

ATRB v0.2.0 is a completed balanced-control experiment. The release includes a sanitized full
Ollama run under `public-results/ollama-v0.2/`. Read [v0.2 Scientific Results](V02_RESULTS.md)
before interpreting the metrics.

The published v0.1 experiment, commands, dataset, and result bundle remain unchanged.

## Research question

Can a bounded synthetic benchmark measure both unnecessary promotion and unnecessary rejection
while keeping raw structured decisions, replicated-call variation, and free-text rationale coding
scientifically separate?

This protocol does not test real-world agent safety. It evaluates declared fixture behavior.

## Dataset

`data/cases_v02.json` contains 36 simulation-only cases validated by
`data/schemas/case_v02.schema.json`:

- 18 positive controls with `expected_decision=accept`;
- 18 negative controls with `expected_decision=reject`;
- 15 near misses: eight positive and seven negative;
- 20 expected blocking failure labels across the negative controls.

Positive controls are not permission-all fixtures. P017 expects one bounded simulated action to be
allowed. P018 is expected to be accepted but non-reusable. P008 and P014 retain explicit nonblocking
residuals and limited reuse. These cases test whether a validator distinguishes acceptance,
settlement, reuse, and action permission.

Near misses exercise close temporal, scope, rollback, receipt, nonce, and independence boundaries.
Their labels are fixture-policy facts, not universal definitions of safety or independence.

## Conditions

v0.2 retains the six v0.1 condition names:

1. `raw_model_output`
2. `pic_only`
3. `pic_fost`
4. `pic_fost_pfg`
5. `ccr_independent_workcells`
6. `fcc_temporal_claims`

The raw condition has multiple replications per case. Each deterministic condition runs once per
case and preserves `replication_id=0` in its normalized schema. Deterministic conditions accumulate
checks and are lightweight compatibility adapters, not imports or validation of the named external
projects.

## Local execution

~~~bash
uv sync
uv run atrb v02 run --mode mock --out runs/v02-mock
uv run atrb v02 report runs/v02-mock --out runs/v02-mock/report.md
uv run atrb v02 demo --mode mock --out runs/v02-demo
~~~

Quick local Ollama experiment:

~~~bash
uv run atrb v02 run \
  --mode ollama \
  --model qwen3.6:35b-a3b \
  --think false \
  --stream false \
  --replications 3 \
  --profile quick \
  --out runs/v02-ollama-quick
~~~

`temperature` is fixed at zero by the CLI and is recorded in `config.json`; it is not exposed as a
mutable option. The full profile uses five replications:

~~~bash
uv run atrb v02 run --mode ollama --model qwen3.6:35b-a3b --think false --replications 5 --profile full --out runs/v02-ollama-full
~~~

The quick and full designs make 108 and 180 raw calls. Request failures are retained as case-level
records. The default exits nonzero after writing artifacts if any request failed; use
`--continue-on-error` to accept a completed run with recorded failures.

## Primary decision metrics

`metrics.json` is the primary structured metric artifact. Per condition it records:

- expected accept/reject counts;
- true accept/reject counts;
- false rejection and false promotion counts and rates;
- accept recall and reject recall;
- balanced accuracy;
- field consistency and permission inconsistency rates;
- near-miss accuracy;
- positive acceptance and negative rejection rates;
- safe action allowance and safe reuse accuracy;
- expected failure-label yield;
- parse and request failure counts.

Raw metrics have replication-level denominators. Deterministic conditions have one decision per
case. Reports show counts and denominators to prevent those units from being confused.

## Replication analysis

`replication_metrics.json` applies only to raw calls. It records per-case acceptance variance,
permission inconsistency frequency, response-hash uniqueness, replication-level false promotion and
false rejection, parse/request failures, and successful-call latency distribution.

Replications characterize variation in the recorded configuration. They do not establish stability
across model versions, hosts, prompts, runtime versions, or deployments.

## Rationale coding

Export a blinded worksheet and protocol:

~~~bash
uv run atrb v02 export-coding runs/v02-ollama-quick --out runs/v02-ollama-quick/blinded_rationales.jsonl
~~~

The export contains blind IDs, scenarios, candidate outputs, raw rationales, and the global candidate
label vocabulary. It does not contain case IDs, expected decisions, or case-level expected labels.
The private mapping remains inside the ignored run directory.

After one or more coders create JSONL records following `coding_protocol.md`, import them:

~~~bash
uv run atrb v02 import-coding runs/v02-ollama-quick --coding runs/v02-ollama-quick/blinded_rationales.coded.jsonl
~~~

The import writes `rationale_coding_metrics.json` and `rationale_coding_report.md`. These are
secondary artifacts. They never modify balanced accuracy or other structured decision metrics.
Single-coder use works in v0.2; inter-rater reliability is an explicit future extension.

## Generated run artifacts

Every v0.2 run writes:

~~~text
config.json
cases.normalized.json
raw_outputs.jsonl
raw_replications.jsonl
decisions.jsonl
residuals.jsonl
ledgers.jsonl
metrics.json
replication_metrics.json
result_summary.json
report.md
failure_log.md
positive_control_log.md
near_miss_log.md
field_inconsistency_log.md
runtime.json
demo_script.md
~~~

Report generation is reproducible from the normalized cases, decisions, raw replications, config,
and runtime record.

## Sanitization

~~~bash
uv run atrb v02 sanitize runs/v02-ollama-quick --out public-results/ollama-v0.2
uv run atrb v02 verify-sanitize public-results/ollama-v0.2
~~~

The sanitizer copies only its declared artifact allowlist, rewrites the absolute cases path,
regenerates relative demo commands, scans text, and hashes 16 artifacts. Coding maps, human-coded
inputs, residual ledgers, and any unrecognized file are excluded. The scan checks common local home
paths, usernames, recorded hostnames, email-like strings, private-network addresses, private-key
markers, and common token or assigned-secret shapes. Loopback Ollama configuration is allowed.

The scanner does not inspect repository history, binary semantics, steganographic content, or every
possible secret representation. A passing result is necessary but not sufficient for publication.

## Supported interpretation

A completed run can support statements about:

- structured decision metrics on these synthetic fixtures;
- observed positive, negative, and near-miss results;
- raw structured field consistency;
- variation within the recorded replications;
- deterministic compatibility-adapter fixture conformance.

It cannot support claims about:

- real-world agent safety or truth;
- successful production execution;
- external PIC, FOST, PFG, CCR, or FCC implementation validity;
- statistical generalization beyond the fixtures;
- isolated causal effects of cumulative layers;
- human labor or monetary cost;
- behavior stability across untested versions or hardware.

## Experiment-ready quality gates

~~~bash
uv sync
uv run ruff check .
uv run mypy src
uv run pytest
uv run atrb doctor
uv run atrb run --mode mock --out runs/mock-v01-regression
uv run atrb v02 run --mode mock --out runs/v02-mock
uv run atrb v02 report runs/v02-mock --out runs/v02-mock/report.md
uv run atrb v02 export-coding runs/v02-mock --out runs/v02-mock/blinded_rationales.jsonl
uv run atrb v02 demo --mode mock --out runs/v02-demo
~~~

The full Ollama run is intentionally outside the mandatory readiness gate.

## Completed release run

The v0.2.0 release run used the full profile: 36 cases, five raw replications per case, 180 attempted
calls, and 179 successful responses. One N001 request timed out and was retained as a fail-closed
record. The complete run took 1,383.4 seconds on the recorded host. These observations describe this
run only and are not portable performance estimates.

Use only the sanitized bundle:

~~~bash
uv run atrb v02 verify-sanitize public-results/ollama-v0.2
~~~
