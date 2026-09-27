"""Transactional ordinary-memory execution at complete flooding boundaries.

The numerical primitives remain the equation owners. This module supplies
decoder-visible operands and commits their private histories with the sweep.
It does not receive a code's logical basis, noise realization, or hidden truth.
"""

from dataclasses import dataclass, fields, replace
from hashlib import sha256
from typing import Any, Mapping

import numpy as np

from .contracts import MemoryCompositionSpec
from .memory import (
    AffinePriorMemory, MemoryAssignmentSpec, MemoryAssignmentState,
    MemoryCompositionState, MemoryState, PDBPFieldMix, PDPrimeDeltaMix,
    PosteriorMomentum, V2CDamping,
)
from .numerics import finite_saturate
from .schedules import EdgeTable, FloodingSchedule, FloodingSweep
from .tracing import TraceResult, TraceSink
from .budgets import BudgetTree, WorkVector


def validate_single_attempt_memory(
    memory: MemoryCompositionSpec, *, schedule: str,
    update: Any = None, max_iterations: int | None = None,
) -> None:
    """Fail before sampling for lifecycle or operand orders not yet executed."""
    if schedule in {"layered", "check_node_serial", "variable_node_serial"}:
        ranks = {"belief": 0, "v2c": 1}
        orders = [ranks.get(binding.target, -1) for binding in memory.bindings]
        if -1 in orders or orders != sorted(orders):
            raise ValueError("memory.local_execution_order_requires_belief_then_v2c")
        for binding in memory.bindings:
            if (binding.kind, binding.target) not in {
                ("pdbp_field_mix", "belief"), ("v2c_damping", "v2c"),
            } or binding.advance_boundary.value != "local_update":
                raise ValueError(
                    f"memory.local_operand_unimplemented:{binding.kind}:{binding.target}:{binding.advance_boundary.value}"
                )
            if (binding.state_lifetime != "attempt"
                    or binding.refresh_boundary.value != "attempt_start"
                    or binding.retain_history):
                raise ValueError(f"memory.local_lifecycle_unimplemented:{binding.binding_id}")
        return
    if schedule != "flooding":
        raise ValueError(f"memory.execution_schedule_unimplemented:{schedule}")
    assignment = getattr(update, "parameter_assignment", None)
    if getattr(assignment, "shape", None) == "source_iteration":
        if max_iterations is not None and len(assignment.values) < max_iterations:
            raise ValueError("memory.execution_update_assignment_shorter_than_attempt")
    ranks = {"prior": 0, "belief": 1, "posterior": 1, "v2c": 2}
    orders = [ranks[binding.target] for binding in memory.bindings]
    if orders != sorted(orders):
        raise ValueError("memory.execution_order_requires_prior_then_fields_then_v2c")
    for index, binding in enumerate(memory.bindings):
        if binding.kind == "pdprime_delta_mix" and index != 0:
            # Its source equation consumes fixed-channel field history and
            # C2V differences, not an upstream modified prior/fresh field.
            raise ValueError("memory.pdprime_requires_fixed_prior_and_first_field_position")
    for binding in memory.bindings:
        if binding.advance_boundary.value != "source_iteration":
            raise ValueError(f"memory.execution_boundary_unimplemented:{binding.binding_id}")
        if (binding.state_lifetime not in {"attempt", "leg"}
                or binding.refresh_boundary.value != f"{binding.state_lifetime}_start"
                or binding.retain_history):
            raise ValueError(f"memory.execution_lifecycle_unimplemented:{binding.binding_id}")


@dataclass(frozen=True, slots=True)
class MemoryFloodingSweep(FloodingSweep):
    """Pure complete messages and all proposed owner-private next histories."""

    histories: tuple[Any, ...]
    owner: object
    revision: int
    source_iteration: int
    assignment_states: tuple[MemoryAssignmentState | None, ...]
    assignment_evidence: tuple[dict[str, Any] | None, ...]


