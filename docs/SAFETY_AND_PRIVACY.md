# Safety and Privacy Review

## Discovered local information

The original local run is not publication-safe as generated:

- <code>config.json</code> contains an absolute Windows path with the local user-directory name.
- <code>demo_script.md</code> contains absolute project and output paths.

These fields are operational metadata, not experimental evidence. The publication exporters replace
the cases path with a repository-relative data path and regenerate demo commands with relative paths.

## Publication workflow

~~~bash
uv run atrb report runs/ollama --out runs/ollama/report.md
uv run atrb prepare-publication runs/ollama --out public-results/ollama-v0.1
uv run atrb safety-audit public-results/ollama-v0.1
uv run atrb verify-publication public-results/ollama-v0.1
uv run atrb v02 sanitize runs/v02-ollama-full --out public-results/ollama-v0.2
uv run atrb v02 verify-sanitize public-results/ollama-v0.2
~~~

The standalone re-audit is written beside the bundle so it does not invalidate manifest hashes.

Do not publish any <code>runs/</code> directory directly. Publish only a sanitized allowlisted bundle.

## Blocking scan classes

The scanner fails closed on:

- Windows and POSIX user-home paths
- the current local username
- file URIs
- email addresses
- private-network IPv4 addresses
- common private-key markers
- common AWS, GitHub, and <code>sk-</code> token formats
- quoted values assigned to password, secret, API-key, or access-token fields
- non-UTF-8 text within the scanned artifact set

Matched values are redacted from the audit output so that the audit does not reproduce the secret.

## Intentional disclosures

The public bundle retains:

- the localhost Ollama endpoint
- model identifier and inference settings
- UTC run timestamps
- coarse operating-system, architecture, and Python-version metadata
- inert prompt-injection fixture text

These are retained for reproducibility. Hostname recording is explicitly disabled.

## Scanner limitations

Passing the scan is not proof that re-identification is impossible. The scanner does not inspect
repository history, remote-hosting metadata, binary files, steganographic content, or every possible
secret format. Human review of raw model rationales and publication metadata remains required.

## Operational safety

The benchmark performs no deployment, deletion, payment, external send, or remote mutation. All
actions are simulated strings. The local model endpoint is loopback-only in the recorded
configuration.
