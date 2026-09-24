"""Canonical edge ordering and double-buffered flooding semantics."""

from __future__ import annotations

from dataclasses import dataclass
import numbers
from typing import Any, Callable, Protocol

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

    def check_message(self, incoming: np.ndarray, syndrome: int) -> float: ...

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

    def sweep(self, old_v2c: np.ndarray, syndrome: np.ndarray, *, error_rate: float) -> FloodingSweep:
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
                c2v[edge_index] = self.kernel.check_message(incoming, int(syndrome_bits[check]))
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


def _binary_syndrome(edge_table: EdgeTable, syndrome: np.ndarray) -> np.ndarray:
    """Copy a checked observation without accepting a decoder-visible ambiguity."""
    bits = np.asarray(syndrome)
    if (
        bits.shape != (edge_table.check_count,)
        or not np.issubdtype(bits.dtype, np.integer)
        or np.any((bits != 0) & (bits != 1))
    ):
        raise ValueError("syndrome must be a binary integer vector matching the check count")
    return np.array(bits, dtype=np.uint8, copy=True)


@dataclass(frozen=True, slots=True)
class ScheduledLocalStepResult:
    """The observable result of one admitted or denied schedule-local unit."""

    admitted: bool
    progress: Any
    candidate: np.ndarray | None
    proposed_work: Any
    termination: Any = None


