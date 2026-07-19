from __future__ import annotations

from atrb.config import DEFAULT_V02_CASES_PATH, DEFAULT_V02_EVALUATION_TIME
from atrb.v02_runner import load_v02_cases
from atrb.v02_validators import inspect_case


def test_v02_negative_controls_fail_closed_with_expected_final_labels() -> None:
    negatives = [
        case
        for case in load_v02_cases(DEFAULT_V02_CASES_PATH)
        if case.control_type == "negative"
    ]
    assert len(negatives) == 18
    assert all(case.expected_failures for case in negatives)
    assert all(not case.expected_reusable for case in negatives)
    assert all(not case.expected_action_allowed for case in negatives)
    for case in negatives:
        detected = inspect_case(case, DEFAULT_V02_EVALUATION_TIME).through(5)
        assert set(detected) == set(case.expected_failures), case.case_id
