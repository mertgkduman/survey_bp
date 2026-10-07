"""Contracts for source-defined scalar BP4 schedule policies."""

from __future__ import annotations

import importlib.util


def test_quaternary_source_schedule_module_is_available() -> None:
    """D-07 requires a dedicated schedule surface, never binary-name reuse."""
    assert importlib.util.find_spec("bp_registry.quaternary.schedules") is not None
