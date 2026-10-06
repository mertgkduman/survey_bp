"""Typed SI method-work leaves, distinct from the outer fallback call."""

from __future__ import annotations

from dataclasses import dataclass

from ..budgets import WorkVector


@dataclass(frozen=True, slots=True)
class OtfWork:
    """Versioned method work for one ordered-Tanner-forest fallback call."""

    stage: str
    vector: WorkVector
    column: int | None = None
    leaf_id: str | None = None

    def __post_init__(self) -> None:
        if self.stage not in {"sort", "union_find_probe", "accepted_column", "forest_bp", "lift", "original_check"}:
            raise ValueError("OTF work stage is not declared")
        if not isinstance(self.vector, WorkVector):
            raise ValueError("OTF work requires a typed work vector")
        if self.column is not None and (type(self.column) is not int or self.column < 0):
            raise ValueError("OTF work column must be a nonnegative integer when present")
        if self.leaf_id is not None and (not isinstance(self.leaf_id, str) or not self.leaf_id):
            raise ValueError("OTF work leaf IDs must be nonempty when present")

    def as_evidence(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "method": "ordered_tanner_forest",
            "stage": self.stage,
            "column": self.column,
            "leaf_id": self.leaf_id,
            "work_vector": self.vector.as_evidence(structural_event_version=4),
        }


@dataclass(frozen=True, slots=True)
class SiTrialWork:
    """The complete, versioned work reserved by one SI trial boundary."""

    trial_index: int
    stage: str
    vector: WorkVector
    leaf_id: str | None = None

    def __post_init__(self) -> None:
        if type(self.trial_index) is not int or self.trial_index < 0:
            raise ValueError("SI trial work needs a nonnegative trial index")
        if self.stage not in {"ranking", "reduction", "rerun", "solve", "lift", "original_check"}:
            raise ValueError("SI work stage is not declared")
        if not isinstance(self.vector, WorkVector):
            raise ValueError("SI work requires a typed work vector")
        if self.leaf_id is not None and (not isinstance(self.leaf_id, str) or not self.leaf_id):
            raise ValueError("SI work leaf IDs must be nonempty when present")

    def as_evidence(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "method": "stabilizer_inactivation",
            "trial_index": self.trial_index,
            "stage": self.stage,
            "leaf_id": self.leaf_id,
            "work_vector": self.vector.as_evidence(structural_event_version=4),
        }
