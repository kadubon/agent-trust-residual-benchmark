from __future__ import annotations

from atrb.config import DEFAULT_V02_CASES_PATH
from atrb.v02_runner import load_v02_cases


def test_v02_near_miss_distribution_and_boundaries() -> None:
    cases = load_v02_cases(DEFAULT_V02_CASES_PATH)
    near_misses = [case for case in cases if case.near_miss]
    near_positive = [case for case in near_misses if case.control_type == "positive"]
    near_negative = [case for case in near_misses if case.control_type == "negative"]
    ids = {case.case_id for case in near_misses}
    assert len(near_misses) >= 12
    assert len(near_positive) >= 6
    assert len(near_negative) >= 6
    assert {"N005", "N007", "N015", "N017", "P005", "P007", "P017"} <= ids
    assert all(case.difficulty == "near_miss" for case in near_misses)
