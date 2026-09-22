"""Shared fixtures for the Phase 1 contract suite."""

import pytest


@pytest.fixture
def small_css_checks():
    """One X check and one Z check that commute over GF(2)."""
    import numpy as np

    return np.array([[1, 1, 0]], dtype=np.uint8), np.array([[0, 0, 1]], dtype=np.uint8)

