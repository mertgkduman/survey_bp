"""Independent algebra fixtures for exact shortening used by impulse adaptations."""

from __future__ import annotations

from dataclasses import replace
from itertools import product

import numpy as np
import pytest


def _original(h, s):
    from bp_registry.canonical.problems import OriginalProblem

    matrix = np.asarray(h, dtype=np.uint8)
    return OriginalProblem("original-shortening-fixture", np.zeros((1, matrix.shape[1]), dtype=np.uint8), matrix, np.asarray(s, dtype=np.uint8))


def test_shortening_lift_exhaustive_matches_independent_gf2_oracle():
    from bp_registry.canonical.transformations import lift_candidate, transform_fixed_coordinates

    cases = 0
    for flat in product((0, 1), repeat=6):
        h = np.asarray(flat, dtype=np.uint8).reshape(2, 3)
        for syndrome in product((0, 1), repeat=2):
            original = _original(h, syndrome)
            for mask in product((0, 1), repeat=3):
                fixed = tuple(i for i, flag in enumerate(mask) if flag)
                free = tuple(i for i in range(3) if i not in fixed)
                for assignment in product((0, 1), repeat=len(fixed)):
                    working, certificate = transform_fixed_coordinates(original, fixed, assignment)
                    assert working.column_map == free
                    assert working.row_map == (0, 1)
                    for y in product((0, 1), repeat=len(free)):
                        lifted = lift_candidate(working, certificate, np.asarray(y, dtype=np.uint8))
                        expected = np.zeros(3, dtype=np.uint8)
                        expected[list(fixed)] = assignment
                        expected[list(free)] = y
                        assert np.array_equal(lifted.candidate, expected)
                        assert lifted.working_valid == bool(np.array_equal((working.check_matrix @ y) % 2, working.syndrome))
                        assert lifted.original_valid == bool(np.array_equal((h @ expected) % 2, syndrome))
                        assert lifted.working_valid == lifted.original_valid
                        cases += 1
    assert cases == 16384


def test_all_fixed_success_and_contradiction_and_bad_lift_certificate():
    from bp_registry.canonical.transformations import lift_candidate, transform_fixed_coordinates

    original = _original([[1]], [1])
    good, good_map = transform_fixed_coordinates(original, (0,), (1,))
    bad, bad_map = transform_fixed_coordinates(original, (0,), (0,))
    assert good.check_matrix.shape == (1, 0)
    assert lift_candidate(good, good_map, np.empty(0, dtype=np.uint8)).original_valid
    denied = lift_candidate(bad, bad_map, np.empty(0, dtype=np.uint8))
    assert not denied.working_valid and not denied.original_valid
    assert denied.reason == "contradictory_empty_check"
    with pytest.raises(ValueError):
        lift_candidate(good, replace(good_map, fixed_values=(0,)), np.empty(0, dtype=np.uint8))
    with pytest.raises(ValueError):
        lift_candidate(good, good_map, np.asarray([1], dtype=np.uint8))


def test_shortening_idempotent_and_concurrent_order_invariant():
    from concurrent.futures import ThreadPoolExecutor
    from bp_registry.canonical.transformations import lift_candidate, transform_fixed_coordinates

    original = _original([[1, 1, 0], [0, 1, 1]], [1, 0])
    first = transform_fixed_coordinates(original, (1,), (1,))
    second = transform_fixed_coordinates(original, (1,), (1,))
    assert first[0].lineage_id == second[0].lineage_id
    assert first[1].digest == second[1].digest
    candidates = [np.asarray(bits, dtype=np.uint8) for bits in product((0, 1), repeat=2)]
    with ThreadPoolExecutor(max_workers=3) as executor:
        shuffled = list(executor.map(lambda y: lift_candidate(*first, y), reversed(candidates)))
    serial = [lift_candidate(*first, y) for y in candidates]
    assert sorted(tuple(item.candidate) for item in shuffled) == sorted(tuple(item.candidate) for item in serial)
