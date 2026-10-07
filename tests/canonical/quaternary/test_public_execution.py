"""Public contract for the Phase 10 joint-Pauli tracer."""

from __future__ import annotations

from pathlib import Path


def test_tracer_public_facade_exists():
    """The installed package must expose a dedicated joint-Pauli tracer."""
    root = Path(__file__).resolve().parents[3]
    assert (root / "src/bp_registry/quaternary/execution.py").is_file()