class MemoryFloodingSchedule(FloodingSchedule):
    """An ordinary one-attempt, one-leg ordered memory composition.

    Prior policies precede complete C2V aggregation; field policies precede
    candidate and original-C2V exclusion; V2C policies follow that exclusion.
    Bindings must declare this dependency order. Repeated kinds have distinct
    histories. No history changes during proposal, denial, or failed compute.
    """

    def __init__(
        self, edge_table: EdgeTable, *, kernel, memory: MemoryCompositionSpec,
        execution_context: Mapping[str, str] | None = None,
        trace_sink: TraceSink | None = None, trace_context: Mapping[str, str] | None = None,
    ):
        validate_single_attempt_memory(memory, schedule="flooding")
        super().__init__(edge_table, kernel=kernel, profile=kernel.profile)
        self.memory = memory
        self._owner = object()
        self._revision = 0
        self._histories: tuple[Any, ...] | None = None
        self._assignment_states: tuple[MemoryAssignmentState | None, ...] | None = None
        self._assignment_evidence: tuple[dict[str, Any] | None, ...] | None = None
        self._base_prior: np.ndarray | None = None
        self._error_rate: float | None = None
        self._trace_sink = trace_sink
        supplied_execution = {} if execution_context is None else dict(execution_context)
        if any(not isinstance(key, str) or not key or not isinstance(value, str) or not value for key, value in supplied_execution.items()):
            raise ValueError("memory execution context must contain only nonempty string identifiers")
        supplied_trace = {} if trace_context is None else dict(trace_context)
        if any(not isinstance(key, str) or not key or not isinstance(value, str) or not value for key, value in supplied_trace.items()):
            raise ValueError("memory trace context must contain only nonempty string identifiers")
        # Assignment draws are decoder state, not observation state.  In
        # particular, enabling a trace must never alter the PCG64 replay key.
        # Direct fixtures retain graph-derived defaults when no public context
        # is available, while public execution always supplies both values.
        self._configuration_identity = supplied_execution.get("configuration_identity", f"memory:{edge_table.graph_sha256}")
        self._decoder_identity = supplied_execution.get("decoder_identity", f"memory-decoder:{edge_table.graph_sha256}")
        self._trace_context = supplied_trace
        policies = []
        assignments: list[MemoryAssignmentSpec | None] = []
        for binding in memory.bindings:
            parameters = binding.parameters
            policy = {
                "affine_prior": AffinePriorMemory,
                "v2c_damping": V2CDamping,
                "pdbp_field_mix": PDBPFieldMix,
                "pdprime_delta_mix": PDPrimeDeltaMix,
                "posterior_momentum": PosteriorMomentum,
            }[binding.kind](binding.binding_id, **parameters)
            policies.append(policy)
            assignment = binding.assignment
            assignments.append(None if assignment is None else MemoryAssignmentSpec(
                mode=assignment.mode, graph_sha256=edge_table.graph_sha256,
                root_seed_identity=assignment.root_seed_identity,
                refresh_boundary=assignment.refresh_boundary, retain_history=False,
                low=assignment.low, high=assignment.high,
            ))
        self._policies = tuple(policies)
        self._assignments = tuple(assignments)

    def _bounded(self, value: np.ndarray, name: str) -> np.ndarray:
        array = np.array(finite_saturate(value, boundary=name, profile=self.profile), copy=True)
        array.setflags(write=False)
        return array

    def initialize(self, error_rate: float) -> np.ndarray:
        # A new lifetime invalidates every uncommitted proposal from the old
        # attempt, even when both have revision zero and the same channel.
        self._owner = object()
        messages = super().initialize(error_rate)
        prior = self._bounded(np.full(self.edge_table.variable_count, self.kernel.prior(error_rate)), "memory_initial_prior")
        histories = []
        for binding, policy in zip(self.memory.bindings, self._policies, strict=True):
            if binding.kind == "affine_prior":
                state = MemoryState(binding.binding_id, prior)
            elif binding.kind == "v2c_damping":
                state = policy.initial_state(messages)
            elif binding.kind == "pdprime_delta_mix":
                # Only the per-variable sum is an operand of the PD-prime
                # equation. Store this sufficient statistic in O(n), avoiding
                # a dense check-by-variable array for a sparse QLDPC graph.
                state = policy.initial_state(prior, np.zeros((1, self.edge_table.variable_count)))
            else:
                state = policy.initial_state(prior)
            histories.append(state)
        self._histories = tuple(histories)
        self._assignment_states = tuple(
            None if assignment is None else assignment.initial_state(
                configuration_identity=self._configuration_identity, decoder_identity=self._decoder_identity,
            )
            for assignment in self._assignments
        )
        self._assignment_evidence = tuple(None for _ in self.memory.bindings)
        self._base_prior, self._error_rate = prior, error_rate
        self._revision = 0
        return messages

    def sweep(self, old_v2c, syndrome, *, error_rate: float, source_iteration: int = 0) -> MemoryFloodingSweep:
        if (self._histories is None or self._assignment_states is None or self._assignment_evidence is None
                or self._base_prior is None or error_rate != self._error_rate):
            raise ValueError("memory sweep requires initialization with the same error rate")
        next_histories = list(self._histories)
        next_assignment_states = list(self._assignment_states)
        next_assignment_evidence = list(self._assignment_evidence)
        prior = self._base_prior
        for index, (binding, policy, state, assignment, assignment_state) in enumerate(zip(
            self.memory.bindings, self._policies, self._histories, self._assignments,
            self._assignment_states, strict=True,
        )):
            if binding.kind == "affine_prior":
                if assignment is None:
                    prior = self._bounded(policy.propose(prior, state.posterior).prior, "memory_affine_prior")
                else:
                    assert assignment_state is not None and state.posterior is not None
                    transition = assignment.refresh(
                        assignment_state, boundary="source_iteration",
                        replay_identity=f"{self._decoder_identity}:source_iteration:{source_iteration}",
                        variable_count=self.edge_table.variable_count,
                        budgets=BudgetTree(limits=(), parents={}), budget_scope="attempt",
                        history_state=MemoryCompositionState(), schedule_cursor=(source_iteration,),
                        work=WorkVector.zero(),
                    )
                    if not transition.admitted:
                        raise RuntimeError("admitted ordinary-memory sweep unexpectedly denied assignment refresh")
                    alpha = np.asarray(transition.values, dtype=np.float64)
                    if alpha.shape != prior.shape or not np.all(np.isfinite(alpha)):
                        raise ValueError("disordered affine-prior assignment does not preserve variable shape")
                    prior = self._bounded((1.0 - alpha) * prior + alpha * state.posterior, "memory_disordered_affine_prior")
                    next_assignment_states[index] = transition.state
                    next_assignment_evidence[index] = transition.evidence

        def field_step(fresh: np.ndarray, c2v: np.ndarray) -> np.ndarray:
            value = fresh
            c2v_sum = None
            for index, (binding, policy, state) in enumerate(zip(self.memory.bindings, self._policies, self._histories, strict=True)):
                if binding.kind == "pdbp_field_mix":
                    proposal = policy.propose(state.field, value, boundary="source_iteration")
                    value = self._bounded(proposal.value, "memory_pdbp_field")
                    next_histories[index] = policy.commit(replace(proposal, value=value, history=(value,)), state)
                elif binding.kind == "pdprime_delta_mix":
                    if c2v_sum is None:
                        c2v_sum = np.zeros((1, self.edge_table.variable_count))
                        np.add.at(c2v_sum[0], list(self._edge_variables), c2v)
                    proposal = policy.propose(state.field, state.c2v, c2v_sum, boundary="source_iteration")
                    value = self._bounded(proposal.value, "memory_pdprime_field")
                    next_histories[index] = policy.commit(replace(proposal, value=value, history=(value, proposal.history[1])), state)
                elif binding.kind == "posterior_momentum":
                    proposal = policy.propose(state, value, boundary="source_iteration")
                    value = self._bounded(proposal.posterior, "memory_momentum_posterior")
                    next_histories[index] = policy.commit(replace(proposal, posterior=value), state)
            return value

        def v2c_step(fresh: np.ndarray) -> np.ndarray:
            value = fresh
            for index, (binding, policy, state) in enumerate(zip(self.memory.bindings, self._policies, self._histories, strict=True)):
                if binding.kind == "v2c_damping":
                    proposal = policy.propose(state.v2c, value, boundary="source_iteration")
                    value = self._bounded(proposal.value, "memory_damped_v2c")
                    next_histories[index] = policy.commit(proposal, state)
            return value

        sweep = super().sweep(
            old_v2c, syndrome, error_rate=error_rate, source_iteration=source_iteration,
            prior_llrs=prior, transform_beliefs=field_step, transform_v2c=v2c_step,
        )
        for index, binding in enumerate(self.memory.bindings):
            if binding.kind == "affine_prior":
                next_histories[index] = MemoryState(binding.binding_id, sweep.beliefs)
        return MemoryFloodingSweep(
            **{field.name: getattr(sweep, field.name) for field in fields(FloodingSweep)},
            histories=tuple(next_histories), owner=self._owner, revision=self._revision,
            source_iteration=source_iteration,
            assignment_states=tuple(next_assignment_states), assignment_evidence=tuple(next_assignment_evidence),
        )

    def commit(self, sweep: MemoryFloodingSweep) -> None:
        if sweep.owner is not self._owner or sweep.revision != self._revision:
            raise ValueError("memory commit received a foreign or stale sweep")
        self._histories = sweep.histories
        self._assignment_states = sweep.assignment_states
        self._assignment_evidence = sweep.assignment_evidence
        self._revision += 1
        if self._trace_sink is not None:
            self._trace_sink.observe(
                kind="memory_sweep", iteration=sweep.source_iteration,
                payload={
                    **self._trace_context,
                    "source_iteration": sweep.source_iteration,
                    "beliefs": sweep.beliefs,
                    "history_sha256": self._history_digests(sweep.histories),
                    "history_values": self._history_values(sweep.histories),
                    "assignment_evidence": {
                        binding.binding_id: evidence
                        for binding, evidence in zip(self.memory.bindings, sweep.assignment_evidence, strict=True)
                        if evidence is not None
                    },
                },
            )

    def observe_candidate(self, *, origin: Mapping[str, object], candidate: np.ndarray | None) -> None:
        """Append an optional decoder-visible candidate record after selection.

        The observer accepts no callback and cannot return a decision to the
        executor.  A caller may include a stable candidate lineage ID once it
        has been derived from public decoder state.
        """
        if self._trace_sink is None:
            return
        if candidate is not None and (candidate.ndim != 1 or not np.issubdtype(candidate.dtype, np.integer)):
            raise ValueError("memory trace candidate must be a one-dimensional integer vector")
        self._trace_sink.observe(
            kind="memory_candidate",
            payload={**self._trace_context, "origin": dict(origin), "candidate": candidate},
        )

    def trace_result(self) -> TraceResult | None:
        """Finalize and return the bounded trace sidecar when observation is enabled."""
        return None if self._trace_sink is None else self._trace_sink.finish()

    @staticmethod
    def _history_digests(histories: tuple[Any, ...]) -> dict[str, str]:
        digests = {}
        for state in histories:
            digest = sha256()
            for field in fields(state):
                value = getattr(state, field.name)
                if isinstance(value, np.ndarray):
                    digest.update(field.name.encode("ascii"))
                    digest.update(str(value.shape).encode("ascii"))
                    digest.update(value.astype("<f8", copy=False).tobytes(order="C"))
            digests[state.binding_id] = digest.hexdigest()
        return digests

    @staticmethod
    def _history_values(histories: tuple[Any, ...]) -> dict[str, dict[str, np.ndarray]]:
        """Copy committed decoder-visible history arrays for an opted-in observer.

        The TraceSink owns record and byte admission.  Thus a large history is
        either retained as an immutable complete committed state or dropped
        with explicit sidecar truncation facts; this method never samples a
        subset that could look like a complete numerical history.
        """
        values: dict[str, dict[str, np.ndarray]] = {}
        for state in histories:
            arrays = {
                field.name: np.array(value, dtype=np.float64, copy=True)
                for field in fields(state)
                if isinstance((value := getattr(state, field.name)), np.ndarray)
            }
            values[state.binding_id] = arrays
        return values

    def _memory_element_updates(self, *, committed_updates: int) -> dict[str, int]:
        """Count every owned history element updated at one committed boundary."""
        return {
            binding.binding_id: committed_updates * (
                self.edge_table.edge_count if binding.kind == "v2c_damping"
                else 2 * self.edge_table.variable_count
                if binding.kind in {"pdprime_delta_mix", "posterior_momentum"}
                else self.edge_table.variable_count
            )
            for binding in self.memory.bindings
        }

    def evidence(self) -> dict[str, Any]:
        digests = {} if self._histories is None else self._history_digests(self._histories)
        return {
            "schema_version": 1,
            "mode": "ordered_single_attempt_flooding",
            "bindings": self.memory.model_dump(mode="json")["bindings"],
            "resolved_primitives": [
                {"binding_id": policy.binding_id, "registered_name": policy.registered_name,
                 "fidelity": "affine_prior_equation_with_declared_source_status" if binding.kind == "affine_prior" else policy.fidelity}
                for binding, policy in zip(self.memory.bindings, self._policies, strict=True)
            ],
            "commit_boundary": "complete_double_buffered_sweep",
            "pdprime_c2v_history": "canonical_edge_order_per_variable_sum",
            "v2c_damping_history": "previous_fresh_input_to_binding",
            "committed_iterations": self._revision,
            "history_sha256": digests,
            "assignment_evidence": {} if self._assignment_evidence is None else {
                binding.binding_id: evidence
                for binding, evidence in zip(self.memory.bindings, self._assignment_evidence, strict=True)
                if evidence is not None
            },
            # Separate from directional BP work; these are vector element
            # updates, not a claimed common instruction or runtime cost.
            "memory_element_updates": self._memory_element_updates(committed_updates=self._revision),
            "memory_c2v_reduction_additions": self._revision * self.edge_table.edge_count if any(binding.kind == "pdprime_delta_mix" for binding in self.memory.bindings) else 0,
        }


