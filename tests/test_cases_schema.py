from __future__ import annotations

import json

import jsonschema

from atrb.benchmark import load_cases
from atrb.config import DEFAULT_CASES_PATH, PROJECT_ROOT


def test_all_18_cases_validate_against_json_schema() -> None:
    schema = json.loads(
        (PROJECT_ROOT / "data" / "schemas" / "case.schema.json").read_text(encoding="utf-8")
    )
    data = json.loads(DEFAULT_CASES_PATH.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    )
    for item in data:
        validator.validate(item)

    cases = load_cases(DEFAULT_CASES_PATH)
    assert len(cases) == 18
    assert len({case.case_id for case in cases}) == 18
    assert all(case.expected_decision == "reject" for case in cases)
