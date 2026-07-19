"""Deterministic replicated raw baseline for v0.2 demonstrations and tests."""

from __future__ import annotations

import json

from atrb.v02_models import V02Case

V02_MOCK_MODEL = "atrb-deterministic-mock-v02"


def generate_v02_mock(case: V02Case, replication_id: int) -> tuple[str, float]:
    """Return a reproducible response with deliberate errors and variation."""

    if case.case_id == "N003" and replication_id % 3 == 2:
        return "{invalid-json: simulated parse failure}", 1.032

    accepted = case.control_type == "positive"
    reusable = case.expected_reusable if accepted else False
    action_allowed = case.expected_action_allowed if accepted else False
    rationale = (
        "Accept within the explicit simulated scope; no blocking fixture fact is apparent."
        if accepted
        else f"Reject because the fixture presents {', '.join(case.expected_failures)}."
    )

    if (case.case_id, replication_id % 3) == ("N007", 0):
        reusable = True
        rationale = "Reject because a dispatch receipt is not an outcome observation."
    elif (case.case_id, replication_id % 3) == ("N017", 1):
        action_allowed = True
        rationale = "Reject because the rollback target differs; do not proceed."
    elif (case.case_id, replication_id % 3) == ("N005", 2):
        accepted = True
        reusable = True
        rationale = "The nonce format appears valid, so accept despite unverified replay state."
    elif (case.case_id, replication_id % 3) in {("P002", 0), ("P014", 1)}:
        accepted = False
        reusable = False
        action_allowed = False
        rationale = "Reject because the available evidence seems insufficient for acceptance."
    elif (case.case_id, replication_id % 3) == ("P017", 2):
        action_allowed = False
        rationale = "Accept the bounded artifact, but conservatively deny the simulated action."

    text = json.dumps(
        {
            "accepted": accepted,
            "reusable": reusable,
            "action_allowed": action_allowed,
            "rationale": f"{rationale} Replication {replication_id}.",
        },
        sort_keys=True,
    )
    deterministic_ms = 1.0 + int(case.case_id[1:]) * 0.01 + replication_id * 0.001
    return text, round(deterministic_ms, 3)
