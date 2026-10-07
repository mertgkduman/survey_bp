"""Behavior contracts for canonical-adaptation CSS aSCED splitters."""

from __future__ import annotations

import numpy as np
import importlib.util

from bp_registry.css import CssCode


def _small_css() -> CssCode:
    """A CSS code with a deterministic, weight-two splitter in each role."""
    return CssCode(
        hx=np.asarray([[1, 1, 0, 0], [0, 0, 1, 1]], dtype=np.uint8),
        hz=np.asarray([[1, 1, 0, 0], [0, 0, 1, 1]], dtype=np.uint8),
    ).validate()


def test_constructs_ordered_canonical_adaptation_splitters() -> None:
    """A complete CSS batch carries deterministic rows and a qualified receipt."""
    assert importlib.util.find_spec("bp_registry.quaternary.asced") is not None, (
        "canonical splitter construction module is required"
    )
    from bp_registry.quaternary.asced import construct_splitter_batch

    batch = construct_splitter_batch(_small_css(), delta=2, row_weight=2, attempt_cap=16)

    assert batch.receipt.run_fidelity == "canonical_adaptation"
    assert tuple(row.role for row in batch.rows) == ("x", "z")
    assert batch.qualification.rank_growth == 2
    assert batch.qualification.detectable_rank == 2
    assert batch.receipt.terminal_status == "completed"
