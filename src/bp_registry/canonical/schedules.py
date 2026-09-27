"""Canonical edge ordering and double-buffered flooding semantics."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import numbers
from threading import RLock
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

    def sweep(
        self, old_v2c: np.ndarray, syndrome: np.ndarray, *, error_rate: float,
        source_iteration: int = 0, prior_llrs: np.ndarray | None = None,
        transform_beliefs: Callable[[np.ndarray, np.ndarray], np.ndarray] | None = None,
        transform_v2c: Callable[[np.ndarray], np.ndarray] | None = None,
    ) -> FloodingSweep:
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
        prior = self.kernel.prior(error_rate) if prior_llrs is None else prior_llrs
        if prior_llrs is not None and prior_llrs.shape != (self.edge_table.variable_count,):
            raise ValueError("prior_llrs must have one value per variable")
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
        if transform_beliefs is not None:
            beliefs = finite_saturate(transform_beliefs(beliefs, c2v), boundary="flooding_memory_beliefs", profile=self.profile)
        candidate = self.kernel.candidate_from_beliefs(beliefs)
        new_v2c = np.empty(self.edge_table.edge_count, dtype=np.float64)
        for edge_index, variable in enumerate(self._edge_variables):
            new_v2c[edge_index] = self.kernel.variable_message(float(beliefs[variable]), float(c2v[edge_index]))
        new_v2c = finite_saturate(new_v2c, boundary="flooding_complete_new_v2c", profile=self.profile)
        if transform_v2c is not None:
            new_v2c = finite_saturate(transform_v2c(new_v2c), boundary="flooding_memory_v2c", profile=self.profile)
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

    @property
    def unit_count(self) -> int:
        """One local unit is one declared layer, not a flooding sweep."""
        return len(self.partitions)

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

    def _compute_layer(
        self, messages: np.ndarray, syndrome: np.ndarray, *, error_rate: float, layer_index: int,
        transform_beliefs: Callable[[np.ndarray], np.ndarray] | None = None,
        transform_v2c: Callable[[np.ndarray], np.ndarray] | None = None,
    ) -> tuple[np.ndarray, np.ndarray]:
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
        if transform_beliefs is not None:
            beliefs = finite_saturate(transform_beliefs(beliefs), boundary="layer_memory_beliefs")
        candidate = self.kernel.candidate_from_beliefs(beliefs)
        affected_variables = set().union(*(self._check_variables[check] for check in layer))
        updated = np.array(entry_snapshot, dtype=np.float64, copy=True)
        for edge_index, variable in enumerate(self._edge_variables):
            if variable in affected_variables:
                updated[edge_index] = self.kernel.variable_message(float(beliefs[variable]), float(c2v[edge_index]))
        if transform_v2c is not None:
            updated = finite_saturate(transform_v2c(updated), boundary="layer_memory_v2c")
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
                candidate_constructions=1,
                convergence_checks=1,
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
        transform_beliefs: Callable[[np.ndarray], np.ndarray] | None = None,
        transform_v2c: Callable[[np.ndarray], np.ndarray] | None = None,
    ) -> ScheduledLocalStepResult:
        """Drive the production atomic executor and advance only an admitted cursor."""
        from .execution import ScheduleProgress

        layer_index = self._step_index(progress)
        candidate_box: list[np.ndarray] = []
        proposal = self.propose_local_step(messages, syndrome, error_rate=error_rate, progress=progress)

        def compute() -> np.ndarray:
            updated, candidate = self._compute_layer(
                messages, _binary_syndrome(self.edge_table, syndrome), error_rate=error_rate,
                layer_index=layer_index, transform_beliefs=transform_beliefs, transform_v2c=transform_v2c,
            )
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


class ScheduleAttemptRegistry:
    """Caller-owned, thread-safe claim registry for one execution cohort.

    The registry deliberately lives outside policy configuration: separate shots
    get independent progress objects, while a coordinator can reject a duplicate
    attempt identity instead of accidentally sharing a cursor across workers.
    """

    def __init__(self) -> None:
        self._claimed: set[str] = set()
        self._lock = RLock()

    def claim(self, attempt_identity: str) -> str:
        if not isinstance(attempt_identity, str) or not attempt_identity:
            raise ValueError("schedule attempt identity must be a nonempty string")
        with self._lock:
            if attempt_identity in self._claimed:
                raise ValueError("duplicate same-shot schedule attempt identity")
            self._claimed.add(attempt_identity)
        return attempt_identity


class _NodeSerialSchedule:
    """Shared proposal/executor seam; subclasses define their scientific unit."""

    schedule_name: str
    atomic_unit: str

    def __init__(self, edge_table: EdgeTable, *, kernel: _FloodingKernel) -> None:
        if not isinstance(edge_table, EdgeTable):
            raise ValueError("serial schedules require an EdgeTable")
        self.edge_table = edge_table
        self.kernel = kernel
        self._check_edges = tuple(
            tuple(index for index, (check, _variable) in enumerate(edge_table.edges) if check == current)
            for current in range(edge_table.check_count)
        )
        self._variable_edges = tuple(
            tuple(index for index, (_check, variable) in enumerate(edge_table.edges) if variable == current)
            for current in range(edge_table.variable_count)
        )
        self._edge_variables = tuple(variable for _check, variable in edge_table.edges)

    @property
    def unit_count(self) -> int:
        raise NotImplementedError

    def _unit_index(self, progress: Any) -> int:
        cursor = getattr(progress, "cursor", ())
        if len(cursor) != 1 or isinstance(cursor[0], bool) or not isinstance(cursor[0], numbers.Integral):
            raise ValueError("serial progress cursor must contain exactly one integer unit index")
        index = int(cursor[0])
        if not 0 <= index < self.unit_count:
            raise ValueError("serial progress cursor does not name an available local unit")
        return index

    def _all_c2v(self, messages: np.ndarray, syndrome: np.ndarray) -> np.ndarray:
        c2v = np.empty(self.edge_table.edge_count, dtype=np.float64)
        for check, indices in enumerate(self._check_edges):
            for edge_index in indices:
                incoming = messages[[other for other in indices if other != edge_index]]
                c2v[edge_index] = self.kernel.check_message(incoming, int(syndrome[check]))
        return c2v

    def _compute_unit(
        self, messages: np.ndarray, syndrome: np.ndarray, *, error_rate: float, unit_index: int,
        transform_beliefs: Callable[[np.ndarray], np.ndarray] | None = None,
        transform_v2c: Callable[[np.ndarray], np.ndarray] | None = None,
    ) -> tuple[np.ndarray, np.ndarray, Any]:
        raise NotImplementedError

    def _proposed_work(self, unit_index: int) -> Any:
        raise NotImplementedError

    def evidence(self) -> dict[str, object]:
        return {
            "schedule": self.schedule_name,
            "atomic_unit": self.atomic_unit,
            "canonical_order": tuple(range(self.unit_count)),
            "stopping_adaptation": "D-09 after serial node local unit",
            "mutable_state_lifetime": "attempt",
        }

    def propose_local_step(self, messages: np.ndarray, syndrome: np.ndarray, *, error_rate: float, progress: Any) -> Any:
        from .execution import LocalStepProposal

        unit_index = self._unit_index(progress)
        syndrome_bits = _binary_syndrome(self.edge_table, syndrome)
        work = self._proposed_work(unit_index)
        return LocalStepProposal(
            label=f"{self.schedule_name}:{unit_index}",
            proposed_work=work,
            compute=lambda: self._compute_unit(messages, syndrome_bits, error_rate=error_rate, unit_index=unit_index)[0],
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
        transform_beliefs: Callable[[np.ndarray], np.ndarray] | None = None,
        transform_v2c: Callable[[np.ndarray], np.ndarray] | None = None,
    ) -> ScheduledLocalStepResult:
        from .execution import ScheduleProgress

        unit_index = self._unit_index(progress)
        candidate_box: list[np.ndarray] = []
        proposal = self.propose_local_step(messages, syndrome, error_rate=error_rate, progress=progress)

        def compute() -> np.ndarray:
            updated, candidate, _visibility = self._compute_unit(
                messages,
                _binary_syndrome(self.edge_table, syndrome),
                error_rate=error_rate,
                unit_index=unit_index,
                transform_beliefs=transform_beliefs,
                transform_v2c=transform_v2c,
            )
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
            cursor=(unit_index + 1,),
            rng_state=progress.rng_state,
        )
        return ScheduledLocalStepResult(True, next_progress, candidate_box[-1], proposal.proposed_work)


class CheckNodeSerialSchedule(_NodeSerialSchedule):
    """SCNS: update a check's complete C2V fanout, then affected V2C state."""

    schedule_name = "check_node_serial"
    atomic_unit = "one_check_all_c2v_then_affected_v2c"

    @property
    def unit_count(self) -> int:
        return self.edge_table.check_count

    def evidence(self) -> dict[str, object]:
        return {
            **super().evidence(),
            "stale_read_set": ("v2c_at_check_unit_entry",),
            "fresh_read_set": ("affected_variable_beliefs", "affected_variable_v2c_for_later_checks"),
            "source_procedure": "Moradi SCNS check-unit order with D-09 stopping adaptation",
        }

    def _proposed_work(self, unit_index: int) -> Any:
        from .budgets import WorkVector

        affected = {self.edge_table.edges[index][1] for index in self._check_edges[unit_index]}
        return WorkVector(
            check_to_variable_updates=len(self._check_edges[unit_index]),
            variable_to_check_updates=sum(variable in affected for variable in self._edge_variables),
            belief_assemblies=len(affected),
            candidate_constructions=1,
            convergence_checks=1,
            candidate_checks=1,
        )

    def _compute_unit(
        self, messages: np.ndarray, syndrome: np.ndarray, *, error_rate: float, unit_index: int,
        transform_beliefs: Callable[[np.ndarray], np.ndarray] | None = None,
        transform_v2c: Callable[[np.ndarray], np.ndarray] | None = None,
    ) -> tuple[np.ndarray, np.ndarray, Any]:
        entry = finite_saturate(messages, boundary="check_serial_entry_v2c")
        if entry.ndim != 1 or entry.shape != (self.edge_table.edge_count,):
            raise ValueError("serial messages must have exactly one value per canonical edge")
        snapshot = np.array(entry, dtype=np.float64, copy=True)
        c2v = self._all_c2v(snapshot, syndrome)
        indices = self._check_edges[unit_index]
        for edge_index in indices:
            incoming = snapshot[[other for other in indices if other != edge_index]]
            c2v[edge_index] = self.kernel.check_message(incoming, int(syndrome[unit_index]))
        c2v = finite_saturate(c2v, boundary="check_serial_complete_c2v")
        prior = self.kernel.prior(error_rate)
        beliefs = self.kernel.assemble_beliefs(self.edge_table.variable_count, self._edge_variables, c2v, prior)
        if transform_beliefs is not None:
            beliefs = finite_saturate(transform_beliefs(beliefs), boundary="check_serial_memory_beliefs")
        candidate = self.kernel.candidate_from_beliefs(beliefs)
        affected = {self.edge_table.edges[index][1] for index in indices}
        updated = np.array(snapshot, dtype=np.float64, copy=True)
        for edge_index, variable in enumerate(self._edge_variables):
            if variable in affected:
                updated[edge_index] = self.kernel.variable_message(float(beliefs[variable]), float(c2v[edge_index]))
        if transform_v2c is not None:
            updated = finite_saturate(transform_v2c(updated), boundary="check_serial_memory_v2c")
        return finite_saturate(updated, boundary="check_serial_complete_v2c"), np.array(candidate, dtype=np.uint8, copy=True), self.evidence()


