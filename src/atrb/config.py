"""Configuration shared by the benchmark runner and CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CASES_PATH = PROJECT_ROOT / "data" / "cases.json"
DEFAULT_MODEL = "qwen3.6:35b-a3b"
DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_EVALUATION_TIME = "2026-07-18T09:10:00Z"

CONDITIONS = (
    "raw_model_output",
    "pic_only",
    "pic_fost",
    "pic_fost_pfg",
    "ccr_independent_workcells",
    "fcc_temporal_claims",
)


class RunConfig(BaseModel):
    """Serializable settings for one benchmark run."""

    mode: Literal["mock", "ollama"]
    requested_mode: Literal["mock", "ollama"]
    model: str = DEFAULT_MODEL
    base_url: str = DEFAULT_BASE_URL
    think: bool = False
    stream: bool = False
    timeout_seconds: float = Field(default=120.0, gt=0)
    temperature: float = 0.0
    evaluation_time: str = DEFAULT_EVALUATION_TIME
    mock_fallback_used: bool = False
    cases_path: str
    case_ids: list[str] | None = None
    conditions: tuple[str, ...] = CONDITIONS
