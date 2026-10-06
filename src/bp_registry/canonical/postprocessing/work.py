"""Typed SI method-work leaves, distinct from the outer fallback call."""

from __future__ import annotations

from dataclasses import dataclass

from ..budgets import WorkVector


@dataclass(frozen=True, slots=True)
class SiTrialWork:
    """The complete, versioned work reserved by one SI trial boundary."""

    trial_index: int
    stage: str
    vector: WorkVector

    def __post_init__(self) -> None:
        if type(self.trial_index) is not int or self.trial_index < 0:
            raise ValueError("SI trial work needs a nonnegative trial index")
        if self.stage not in {"ranking", "reduction", "rerun", "solve", "lift", "original_check"}:
            raise ValueError("SI work stage is not declared")
        if not isinstance(self.vector, WorkVector):
            raise ValueError("SI work requires a typed work vector")

    def as_evidence(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "method": "stabilizer_inactivation",
            "trial_index": self.trial_index,
            "stage": self.stage,
            "work_vector": self.vector.as_evidence(structural_event_version=4),
        }
