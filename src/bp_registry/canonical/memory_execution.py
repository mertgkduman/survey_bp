"""Transactional ordinary-memory execution at complete flooding boundaries.

The numerical primitives remain the equation owners. This module supplies
decoder-visible operands and commits their private histories with the sweep.
It does not receive a code's logical basis, noise realization, or hidden truth.
"""

from dataclasses import dataclass, fields, replace
from hashlib import sha256
from typing import Any

import numpy as np

from .contracts import MemoryCompositionSpec
from .memory import (
    AffinePriorMemory, MemoryState, PDBPFieldMix, PDPrimeDeltaMix,
    PosteriorMomentum, V2CDamping,
)
from .numerics import finite_saturate
from .schedules import EdgeTable, FloodingSchedule, FloodingSweep


def validate_single_attempt_memory(
    memory: MemoryCompositionSpec, *, schedule: str,
    update: Any = None, max_iterations: int | None = None,
) -> None:
    """Fail before sampling for lifecycle or operand orders not yet executed."""
    if schedule != "flooding":
        raise ValueError(f"memory.execution_schedule_unimplemented:{schedule}")
    assignment = getattr(update, "parameter_assignment", None)
    if getattr(assignment, "shape", None) == "source_iteration":
        if update.kind == "normalized_min_sum":
            raise ValueError("memory.execution_update_assignment_unimplemented:normalized_min_sum:source_iteration")
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


class MemoryFloodingSchedule(FloodingSchedule):
    """An ordinary one-attempt, one-leg ordered memory composition.

    Prior policies precede complete C2V aggregation; field policies precede
    candidate and original-C2V exclusion; V2C policies follow that exclusion.
    Bindings must declare this dependency order. Repeated kinds have distinct
    histories. No history changes during proposal, denial, or failed compute.
    """

    def __init__(self, edge_table: EdgeTable, *, kernel, memory: MemoryCompositionSpec):
        validate_single_attempt_memory(memory, schedule="flooding")
        super().__init__(edge_table, kernel=kernel, profile=kernel.profile)
        self.memory = memory
        self._owner = object()
        self._revision = 0
        self._histories: tuple[Any, ...] | None = None
        self._base_prior: np.ndarray | None = None
        self._error_rate: float | None = None
        policies = []
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
        self._policies = tuple(policies)

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
        self._base_prior, self._error_rate = prior, error_rate
        self._revision = 0
        return messages

    def sweep(self, old_v2c, syndrome, *, error_rate: float, source_iteration: int = 0) -> MemoryFloodingSweep:
        if self._histories is None or self._base_prior is None or error_rate != self._error_rate:
            raise ValueError("memory sweep requires initialization with the same error rate")
        next_histories = list(self._histories)
        prior = self._base_prior
        for binding, policy, state in zip(self.memory.bindings, self._policies, self._histories, strict=True):
            if binding.kind == "affine_prior":
                prior = self._bounded(policy.propose(prior, state.posterior).prior, "memory_affine_prior")

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
        )

    def commit(self, sweep: MemoryFloodingSweep) -> None:
        if sweep.owner is not self._owner or sweep.revision != self._revision:
            raise ValueError("memory commit received a foreign or stale sweep")
        self._histories = sweep.histories
        self._revision += 1

    def evidence(self) -> dict[str, Any]:
        digests = {}
        if self._histories is not None:
            for state in self._histories:
                digest = sha256()
                for field in fields(state):
                    value = getattr(state, field.name)
                    if isinstance(value, np.ndarray):
                        digest.update(field.name.encode("ascii"))
                        digest.update(str(value.shape).encode("ascii"))
                        digest.update(value.astype("<f8", copy=False).tobytes(order="C"))
                digests[state.binding_id] = digest.hexdigest()
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
            # Separate from directional BP work; these are vector element
            # updates, not a claimed common instruction or runtime cost.
            "memory_element_updates": {
                binding.binding_id: self._revision * (self.edge_table.edge_count if binding.target == "v2c" else self.edge_table.variable_count)
                for binding in self.memory.bindings
            },
            "memory_c2v_reduction_additions": self._revision * self.edge_table.edge_count if any(binding.kind == "pdprime_delta_mix" for binding in self.memory.bindings) else 0,
        }
