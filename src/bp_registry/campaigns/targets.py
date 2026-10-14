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


class NativeMetricV1(StrictModel):
    """One native measurement with explicit observed or unavailable meaning."""

    name: Literal["decoder_work", "runtime_seconds", "counters"]
    status: Literal["observed", "unavailable"]
    value: float | None = Field(default=None, ge=0.0)
    reason: str | None = Field(default=None, min_length=1, max_length=1_024)

    @field_validator("value")
    @classmethod
    def finite_value(cls, value: float | None) -> float | None:
        if value is not None:
            return _finite(value, name="native measurement")
        return value

    @model_validator(mode="after")
    def explicit_measurement_status(self) -> "NativeMetricV1":
        if self.status == "observed":
            if self.value is None or self.reason is not None:
                raise ValueError("observed native measurement needs a value and no unavailable reason")
        elif self.value is not None or self.reason is None:
            raise ValueError("unavailable native measurement needs a reason and no numeric default")
        return self


class NativeReferenceAssessmentV1(StrictModel):
    """Per-target native-reference observation that never treats absence as zero."""

    schema_name: Literal["campaign_native_reference_assessment_v1"] = Field(alias="schema", serialization_alias="schema")
    target_id: str = Field(min_length=1, max_length=256)
    status: Literal[
        "identity_unverified", "source_obtained_not_executable", "executed", "execution_discrepant",
    ]
    reasons: tuple[str, ...] = Field(default=(), max_length=_MAX_QUALIFICATION_BLOCKERS)
    source_snapshot: ByteSnapshotV1 | None = None
    repository_uri: str | None = Field(default=None, min_length=1, max_length=2_048)
    repository_revision: str | None = Field(default=None, min_length=1, max_length=512)
    environment_snapshot: ByteSnapshotV1 | None = None
    settings_snapshot: ByteSnapshotV1 | None = None
    command_snapshot: ByteSnapshotV1 | None = None
    output_snapshot: ByteSnapshotV1 | None = None
    metrics: tuple[NativeMetricV1, ...] = Field(min_length=3, max_length=3)
    discrepancy_evidence: tuple[str, ...] = Field(default=(), max_length=_MAX_QUALIFICATION_BLOCKERS)

    @field_validator("reasons", "discrepancy_evidence", mode="before")
    @classmethod
    def tuple_strings(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @field_validator("reasons", "discrepancy_evidence")
    @classmethod
    def bounded_strings(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not item or len(item) > 1_024 for item in value) or len(set(value)) != len(value):
            raise ValueError("native assessment reasons must be unique bounded nonempty strings")
        return value

    @field_validator("repository_uri")
    @classmethod
    def https_repository_uri(cls, value: str | None) -> str | None:
        if value is not None and not value.startswith("https://"):
            raise ValueError("native repository URI must use HTTPS")
        return value

    @field_validator("metrics", mode="before")
    @classmethod
    def tuple_metrics(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def status_specific_evidence(self) -> "NativeReferenceAssessmentV1":
        expected_names = ("decoder_work", "runtime_seconds", "counters")
        if tuple(metric.name for metric in self.metrics) != expected_names:
            raise ValueError("native metrics must retain the declared work, runtime, counter order")
        execution_fields = (
            self.repository_uri, self.repository_revision, self.environment_snapshot,
            self.settings_snapshot, self.command_snapshot, self.output_snapshot,
        )
        all_unavailable = all(metric.status == "unavailable" for metric in self.metrics)
        if self.status == "identity_unverified":
            if not self.reasons or self.source_snapshot is not None or any(field is not None for field in execution_fields):
                raise ValueError("unverified native identity needs reasons and no inferred execution evidence")
            if not all_unavailable or self.discrepancy_evidence:
                raise ValueError("unverified native identity requires unavailable metrics only")
        elif self.status == "source_obtained_not_executable":
            if not self.reasons or self.source_snapshot is None or any(field is not None for field in execution_fields):
                raise ValueError("obtained but non-executable source needs snapshot, reasons, and no execution evidence")
            if not all_unavailable or self.discrepancy_evidence:
                raise ValueError("non-executable native source requires unavailable metrics only")
        else:
            if self.source_snapshot is None or any(field is None for field in execution_fields):
                raise ValueError("executed native receipt needs source, repository, environment, settings, command, and output evidence")
            if self.reasons:
                raise ValueError("executed native receipt cannot use unavailable-state reasons")
            if self.status == "executed" and self.discrepancy_evidence:
                raise ValueError("executed native receipt cannot carry discrepancy evidence")
            if self.status == "execution_discrepant" and not self.discrepancy_evidence:
                raise ValueError("discrepant native receipt needs explicit discrepancy evidence")
        snapshots = tuple(
            snapshot for snapshot in (
                self.source_snapshot, self.environment_snapshot, self.settings_snapshot,
                self.command_snapshot, self.output_snapshot,
            ) if snapshot is not None
        )
        paths = tuple(snapshot.relative_path for snapshot in snapshots)
        if len(paths) != len(set(paths)):
            raise ValueError("native evidence snapshots must have distinct confined paths")
        return self

    @property
    def executed_successfully(self) -> bool:
        return self.status == "executed"

    def digest(self) -> str:
        return _receipt_digest("bp-registry-campaign-native-reference-assessment-v1", self)


class SourceExperimentQualificationReceiptV1(StrictModel):
    """A digest-bound eligibility event; later evidence creates a new receipt."""

    schema_name: Literal["campaign_source_experiment_qualification_v1"] = Field(alias="schema", serialization_alias="schema")
    source_experiment: SourceExperimentIdentityV1
    target_receipt_sha256: str = Field(pattern=_SHA256)
    native_assessment: NativeReferenceAssessmentV1
    qualification_blockers: tuple[str, ...] = Field(default=(), max_length=_MAX_QUALIFICATION_BLOCKERS)
    faithful_eligible: bool
    prior_qualification_receipt_sha256: str | None = Field(default=None, pattern=_SHA256)

    @field_validator("qualification_blockers", mode="before")
    @classmethod
    def tuple_blockers(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @field_validator("qualification_blockers")
    @classmethod
    def valid_blockers(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(not blocker or len(blocker) > 1_024 for blocker in value) or len(set(value)) != len(value):
            raise ValueError("qualification receipt blockers must be unique bounded nonempty strings")
        return value

    @model_validator(mode="after")
    def source_faithful_gate(self) -> "SourceExperimentQualificationReceiptV1":
        if self.native_assessment.target_id != self.source_experiment.target_id:
            raise ValueError("native assessment must bind the same target as the source experiment")
        expected_eligibility = (
            self.source_experiment.complete_for_faithful_assessment
            and self.native_assessment.executed_successfully
            and not self.qualification_blockers
        )
        if self.faithful_eligible != expected_eligibility:
            raise ValueError("faithful eligibility must exactly match complete source and native evidence")
        return self

    def digest(self) -> str:
        return _receipt_digest("bp-registry-campaign-source-experiment-qualification-v1", self)


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


class QuaternaryDecoderSettingsV1(StrictModel):
    """Paper-bound BP4/aSCED settings for one Figure 2 curve member."""

    baseline: Literal["BP4", "OBP4"]
    variant: Literal["BP4-aSCED", "OBP4-aSCED"]
    iterations: int = Field(ge=1, le=1_000_000)
    K: int = Field(ge=1, le=1_000_000)
    Delta: int = Field(ge=1, le=1_000_000)
    L: int = Field(ge=1, le=1_000_000)
    p0: float | None = Field(default=None, gt=0.0, lt=1.0)

    @model_validator(mode="after")
    def paper_curve_configuration(self) -> "QuaternaryDecoderSettingsV1":
        if self.baseline == "BP4":
            if self.variant != "BP4-aSCED" or self.p0 is not None:
                raise ValueError("BP4 Figure 2 members require BP4-aSCED and no p0")
        elif self.variant != "OBP4-aSCED" or self.p0 is None:
            raise ValueError("OBP4 Figure 2 members require OBP4-aSCED and p0")
        return self


class QuaternaryStoppingRuleV1(StrictModel):
    """A source stopping rule that cannot silently become a local default."""

    minimum_logical_errors: int = Field(ge=1)
    maximum_trials: int = Field(ge=1)

    @model_validator(mode="after")
    def feasible_rule(self) -> "QuaternaryStoppingRuleV1":
        if self.minimum_logical_errors > self.maximum_trials:
            raise ValueError("stopping logical-error target cannot exceed maximum trials")
        return self


class QuaternaryExtractionEvidenceV1(StrictModel):
    """A reviewed digitization or an explicit, non-numeric blocked state."""

    status: Literal["reviewed", "blocked_metadata"]
    digitization: DigitizationTargetReceiptV1 | None = None
    selected_point: FrozenDigitizationIntervalV1 | None = None
    acceptance_tolerance: float | None = Field(default=None, gt=0.0)
    reviewer: str | None = Field(default=None, min_length=1, max_length=256)
    blockers: tuple[str, ...] = Field(default=(), max_length=_MAX_QUALIFICATION_BLOCKERS)

    @field_validator("blockers", mode="before")
    @classmethod
    def tuple_blockers(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def reviewed_or_explicitly_blocked(self) -> "QuaternaryExtractionEvidenceV1":
        if len(set(self.blockers)) != len(self.blockers) or any(not item for item in self.blockers):
            raise ValueError("extraction blockers must be unique nonempty strings")
        if self.status == "reviewed":
            if (self.digitization is None or self.selected_point is None
                    or self.acceptance_tolerance is None or self.reviewer is None or self.blockers):
                raise ValueError("reviewed extraction needs digitization, point, tolerance, and reviewer only")
        elif (self.digitization is not None or self.selected_point is not None
              or self.acceptance_tolerance is not None or self.reviewer is not None or not self.blockers):
            raise ValueError("blocked extraction needs blockers and no inferred coordinates or tolerance")
        return self


class QuaternarySourceTargetMemberV1(StrictModel):
    """One separately assessed ordinary or overcomplete aSCED curve member."""

    member_id: str = Field(min_length=1, max_length=256)
    target_slot: str = Field(min_length=1, max_length=256)
    evidence_kind: Literal["paper_figure"]
    channel: Literal["depolarizing"]
    decoder: QuaternaryDecoderSettingsV1
    stopping: QuaternaryStoppingRuleV1
    source_denominator: SourceDenominatorV1
    extraction: QuaternaryExtractionEvidenceV1
    source_experiment: SourceExperimentIdentityV1 | None = None
    eligibility: Literal["eligible", "blocked_metadata"]
    admitted_shots: int = Field(ge=0)
    blockers: tuple[str, ...] = Field(default=(), max_length=_MAX_QUALIFICATION_BLOCKERS)

    @field_validator("blockers", mode="before")
    @classmethod
    def tuple_blockers(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def immutable_admission_gate(self) -> "QuaternarySourceTargetMemberV1":
        if len(set(self.blockers)) != len(self.blockers) or any(not item for item in self.blockers):
            raise ValueError("member blockers must be unique nonempty strings")
        complete = (
            self.extraction.status == "reviewed"
            and self.source_experiment is not None
            and self.source_experiment.complete_for_faithful_assessment
            and not self.blockers
        )
        if self.eligibility == "eligible":
            if not complete or self.admitted_shots != 0:
                raise ValueError("eligible target must be complete and freeze zero shots before execution")
        elif self.admitted_shots != 0 or not self.blockers or self.extraction.status != "blocked_metadata":
            raise ValueError("blocked target must retain blockers and admit zero shots")
        return self


class QuaternarySourceTargetV1(StrictModel):
    """Frozen source-only aSCED Figure 2 GB46 target contract."""

    schema_name: Literal["campaign_quaternary_source_target_v1"] = Field(alias="schema", serialization_alias="schema")
    source_panel: dict[Literal["figure", "code"], str]
    source_snapshot_sha256: str = Field(pattern=_SHA256)
    members: tuple[QuaternarySourceTargetMemberV1, ...] = Field(min_length=1, max_length=2)
    target_receipt_sha256: str | None = Field(default=None, pattern=_SHA256)

    @field_validator("members", mode="before")
    @classmethod
    def tuple_members(cls, value: Any) -> Any:
        return tuple(value) if isinstance(value, list) else value

    @model_validator(mode="after")
    def exact_figure_two_members(self) -> "QuaternarySourceTargetV1":
        if self.source_panel != {"figure": "Figure 2", "code": "GB46"}:
            raise ValueError("the first quaternary source target must be exactly aSCED Figure 2 GB46")
        expected_ids = {"asced-figure2-gb46-ordinary", "asced-figure2-gb46-overcomplete"}
        actual_ids = {member.member_id for member in self.members}
        if not actual_ids.issubset(expected_ids) or "asced-figure2-gb46-ordinary" not in actual_ids:
            raise ValueError("Figure 2 target must contain its exact ordinary member and no unrelated curves")
        ordinary = next(member for member in self.members if member.member_id.endswith("ordinary"))
        if (ordinary.decoder.baseline, ordinary.decoder.iterations, ordinary.decoder.K, ordinary.decoder.Delta, ordinary.decoder.L) != ("BP4", 25, 16, 2, 4):
            raise ValueError("ordinary Figure 2 settings must freeze BP4 25 and K=16, Delta=2, L=4")
        if "asced-figure2-gb46-overcomplete" in actual_ids:
            overcomplete = next(member for member in self.members if member.member_id.endswith("overcomplete"))
            if (overcomplete.decoder.baseline, overcomplete.decoder.iterations, overcomplete.decoder.p0, overcomplete.decoder.K, overcomplete.decoder.Delta, overcomplete.decoder.L) != ("OBP4", 12, 0.3, 16, 2, 4):
                raise ValueError("overcomplete Figure 2 settings must freeze OBP4 12, p0=0.3 and K=16, Delta=2, L=4")
        expected_stopping = QuaternaryStoppingRuleV1(minimum_logical_errors=400, maximum_trials=1_000_000)
        if any(member.stopping != expected_stopping for member in self.members):
            raise ValueError("all Figure 2 members must retain the paper stopping rule")
        if self.target_receipt_sha256 is not None and self.target_receipt_sha256 != self.digest():
            raise ValueError("frozen target receipt digest does not match its immutable content")
        return self

    def digest(self) -> str:
        payload = self.model_dump(mode="json", by_alias=True, exclude={"target_receipt_sha256"})
        return sha256(_canonical_json_bytes(payload)).hexdigest()
