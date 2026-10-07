"""Independent probability-vector and exact references for tiny BP4 graphs.

These helpers deliberately use probability arithmetic and parity convolution.  They
must not import the production quaternary numerical/kernel modules: their job is to
detect mistakes in the scalar log-domain implementation.
"""

from __future__ import annotations

import importlib.util
from itertools import product

import numpy as np

from bp_registry.quaternary.algebra import anticommutes


_STATES = np.arange(4, dtype=np.uint8)


def _normalize(values: np.ndarray) -> np.ndarray:
    result = np.asarray(values, dtype=np.float64)
    total = float(result.sum())
    if not np.isfinite(total) or total <= 0.0:
        raise ValueError("oracle probability mass must be finite and positive")
    return result / total


def _parity_message(incoming: list[np.ndarray], labels: list[int], syndrome: int, target_label: int) -> np.ndarray:
    """Conventional BP4 check-to-variable factor message by explicit parity sums."""
    result = np.zeros(4, dtype=np.float64)
    for target in _STATES:
        wanted = int(syndrome) ^ int(anticommutes(target_label, int(target)))
        mass = 0.0
        for assignment in product(range(4), repeat=len(incoming)):
            parity = 0
            weight = 1.0
            for value, distribution, label in zip(assignment, incoming, labels, strict=True):
                parity ^= int(anticommutes(label, value))
                weight *= float(distribution[value])
            if parity == wanted:
                mass += weight
        result[target] = mass
    return _normalize(result)


def vector_bp4_one_check(priors: np.ndarray, labels: np.ndarray, syndrome: int) -> tuple[np.ndarray, np.ndarray]:
    """One flooding sweep for one check, returning factor messages and marginals."""
    priors = np.asarray(priors, dtype=np.float64)
    labels = np.asarray(labels, dtype=np.uint8)
    if priors.ndim != 2 or priors.shape[1] != 4 or labels.shape != (priors.shape[0],):
        raise ValueError("oracle inputs require one four-state prior per labeled edge")
    c2v = np.empty_like(priors)
    for target in range(priors.shape[0]):
        excluded = [priors[index] for index in range(priors.shape[0]) if index != target]
        excluded_labels = [int(labels[index]) for index in range(priors.shape[0]) if index != target]
        c2v[target] = _parity_message(excluded, excluded_labels, syndrome, int(labels[target]))
    marginals = np.asarray([_normalize(prior * message) for prior, message in zip(priors, c2v, strict=True)])
    return c2v, marginals


def exact_one_check(priors: np.ndarray, labels: np.ndarray, syndrome: int) -> np.ndarray:
    """Exact posterior enumeration for a single Pauli parity check."""
    priors = np.asarray(priors, dtype=np.float64)
    labels = np.asarray(labels, dtype=np.uint8)
    posterior = np.zeros_like(priors)
    normalizer = 0.0
    for assignment in product(range(4), repeat=priors.shape[0]):
        parity = 0
        weight = 1.0
        for index, state in enumerate(assignment):
            parity ^= int(anticommutes(int(labels[index]), state))
            weight *= float(priors[index, state])
        if parity == syndrome:
            normalizer += weight
            for index, state in enumerate(assignment):
                posterior[index, state] += weight
    if normalizer <= 0.0:
        raise ValueError("syndrome has zero exact probability")
    return posterior / normalizer


def test_quaternary_numerical_profile_is_available() -> None:
    """The dedicated production numerical module is part of QBP-01's contract."""
    assert importlib.util.find_spec("bp_registry.quaternary.numerics") is not None, (
        "bp_registry.quaternary.numerics is absent"
    )


def test_independent_vector_oracle_normalizes_four_state_marginals() -> None:
    priors = np.asarray(((0.70, 0.10, 0.15, 0.05), (0.40, 0.30, 0.10, 0.20)), dtype=np.float64)
    messages, marginals = vector_bp4_one_check(priors, np.asarray((1, 3), dtype=np.uint8), syndrome=1)
    assert np.allclose(messages.sum(axis=1), 1.0)
    assert np.allclose(marginals.sum(axis=1), 1.0)


def test_vector_oracle_matches_exact_enumeration_on_a_tree() -> None:
    priors = np.asarray(((0.55, 0.10, 0.25, 0.10), (0.25, 0.30, 0.20, 0.25)), dtype=np.float64)
    _messages, marginals = vector_bp4_one_check(priors, np.asarray((2, 1), dtype=np.uint8), syndrome=0)
    assert np.allclose(marginals, exact_one_check(priors, np.asarray((2, 1), dtype=np.uint8), syndrome=0), atol=1e-14)