class VariableNodeSerialSchedule(_NodeSerialSchedule):
    """SVNS: gather a variable's current C2V state, then update its V2C fanout."""

    schedule_name = "variable_node_serial"
    atomic_unit = "one_variable_belief_then_incident_v2c"

    @property
    def unit_count(self) -> int:
        return self.edge_table.variable_count

    def evidence(self) -> dict[str, object]:
        return {
            **super().evidence(),
            "stale_read_set": ("incident_c2v_at_variable_unit_entry",),
            "fresh_read_set": ("variable_belief", "incident_v2c_for_later_variables"),
            "source_procedure": "Moradi SVNS variable-unit order with D-09 stopping adaptation",
        }

    def _proposed_work(self, unit_index: int) -> Any:
        from .budgets import WorkVector

        return WorkVector(
            variable_to_check_updates=len(self._variable_edges[unit_index]),
            belief_assemblies=1,
            candidate_constructions=1,
            convergence_checks=1,
            candidate_checks=1,
        )

    def _compute_unit(
        self, messages: np.ndarray, syndrome: np.ndarray, *, error_rate: float, unit_index: int,
        transform_beliefs: Callable[[np.ndarray], np.ndarray] | None = None,
        transform_v2c: Callable[[np.ndarray], np.ndarray] | None = None,
    ) -> tuple[np.ndarray, np.ndarray, Any]:
        entry = finite_saturate(messages, boundary="variable_serial_entry_v2c")
        if entry.ndim != 1 or entry.shape != (self.edge_table.edge_count,):
            raise ValueError("serial messages must have exactly one value per canonical edge")
        snapshot = np.array(entry, dtype=np.float64, copy=True)
        c2v = finite_saturate(self._all_c2v(snapshot, syndrome), boundary="variable_serial_incident_c2v")
        prior = self.kernel.prior(error_rate)
        beliefs = self.kernel.assemble_beliefs(self.edge_table.variable_count, self._edge_variables, c2v, prior)
        if transform_beliefs is not None:
            beliefs = finite_saturate(transform_beliefs(beliefs), boundary="variable_serial_memory_beliefs")
        candidate = self.kernel.candidate_from_beliefs(beliefs)
        updated = np.array(snapshot, dtype=np.float64, copy=True)
        for edge_index in self._variable_edges[unit_index]:
            updated[edge_index] = self.kernel.variable_message(float(beliefs[unit_index]), float(c2v[edge_index]))
        if transform_v2c is not None:
            updated = finite_saturate(transform_v2c(updated), boundary="variable_serial_memory_v2c")
        return finite_saturate(updated, boundary="variable_serial_complete_v2c"), np.array(candidate, dtype=np.uint8, copy=True), self.evidence()


