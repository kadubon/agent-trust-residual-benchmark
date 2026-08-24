# Metric semantics

- **False promotion**: an invalid fixture receives an acceptance, reuse, or action permission the fixture denies.
- **False rejection**: a valid fixture is rejected or a required permission is denied.
- **Balanced accuracy**: combines accept and reject recall; keep its denominator and condition visible.
- **Field consistency**: the decision object's related fields agree under fixture rules.
- **Near-miss accuracy**: correctness on deliberately close boundary cases.
- **Safe action allowance / safe reuse**: action permission and reuse permission; neither follows from `accepted` alone.

Raw model rows are replication-level; deterministic condition rows are one decision per case. Do not compare them as if they had the same sampling unit.
