"""Canonical edge ordering and double-buffered flooding semantics."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import numbers
from typing import Protocol

import numpy as np

from .numerics import NumericalProfile, REFERENCE_CPU_F64, finite_saturate


Edge = tuple[int, int]


@dataclass(frozen=True, slots=True)
class EdgeTable:
    """The canonical check-major, variable-minor edge identity for one graph."""

    check_count: int
    variable_count: int
    edges: tuple[Edge, ...]

    @classmethod
    def from_edges(cls, check_count: int, variable_count: int, edges: list[Edge] | tuple[Edge, ...]) -> "EdgeTable":
        if (
            isinstance(check_count, (bool, np.bool_))
            or isinstance(variable_count, (bool, np.bool_))
            or not isinstance(check_count, numbers.Integral)
            or not isinstance(variable_count, numbers.Integral)
            or check_count < 0
            or variable_count < 0
        ):
            raise ValueError("check and variable counts must be nonnegative integers")
        canonical: list[Edge] = []
        for edge in edges:
            if not isinstance(edge, tuple) or len(edge) != 2 or any(
                isinstance(value, (bool, np.bool_)) or not isinstance(value, numbers.Integral) for value in edge
            ):
                raise ValueError("each edge must be a pair of integer check and variable IDs")
            check, variable = (int(edge[0]), int(edge[1]))
            if not 0 <= check < check_count or not 0 <= variable < variable_count:
                raise ValueError("edge is outside declared graph bounds")
            canonical.append((check, variable))
        if len(set(canonical)) != len(canonical):
            raise ValueError("duplicate edges are not a valid canonical graph encoding")
        return cls(int(check_count), int(variable_count), tuple(sorted(canonical)))

    @classmethod
    def from_check_matrix(cls, check_matrix: np.ndarray) -> "EdgeTable":
        matrix = np.asarray(check_matrix)
        if matrix.ndim != 2 or not np.issubdtype(matrix.dtype, np.integer) or np.any((matrix != 0) & (matrix != 1)):
            raise ValueError("check_matrix must be a binary integer matrix")
        edges = [(check, int(variable)) for check in range(matrix.shape[0]) for variable in np.flatnonzero(matrix[check])]
        return cls.from_edges(matrix.shape[0], matrix.shape[1], edges)

    @property
    def edge_count(self) -> int:
        return len(self.edges)

    @property
    def graph_sha256(self) -> str:
        """Stable graph identity for assignments indexed by canonical EdgeTable positions."""
        payload = {"check_count": self.check_count, "variable_count": self.variable_count, "edges": self.edges}
        return sha256(json.dumps(payload, separators=(",", ":")).encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class FloodingWork:
    """Proposed leaf work for one sweep; Plan 04 owns budget reservation and commit."""

    check_to_variable: int
    variable_to_check: int
    belief_assembly: int
    candidate_checks: int

    def as_evidence(self) -> dict[str, int]:
        return {
            "check_to_variable": self.check_to_variable,
            "variable_to_check": self.variable_to_check,
            "belief_assembly": self.belief_assembly,
            "candidate_checks": self.candidate_checks,
        }


@dataclass(frozen=True, slots=True)
class FloodingSweep:
    """One complete sweep whose old and new directional buffers never alias."""

    edge_count: int
    old_v2c: np.ndarray
    check_to_variable: np.ndarray
    new_v2c: np.ndarray
    beliefs: np.ndarray
    candidate: np.ndarray
    proposed_work: FloodingWork


class _FloodingKernel(Protocol):
    def prior(self, error_rate: float) -> float: ...

    def check_message(self, incoming: np.ndarray, syndrome: int, *, check_index: int = 0, edge_index: int = 0, source_iteration: int = 0) -> float: ...

    def assemble_beliefs(self, variable_count: int, edge_variables: tuple[int, ...], messages: np.ndarray, prior: float) -> np.ndarray: ...

    def variable_message(self, belief: float, check_message: float) -> float: ...

    def candidate_from_beliefs(self, beliefs: np.ndarray) -> np.ndarray: ...


class FloodingSchedule:
    """Within-attempt flooding order: old v2c → complete c2v → complete new v2c."""

    def __init__(self, edge_table: EdgeTable, *, kernel: _FloodingKernel, profile: NumericalProfile = REFERENCE_CPU_F64) -> None:
        self.edge_table = edge_table
        self.kernel = kernel
        self.profile = profile
        self._check_edges = tuple(
            tuple(index for index, (check, _variable) in enumerate(edge_table.edges) if check == current)
            for current in range(edge_table.check_count)
        )
        self._edge_variables = tuple(variable for _check, variable in edge_table.edges)

    def initialize(self, error_rate: float) -> np.ndarray:
        """Create the initial variable-to-check snapshot from the declared prior."""
        return np.full(self.edge_table.edge_count, self.kernel.prior(error_rate), dtype=np.float64)

    def sweep(self, old_v2c: np.ndarray, syndrome: np.ndarray, *, error_rate: float, source_iteration: int = 0) -> FloodingSweep:
        """Build a finite full sweep without mutating the supplied old snapshot."""
        old = finite_saturate(old_v2c, boundary="flooding_old_v2c", profile=self.profile)
        if old.ndim != 1 or old.shape != (self.edge_table.edge_count,):
            raise ValueError("old_v2c must have exactly one value per canonical edge")
        syndrome_bits = np.asarray(syndrome)
        if (
            syndrome_bits.shape != (self.edge_table.check_count,)
            or not np.issubdtype(syndrome_bits.dtype, np.integer)
            or np.any((syndrome_bits != 0) & (syndrome_bits != 1))
        ):
            raise ValueError("syndrome must be a binary integer vector matching the check count")
        old_snapshot = np.array(old, dtype=np.float64, copy=True)
        prior = self.kernel.prior(error_rate)
        c2v = np.empty(self.edge_table.edge_count, dtype=np.float64)
        for check, edge_indices in enumerate(self._check_edges):
            for edge_index in edge_indices:
                incoming = old_snapshot[[other for other in edge_indices if other != edge_index]]
                c2v[edge_index] = self.kernel.check_message(
                    incoming, int(syndrome_bits[check]), check_index=check,
                    edge_index=edge_index, source_iteration=source_iteration,
                )
        c2v = finite_saturate(c2v, boundary="flooding_complete_c2v", profile=self.profile)
        beliefs = self.kernel.assemble_beliefs(self.edge_table.variable_count, self._edge_variables, c2v, prior)
        beliefs = finite_saturate(beliefs, boundary="flooding_belief_assembly", profile=self.profile)
        candidate = self.kernel.candidate_from_beliefs(beliefs)
        new_v2c = np.empty(self.edge_table.edge_count, dtype=np.float64)
        for edge_index, variable in enumerate(self._edge_variables):
            new_v2c[edge_index] = self.kernel.variable_message(float(beliefs[variable]), float(c2v[edge_index]))
        new_v2c = finite_saturate(new_v2c, boundary="flooding_complete_new_v2c", profile=self.profile)
        for array in (old_snapshot, c2v, beliefs, candidate, new_v2c):
            array.setflags(write=False)
        return FloodingSweep(
            edge_count=self.edge_table.edge_count,
            old_v2c=old_snapshot,
            check_to_variable=c2v,
            new_v2c=new_v2c,
            beliefs=beliefs,
            candidate=candidate,
            proposed_work=FloodingWork(
                check_to_variable=self.edge_table.edge_count,
                variable_to_check=self.edge_table.edge_count,
                belief_assembly=self.edge_table.variable_count,
                candidate_checks=self.edge_table.variable_count,
            ),
        )
