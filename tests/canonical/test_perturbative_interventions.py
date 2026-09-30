"""Syndrome-transform certificates and original-check boundary fixtures."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest


def test_syndrome_certificate_lift_and_original_invalid_without_it():
    from bp_registry.canonical.problems import OriginalProblem
    from bp_registry.canonical.transformations import lift_candidate, transform_syndrome

    original = OriginalProblem(
        "original-syndrome-fixture", np.zeros((1, 2), dtype=np.uint8),
        np.asarray([[1, 1]], dtype=np.uint8), np.asarray([1], dtype=np.uint8),
    )
    working, certificate = transform_syndrome(original, np.asarray([1, 0], dtype=np.uint8))
    assert np.array_equal(working.syndrome, np.asarray([0], dtype=np.uint8))
    raw = np.asarray([0, 0], dtype=np.uint8)
    assert np.array_equal((original.hz @ raw) % 2, [0])
    lifted = lift_candidate(working, certificate, raw)
    assert lifted.working_valid and lifted.original_valid
    assert np.array_equal(lifted.candidate, np.asarray([1, 0], dtype=np.uint8))
    with pytest.raises(ValueError):
        lift_candidate(working, replace(certificate, test_vector=(0, 0)), raw)
    with pytest.raises(ValueError):
        transform_syndrome(original, row_mask=np.asarray([1], dtype=np.uint8))
