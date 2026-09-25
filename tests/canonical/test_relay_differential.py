"""Pinned-author Relay-BP qualification and differential contracts."""

from __future__ import annotations

import numpy as np
import pytest


def test_author_v022_adapter_is_available_for_strict_translation():
    """The approved source has an independently named adapter, not a fork alias."""
    import importlib.util

    try:
        module = importlib.util.find_spec("bp_registry.native.relay_v022")
    except ModuleNotFoundError:
        module = None
    assert module is not None


def test_source_identity_rejects_fork_and_requires_exact_author_pin():
    from bp_registry.native.relay_v022 import AUTHOR_COMMIT, RelayV022Adapter

    adapter = RelayV022Adapter()
    assert AUTHOR_COMMIT == "14cb31a18f9b9d7d099791b793e35b8a2951f8f3"
    with pytest.raises(ValueError, match="author commit"):
        adapter.verify_source_identity({"author_commit": "fork-head"})


def test_translation_accepts_only_decoder_visible_inputs_and_source_options():
    from bp_registry.native.relay_v022 import RelayV022Adapter

    adapter = RelayV022Adapter()
    translation = adapter.translate(
        check_matrix=np.asarray([[1, 1, 0], [0, 1, 1]], dtype=np.uint8),
        syndrome=np.asarray([1, 0], dtype=np.uint8),
        error_priors=np.asarray([0.1, 0.1, 0.1]),
        relay_settings={"pre_iter": 2, "num_sets": 1, "set_max_iter": 2},
        seed=7,
        numerical_profile="f64",
    )

    assert translation["decoder_class"] == "RelayDecoderF64"
    assert translation["seed"] == 7
    assert translation["syndrome"].tolist() == [1, 0]
    with pytest.raises(TypeError):
        adapter.translate(  # type: ignore[call-arg]
            check_matrix=np.eye(2, dtype=np.uint8), syndrome=np.zeros(2, dtype=np.uint8),
            error_priors=np.full(2, 0.1), relay_settings={}, seed=0,
            numerical_profile="f64", hidden_truth=np.zeros(2, dtype=np.uint8),
        )


def test_unmodified_author_record_is_required_for_native_execution(tmp_path):
    from bp_registry.native.relay_v022 import RelayV022Adapter

    adapter = RelayV022Adapter(source_record=tmp_path / "missing-source.json")
    with pytest.raises(RuntimeError, match="qualification"):
        adapter.run(
            check_matrix=np.eye(2, dtype=np.uint8), syndrome=np.zeros(2, dtype=np.uint8),
            error_priors=np.full(2, 0.1), relay_settings={}, seed=0, numerical_profile="f64",
        )


def test_numerical_profile_is_explicit_and_unspecified_precision_is_not_faithful():
    from bp_registry.native.relay_v022 import RelayV022Adapter

    adapter = RelayV022Adapter()
    with pytest.raises(ValueError, match="numerical_profile"):
        adapter.translate(
            check_matrix=np.eye(2, dtype=np.uint8), syndrome=np.zeros(2, dtype=np.uint8),
            error_priors=np.full(2, 0.1), relay_settings={}, seed=0, numerical_profile="paper-faithful",
        )

