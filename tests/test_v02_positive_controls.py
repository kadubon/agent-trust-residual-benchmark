from __future__ import annotations

from atrb.config import DEFAULT_V02_CASES_PATH
from atrb.v02_runner import load_v02_cases


def test_v02_positive_controls_cover_bounded_permission_variants() -> None:
    positives = [
        case
        for case in load_v02_cases(DEFAULT_V02_CASES_PATH)
        if case.control_type == "positive"
    ]
    by_id = {case.case_id: case for case in positives}
    assert len(positives) == 18
    assert all(case.expected_decision == "accept" for case in positives)
    assert sum(not case.expected_failures for case in positives) >= 16
    assert by_id["P017"].expected_action_allowed is True
    assert by_id["P018"].expected_reusable is False
    assert by_id["P014"].expected_residuals
    assert by_id["P015"].expected_residuals == []
    assert any(case.expected_reusable for case in positives)
    assert any(not case.expected_reusable for case in positives)
