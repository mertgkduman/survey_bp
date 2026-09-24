"""Hsu et al. non-disjoint group-shuffled BP construction for binary CSS adaptation.

The source's explicit size-two, overlap-one example is the only supported
configuration.  A sampled check order is converted to overlapping adjacent
pairs; no learned policy or external parameter artifact is involved.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import numbers

import numpy as np


SOURCE_ID = "hsu-ndgsbp-2012-v1"
SOURCE_URI = "https://arxiv.org/html/1202.1060"


@dataclass(frozen=True, slots=True)
class GroupTraversal:
    """A complete source-iteration order and its overlapping check groups."""

    iteration: int
    order: tuple[int, ...]
    groups: tuple[tuple[int, int], ...]
    derived_identity: str

    def evidence(self) -> dict[str, object]:
        return {
            "source_id": SOURCE_ID,
            "source_uri": SOURCE_URI,
            "source_configuration": "group_size=2;overlap=1",
            "iteration": self.iteration,
            "order": self.order,
            "groups": self.groups,
            "derived_identity": self.derived_identity,
            "membership_multiplicity": tuple(
                (check, sum(check in group for group in self.groups))
                for check in self.order
            ),
        }


def groups_from_order(order: tuple[int, ...] | list[int], *, check_count: int) -> tuple[tuple[int, int], ...]:
    """Realize the paper's (c1,c2),(c2,c3),... worked construction."""
    if isinstance(check_count, bool) or not isinstance(check_count, numbers.Integral) or check_count < 2:
        raise ValueError("Hsu groups require at least two checks")
    if not isinstance(order, (tuple, list)) or len(order) != check_count:
        raise ValueError("check order must contain every check exactly once")
    if any(isinstance(check, (bool, np.bool_)) or not isinstance(check, numbers.Integral) for check in order):
        raise ValueError("check order must use exact integer IDs")
    normalized = tuple(int(check) for check in order)
    if set(normalized) != set(range(int(check_count))):
        raise ValueError("check order must be a permutation of canonical check IDs")
    return tuple((normalized[index], normalized[index + 1]) for index in range(len(normalized) - 1))


@dataclass(frozen=True, slots=True)
class HsuGroupPlan:
    """Purpose-separated schedule RNG, independent of physical-error sampling."""

    check_count: int
    root_identity: str

    def __post_init__(self) -> None:
        if isinstance(self.check_count, bool) or not isinstance(self.check_count, numbers.Integral) or self.check_count < 2:
            raise ValueError("Hsu groups require at least two checks")
        if not isinstance(self.root_identity, str) or len(self.root_identity) != 64 or any(ch not in "0123456789abcdef" for ch in self.root_identity):
            raise ValueError("schedule root_identity must be a lowercase SHA-256 hex digest")

    def traversal(self, *, attempt_identity: str, iteration: int) -> GroupTraversal:
        if not isinstance(attempt_identity, str) or not attempt_identity:
            raise ValueError("attempt_identity must be a nonempty string")
        if isinstance(iteration, bool) or not isinstance(iteration, numbers.Integral) or iteration < 0:
            raise ValueError("source iteration must be a nonnegative integer")
        material = {
            "purpose": "hsu_group_order",
            "source_id": SOURCE_ID,
            "root_identity": self.root_identity,
            "attempt_identity": attempt_identity,
            "iteration": int(iteration),
            "check_count": int(self.check_count),
        }
        identity = sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        generator = np.random.Generator(np.random.PCG64(int(identity[:32], 16)))
        order = tuple(int(check) for check in generator.permutation(int(self.check_count)))
        return GroupTraversal(int(iteration), order, groups_from_order(order, check_count=self.check_count), identity)
