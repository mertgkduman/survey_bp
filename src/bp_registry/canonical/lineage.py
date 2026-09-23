"""Stable, typed append-only lineage for canonical decoder control flow.

The graph identifies scientific entities from logical parents and canonical
content. It never uses a journal sequence number, completion order, wall time,
or process-local identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from typing import Literal, Mapping

import numpy as np


LineageKind = Literal[
    "original", "working", "transformation", "member", "leg", "branch",
    "attempt", "candidate", "lift", "validation", "selection", "evaluation",
]
LineageRelation = Literal[
    "identity", "transform", "member", "leg", "branch", "attempt",
    "candidate", "lift", "validate", "select", "evaluate",
]

_PARENTS: dict[str, frozenset[str]] = {
    "working": frozenset({"original", "transformation"}),
    "transformation": frozenset({"original", "working"}),
    "member": frozenset({"working", "attempt"}),
    "leg": frozenset({"member", "leg"}),
    "branch": frozenset({"member", "leg", "branch", "attempt"}),
    "attempt": frozenset({"original", "working", "member", "leg", "branch"}),
    "candidate": frozenset({"working", "attempt", "branch", "leg"}),
    "lift": frozenset({"candidate"}),
    "validation": frozenset({"candidate", "lift"}),
    "selection": frozenset({"candidate", "validation"}),
    "evaluation": frozenset({"selection"}),
}


def _canonical(value: object) -> str:
    """Encode finite, JSON-native evidence in one unambiguous form."""

    def normalize(item: object) -> object:
        if isinstance(item, float) and not math.isfinite(item):
            raise ValueError("lineage content must contain finite values")
        if isinstance(item, np.generic):
            return normalize(item.item())
        if isinstance(item, np.ndarray):
            return [normalize(value) for value in item.tolist()]
        if isinstance(item, Mapping):
            return {str(key): normalize(value) for key, value in item.items()}
        if isinstance(item, (tuple, list)):
            return [normalize(value) for value in item]
        if item is None or isinstance(item, (str, bool, int, float)):
            return item
        raise ValueError(f"lineage content is not canonical JSON: {type(item).__name__}")

    return json.dumps(normalize(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


@dataclass(frozen=True, order=True)
class LineageId:
    kind: LineageKind
    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.startswith(f"{self.kind}-"):
            raise ValueError("lineage values must be nonempty type-prefixed IDs")


@dataclass(frozen=True)
class LineageEdge:
    relation: LineageRelation
    parent: LineageId
    child: LineageId


@dataclass(frozen=True)
class LineageNode:
    """Immutable node facts; evaluation nodes are post-selection annotations."""

    id: LineageId
    content_sha256: str
    parents: tuple[LineageId, ...] = ()
    relation: LineageRelation | None = None

    @property
    def kind(self) -> LineageKind:
        return self.id.kind


def stable_lineage_id(kind: LineageKind, payload: object) -> LineageId:
    """Content identity intentionally excludes arrival order and elapsed time."""
    return LineageId(kind, f"{kind}-{sha256(_canonical(payload).encode('utf-8')).hexdigest()[:20]}")


class LineageGraph:
    """In-memory append-only graph with typed adjacency and conflict rejection."""

    def __init__(self) -> None:
        self._nodes: dict[LineageId, LineageNode] = {}
        self._order: list[LineageId] = []
        self._edges: list[LineageEdge] = []

    def append_node(
        self,
        kind: LineageKind,
        content: object,
        *,
        parent: LineageId | LineageNode | None = None,
        relation: LineageRelation | None = None,
        node_id: LineageId | None = None,
    ) -> LineageNode:
        if node_id is not None and node_id in self._nodes:
            raise ValueError("conflicting immutable lineage node")
        if kind == "original":
            if parent is not None or relation is not None:
                raise ValueError("original lineage nodes must not have parents")
            parents: tuple[LineageId, ...] = ()
        else:
            if parent is None or relation is None:
                raise ValueError(f"{kind} lineage nodes require a typed parent edge")
            parent_id = parent.id if isinstance(parent, LineageNode) else parent
            if parent_id not in self._nodes:
                raise ValueError("unknown parent lineage node")
            if parent_id.kind not in _PARENTS[kind]:
                raise ValueError(f"{relation} edge from {parent_id.kind} to {kind} is not allowed")
            parents = (parent_id,)
        semantic = {"parents": [item.value for item in parents], "relation": relation, "content": json.loads(_canonical(content))}
        derived = stable_lineage_id(kind, semantic)
        if node_id is not None and node_id != derived:
            raise ValueError("provided lineage ID does not match semantic ancestry and content")
        node = LineageNode(derived, sha256(_canonical(content).encode("utf-8")).hexdigest(), parents, relation)
        existing = self._nodes.get(derived)
        if existing is not None:
            if existing != node:
                raise ValueError("conflicting immutable lineage node")
            return existing
        self._nodes[derived] = node
        self._order.append(derived)
        if parents:
            self._edges.append(LineageEdge(relation, parents[0], derived))  # type: ignore[arg-type]
        return node

    def nodes(self) -> tuple[LineageNode, ...]:
        return tuple(self._nodes[item] for item in self._order)

    def edges(self) -> tuple[LineageEdge, ...]:
        return tuple(self._edges)

    def parents(self, identifier: LineageId) -> tuple[LineageId, ...]:
        try:
            return self._nodes[identifier].parents
        except KeyError as error:
            raise ValueError("unknown lineage node") from error

    def append_evaluation(self, selection: "SelectionRecord", annotation: Mapping[str, object]) -> LineageNode:
        """Append truth-aware evidence only after immutable selection has frozen."""
        if selection.lineage_id not in self._nodes:
            raise ValueError("selection must be recorded before evaluation")
        return self.append_node("evaluation", dict(annotation), parent=selection.lineage_id, relation="evaluate")


def _payload_tuple(payload: np.ndarray | tuple[int, ...] | list[int]) -> tuple[int, ...]:
    values = tuple(int(value) for value in np.asarray(payload).tolist())
    if not values or any(value not in (0, 1) for value in values):
        raise ValueError("candidate payload must be a nonempty binary vector")
    return values


@dataclass(frozen=True)
class CandidateRecord:
    """Candidate evidence retained even when a full rejected payload is dropped."""

    lineage_id: LineageId
    parent_id: LineageId
    payload_sha256: str
    score: float | int | None
    validations: tuple[str, ...]
    reason: str
    local_ordinal: int
    retained_payload: tuple[int, ...] | None
    _staged_payload: tuple[int, ...] | None

    @classmethod
    def create(
        cls,
        *,
        graph: LineageGraph,
        parent: LineageId,
        payload: np.ndarray | tuple[int, ...] | list[int],
        score: float | int | None,
        validations: tuple[str, ...] | list[str],
        reason: str,
        local_ordinal: int,
        retain_full: bool = False,
    ) -> "CandidateRecord":
        bits = _payload_tuple(payload)
        if type(local_ordinal) is not int or local_ordinal < 0:
            raise ValueError("candidate local ordinal must be nonnegative")
        if score is not None and (not isinstance(score, (int, float)) or not math.isfinite(score)):
            raise ValueError("candidate score must be finite or absent")
        if not reason or any(not isinstance(item, str) or not item for item in validations):
            raise ValueError("candidate reasons and validations must be nonempty strings")
        digest = sha256(_canonical(bits).encode("utf-8")).hexdigest()
        node = graph.append_node(
            "candidate",
            {"payload_sha256": digest, "score": score, "validations": list(validations), "reason": reason, "local_ordinal": local_ordinal},
            parent=parent,
            relation="candidate",
        )
        return cls(node.id, parent, digest, score, tuple(validations), reason, local_ordinal, bits if retain_full else None, bits)


@dataclass(frozen=True)
class SelectionRecord:
    """Frozen decoder-visible choice and complete ordered candidate evidence."""

    lineage_id: LineageId
    selected_id: LineageId
    candidates: tuple[CandidateRecord, ...]

    @classmethod
    def freeze(cls, *, graph: LineageGraph, candidates: tuple[CandidateRecord, ...], selected_id: LineageId) -> "SelectionRecord":
        if not candidates or selected_id not in {item.lineage_id for item in candidates}:
            raise ValueError("frozen selection must name one known candidate")
        if tuple(sorted(candidates, key=lambda item: (item.local_ordinal, item.lineage_id.value))) != candidates:
            raise ValueError("candidate selection must use declared stable order")
        selected = next(item for item in candidates if item.lineage_id == selected_id)
        # Retention is a post-candidate storage decision; it never changes identity or visible evidence.
        object.__setattr__(selected, "retained_payload", selected._staged_payload)
        for item in candidates:
            object.__setattr__(item, "_staged_payload", None)
        node = graph.append_node("selection", {"selected_id": selected_id.value, "candidate_ids": [item.lineage_id.value for item in candidates]}, parent=selected_id, relation="select")
        return cls(node.id, selected_id, candidates)

    def annotate_evaluation(self, _annotation: Mapping[str, object]) -> None:
        raise ValueError("frozen selection cannot be mutated; append an evaluation annotation to the graph")
