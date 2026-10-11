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
_MAX_SNAPSHOT_BYTES = 64 * 1024 * 1024
_MAX_QUALIFICATION_BLOCKERS = 256


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
    byte_count: int = Field(ge=0, le=_MAX_SNAPSHOT_BYTES)
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
    if root.is_symlink():
        raise ValueError("evidence root cannot be a symlink")
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
    if candidate.stat().st_size > _MAX_SNAPSHOT_BYTES:
        raise ValueError("evidence snapshot exceeds the bounded receipt size")
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


class SourceTargetLocatorV1(StrictModel):
    """The source location of one named experiment variant and point."""

    paper_id: str = Field(min_length=1, max_length=512)
    figure_or_table_id: str = Field(min_length=1, max_length=512)
    curve_id: str = Field(min_length=1, max_length=512)
    variant_id: str = Field(min_length=1, max_length=512)
    point_id: str = Field(min_length=1, max_length=512)


class SourceStoppingEvidenceV1(StrictModel):
    """Source stopping evidence whose unknown state cannot become a default."""

    status: Literal["observed", "unavailable"]
    rule: str | None = Field(default=None, min_length=1, max_length=2_048)
    snapshot: ByteSnapshotV1 | None = None
    reason: str | None = Field(default=None, min_length=1, max_length=1_024)

    @model_validator(mode="after")
    def explicit_stopping_status(self) -> "SourceStoppingEvidenceV1":
        if self.status == "observed":
            if self.rule is None or self.snapshot is None or self.reason is not None:
                raise ValueError("observed source stopping needs rule and snapshot only")
        elif self.rule is not None or self.snapshot is not None or self.reason is None:
            raise ValueError("unavailable source stopping needs a reason and no inferred rule")
        return self


