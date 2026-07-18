"""Deterministic model substitute used for reproducible local runs."""

from __future__ import annotations

import json

from atrb.models import BenchmarkCase


class MockLLM:
    """Return fixed unsafe judgments without any external dependency."""

    model = "atrb-deterministic-mock-v1"

    def generate(self, case: BenchmarkCase) -> tuple[str, float]:
        """Generate one deterministic raw-model baseline response."""

        if case.case_id == "C003":
            response = "{invalid-json: verification skipped}"
        else:
            response = json.dumps(
                {
                    "accepted": True,
                    "reusable": True,
                    "action_allowed": True,
                    "rationale": (
                        "The candidate output appears plausible. This intentionally unsafe "
                        "mock baseline does not validate evidence or authority."
                    ),
                },
                sort_keys=True,
            )
        deterministic_ms = 1.0 + int(case.case_id[1:]) * 0.01
        return response, deterministic_ms
