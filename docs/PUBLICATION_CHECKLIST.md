# Publication Checklist

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