class SourceExperimentIdentityV1(StrictModel):
    """Complete D-02 identity for one paper experiment without fidelity inference."""

    schema_name: Literal["campaign_source_experiment_identity_v1"] = Field(alias="schema", serialization_alias="schema")
    target_id: str = Field(min_length=1, max_length=256)
    paper: SourceIdentityV1
    paper_snapshot: ByteSnapshotV1
    locator: SourceTargetLocatorV1
    ordered_check_artifacts: tuple[ByteSnapshotV1, ...] = Field(min_length=1, max_length=128)
    ordered_logical_artifacts: tuple[ByteSnapshotV1, ...] = Field(min_length=1, max_length=128)
    channel_convention: str = Field(min_length=1, max_length=1_024)
    source_denominator: SourceDenominatorV1
    stopping: SourceStoppingEvidenceV1
    author_implementation_status: Literal["verified", "unverified", "unavailable"]
    author_implementation_uri: str | None = Field(default=None, min_length=1, max_length=2_048)
    author_implementation_revision: str | None = Field(default=None, min_length=1, max_length=512)
    author_environment_snapshot: ByteSnapshotV1 | None = None
    author_settings_snapshot: ByteSnapshotV1 | None = None
    executable_policy_sha256: str = Field(pattern=_SHA256)
    qualification_blockers: tuple[str, ...] = Field(default=(), max_length=_MAX_QUALIFICATION_BLOCKERS)

    @field_validator("ordered_check_artifacts", "ordered_logical_artifacts", "qualification_blockers", mode="before")
    @classmethod
    def tuple_records(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @field_validator("qualification_blockers")
    @classmethod
    def bounded_blockers(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not blocker or len(blocker) > 1_024 for blocker in value):
            raise ValueError("qualification blockers must be bounded nonempty strings")
        if len(set(value)) != len(value):
            raise ValueError("qualification blockers must be unique")
        return value

    @field_validator("author_implementation_uri")
    @classmethod
    def https_implementation_uri(cls, value: str | None) -> str | None:
        if value is not None and not value.startswith("https://"):
            raise ValueError("author implementation URI must use HTTPS")
        return value

    @model_validator(mode="after")
    def complete_or_explicitly_gapped_author_evidence(self) -> "SourceExperimentIdentityV1":
        author_fields = (
            self.author_implementation_uri,
            self.author_implementation_revision,
            self.author_environment_snapshot,
            self.author_settings_snapshot,
        )
        if self.author_implementation_status == "verified":
            if any(field is None for field in author_fields):
                raise ValueError("verified author implementation needs URI, revision, environment, and settings")
        elif any(field is not None for field in author_fields):
            raise ValueError("unverified author implementation fields cannot be inferred")
        elif not self.qualification_blockers:
            raise ValueError("unverified author implementation needs an explicit qualification blocker")
        snapshots = (
            self.paper_snapshot,
            *self.ordered_check_artifacts,
            *self.ordered_logical_artifacts,
            *(() if self.stopping.snapshot is None else (self.stopping.snapshot,)),
            *(() if self.author_environment_snapshot is None else (self.author_environment_snapshot,)),
            *(() if self.author_settings_snapshot is None else (self.author_settings_snapshot,)),
        )
        paths = tuple(snapshot.relative_path for snapshot in snapshots)
        if len(set(paths)) != len(paths):
            raise ValueError("source identity snapshots must have distinct confined paths")
        return self

    @property
    def complete_for_faithful_assessment(self) -> bool:
        return (
            self.author_implementation_status == "verified"
            and self.source_denominator.status == "observed"
            and self.stopping.status == "observed"
            and not self.qualification_blockers
        )

    def digest(self) -> str:
        return _receipt_digest("bp-registry-campaign-source-experiment-identity-v1", self)


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


class AxisCalibrationPointV1(StrictModel):
    """One WebPlotDigitizer-style calibration point with pixel and data values."""

    pixel_x: float
    pixel_y: float
    value: float

    @field_validator("pixel_x", "pixel_y", "value")
    @classmethod
    def finite_coordinates(cls, value: float, info: Any) -> float:
        return _finite(value, name=info.field_name)


class XYCalibrationV1(StrictModel):
    """The four X1/X2/Y1/Y2 evidence points and their declared axis scales."""

    x_scale: Literal["linear", "log10"]
    y_scale: Literal["linear", "log10"]
    x1: AxisCalibrationPointV1
    x2: AxisCalibrationPointV1
    y1: AxisCalibrationPointV1
    y2: AxisCalibrationPointV1

    @model_validator(mode="after")
    def usable_four_point_calibration(self) -> "XYCalibrationV1":
        if self.x1.pixel_x == self.x2.pixel_x or self.x1.value == self.x2.value:
            raise ValueError("X1 and X2 must have distinct pixel-x and data values")
        if self.y1.pixel_y == self.y2.pixel_y or self.y1.value == self.y2.value:
            raise ValueError("Y1 and Y2 must have distinct pixel-y and data values")
        if self.x_scale == "log10" and (self.x1.value <= 0.0 or self.x2.value <= 0.0):
            raise ValueError("logarithmic X calibration values must be positive")
        if self.y_scale == "log10" and (self.y1.value <= 0.0 or self.y2.value <= 0.0):
            raise ValueError("logarithmic Y calibration values must be positive")
        return self

    @staticmethod
    def _transform(pixel: float, first: AxisCalibrationPointV1, second: AxisCalibrationPointV1, scale: Literal["linear", "log10"], *, coordinate: Literal["x", "y"]) -> float:
        numerator = pixel - (first.pixel_x if coordinate == "x" else first.pixel_y)
        denominator = (second.pixel_x if coordinate == "x" else second.pixel_y) - (first.pixel_x if coordinate == "x" else first.pixel_y)
        fraction = numerator / denominator
        if scale == "linear":
            return first.value + fraction * (second.value - first.value)
        return 10.0 ** (math.log10(first.value) + fraction * (math.log10(second.value) - math.log10(first.value)))

    def transformed_values(self, pixel_x: float, pixel_y: float) -> tuple[float, float]:
        """Return the data values implied by this immutable calibration."""
        return (
            self._transform(pixel_x, self.x1, self.x2, self.x_scale, coordinate="x"),
            self._transform(pixel_y, self.y1, self.y2, self.y_scale, coordinate="y"),
        )


class FigureLocatorV1(StrictModel):
    """Exact page, panel, curve, crop, dimensions, and image transform identity."""

    figure_id: str = Field(min_length=1, max_length=256)
    page: int = Field(ge=1, le=100_000)
    panel_id: str = Field(min_length=1, max_length=256)
    curve_id: str = Field(min_length=1, max_length=256)
    image_width: int = Field(ge=1, le=100_000)
    image_height: int = Field(ge=1, le=100_000)
    crop_left: int = Field(ge=0)
    crop_top: int = Field(ge=0)
    crop_width: int = Field(ge=1)
    crop_height: int = Field(ge=1)
    image_transform: Literal["source_page_to_crop_pixels_v1"]

    @model_validator(mode="after")
    def crop_is_inside_image(self) -> "FigureLocatorV1":
        if self.crop_left + self.crop_width > self.image_width or self.crop_top + self.crop_height > self.image_height:
            raise ValueError("figure crop must lie within recorded image dimensions")
        return self

    def contains_pixel(self, pixel_x: float, pixel_y: float) -> bool:
        return (
            self.crop_left <= pixel_x <= self.crop_left + self.crop_width
            and self.crop_top <= pixel_y <= self.crop_top + self.crop_height
        )


class DigitizedClickV1(StrictModel):
    """A raw click and its tool-produced data coordinates for one curve point."""

    point_id: str = Field(min_length=1, max_length=256)
    pixel_x: float
    pixel_y: float
    x: float
    y: float

    @field_validator("pixel_x", "pixel_y", "x", "y")
    @classmethod
    def finite_click_values(cls, value: float, info: Any) -> float:
        return _finite(value, name=info.field_name)


class DigitizationExtractionPassV1(StrictModel):
    """One independently attributed WebPlotDigitizer project/export observation."""

    pass_id: str = Field(min_length=1, max_length=256)
    operator_label: str = Field(min_length=1, max_length=256)
    extracted_at: str = Field(min_length=1, max_length=64)
    project_snapshot: ByteSnapshotV1
    export_snapshot: ByteSnapshotV1
    clicks: tuple[DigitizedClickV1, ...] = Field(min_length=1, max_length=10_000)

    @field_validator("clicks", mode="before")
    @classmethod
    def tuple_clicks(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @field_validator("extracted_at")
    @classmethod
    def timezone_timestamp(cls, value: str) -> str:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("extraction timestamp must be ISO-8601") from error
        if parsed.tzinfo is None:
            raise ValueError("extraction timestamp must include a timezone")
        return value

    @model_validator(mode="after")
    def unique_points(self) -> "DigitizationExtractionPassV1":
        ids = tuple(click.point_id for click in self.clicks)
        if len(set(ids)) != len(ids):
            raise ValueError("an extraction pass cannot contain duplicate point IDs")
        return self


class FrozenDigitizationIntervalV1(StrictModel):
    """The exact min/max interval and repeated-pass spread frozen before simulation."""

    point_id: str = Field(min_length=1, max_length=256)
    x_lower: float
    x_upper: float
    y_lower: float
    y_upper: float
    x_spread: float = Field(ge=0.0)
    y_spread: float = Field(ge=0.0)

    @field_validator("x_lower", "x_upper", "y_lower", "y_upper", "x_spread", "y_spread")
    @classmethod
    def finite_interval_values(cls, value: float, info: Any) -> float:
        return _finite(value, name=info.field_name)

    @model_validator(mode="after")
    def ordered_interval(self) -> "FrozenDigitizationIntervalV1":
        if self.x_lower > self.x_upper or self.y_lower > self.y_upper:
            raise ValueError("digitization interval bounds must be ordered")
        if not math.isclose(self.x_spread, self.x_upper - self.x_lower, rel_tol=1e-12, abs_tol=1e-15):
            raise ValueError("x spread must equal the frozen interval width")
        if not math.isclose(self.y_spread, self.y_upper - self.y_lower, rel_tol=1e-12, abs_tol=1e-15):
            raise ValueError("y spread must equal the frozen interval width")
        return self


class DigitizationTargetReceiptV1(StrictModel):
    """A reconstructable publication figure target with independent extractions."""

    schema_name: Literal["campaign_digitization_target_v1"] = Field(alias="schema", serialization_alias="schema")
    target_id: str = Field(min_length=1, max_length=256)
    source: SourceIdentityV1
    source_snapshot: ByteSnapshotV1
    image_snapshot: ByteSnapshotV1
    figure: FigureLocatorV1
    tool_name: str = Field(min_length=1, max_length=256)
    tool_version: str = Field(min_length=1, max_length=256)
    calibration: XYCalibrationV1
    passes: tuple[DigitizationExtractionPassV1, ...] = Field(min_length=2, max_length=100)
    intervals: tuple[FrozenDigitizationIntervalV1, ...] = Field(min_length=1, max_length=10_000)
    source_denominator: SourceDenominatorV1

    @field_validator("passes", "intervals", mode="before")
    @classmethod
    def tuple_records(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def reconstructable_repeated_extraction(self) -> "DigitizationTargetReceiptV1":
        pass_ids = tuple(item.pass_id for item in self.passes)
        operators = tuple(item.operator_label for item in self.passes)
        if len(set(pass_ids)) != len(pass_ids) or len(set(operators)) != len(operators):
            raise ValueError("publication target passes must have distinct pass and operator identities")
        expected_ids = tuple(click.point_id for click in self.passes[0].clicks)
        if any(tuple(click.point_id for click in item.clicks) != expected_ids for item in self.passes[1:]):
            raise ValueError("every extraction pass must retain the same ordered point IDs")
        for extraction in self.passes:
            for click in extraction.clicks:
                if not self.figure.contains_pixel(click.pixel_x, click.pixel_y):
                    raise ValueError("digitization click must lie inside the retained crop")
                expected_x, expected_y = self.calibration.transformed_values(click.pixel_x, click.pixel_y)
                if not math.isclose(click.x, expected_x, rel_tol=1e-12, abs_tol=1e-15) or not math.isclose(click.y, expected_y, rel_tol=1e-12, abs_tol=1e-15):
                    raise ValueError("digitized values must match the frozen calibration transform")
        interval_by_id = {item.point_id: item for item in self.intervals}
        if len(interval_by_id) != len(self.intervals) or set(interval_by_id) != set(expected_ids):
            raise ValueError("frozen intervals must cover each extracted point exactly once")
        for point_id, interval in interval_by_id.items():
            clicks = [next(click for click in extraction.clicks if click.point_id == point_id) for extraction in self.passes]
            x_values = [click.x for click in clicks]
            y_values = [click.y for click in clicks]
            expected = (min(x_values), max(x_values), min(y_values), max(y_values))
            observed = (interval.x_lower, interval.x_upper, interval.y_lower, interval.y_upper)
            if any(not math.isclose(actual, frozen, rel_tol=1e-12, abs_tol=1e-15) for actual, frozen in zip(observed, expected, strict=True)):
                raise ValueError("frozen interval must exactly cover repeated extraction extrema")
        return self

    def digest(self) -> str:
        return _receipt_digest("bp-registry-campaign-digitization-target-v1", self)