@dataclass(frozen=True, slots=True)
class RandomizedTraversalState:
    """Attempt-local RNG state and realized traversal evidence."""

    derived_identity: str
    rng_state: str
    realized_orders: tuple[tuple[int, ...], ...] = ()


@dataclass(frozen=True, slots=True)
class RandomizedTraversalRefresh:
    """Admission outcome for a boundary-owned order refresh."""

    admitted: bool
    state: RandomizedTraversalState
    order: tuple[int, ...] | None
    order_generation_operations: int
    termination: Any = None


class RandomizedTraversalPlan:
    """Purpose-separated, replayable permutations over a declared base schedule.

    This class never sees sampling state.  Its root identity produces only a
    schedule-order substream; callers retain physical-error identities elsewhere.
    Plan 03-05 will widen the WorkVector with an explicit order-generation
    resource, while this policy already makes the required pre-draw admission
    and state-commit boundary observable.
    """

    _BOUNDARY_BY_SCOPE = {"configuration": "configuration", "attempt": "attempt", "sweep": "sweep"}

    def __init__(self, base_schedule: Any, *, refresh_scope: str, root_identity: str) -> None:
        if refresh_scope not in self._BOUNDARY_BY_SCOPE:
            raise ValueError("randomized traversal refresh_scope must be configuration, attempt, or sweep")
        if not isinstance(root_identity, str) or len(root_identity) != 64 or any(character not in "0123456789abcdef" for character in root_identity):
            raise ValueError("randomized traversal root_identity must be a lowercase SHA-256 hex digest")
        unit_count = getattr(base_schedule, "unit_count", None)
        if isinstance(unit_count, bool) or not isinstance(unit_count, numbers.Integral) or unit_count < 1:
            raise ValueError("randomized traversal requires a nonempty layered or node-serial base schedule")
        self.base_schedule = base_schedule
        self.refresh_scope = refresh_scope
        self.root_identity = root_identity
        self._unit_count = int(unit_count)

    def initial_state(self, *, configuration_identity: str, attempt_identity: str) -> RandomizedTraversalState:
        if not isinstance(configuration_identity, str) or not configuration_identity or not isinstance(attempt_identity, str) or not attempt_identity:
            raise ValueError("randomized traversal identities must be nonempty strings")
        material = {
            "purpose": "schedule_order",
            "root_identity": self.root_identity,
            "configuration_identity": configuration_identity,
            "refresh_scope": self.refresh_scope,
        }
        if self.refresh_scope in {"attempt", "sweep"}:
            material["attempt_identity"] = attempt_identity
        derived = sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        generator = np.random.Generator(np.random.PCG64(int(derived[:32], 16)))
        return RandomizedTraversalState(derived, json.dumps(generator.bit_generator.state, sort_keys=True), ())

    def evidence(self, state: RandomizedTraversalState) -> dict[str, object]:
        return {
            "purpose": "schedule_order",
            "algorithm": "numpy.PCG64",
            "version": np.__version__,
            "root_identity": self.root_identity,
            "derived_identity": state.derived_identity,
            "refresh_scope": self.refresh_scope,
            "realized_orders": state.realized_orders,
            "base_schedule": getattr(self.base_schedule, "schedule_name", "layered"),
        }

    def refresh(
        self,
        state: RandomizedTraversalState,
        *,
        boundary: str,
        budgets: Any,
        budget_scope: str,
    ) -> RandomizedTraversalRefresh:
        """Reserve before cloning/drawing; denial leaves state and order untouched."""
        from .budgets import WorkVector

        if not isinstance(state, RandomizedTraversalState):
            raise ValueError("randomized traversal refresh requires its own immutable state")
        if boundary != self._BOUNDARY_BY_SCOPE[self.refresh_scope]:
            raise ValueError("randomized traversal may refresh only at its declared boundary")
        if state.realized_orders and self.refresh_scope != "sweep":
            return RandomizedTraversalRefresh(True, state, state.realized_orders[-1], 0)
        reservation = budgets.reserve(
            budget_scope,
            WorkVector(order_generation=self._unit_count, order_selection=self._unit_count),
            leaf_id=f"{budget_scope}:schedule-order:{state.derived_identity}:{len(state.realized_orders)}",
        )
        if reservation is None:
            return RandomizedTraversalRefresh(False, state, None, 1, budgets.last_termination)
        try:
            generator = np.random.Generator(np.random.PCG64())
            generator.bit_generator.state = json.loads(state.rng_state)
            order = tuple(int(item) for item in generator.permutation(self._unit_count))
            next_state = RandomizedTraversalState(
                state.derived_identity,
                json.dumps(generator.bit_generator.state, sort_keys=True),
                state.realized_orders + (order,),
            )
            reservation.commit_once()
            return RandomizedTraversalRefresh(True, next_state, order, 1)
        except BaseException:
            if reservation.active:
                reservation.rollback()
            raise
