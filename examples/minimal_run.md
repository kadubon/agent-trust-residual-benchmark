# Minimal Reproduction

From the project root:

~~~bash
uv sync
uv run atrb doctor
uv run atrb run --mode mock --out runs/mock
uv run atrb report runs/mock --out runs/mock/report.md
~~~

The run is successful when the command exits with code 0 and the output directory contains 108
decisions: 18 cases multiplied by six conditions.
