"""Executable all-path CSS aSCED controller contract."""

from __future__ import annotations

import importlib
import importlib.util
from dataclasses import replace

import numpy as np
import pytest

from bp_registry.css import CssCode
from bp_registry.quaternary.asced import construct_splitter_batch, materialize_asced_batches
from bp_registry.quaternary.kernel import ScalarLlrBp4Kernel
from bp_registry.quaternary.problems import QuaternaryOriginalProblem, compile_css_artifact


def _original() -> QuaternaryOriginalProblem:
    code = CssCode(
        np.asarray(((1, 1, 0, 0),), dtype=np.uint8),
        np.asarray(((0, 0, 1, 1),), dtype=np.uint8),
    ).validate()
    return QuaternaryOriginalProblem(
        "original-asced-controller", compile_css_artifact(code, source_artifact_identity="asced-controller-fixture"),
        np.asarray((0, 0), dtype=np.uint8),
    )


def _batch():
    code = CssCode(
        np.asarray(((1, 1, 0, 0),), dtype=np.uint8),
        np.asarray(((0, 0, 1, 1),), dtype=np.uint8),
    ).validate()
    qualified = construct_splitter_batch(code, delta=2, row_weight=1, attempt_cap=4)
    assert not hasattr(qualified, "terminal_status")
    return materialize_asced_batches(_original(), (qualified,), path_cap=4)


def test_all_paths_are_lsb_first_and_selection_uses_original_syndrome() -> None:
    assert importlib.util.find_spec("bp_registry.quaternary.asced") is not None
    module = importlib.import_module("bp_registry.quaternary.asced")
    controller = module.AscedController(module.AscedSpec(max_iterations=1, path_cap=4, max_total_bp_calls=4))
    result = controller.run(
        _original(), _batch(), np.full((4, 4), 0.25, dtype=np.float64),
        kernel=ScalarLlrBp4Kernel(),
    )
    assert len(result.paths) == 4
    assert tuple(path.virtual_bits for path in result.paths) == ((0, 0), (1, 0), (0, 1), (1, 1))
    assert all(path.extended_syndrome[0] == 0 and path.extended_syndrome[2] == 0 for path in result.paths)
    assert result.run_fidelity == "canonical_adaptation"
    assert result.termination in {"selected", "type_i_failure"}
    module.reconstruct_asced(module.AscedSpec(max_iterations=1, path_cap=4, max_total_bp_calls=4), _original(), _batch(), np.full((4, 4), 0.25), result, kernel=ScalarLlrBp4Kernel())


def test_asced_rejects_non_css_and_over_cap_before_paths() -> None:
    module = importlib.import_module("bp_registry.quaternary.asced")
    with pytest.raises(ValueError, match="path cardinality"):
        module.AscedController(module.AscedSpec(max_iterations=1, path_cap=3, max_total_bp_calls=3)).run(
            _original(), _batch(), np.full((4, 4), 0.25), kernel=ScalarLlrBp4Kernel(),
        )


def test_overcomplete_paths_require_the_exact_constructed_map_pair() -> None:
    from bp_registry.quaternary.asced_overcomplete import construct_overcomplete_map

    module = importlib.import_module("bp_registry.quaternary.asced")
    batches = _batch()
    created = construct_overcomplete_map(batches[0].qualified)
    assert not hasattr(created, "terminal_status")
    ordinary = module.AscedController(module.AscedSpec(max_iterations=1, path_cap=4, max_total_bp_calls=4)).run(
        _original(), batches, np.full((4, 4), 0.25), kernel=ScalarLlrBp4Kernel(),
    )
    result = module.AscedController(module.AscedSpec(max_iterations=1, path_cap=4, max_total_bp_calls=4)).run(
        _original(), batches, np.full((4, 4), 0.25), kernel=ScalarLlrBp4Kernel(),
        overcomplete={batches[0].batch_id: created},
    )
    assert len(result.paths) == 4
    assert {path.graph_identity for path in result.paths}.isdisjoint({path.graph_identity for path in ordinary.paths})
    assert all(path.overcomplete_map_receipt == created[1].receipt_sha256 for path in result.paths)
    with pytest.raises(ValueError, match="deterministic batch construction"):
        module.AscedController(module.AscedSpec(max_iterations=1, path_cap=4, max_total_bp_calls=4)).run(
            _original(), batches, np.full((4, 4), 0.25), kernel=ScalarLlrBp4Kernel(),
            overcomplete={batches[0].batch_id: (created[0], created[1].__class__(
                created[1].run_fidelity, "0" * 64, created[1].h_ext_sha256, created[1].h_ext_row_map_sha256,
                created[1].construction_profile_sha256, created[1].mapping_sha256, created[1].h_oc_sha256,
                created[1].row_order_sha256, created[1].qualification_sha256, created[1].receipt_sha256,
            ), created[2])},
        )
    with pytest.raises(ValueError, match="deterministic batch construction"):
        module.AscedController(module.AscedSpec(max_iterations=1, path_cap=4, max_total_bp_calls=4)).run(
            _original(), batches, np.full((4, 4), 0.25), kernel=ScalarLlrBp4Kernel(),
            overcomplete={batches[0].batch_id: (created[0], replace(created[1], receipt_sha256="0" * 64), created[2])},
        )
    with pytest.raises(ValueError, match="deterministic batch construction"):
        module.AscedController(module.AscedSpec(max_iterations=1, path_cap=4, max_total_bp_calls=4)).run(
            _original(), batches, np.full((4, 4), 0.25), kernel=ScalarLlrBp4Kernel(),
            overcomplete={batches[0].batch_id: (created[0], created[1], (replace(created[2][0], pairs_examined=99), created[2][1]))},
        )


def test_asced_total_bp_call_cap_fails_before_paths_start() -> None:
    module = importlib.import_module("bp_registry.quaternary.asced")
    with pytest.raises(ValueError, match="BP work"):
        module.AscedController(module.AscedSpec(max_iterations=1, path_cap=4, max_total_bp_calls=3)).run(
            _original(), _batch(), np.full((4, 4), 0.25), kernel=ScalarLlrBp4Kernel(),
        )
