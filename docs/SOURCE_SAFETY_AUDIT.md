# Source and Result Safety Audit

## Scope

The publication-oriented scan covered <code>pyproject.toml</code>, <code>uv.lock</code>,
<code>README.md</code>, <code>docs/</code>, <code>src/</code>, <code>tests/</code>,
<code>examples/</code>, and <code>public-results/</code>. Local virtual environments, tool caches,
and <code>runs/</code> were excluded because they are ignored working data.

No Git command was used, so repository history and remote metadata were not inspected.

## Automated pattern result

No publishable-source match was found for:

- Windows or POSIX user-home paths
- the local username
- email addresses
- AWS access-key shapes
- GitHub token shapes
- <code>sk-</code> key shapes
- quoted password, secret, API-key, or access-token assignments

The scanner implementation necessarily contains a regular-expression string describing a private
key marker. That source-code pattern is not key material.

## Original run finding

The ignored local <code>runs/ollama/</code> directory contained two classes of local path:

1. An absolute <code>cases_path</code> in <code>config.json</code>.
2. Absolute output paths in <code>demo_script.md</code>.

The public exporter removes both. The sanitized bundle passed its content scan with zero blocking
findings, and all 13 manifest hashes were verified.

## Raw-output content review

All 18 raw rationales were reviewed during publication preparation. No personal data, credentials,
external URLs, executable commands, filesystem paths, or real-world action instructions were
observed. The files contain expected security terminology and inert descriptions of prompt
injection, replay, rollback, and data-corruption risks.

This review is bounded to the current files and does not guarantee that future model runs will
remain free of sensitive or objectionable content.
