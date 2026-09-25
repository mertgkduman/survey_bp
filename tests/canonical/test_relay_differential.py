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
        adapter.verify_source_identity({
            "author_repository": "https://github.com/trmue/relay.git",
            "author_tag": "v0.2.2", "author_commit": "fork-head",
        })


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


def test_observer_patch_is_based_on_exact_author_source():
    from bp_registry.native.relay_v022 import observer_patch_identity

    identity = observer_patch_identity()
    assert identity["base_commit"] == "14cb31a18f9b9d7d099791b793e35b8a2951f8f3"
    assert len(identity["patch_sha256"]) == 64


def test_observer_equivalence_requires_all_terminal_fields():
    from bp_registry.native.relay_v022 import assert_terminal_equivalence

    terminal = {
        "candidate": [1, 0], "success": True, "score": 0.1,
        "aggregate_iterations": 2, "final_posterior": [0.2, -0.2], "log_output": "",
    }
    assert_terminal_equivalence(terminal, dict(terminal)) is True
    with pytest.raises(ValueError, match="aggregate_iterations"):
        assert_terminal_equivalence(terminal, dict(terminal, aggregate_iterations=3))


def test_bb144_observer_record_keeps_unavailable_facts_explicit():
    from bp_registry.native.relay_v022 import unavailable_native_facts

    facts = unavailable_native_facts()
    assert facts["gamma"] == "unavailable: observer would change decoder behavior"
    assert facts["edge_work"] == "unavailable: observer would change decoder behavior"


def test_bb144_observer_record_compares_exact_author_terminal_fields():
    import json
    from pathlib import Path

    record = json.loads(Path("data/evidence/relay-v0.2.2-source.json").read_text())
    comparison = record["observer_patch"]["bb144_terminal_equivalence"]
    assert comparison["passed"] is True
    assert comparison["timeout_seconds"] == 60
    assert comparison["fields"] == ["candidate", "success", "score", "aggregate_iterations", "final_posterior", "log_output"]
    assert comparison["unmodified"]["candidate_sha256"] == comparison["patched"]["candidate_sha256"]
    assert comparison["unmodified"]["posterior_sha256"] == comparison["patched"]["posterior_sha256"]
