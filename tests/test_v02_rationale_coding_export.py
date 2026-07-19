from __future__ import annotations

import json
from pathlib import Path

from atrb.config import (
    DEFAULT_BASE_URL,
    DEFAULT_V02_CASES_PATH,
    DEFAULT_V02_EVALUATION_TIME,
)
from atrb.v02_coding import export_rationale_coding, import_rationale_coding
from atrb.v02_mock import V02_MOCK_MODEL
from atrb.v02_models import V02RunConfig
from atrb.v02_runner import run_v02_benchmark


def test_v02_coding_export_is_blinded_and_import_stays_separate(tmp_path: Path) -> None:
    run_dir = tmp_path / "run"
    config = V02RunConfig(
        mode="mock",
        requested_mode="mock",
        model=V02_MOCK_MODEL,
        base_url=DEFAULT_BASE_URL,
        evaluation_time=DEFAULT_V02_EVALUATION_TIME,
        replications=1,
        cases_path=str(DEFAULT_V02_CASES_PATH),
    )
    run_v02_benchmark(config, run_dir)
    export_path = run_dir / "blinded_rationales.jsonl"
    export_rationale_coding(run_dir, export_path)
    records = [
        json.loads(line) for line in export_path.read_text(encoding="utf-8").splitlines()
    ]
    assert len(records) == 36
    serialized = json.dumps(records)
    assert "case_id" not in serialized
    assert "expected_decision" not in serialized
    assert "expected_failures" not in serialized
    assert all(record["blind_id"].startswith("B") for record in records)
    assert (run_dir / "coding_protocol.md").is_file()

    coded = run_dir / "coded.jsonl"
    coded.write_text(
        json.dumps(
            {
                "blind_id": records[0]["blind_id"],
                "coder_id": "coder-a",
                "recognized_hazards": ["missing_agent_identity"],
                "rationale_supports_reject": True,
                "rationale_permission_inconsistent": False,
                "confidence": 0.8,
                "notes": "The rationale explicitly supports rejection.",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    metrics = import_rationale_coding(run_dir, coded)
    assert metrics["primary_score_included"] is False
    assert metrics["aggregate"]["coded_record_count"] == 1
    assert metrics["inter_rater_reliability"] is None
    assert (run_dir / "rationale_coding_report.md").is_file()
