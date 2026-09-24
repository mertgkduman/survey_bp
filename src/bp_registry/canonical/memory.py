"""Typed affine prior-memory proposals with explicit commit ownership."""

from __future__ import annotations

from dataclasses import dataclass
import math

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
        value = (1.0 - self.gamma) * old + self.gamma * fresh
        return TargetMemoryProposal(self.binding_id, self.target, _finite_vector(value, name="damped_v2c"), (fresh,))

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
