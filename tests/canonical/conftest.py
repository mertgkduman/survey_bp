"""Small deterministic graph values shared by canonical schedule contracts."""

from __future__ import annotations

import numpy as np
import pytest


@pytest.fixture
def two_by_two_edges() -> list[tuple[int, int]]:
    """A complete two-check/two-variable graph in deliberately canonical order."""
    return [(0, 0), (0, 1), (1, 0), (1, 1)]


@pytest.fixture
def flooding_old_messages() -> np.ndarray:
    """A finite old v2c snapshot whose signs distinguish both buffer phases."""
    return np.array([1.5, -0.7, 0.2, 2.0], dtype=np.float64)