@dataclass(frozen=True, slots=True)
class LocalMemoryProposal:
    """One local-unit history proposal, detached from the durable owner."""

    histories: tuple[Any, ...]
    owner: object
    revision: int


class LocalMemoryExecution:
    """Commit PDBP fields and V2C damping with an admitted local unit.

    Phase 3 local schedules assemble an entire decoder-visible belief vector,
    then build the affected V2C messages.  This coordinator inserts only the
    policies with exactly those operands.  It has no control-flow callback and
    keeps the proposed histories private until the caller reports an admitted
    local unit whose convergence check succeeded.
    """

    def __init__(self, edge_table: EdgeTable, *, memory: MemoryCompositionSpec):
        validate_single_attempt_memory(memory, schedule="layered")
        self.edge_table = edge_table
        self.memory = memory
        self._owner = object()
        self._revision = 0
        policies = []
        for binding in memory.bindings:
            policy_type = {"pdbp_field_mix": PDBPFieldMix, "v2c_damping": V2CDamping}[binding.kind]
            policies.append(policy_type(binding.binding_id, **binding.parameters, advance_boundary="local_update"))
        self._policies = tuple(policies)
        self._histories: tuple[Any, ...] | None = None
        self._pending: list[Any] | None = None
        self._seen_beliefs = False
        self._seen_v2c = False

    def initialize(self, *, error_rate: float, initial_v2c: np.ndarray, initial_beliefs: np.ndarray) -> None:
        del error_rate  # The caller computes initial decoder-visible operands.
        v2c = np.asarray(initial_v2c, dtype=np.float64)
        beliefs = np.asarray(initial_beliefs, dtype=np.float64)
        if v2c.shape != (self.edge_table.edge_count,) or beliefs.shape != (self.edge_table.variable_count,):
            raise ValueError("local memory initialization must preserve canonical edge and variable shapes")
        if not np.all(np.isfinite(v2c)) or not np.all(np.isfinite(beliefs)):
            raise ValueError("local memory initialization requires finite decoder-visible operands")
        histories = []
        for binding, policy in zip(self.memory.bindings, self._policies, strict=True):
            histories.append(policy.initial_state(beliefs) if binding.kind == "pdbp_field_mix" else policy.initial_state(v2c))
        self._owner = object()
        self._revision = 0
        self._histories = tuple(histories)
        self.discard()

    def begin_step(self) -> None:
        if self._histories is None:
            raise ValueError("local memory requires initialization before a local step")
        self._pending = list(self._histories)
        self._seen_beliefs = not any(binding.kind == "pdbp_field_mix" for binding in self.memory.bindings)
        self._seen_v2c = not any(binding.kind == "v2c_damping" for binding in self.memory.bindings)

    def transform_beliefs(self, fresh_beliefs: np.ndarray) -> np.ndarray:
        if self._histories is None or self._pending is None:
            raise ValueError("local memory belief transform requires an active local step")
        value = self._bounded(fresh_beliefs, "local_memory_fresh_beliefs", self.edge_table.variable_count)
        for index, (binding, policy, state) in enumerate(zip(self.memory.bindings, self._policies, self._histories, strict=True)):
            if binding.kind == "pdbp_field_mix":
                proposal = policy.propose(state.field, value, boundary="local_update")
                value = self._bounded(proposal.value, "local_memory_pdbp_field", self.edge_table.variable_count)
                self._pending[index] = policy.commit(replace(proposal, value=value, history=(value,)), state)
        self._seen_beliefs = True
        return value

    def transform_v2c(self, fresh_v2c: np.ndarray) -> np.ndarray:
        if self._histories is None or self._pending is None:
            raise ValueError("local memory V2C transform requires an active local step")
        value = self._bounded(fresh_v2c, "local_memory_fresh_v2c", self.edge_table.edge_count)
        for index, (binding, policy, state) in enumerate(zip(self.memory.bindings, self._policies, self._histories, strict=True)):
            if binding.kind == "v2c_damping":
                proposal = policy.propose(state.v2c, value, boundary="local_update")
                value = self._bounded(proposal.value, "local_memory_damped_v2c", self.edge_table.edge_count)
                self._pending[index] = policy.commit(proposal, state)
        self._seen_v2c = True
        return value

    def proposal(self) -> LocalMemoryProposal:
        if self._pending is None or not self._seen_beliefs or not self._seen_v2c:
            raise ValueError("local memory proposal lacks a complete declared operand set")
        return LocalMemoryProposal(tuple(self._pending), self._owner, self._revision)

    def commit(self, proposal: LocalMemoryProposal) -> None:
        if proposal.owner is not self._owner or proposal.revision != self._revision:
            raise ValueError("local memory commit received a foreign or stale proposal")
        self._histories = proposal.histories
        self._revision += 1
        self.discard()

    def discard(self) -> None:
        """Drop an unadmitted proposal after a denial or compute/check failure."""
        self._pending = None
        self._seen_beliefs = False
        self._seen_v2c = False

    @staticmethod
    def _bounded(value: np.ndarray, boundary: str, length: int) -> np.ndarray:
        array = np.asarray(value, dtype=np.float64)
        if array.shape != (length,) or not np.all(np.isfinite(array)):
            raise ValueError(f"{boundary} must be a finite canonical vector")
        copied = np.array(array, copy=True)
        copied.setflags(write=False)
        return copied

    def evidence(self) -> dict[str, Any]:
        histories = () if self._histories is None else self._histories
        return {
            "schema_version": 1,
            "mode": "ordered_attempt_local_update",
            "bindings": self.memory.model_dump(mode="json")["bindings"],
            "commit_boundary": "admitted_local_unit_after_convergence_check",
            "operand_order": "complete_fresh_belief_then_affected_fresh_v2c",
            "committed_local_updates": self._revision,
            "history_sha256": MemoryFloodingSchedule._history_digests(histories),
            "memory_element_updates": {
                binding.binding_id: self._revision * (
                    self.edge_table.variable_count if binding.target == "belief" else self.edge_table.edge_count
                ) for binding in self.memory.bindings
            },
        }
