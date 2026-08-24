# Mode selection

| Need | Existing interface | Boundary |
| --- | --- | --- |
| Installation or deterministic smoke test | `uv run atrb doctor`; `uv run atrb v02 run --mode mock --out ...` | mock results are not model performance |
| Three-case walkthrough | `uv run atrb v02 demo --mode mock --out ...` | no Ollama dependency |
| Explicit local-model study | `uv run atrb v02 run --mode ollama ... --profile quick` | run only on explicit request; retain failures |
| Existing-result interpretation | inspect structured artifacts, then `uv run atrb v02 report RUN_DIR --out ...` | do not rerun needlessly |

Use an ignored `runs/` directory for generated work. The public result path is a separate sanitization workflow.
