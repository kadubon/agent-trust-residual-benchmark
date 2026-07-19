# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-07-19

### Added

- Experiment-ready v0.2 command group with balanced positive and negative controls.
- Thirty-six dedicated fixtures, including 15 near-miss boundary cases.
- Replicated raw-model calls, field-consistency analysis, and balanced decision metrics.
- Blinded rationale coding export/import with primary-score separation.
- Dedicated allowlisted v0.2 sanitization and bundle verification.
- v0.2 scientific reports, control logs, replication artifacts, documentation, and tests.

### Compatibility

- All v0.1 commands, fixtures, reports, and publication workflows remain available.
- The v0.2 result bundle records 180 attempted local-model calls, including one fail-closed timeout.

### Results

- The raw condition accepted all 90 positive-control replications and produced 20 permission-level
  false promotions across 90 negative-control attempts.
- The final cumulative compatibility condition matched 36/36 fixture decisions and 20/20 expected
  negative-control labels. This is bounded fixture conformance, not external safety validation.
- A sanitized full-run Ollama bundle contains 16 hashed artifacts and zero blocking safety-scan
  findings.

## [0.1.0] - 2026-07-18

### Added

- Six-condition benchmark for progressively layered trust and residual checks.
- Eighteen synthetic negative-control fixtures and deterministic validators.
- Local Ollama and deterministic mock execution modes.
- Machine-readable decisions, ledgers, residuals, metrics, and runtime metadata.
- Scientific result summaries with explicit design limitations and uncertainty boundaries.
- Sanitized full-run result bundle with allowlisting, SHA-256 manifests, and safety verification.
- Publication-preparation commands, documentation, citation metadata, and related-project guidance.

See the [v0.1.0 release notes](docs/releases/v0.1.0.md) for the bounded scientific result and its
essential limitations.

[0.1.0]: https://github.com/kadubon/agent-trust-residual-benchmark/releases/tag/v0.1.0
[0.2.0]: https://github.com/kadubon/agent-trust-residual-benchmark/releases/tag/v0.2.0
