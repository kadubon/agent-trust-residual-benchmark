from __future__ import annotations

import json

import jsonschema

from atrb.config import DEFAULT_V02_CASES_PATH
from atrb.v02_models import V02Case


def test_v02_dataset_is_schema_valid_and_balanced() -> None:
    data = json.loads(DEFAULT_V02_CASES_PATH.read_text(encoding="utf-8"))
    schema = json.loads(
        (DEFAULT_V02_CASES_PATH.parent / "schemas" / "case_v02.schema.json").read_text(
            encoding="utf-8"
        )
    )
    validator = jsonschema.Draft202012Validator(
        schema, format_checker=jsonschema.FormatChecker()
    )
    errors = [error for item in data for error in validator.iter_errors(item)]
    assert errors == []
    cases = [V02Case.model_validate(item) for item in data]
    positives = sum(case.control_type == "positive" for case in cases)
    negatives = sum(case.control_type == "negative" for case in cases)
    assert len(cases) >= 36
    assert abs(positives - negatives) <= 1
    assert positives == negatives == 18
