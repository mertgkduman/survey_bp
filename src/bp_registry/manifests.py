"""Versioned, strict input contract for the Phase 1 tracer."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Manifest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    schema_version: Literal[1]
    run_id: str = Field(min_length=1)
    source_uri: str = Field(min_length=1)
    source_revision: str = Field(min_length=1)
    source_anchor: str = Field(min_length=1)
    code_id: Literal["project-three-qubit-css-fixture"]
    experiment_relation: Literal["pilot_adaptation"]
    expected_output_status: Literal["not_assessed"]
    x_error_rate: float
    seed: int = Field(ge=0)
    max_iter: int = Field(ge=1)
    bp_method: Literal["product_sum"]
    schedule: Literal["parallel"]
    input_vector_type: Literal["syndrome"]

    @field_validator("x_error_rate")
    @classmethod
    def valid_rate(cls, value: float) -> float:
        if not math.isfinite(value) or not 0 <= value <= 1:
            raise ValueError("x_error_rate must be finite and in [0,1]")
        return value


def preflight(value: Manifest | dict | str | Path) -> Manifest:
    """Validate the whole fixture before sampling or invoking native code."""
    if isinstance(value, Manifest):
        manifest = value
    elif isinstance(value, (str, Path)):
        path = Path(value)
        if not path.is_file():
            raise FileNotFoundError(path)
        manifest = Manifest.model_validate_json(path.read_text(encoding="utf-8"))
    else:
        manifest = Manifest.model_validate(value)
    if not manifest.source_uri.startswith("https://"):
        raise ValueError("source_uri must be an HTTPS source reference")
    if not manifest.source_revision.strip() or not manifest.source_anchor.strip():
        raise ValueError("source revision and anchor are required")
    return manifest


def manifest_digest(manifest: Manifest) -> str:
    import hashlib

    payload = json.dumps(manifest.model_dump(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