class LayeredSchedule:
    """Explicit conflict-free check layers with source-qualified structural evidence.

    A layer reads one V2C snapshot.  Its C2V updates commit together, then every
    V2C incident to an affected variable is refreshed.  Later layers therefore
    observe the prior layer's committed V2C values without allowing peers inside
    a layer to observe partial updates.
    """

    _PROVENANCE = frozenset({"explicit", "source_explicit", "graph_coloring"})

    def __init__(
        self,
        edge_table: EdgeTable,
        *,
        kernel: _FloodingKernel,
        partitions: tuple[tuple[int, ...], ...] | list[list[int]] | list[tuple[int, ...]],
        provenance: str,
        construction_rule: str | None = None,
    ) -> None:
        if not isinstance(edge_table, EdgeTable):
            raise ValueError("layered schedules require an EdgeTable")
        if provenance not in self._PROVENANCE:
            raise ValueError("layer provenance must be explicit, source_explicit, or graph_coloring")
        if provenance == "graph_coloring" and (not isinstance(construction_rule, str) or not construction_rule):
            raise ValueError("graph_coloring partitions require a deterministic construction rule")
        if provenance != "graph_coloring" and construction_rule is not None:
            raise ValueError("only graph_coloring partitions may declare a construction rule")
        if not isinstance(partitions, (tuple, list)):
            raise ValueError("partitions must be an array of nonempty check layers")
        if not partitions:
            raise ValueError("partitions must contain at least one layer")

        check_edges = tuple(
            tuple(index for index, (check, _variable) in enumerate(edge_table.edges) if check == current)
            for current in range(edge_table.check_count)
        )
        check_variables = tuple(
            frozenset(edge_table.edges[index][1] for index in indices) for indices in check_edges
        )
        canonical_layers: list[tuple[int, ...]] = []
        memberships = [0] * edge_table.check_count
        for layer in partitions:
            if not isinstance(layer, (tuple, list)):
                raise ValueError("each layer must be an array of integer check IDs")
            if not layer:
                raise ValueError("layers must not be empty")
            normalized: list[int] = []
            variables: set[int] = set()
            for check in layer:
                if isinstance(check, (bool, np.bool_)) or not isinstance(check, numbers.Integral):
                    raise ValueError("layer membership uses exact integer IDs, never text")
                check_id = int(check)
                if not 0 <= check_id < edge_table.check_count:
                    raise ValueError("layer contains an unknown check")
                if check_id in normalized:
                    raise ValueError("a layer cannot repeat a check")
                overlap = variables.intersection(check_variables[check_id])
                if overlap:
                    raise ValueError("a layer contains conflicting simultaneous check updates")
                normalized.append(check_id)
                variables.update(check_variables[check_id])
                memberships[check_id] += 1
            canonical_layers.append(tuple(normalized))
        if any(count == 0 for count in memberships):
            raise ValueError("layer partitions must cover every check at least once")

        self.edge_table = edge_table
        self.kernel = kernel
        self.provenance = provenance
        self.construction_rule = construction_rule
        self.partitions = tuple(canonical_layers)
        self._check_edges = check_edges
        self._check_variables = check_variables
        self._edge_variables = tuple(variable for _check, variable in edge_table.edges)
        self._memberships = tuple(memberships)

    @classmethod
    def deterministic_graph_coloring(cls, edge_table: EdgeTable, *, kernel: _FloodingKernel) -> "LayeredSchedule":
        """Greedily color checks in canonical order; this is never a source cluster claim."""
        check_variables = tuple(
            frozenset(variable for check, variable in edge_table.edges if check == current)
            for current in range(edge_table.check_count)
        )
        layers: list[list[int]] = []
        for check, variables in enumerate(check_variables):
            for layer in layers:
                occupied = set().union(*(check_variables[item] for item in layer))
                if not occupied.intersection(variables):
                    layer.append(check)
                    break
            else:
                layers.append([check])
        return cls(
            edge_table,
            kernel=kernel,
            partitions=layers,
            provenance="graph_coloring",
            construction_rule="greedy canonical check-order graph coloring by shared variable",
        )

    def evidence(self) -> dict[str, object]:
        """Retain integer graph structure and realized membership without textual identity."""
        return {
            "provenance": self.provenance,
            "construction_rule": self.construction_rule,
            "partitions": self.partitions,
            "realized_order": tuple(check for layer in self.partitions for check in layer),
            "membership_multiplicity": tuple(enumerate(self._memberships)),
            "graph_identity": (self.edge_table.check_count, self.edge_table.variable_count, self.edge_table.edges),
            "stopping_adaptation": "D-09 after completed layer local unit",
        }

    def _step_index(self, progress: Any) -> int:
        cursor = getattr(progress, "cursor", ())
        if len(cursor) != 1 or isinstance(cursor[0], bool) or not isinstance(cursor[0], numbers.Integral):
            raise ValueError("layer progress cursor must contain exactly one integer layer index")
        index = int(cursor[0])
        if not 0 <= index < len(self.partitions):
            raise ValueError("layer progress cursor does not name an available layer")
        return index

    def _all_c2v(self, messages: np.ndarray, syndrome: np.ndarray) -> np.ndarray:
        c2v = np.empty(self.edge_table.edge_count, dtype=np.float64)
        for check, indices in enumerate(self._check_edges):
            for edge_index in indices:
                incoming = messages[[other for other in indices if other != edge_index]]
                c2v[edge_index] = self.kernel.check_message(incoming, int(syndrome[check]))
        return c2v

    def _compute_layer(self, messages: np.ndarray, syndrome: np.ndarray, *, error_rate: float, layer_index: int) -> tuple[np.ndarray, np.ndarray]:
        entry = finite_saturate(messages, boundary="layer_entry_v2c")
        if entry.ndim != 1 or entry.shape != (self.edge_table.edge_count,):
            raise ValueError("layered messages must have exactly one value per canonical edge")
        entry_snapshot = np.array(entry, dtype=np.float64, copy=True)
        layer = self.partitions[layer_index]
        c2v = self._all_c2v(entry_snapshot, syndrome)
        for check in layer:
            indices = self._check_edges[check]
            for edge_index in indices:
                incoming = entry_snapshot[[other for other in indices if other != edge_index]]
                c2v[edge_index] = self.kernel.check_message(incoming, int(syndrome[check]))
        c2v = finite_saturate(c2v, boundary="layer_complete_c2v")
        prior = self.kernel.prior(error_rate)
        beliefs = self.kernel.assemble_beliefs(self.edge_table.variable_count, self._edge_variables, c2v, prior)
        candidate = self.kernel.candidate_from_beliefs(beliefs)
        affected_variables = set().union(*(self._check_variables[check] for check in layer))
        updated = np.array(entry_snapshot, dtype=np.float64, copy=True)
        for edge_index, variable in enumerate(self._edge_variables):
            if variable in affected_variables:
                updated[edge_index] = self.kernel.variable_message(float(beliefs[variable]), float(c2v[edge_index]))
        return finite_saturate(updated, boundary="layer_complete_v2c"), np.array(candidate, dtype=np.uint8, copy=True)

    def propose_local_step(self, messages: np.ndarray, syndrome: np.ndarray, *, error_rate: float, progress: Any) -> Any:
        """Return an immutable local mutation proposal; no schedule cursor is mutated."""
        from .budgets import WorkVector
        from .execution import LocalStepProposal

        layer_index = self._step_index(progress)
        syndrome_bits = _binary_syndrome(self.edge_table, syndrome)
        layer = self.partitions[layer_index]
        layer_edges = tuple(index for check in layer for index in self._check_edges[check])
        affected_variables = set().union(*(self._check_variables[check] for check in layer))
        v2c_refreshes = sum(variable in affected_variables for variable in self._edge_variables)
        return LocalStepProposal(
            label=f"layer:{layer_index}",
            proposed_work=WorkVector(
                check_to_variable_updates=len(layer_edges),
                variable_to_check_updates=v2c_refreshes,
                belief_assemblies=self.edge_table.variable_count,
                candidate_checks=1,
            ),
            compute=lambda: self._compute_layer(messages, syndrome_bits, error_rate=error_rate, layer_index=layer_index)[0],
        )

    def execute_local_step(
        self,
        executor: Any,
        messages: np.ndarray,
        syndrome: np.ndarray,
        *,
        error_rate: float,
        progress: Any,
        is_converged: Callable[[np.ndarray], bool],
    ) -> ScheduledLocalStepResult:
        """Drive the production atomic executor and advance only an admitted cursor."""
        from .execution import ScheduleProgress

        layer_index = self._step_index(progress)
        candidate_box: list[np.ndarray] = []
        proposal = self.propose_local_step(messages, syndrome, error_rate=error_rate, progress=progress)

        def compute() -> np.ndarray:
            updated, candidate = self._compute_layer(messages, _binary_syndrome(self.edge_table, syndrome), error_rate=error_rate, layer_index=layer_index)
            candidate.setflags(write=False)
            candidate_box.append(candidate)
            return updated

        result = executor.execute(
            type(proposal)(proposal.label, proposal.proposed_work, compute),
            messages=messages,
            progress=progress,
            policy_state={},
            cache={},
            is_converged=lambda _messages: bool(candidate_box and is_converged(candidate_box[-1])),
        )
        if not result.admitted:
            return ScheduledLocalStepResult(False, progress, None, proposal.proposed_work, result.termination)
        next_progress = ScheduleProgress(
            iteration=progress.iteration,
            local_steps=result.progress.local_steps,
            cursor=(layer_index + 1,),
            rng_state=progress.rng_state,
        )
        return ScheduledLocalStepResult(True, next_progress, candidate_box[-1], proposal.proposed_work)
