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

    def __post_init__(self) -> None:
        if not self.binding_id:
            raise ValueError("memory binding_id must be nonempty")
        if not isinstance(self.alpha, float) or not math.isfinite(self.alpha) or not 0.0 <= self.alpha <= 1.0:
            raise ValueError("affine prior alpha must be a finite value in [0, 1]")

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
