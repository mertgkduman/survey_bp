"""Independent contract tests for the reusable Pauli algebra."""

from __future__ import annotations

import importlib.util


def test_public_pauli_algebra_module_is_available():
    """The reusable algebra is a public Phase 10 contract."""
    assert importlib.util.find_spec("bp_registry.quaternary.algebra") is not None
