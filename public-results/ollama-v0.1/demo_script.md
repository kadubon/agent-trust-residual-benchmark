# Three-Minute Demo Script

This run contains 18 safe simulation cases.

1. Start with `report.md` and read the validity warning: all fixtures are expected rejects.
2. Compare raw and final counts, including the denominators rather than rates alone.
3. Show `result_summary.json` to separate supported findings from unsupported inferences.
4. Show `runtime.json` and explain that timing is local and host-specific.
5. Open `failure_log.md`, then inspect one finite record in `ledgers.jsonl`.

Reproduce this demo from the project root:

```bash
uv run atrb demo --mode mock --out runs/demo
uv run atrb report runs/demo --out runs/demo/report.md
```

Closing statement: accepted candidate work is not a truth guarantee, and a provider receipt is not
a real-world outcome observation.
