"""Strict public admission tests for the externally supplied cluster policy."""

from __future__ import annotations

import importlib.util


def test_public_cluster_artifact_boundary_exists():
    """Cluster policy support begins with an explicit, non-executable artifact gate."""
    assert importlib.util.find_spec("bp_registry.canonical.cluster_schedule") is not None
