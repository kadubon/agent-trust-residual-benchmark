# Publication Checklist

## v0.2.0 release checks

- [x] Full 36-case, five-replication Ollama run completed without mock fallback.
- [x] The one request timeout is retained and disclosed; 179/180 responses parsed successfully.
- [x] Decision matrix contains 360/360 normalized entries.
- [x] Positive, negative, near-miss, reuse, and action-permission metrics report denominators.
- [x] Timeout-inclusive operational metrics and successful-response sensitivity are distinguished.
- [x] Final fixture decisions match 36/36 and expected negative labels match 20/20.
- [x] Scientific docs distinguish raw-model observations from deterministic fixture conformance.
- [x] Rationale coding remains separate and no uncoded rationale-quality claim is made.
- [x] Local absolute paths are removed from the v0.2 public bundle.
- [x] Sixteen allowlisted publication artifacts are SHA-256 hashed and verified.
- [x] Automated publication safety audit has zero blocking findings.
- [x] Source and documentation safety review has zero blocking findings after inspecting the
  scanner's self-referential pattern definition.
- [x] Release identifier `v0.2.0` and citation metadata are synchronized.

## Historical v0.1.0 release checks

## Required technical checks

- [x] Full 18-case Ollama run completed without mock fallback.
- [x] Eighteen raw responses parsed as valid JSON.
- [x] Decision matrix contains 108/108 entries.
- [x] Expected final failure labels match 20/20 with no unexpected final labels.
- [x] Scientific report states that positive-control count is zero.
- [x] Raw C007 and C017 permission inconsistencies are reported.
- [x] Heuristic metrics are distinguished from observed measurements.
- [x] Local absolute paths are removed from the public bundle.
- [x] Publication artifacts are allowlisted and SHA-256 hashed.
- [x] Automated safety audit has zero blocking findings.
- [x] Publishable source paths, usernames, emails, and common secret shapes have zero matches.
- [x] Source, tests, and documentation pass project quality gates.

## Required human checks before external release

- [x] Read all 18 raw rationales for unexpected personal or offensive content.
- [x] Confirm that the Apache-2.0 license and repository attribution apply to the result bundle.
- [x] Confirm that the initial public commit and remote-hosting metadata contain no secrets.
- [x] Confirm that no local <code>runs/</code> directory is uploaded.
- [x] Confirm that release claims do not exceed [Results](RESULTS.md).
- [x] Record release identifier <code>v0.1.0</code> and citation metadata in
  [CITATION.cff](../CITATION.cff). No DOI or external archival identifier is claimed.

The automated checks are necessary but not sufficient. External publication remains a deliberate
maintainer action.
