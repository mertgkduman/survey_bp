"""Typed affine prior-memory proposals with explicit commit ownership."""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
import math
from threading import RLock
from typing import Any, Literal

import numpy as np


def _finite_vector(value: np.ndarray | tuple[float, ...], *, name: str) -> np.ndarray:
    vector = np.asarray(value, dtype=np.float64)
    if vector.ndim != 1 or vector.size == 0 or not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} must be a nonempty finite float64 vector")
    copied = np.array(vector, dtype=np.float64, copy=True)
    copied.setflags(write=False)
    return copied


def _finite_matrix(value: np.ndarray, *, name: str) -> np.ndarray:
    matrix = np.asarray(value, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[1] == 0 or not np.all(np.isfinite(matrix)):
        raise ValueError(f"{name} must be a nonempty finite float64 matrix")
    copied = np.array(matrix, dtype=np.float64, copy=True)
    copied.setflags(write=False)
    return copied


def _coefficient(value: float, *, name: str, upper_inclusive: bool) -> float:
    if not isinstance(value, float) or not math.isfinite(value) or value < 0.0 or value > 1.0:
        bracket = "]" if upper_inclusive else ")"
        raise ValueError(f"{name} must be a finite value in [0, 1{bracket}")
    if not upper_inclusive and value == 1.0:
        raise ValueError(f"{name} must be a finite value in [0, 1)")
    return value


def _boundary(value: str, *, expected: str) -> None:
    if value != expected:
        raise ValueError(f"policy history may advance only at its declared {expected} boundary")


@dataclass(frozen=True, slots=True)
class TargetMemoryProposal:
    """A target value paired with owned next history for one pure policy step."""

    binding_id: str
    target: str
    value: np.ndarray
    history: tuple[np.ndarray, ...]


@dataclass(frozen=True, slots=True)
class V2CDampingState:
    """The initialized or most recently committed V2C history."""

    binding_id: str
    v2c: np.ndarray


@dataclass(frozen=True, slots=True)
class PDBPFieldState:
    """The most recently committed effective-field history."""

    binding_id: str
    field: np.ndarray


@dataclass(frozen=True, slots=True)
class PDPrimeDeltaState:
    """The effective field and edge-aligned C2V history committed together."""

    binding_id: str
    field: np.ndarray
    c2v: np.ndarray


@dataclass(frozen=True, slots=True)
class V2CDamping:
    """Gökduman--Yao--Pfister V2C damping: fresh ``gamma`` orientation."""

    binding_id: str
    gamma: float
    target: str = "v2c"
    advance_boundary: str = "source_iteration"
    registered_name: str = "gy-pfister-v2c-damping-v1"
    fidelity: str = "source_equation_css_component_adaptation"

    def __post_init__(self) -> None:
        if not self.binding_id:
            raise ValueError("memory binding_id must be nonempty")
        _coefficient(self.gamma, name="V2C damping gamma", upper_inclusive=True)
        if self.target != "v2c":
            raise ValueError("V2C damping may target only v2c")
        if self.advance_boundary not in {"local_update", "source_iteration"}:
            raise ValueError("V2C damping requires a declared local_update or source_iteration boundary")

    def initial_state(self, channel_v2c: np.ndarray | tuple[float, ...]) -> V2CDampingState:
        return V2CDampingState(self.binding_id, _finite_vector(channel_v2c, name="channel_v2c"))

    def propose(
        self, old_v2c: np.ndarray | tuple[float, ...], fresh_v2c: np.ndarray | tuple[float, ...], *, boundary: str,
    ) -> TargetMemoryProposal:
        _boundary(boundary, expected=self.advance_boundary)
        old = _finite_vector(old_v2c, name="old_v2c")
        fresh = _finite_vector(fresh_v2c, name="fresh_v2c")
        if old.shape != fresh.shape:
            raise ValueError("old_v2c and fresh_v2c must have the same shape")
        value = _finite_vector(
            (1.0 - self.gamma) * old + self.gamma * fresh,
            name="damped_v2c",
        )
        # Equation (17) uses the previous decoder-visible damped message as
        # m^(t), rather than the raw proposal that produced it.
        return TargetMemoryProposal(self.binding_id, self.target, value, (value,))

    def commit(self, proposal: TargetMemoryProposal, state: V2CDampingState | None = None) -> V2CDampingState:
        if proposal.binding_id != self.binding_id or proposal.target != self.target or len(proposal.history) != 1:
            raise ValueError("V2C damping may commit only its own V2C proposal")
        if state is not None and state.binding_id != self.binding_id:
            raise ValueError("V2C damping may not overwrite another binding's state")
        return V2CDampingState(self.binding_id, proposal.history[0])

    def reset(self, channel_v2c: np.ndarray | tuple[float, ...]) -> V2CDampingState:
        """Reset at an attempt or Relay leg to the declared channel-prior V2C value."""
        return self.initial_state(channel_v2c)


@dataclass(frozen=True, slots=True)
class PDBPFieldMix:
    """Pretti PDBP mixes complete old and fresh effective fields."""

    binding_id: str
    gamma: float
    target: str = "belief"
    advance_boundary: str = "source_iteration"
    registered_name: str = "pretti-pdbp-field-mix-v1"
    fidelity: str = "classical_source_css_adaptation"

    def __post_init__(self) -> None:
        if not self.binding_id:
            raise ValueError("memory binding_id must be nonempty")
        _coefficient(self.gamma, name="PDBP gamma", upper_inclusive=False)
        if self.target not in {"belief", "effective_field"}:
            raise ValueError("PDBP may target only belief/effective_field")
        if self.advance_boundary not in {"local_update", "source_iteration"}:
            raise ValueError("PDBP requires a declared local_update or source_iteration boundary")

    def initial_state(self, channel_field: np.ndarray | tuple[float, ...]) -> PDBPFieldState:
        return PDBPFieldState(self.binding_id, _finite_vector(channel_field, name="channel_field"))

    def propose(
        self, old_field: np.ndarray | tuple[float, ...], fresh_field: np.ndarray | tuple[float, ...], *, boundary: str,
    ) -> TargetMemoryProposal:
        _boundary(boundary, expected=self.advance_boundary)
        old = _finite_vector(old_field, name="old_field")
        fresh = _finite_vector(fresh_field, name="fresh_field")
        if old.shape != fresh.shape:
            raise ValueError("old_field and fresh_field must have the same shape")
        value = (1.0 - self.gamma) * fresh + self.gamma * old
        return TargetMemoryProposal(self.binding_id, self.target, _finite_vector(value, name="mixed_field"), (value,))

    def commit(self, proposal: TargetMemoryProposal, state: PDBPFieldState | None = None) -> PDBPFieldState:
        if proposal.binding_id != self.binding_id or proposal.target != self.target or len(proposal.history) != 1:
            raise ValueError("PDBP may commit only its own field proposal")
        if state is not None and state.binding_id != self.binding_id:
            raise ValueError("PDBP may not overwrite another binding's state")
        return PDBPFieldState(self.binding_id, proposal.history[0])

    def reset(self, channel_field: np.ndarray | tuple[float, ...]) -> PDBPFieldState:
        return self.initial_state(channel_field)


@dataclass(frozen=True, slots=True)
class PDPrimeDeltaMix:
    """Pretti PD-prime applies a C2V edge-aligned delta to the old field."""

    binding_id: str
    gamma: float
    target: str = "belief"
    advance_boundary: str = "source_iteration"
    registered_name: str = "pretti-pdprime-delta-mix-v1"
    fidelity: str = "classical_source_css_adaptation"

    def __post_init__(self) -> None:
        if not self.binding_id:
            raise ValueError("memory binding_id must be nonempty")
        _coefficient(self.gamma, name="PD-prime gamma", upper_inclusive=False)
        if self.target not in {"belief", "effective_field"}:
            raise ValueError("PD-prime may target only belief/effective_field")
        if self.advance_boundary not in {"local_update", "source_iteration"}:
            raise ValueError("PD-prime requires a declared local_update or source_iteration boundary")

    def initial_state(
        self, channel_field: np.ndarray | tuple[float, ...], c2v: np.ndarray,
    ) -> PDPrimeDeltaState:
        field = _finite_vector(channel_field, name="channel_field")
        messages = _finite_matrix(c2v, name="c2v")
        if field.shape != (messages.shape[1],):
            raise ValueError("channel_field width must match the C2V variable axis")
        return PDPrimeDeltaState(self.binding_id, field, messages)

    def propose(
        self, old_field: np.ndarray | tuple[float, ...], old_c2v: np.ndarray, fresh_c2v: np.ndarray, *, boundary: str,
    ) -> TargetMemoryProposal:
        _boundary(boundary, expected=self.advance_boundary)
        field = _finite_vector(old_field, name="old_field")
        old = _finite_matrix(old_c2v, name="old_c2v")
        fresh = _finite_matrix(fresh_c2v, name="fresh_c2v")
        if old.shape != fresh.shape:
            raise ValueError("old_c2v and fresh_c2v must have the same edge-aligned shape")
        if field.shape != (old.shape[1],):
            raise ValueError("old_field width must match the C2V variable axis")
        delta = np.sum(fresh - old, axis=0)
        value = field + (1.0 - self.gamma) * delta
        return TargetMemoryProposal(self.binding_id, self.target, _finite_vector(value, name="delta_mixed_field"), (value, fresh))

    def commit(self, proposal: TargetMemoryProposal, state: PDPrimeDeltaState | None = None) -> PDPrimeDeltaState:
        if proposal.binding_id != self.binding_id or proposal.target != self.target or len(proposal.history) != 2:
            raise ValueError("PD-prime may commit only its own field-and-C2V proposal")
        if state is not None and state.binding_id != self.binding_id:
            raise ValueError("PD-prime may not overwrite another binding's state")
        return PDPrimeDeltaState(self.binding_id, proposal.history[0], proposal.history[1])

    def reset(self, channel_field: np.ndarray | tuple[float, ...], c2v: np.ndarray) -> PDPrimeDeltaState:
        return self.initial_state(channel_field, c2v)


@dataclass(frozen=True, slots=True)
class PosteriorMomentumState:
    """Chen's retained posterior ``Q`` and velocity ``g`` at one binding."""

    binding_id: str
    posterior: np.ndarray
    velocity: np.ndarray


@dataclass(frozen=True, slots=True)
class PosteriorMomentumProposal:
    """A pure Chen momentum update and its next owned history."""

    binding_id: str
    posterior: np.ndarray
    velocity: np.ndarray


@dataclass(frozen=True, slots=True)
class PosteriorMomentum:
    """Chen posterior momentum with an explicit original-C2V extrinsic step."""

    binding_id: str
    alpha: float
    gamma: float
    target: str = "belief"
    advance_boundary: str = "source_iteration"
    registered_name: str = "chen-posterior-momentum-v1"
    fidelity: str = "gf4_source_scalar_llr_css_adaptation"

    def __post_init__(self) -> None:
        if not self.binding_id:
            raise ValueError("memory binding_id must be nonempty")
        if not isinstance(self.alpha, float) or not math.isfinite(self.alpha) or not 0.0 < self.alpha <= 1.0:
            raise ValueError("momentum alpha must be a finite value in (0, 1]")
        _coefficient(self.gamma, name="momentum gamma", upper_inclusive=False)
        if self.target != "belief":
            raise ValueError("posterior momentum may target only belief")
        if self.advance_boundary not in {"local_update", "source_iteration"}:
            raise ValueError("momentum requires a declared local_update or source_iteration boundary")

    def initial_state(self, prior: np.ndarray | tuple[float, ...]) -> PosteriorMomentumState:
        posterior = _finite_vector(prior, name="prior")
        return PosteriorMomentumState(self.binding_id, posterior, _finite_vector(np.zeros_like(posterior), name="initial_velocity"))

    def propose(
        self, state: PosteriorMomentumState, fresh_posterior: np.ndarray | tuple[float, ...], *, boundary: str,
    ) -> PosteriorMomentumProposal:
        _boundary(boundary, expected=self.advance_boundary)
        if state.binding_id != self.binding_id:
            raise ValueError("momentum may use only its own state")
        previous = _finite_vector(state.posterior, name="previous_posterior")
        velocity = _finite_vector(state.velocity, name="previous_velocity")
        fresh = _finite_vector(fresh_posterior, name="fresh_posterior")
        if previous.shape != velocity.shape or previous.shape != fresh.shape:
            raise ValueError("momentum posterior, velocity, and fresh_posterior must have the same shape")
        next_velocity = self.gamma * velocity + (1.0 - self.gamma) * (previous - fresh)
        next_posterior = previous - self.alpha * next_velocity
        return PosteriorMomentumProposal(
            self.binding_id,
            _finite_vector(next_posterior, name="momentum_posterior"),
            _finite_vector(next_velocity, name="momentum_velocity"),
        )

    def v2c_extrinsic(
        self, posterior: np.ndarray | tuple[float, ...], original_current_c2v: np.ndarray | tuple[float, ...],
    ) -> np.ndarray:
        """Subtract the unsmoothed current C2V contribution required by Algorithm 1."""
        belief = _finite_vector(posterior, name="posterior")
        c2v = _finite_vector(original_current_c2v, name="original_current_c2v")
        if belief.shape != c2v.shape:
            raise ValueError("posterior and original_current_c2v must have the same shape")
        return _finite_vector(belief - c2v, name="momentum_v2c")

    def commit(
        self, proposal: PosteriorMomentumProposal, state: PosteriorMomentumState | None = None,
    ) -> PosteriorMomentumState:
        if proposal.binding_id != self.binding_id:
            raise ValueError("momentum may commit only its own proposal")
        if state is not None and state.binding_id != self.binding_id:
            raise ValueError("momentum may not overwrite another binding's state")
        return PosteriorMomentumState(self.binding_id, proposal.posterior, proposal.velocity)

    def reset(self, prior: np.ndarray | tuple[float, ...]) -> PosteriorMomentumState:
        """Reset a new attempt or Relay leg to ``Q0=prior`` and ``g0=0``."""
        return self.initial_state(prior)


@dataclass(frozen=True, slots=True)
class MemoryState:
    """Committed decoder-visible posterior history owned by one memory binding."""

    binding_id: str
    posterior: np.ndarray | None = None


@dataclass(frozen=True, slots=True)
class MemoryProposal:
    """Validated next prior and the posterior to retain only after admission."""

    binding_id: str
    prior: np.ndarray
    posterior: np.ndarray


@dataclass(frozen=True, slots=True)
class MemoryCompositionState:
    """Private state slots keyed by the binding that owns each history."""

    histories: tuple[MemoryState, ...] = ()

    def by_binding(self) -> dict[str, MemoryState]:
        state = {item.binding_id: item for item in self.histories}
        if len(state) != len(self.histories):
            raise ValueError("memory composition state has duplicate binding ownership")
        return state


@dataclass(frozen=True, slots=True)
class MemoryCompositionProposal:
    """A complete ordered proposal that becomes visible only through commit."""

    value: np.ndarray
    proposals: tuple[MemoryProposal, ...]


@dataclass(frozen=True, slots=True)
class OrderedAffineMemoryComposition:
    """Execute declared affine-prior bindings in order with disjoint histories."""

    bindings: tuple[AffinePriorMemory, ...]

    def __post_init__(self) -> None:
        ids = tuple(binding.binding_id for binding in self.bindings)
        if not ids or len(ids) != len(set(ids)):
            raise ValueError("ordered memory composition requires distinct nonempty binding IDs")

    def propose(
        self,
        base_prior: np.ndarray | tuple[float, ...],
        state: MemoryCompositionState = MemoryCompositionState(),
    ) -> MemoryCompositionProposal:
        """Build every next value from immutable owner-local history, in order."""
        histories = state.by_binding()
        base = _finite_vector(base_prior, name="base_prior")
        value = base
        proposals: list[MemoryProposal] = []
        for binding in self.bindings:
            previous = histories.get(binding.binding_id)
            posterior = base if previous is None or previous.posterior is None else previous.posterior
            proposal = binding.propose(value, posterior)
            value = proposal.prior
            proposals.append(proposal)
        return MemoryCompositionProposal(value, tuple(proposals))

    def commit(
        self,
        proposal: MemoryCompositionProposal,
        state: MemoryCompositionState = MemoryCompositionState(),
    ) -> MemoryCompositionState:
        """Atomically replace only the slots that own this complete proposal."""
        if tuple(item.binding_id for item in proposal.proposals) != tuple(binding.binding_id for binding in self.bindings):
            raise ValueError("memory composition proposal does not match its declared binding order")
        next_state = state.by_binding()
        for binding, item in zip(self.bindings, proposal.proposals, strict=True):
            next_state[binding.binding_id] = binding.commit(item, next_state.get(binding.binding_id))
        return MemoryCompositionState(tuple(next_state[binding.binding_id] for binding in self.bindings))


_MEMORY_REFRESH_BOUNDARIES = frozenset({"attempt_start", "leg_start", "local_update", "source_iteration"})


@dataclass(frozen=True, slots=True)
class MemoryAssignmentState:
    """Immutable decoder-local generator state and its complete replay history."""

    derived_identity: str
    rng_state: str
    resolved: tuple[tuple[str, tuple[float, ...]], ...] = ()


@dataclass(frozen=True, slots=True)
class MemoryAssignmentResult:
    """One proposed-and-committed assignment transition or an exact rollback."""

    admitted: bool
    owner: bool
    replayed: bool
    state: MemoryAssignmentState
    values: tuple[float, ...]
    history_state: MemoryCompositionState
    schedule_cursor: tuple[int, ...]
    evidence: dict[str, Any] | None
    termination: Any = None


@dataclass(frozen=True, slots=True)
class MemoryAssignmentSpec:
    """Fixed, vector, or uniform per-variable memory assignment declaration.

    Assignment randomness is derived solely from a decoder identity and a
    purpose label.  It never accepts a physical sample RNG or sample payload.
    """

    mode: Literal["fixed", "vector", "uniform"]
    graph_sha256: str
    root_seed_identity: str
    refresh_boundary: Literal["attempt_start", "leg_start", "local_update", "source_iteration"]
    retain_history: bool
    value: float | None = None
    values: tuple[float, ...] | None = None
    low: float | None = None
    high: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.graph_sha256, str) or len(self.graph_sha256) != 64 or any(char not in "0123456789abcdef" for char in self.graph_sha256):
            raise ValueError("memory assignment graph_sha256 must be a SHA-256 identity")
        if not isinstance(self.root_seed_identity, str) or len(self.root_seed_identity) != 64 or any(char not in "0123456789abcdef" for char in self.root_seed_identity):
            raise ValueError("memory assignment root_seed_identity must be a SHA-256 identity")
        if self.refresh_boundary not in _MEMORY_REFRESH_BOUNDARIES:
            raise ValueError("memory assignment refresh boundary is unsupported")
        if self.mode == "fixed":
            if self.value is None or self.values is not None or self.low is not None or self.high is not None or not math.isfinite(self.value):
                raise ValueError("fixed memory assignment requires exactly one finite value")
        elif self.mode == "vector":
            if self.value is not None or not self.values or self.low is not None or self.high is not None or any(not math.isfinite(item) for item in self.values):
                raise ValueError("vector memory assignment requires exactly one nonempty finite vector")
        else:
            if self.value is not None or self.values is not None or self.low is None or self.high is None or not math.isfinite(self.low) or not math.isfinite(self.high) or self.low > self.high:
                raise ValueError("uniform memory assignment requires one ordered finite interval")

    def initial_state(self, *, configuration_identity: str, decoder_identity: str) -> MemoryAssignmentState:
        if not all(isinstance(value, str) and value for value in (configuration_identity, decoder_identity)):
            raise ValueError("configuration and decoder identities must be nonempty strings")
        material = {
            "purpose": "memory_assignment",
            "root_seed_identity": self.root_seed_identity,
            "assignment": self._identity_payload(),
            "configuration_identity": configuration_identity,
            "decoder_identity": decoder_identity,
        }
        derived = sha256(json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        rng = np.random.Generator(np.random.PCG64(int(derived[:32], 16)))
        return MemoryAssignmentState(derived, json.dumps(rng.bit_generator.state, sort_keys=True))

    def refresh(
        self,
        state: MemoryAssignmentState,
        *,
        boundary: str,
        replay_identity: str,
        variable_count: int,
        budgets: Any,
        budget_scope: str,
        history_state: MemoryCompositionState,
        schedule_cursor: tuple[int, ...],
        work: Any,
    ) -> MemoryAssignmentResult:
        """Reserve all declared work before generating or changing lifecycle state."""
        if not isinstance(state, MemoryAssignmentState):
            raise ValueError("memory refresh requires immutable MemoryAssignmentState")
        if boundary != self.refresh_boundary:
            raise ValueError("memory assignment may refresh only at its declared boundary")
        if not isinstance(replay_identity, str) or not replay_identity:
            raise ValueError("memory refresh requires a complete replay identity")
        if type(variable_count) is not int or variable_count < 1:
            raise ValueError("memory assignment variable_count must be a positive integer")
        if not isinstance(history_state, MemoryCompositionState) or not isinstance(schedule_cursor, tuple) or any(type(item) is not int or item < 0 for item in schedule_cursor):
            raise ValueError("memory refresh requires immutable history and a nonnegative schedule cursor")
        prior = dict(state.resolved)
        if replay_identity in prior:
            return MemoryAssignmentResult(
                True, False, True, state, prior[replay_identity], history_state, schedule_cursor,
                self._evidence(state, replay_identity, prior[replay_identity]),
            )
        reservation = budgets.reserve(
            budget_scope, work,
            leaf_id=f"{budget_scope}:memory-assignment:{state.derived_identity}:{replay_identity}",
        )
        if reservation is None:
            return MemoryAssignmentResult(
                False, False, False, state, (), history_state, schedule_cursor, None,
                getattr(budgets, "last_termination", None),
            )
        try:
            values, next_rng_state = self._resolve(state, replay_identity, variable_count)
            next_state = MemoryAssignmentState(
                state.derived_identity, next_rng_state, state.resolved + ((replay_identity, values),),
            )
            next_history = history_state if self.retain_history else MemoryCompositionState()
            evidence = self._evidence(next_state, replay_identity, values)
            reservation.commit_once()
            return MemoryAssignmentResult(True, True, False, next_state, values, next_history, schedule_cursor, evidence)
        except BaseException:
            if reservation.active:
                reservation.rollback()
            raise

    def _resolve(self, state: MemoryAssignmentState, replay_identity: str, variable_count: int) -> tuple[tuple[float, ...], str]:
        if self.mode == "fixed":
            assert self.value is not None
            return (float(self.value),) * variable_count, state.rng_state
        if self.mode == "vector":
            assert self.values is not None
            if len(self.values) != variable_count:
                raise ValueError("vector memory assignment length must equal graph variable_count")
            return tuple(float(item) for item in self.values), state.rng_state
        seed_material = f"{state.derived_identity}:memory_assignment:{replay_identity}".encode("utf-8")
        seed = int(sha256(seed_material).hexdigest()[:32], 16)
        rng = np.random.Generator(np.random.PCG64(seed))
        assert self.low is not None and self.high is not None
        values = tuple(float(item) for item in rng.uniform(self.low, self.high, size=variable_count))
        return values, json.dumps(rng.bit_generator.state, sort_keys=True)

    def _identity_payload(self) -> dict[str, Any]:
        return {
            "mode": self.mode, "graph_sha256": self.graph_sha256, "refresh_boundary": self.refresh_boundary,
            "retain_history": self.retain_history, "value": self.value, "values": self.values,
            "low": self.low, "high": self.high,
        }

    def _evidence(self, state: MemoryAssignmentState, replay_identity: str, values: tuple[float, ...]) -> dict[str, Any]:
        return {
            "purpose": "memory_assignment",
            "algorithm": "numpy.PCG64",
            "root_seed_identity": self.root_seed_identity,
            "decoder_seed_identity": state.derived_identity,
            "graph_sha256": self.graph_sha256,
            "generator": self._identity_payload(),
            "refresh_boundary": self.refresh_boundary,
            "retain_history": self.retain_history,
            "replay_identity": replay_identity,
            "resolved_values": list(values),
        }


class MemoryAssignmentLifecycle:
    """Single-owner transition coordinator for duplicate complete replay identities."""

    def __init__(self, assignment: MemoryAssignmentSpec) -> None:
        self.assignment = assignment
        self._lock = RLock()
        self._completed: dict[str, MemoryAssignmentResult] = {}

    def refresh(self, state: MemoryAssignmentState, **kwargs: Any) -> MemoryAssignmentResult:
        replay_identity = kwargs.get("replay_identity")
        if not isinstance(replay_identity, str) or not replay_identity:
            raise ValueError("memory lifecycle requires a complete replay identity")
        key_material = {
            "decoder_seed_identity": state.derived_identity,
            "replay_identity": replay_identity,
            "graph_sha256": self.assignment.graph_sha256,
            "boundary": kwargs.get("boundary"),
            "variable_count": kwargs.get("variable_count"),
        }
        key = sha256(json.dumps(key_material, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
        with self._lock:
            prior = self._completed.get(key)
            if prior is not None:
                return replace(prior, owner=False, replayed=True)
            result = self.assignment.refresh(state, **kwargs)
            if result.admitted:
                self._completed[key] = result
            return result


@dataclass(frozen=True, slots=True)
class AffinePriorMemory:
    """``(1-alpha) * base_prior + alpha * previous_posterior`` with no hidden inputs."""

    binding_id: str
    alpha: float
    target: str = "prior"
    advance_boundary: str = "source_iteration"
    registered_name: str = "affine-prior-memory-primitive-v1"

    def __post_init__(self) -> None:
        if not self.binding_id:
            raise ValueError("memory binding_id must be nonempty")
        if not isinstance(self.alpha, float) or not math.isfinite(self.alpha) or not 0.0 <= self.alpha <= 1.0:
            raise ValueError("affine prior alpha must be a finite value in [0, 1]")
        if self.target != "prior" or self.advance_boundary != "source_iteration":
            raise ValueError("the affine prior primitive targets prior at the source_iteration boundary")

    def propose(self, base_prior: np.ndarray | tuple[float, ...], previous_posterior: np.ndarray | tuple[float, ...]) -> MemoryProposal:
        base = _finite_vector(base_prior, name="base_prior")
        posterior = _finite_vector(previous_posterior, name="previous_posterior")
        if base.shape != posterior.shape:
            raise ValueError("base_prior and previous_posterior must have the same shape")
        prior = (1.0 - self.alpha) * base + self.alpha * posterior
        return MemoryProposal(self.binding_id, _finite_vector(prior, name="affine prior"), posterior)

    def commit(self, proposal: MemoryProposal, state: MemoryState | None = None) -> MemoryState:
        if proposal.binding_id != self.binding_id:
            raise ValueError("a memory binding may commit only its own proposal")
        if state is not None and state.binding_id != self.binding_id:
            raise ValueError("a memory binding may not overwrite another binding's state")
        return MemoryState(self.binding_id, proposal.posterior)


@dataclass(frozen=True, slots=True)
class EWAInitPriorMemory:
    """Chen EWAInit source alias over the common affine prior primitive."""

    binding_id: str
    alpha: float
    target: str = "prior"
    advance_boundary: str = "source_iteration"
    state_lifetime: str = "attempt"
    registered_name: str = "ewa-prior-memory-v1"
    fidelity: str = "source_equation_css_adaptation"

    def __post_init__(self) -> None:
        _coefficient(self.alpha, name="EWAInit alpha", upper_inclusive=True)
        if not self.binding_id or self.target != "prior" or self.advance_boundary != "source_iteration":
            raise ValueError("EWAInit requires a binding and the source prior/source_iteration target")

    @property
    def primitive(self) -> AffinePriorMemory:
        return AffinePriorMemory(self.binding_id, 1.0 - self.alpha)

    def initial_state(self, prior0: np.ndarray | tuple[float, ...]) -> MemoryState:
        return MemoryState(self.binding_id, _finite_vector(prior0, name="prior0"))

    def propose(
        self, prior0: np.ndarray | tuple[float, ...], previous_posterior: np.ndarray | tuple[float, ...], *, boundary: str,
    ) -> MemoryProposal:
        _boundary(boundary, expected=self.advance_boundary)
        return self.primitive.propose(prior0, previous_posterior)

    def commit(self, proposal: MemoryProposal, state: MemoryState | None = None) -> MemoryState:
        return self.primitive.commit(proposal, state)

    def reset(self, prior0: np.ndarray | tuple[float, ...]) -> MemoryState:
        return self.initial_state(prior0)


@dataclass(frozen=True, slots=True)
class RelayAffinePriorMemory:
    """Relay Mem-BP source alias over the same affine prior primitive."""

    binding_id: str
    gamma: float
    target: str = "prior"
    advance_boundary: str = "source_iteration"
    state_lifetime: str = "leg"
    registered_name: str = "relay-affine-prior-memory-v1"
    fidelity: str = "source_equation_css_adaptation"

    def __post_init__(self) -> None:
        _coefficient(self.gamma, name="Relay gamma", upper_inclusive=True)
        if not self.binding_id or self.target != "prior" or self.advance_boundary != "source_iteration":
            raise ValueError("Relay affine memory requires a binding and the source prior/source_iteration target")

    @property
    def primitive(self) -> AffinePriorMemory:
        return AffinePriorMemory(self.binding_id, self.gamma)

    def initial_state(self, initial_posterior: np.ndarray | tuple[float, ...]) -> MemoryState:
        return MemoryState(self.binding_id, _finite_vector(initial_posterior, name="initial_posterior"))

    def propose(
        self, prior0: np.ndarray | tuple[float, ...], previous_posterior: np.ndarray | tuple[float, ...], *, boundary: str,
    ) -> MemoryProposal:
        _boundary(boundary, expected=self.advance_boundary)
        return self.primitive.propose(prior0, previous_posterior)

    def commit(self, proposal: MemoryProposal, state: MemoryState | None = None) -> MemoryState:
        return self.primitive.commit(proposal, state)

    def reset(self, initial_posterior: np.ndarray | tuple[float, ...]) -> MemoryState:
        return self.initial_state(initial_posterior)
