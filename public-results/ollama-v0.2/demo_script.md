# ATRB v0.2 Three-Minute Demo

1. Read `report.md` and its central validity warning.
2. Compare positive acceptance, negative rejection, and balanced accuracy.
3. Inspect `near_miss_log.md` and `field_inconsistency_log.md`.
4. Open `replication_metrics.json`; repeated calls are not a deployment guarantee.
5. Keep rationale coding separate from primary structured metrics.

```bash
uv run atrb v02 demo --mode mock --out runs/v02-demo
uv run atrb v02 report runs/v02-demo --out runs/v02-demo/report.md
```

Mock output is deterministic demonstration data, not model-performance evidence.
