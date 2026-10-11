"""Immutable source and plot-digitization receipts for campaign targets.

The SHA-256 fields in this module bind evidence bytes to a receipt.  They are
integrity linkage, not a claim about who authored a source document.
"""

from __future__ import annotations

from datetime import date, datetime
from hashlib import sha256
import json
import math
from pathlib import Path, PurePosixPath
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from ..manifests import StrictModel


_SHA256 = r"^[0-9a-f]{64}$"
_INTEGRITY_STATEMENT = "sha256_integrity_linkage_not_authorship_v1"


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False,
    ).encode("utf-8")


def _receipt_digest(domain: str, value: StrictModel) -> str:
    return sha256(domain.encode("ascii") + b"\0" + _canonical_json_bytes(value.model_dump(mode="json", by_alias=True))).hexdigest()


def _finite(value: float, *, name: str) -> float:
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    return value


def _confined_relative_path(value: str) -> str:
    path = PurePosixPath(value)
    if not value or "\\" in value or path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("snapshot path must be a confined relative POSIX path")
    return value


class ByteSnapshotV1(StrictModel):
    """A caller-owned immutable byte observation recorded by relative evidence path."""

    relative_path: str = Field(min_length=1, max_length=1_024)
    sha256: str = Field(pattern=_SHA256)
    byte_count: int = Field(ge=0, le=64 * 1024 * 1024)
    integrity_statement: Literal["sha256_integrity_linkage_not_authorship_v1"] = _INTEGRITY_STATEMENT

    @field_validator("relative_path")
    @classmethod
    def confined_relative_path(cls, value: str) -> str:
        return _confined_relative_path(value)

    @classmethod
    def from_bytes(cls, relative_path: str, contents: bytes) -> "ByteSnapshotV1":
        """Create a receipt from one already-owned byte snapshot without rereading it."""
        return cls(
            relative_path=relative_path,
            sha256=sha256(contents).hexdigest(),
            byte_count=len(contents),
        )


def read_confined_snapshot(evidence_root: str | Path, relative_path: str) -> ByteSnapshotV1:
    """Read one regular evidence file, rejecting traversal and every symlink hop."""
    _confined_relative_path(relative_path)
    root = Path(evidence_root)
    if not root.is_dir():
        raise ValueError("evidence root must be an existing directory")
    resolved_root = root.resolve(strict=True)
    candidate = root.joinpath(*PurePosixPath(relative_path).parts)
    current = root
    for part in PurePosixPath(relative_path).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("evidence snapshot path cannot traverse a symlink")
    if not candidate.is_file():
        raise ValueError("evidence snapshot path must be a regular file")
    resolved_candidate = candidate.resolve(strict=True)
    if not resolved_candidate.is_relative_to(resolved_root):
        raise ValueError("evidence snapshot path escapes its root")
    contents = candidate.read_bytes()
    return ByteSnapshotV1.from_bytes(relative_path, contents)


class SourceIdentityV1(StrictModel):
    """Verbatim bibliographic identity retained separately from content integrity."""

    uri_or_doi: str = Field(min_length=1, max_length=2_048)
    revision: str = Field(min_length=1, max_length=512)
    accessed_on: date

    @field_validator("uri_or_doi")
    @classmethod
    def source_uri_or_doi(cls, value: str) -> str:
        if not (value.startswith("https://") or value.startswith("doi:") or value.startswith("10.")):
            raise ValueError("source identity must be an HTTPS URI or DOI")
        return value


class TableCellLocatorV1(StrictModel):
    """Exact location of one reported table or data value."""

    table_id: str = Field(min_length=1, max_length=256)
    row_id: str = Field(min_length=1, max_length=512)
    column_id: str = Field(min_length=1, max_length=512)
    marker_id: str | None = Field(default=None, min_length=1, max_length=256)


class ValueBoundsV1(StrictModel):
    """Reported central value, asymmetric source bounds, and source precision."""

    value: float
    lower_error: float = Field(ge=0.0)
    upper_error: float = Field(ge=0.0)
    precision: float = Field(gt=0.0)

    @field_validator("value", "lower_error", "upper_error", "precision")
    @classmethod
    def finite_values(cls, value: float, info: Any) -> float:
        return _finite(value, name=info.field_name)


class SourceDenominatorV1(StrictModel):
    """Published sample-count evidence; unavailable values are never guessed."""

    status: Literal["observed", "unavailable", "not_applicable"]
    count: int | None = Field(default=None, ge=1)
    reason: str | None = Field(default=None, min_length=1, max_length=1_024)

    @model_validator(mode="after")
    def explicit_denominator_status(self) -> "SourceDenominatorV1":
        if self.status == "observed":
            if self.count is None or self.reason is not None:
                raise ValueError("an observed denominator needs only its explicit positive count")
        elif self.count is not None or self.reason is None:
            raise ValueError("an unavailable or not-applicable denominator needs a reason and no count")
        return self


class TableTargetReceiptV1(StrictModel):
    """A direct source/table target frozen before simulation assessment."""

    schema_name: Literal["campaign_table_target_v1"] = Field(alias="schema", serialization_alias="schema")
    target_id: str = Field(min_length=1, max_length=256)
    source: SourceIdentityV1
    location: TableCellLocatorV1
    source_snapshot: ByteSnapshotV1
    reported: ValueBoundsV1
    source_denominator: SourceDenominatorV1

    def digest(self) -> str:
        return _receipt_digest("bp-registry-campaign-table-target-v1", self)
