# Publication boundary

Never publish a raw `runs/` directory. For a requested public artifact, use the project's existing workflow: `uv run atrb v02 sanitize RUN_DIR --out public-results/NAME`, then `uv run atrb v02 verify-sanitize public-results/NAME`. The allowlisted sanitizer and scan reduce specific local-information risks; a passing scan is necessary but not sufficient for publication and does not inspect all secret forms or repository history.
