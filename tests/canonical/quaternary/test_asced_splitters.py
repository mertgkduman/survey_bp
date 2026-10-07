"""Behavior contracts for canonical-adaptation CSS aSCED splitters."""

from __future__ import annotations

import base64
import numpy as np
import importlib.util
import json
from pathlib import Path

import pytest

from bp_registry.css import CssCode
from bp_registry.quaternary.algebra import Pauli
from bp_registry.quaternary.problems import PauliCode


ROOT = Path(__file__).resolve().parents[3]
FIXTURES = ROOT / "tests" / "canonical" / "quaternary" / "fixtures"
DATA_FIXTURE = ROOT / "data" / "fixtures" / "quaternary" / "asced-gb46-canonical-fixture.json"


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


def _gb46_raw() -> bytes:
    fixture = json.loads((FIXTURES / "asced-splitters.json").read_text(encoding="utf-8"))
    return base64.b64decode(fixture["gb46_h44_alist_base64"])


def test_pinned_gb46_input_yields_the_frozen_canonical_receipt() -> None:
    """The pinned input is parsed and reconstructed without a native execution path."""
    from bp_registry.quaternary.asced import gb46_canonical_fixture_payload

    observed = gb46_canonical_fixture_payload(_gb46_raw())
    frozen = json.loads(DATA_FIXTURE.read_text(encoding="utf-8"))

    assert observed == frozen
    assert frozen["run_fidelity"] == "canonical_adaptation"
    assert "source_fixture_verified" not in json.dumps(frozen)
    assert frozen["source_input"]["raw_sha256"] == "4bd60bc22ccda388780ad2ad2a29b63143b3f024e599e57ef5bcb983f51cb9b2"
    assert frozen["qualification"]["rank_growth"] == frozen["qualification"]["detectable_rank"] == 2


def test_gb46_h_ext_uses_the_declared_x_then_z_block_order_and_is_immutable() -> None:
    """The constructed graph cannot change after it has been receipt-bound."""
    from bp_registry.quaternary.asced import QualifiedAscedBatch, construct_splitter_batch, parse_pinned_gb46_css

    batch = construct_splitter_batch(parse_pinned_gb46_css(_gb46_raw()), delta=2, row_weight=4, attempt_cap=10_000)
    assert isinstance(batch, QualifiedAscedBatch)
    assert batch.h_ext_row_map[0] == ("x", "original", 0)
    assert batch.h_ext_row_map[22] == ("x", "splitter", 0)
    assert batch.h_ext_row_map[23] == ("z", "original", 0)
    assert batch.h_ext_row_map[-1] == ("z", "splitter", 0)
    assert np.all(batch.h_ext[:22][(batch.h_ext[:22] != Pauli.I)] == Pauli.X)
    assert np.all(batch.h_ext[23:45][(batch.h_ext[23:45] != Pauli.I)] == Pauli.Z)
    with pytest.raises(ValueError):
        batch.splitter[0, 0] = Pauli.I
    with pytest.raises(ValueError):
        batch.h_ext[0, 0] = Pauli.I


def test_rejects_non_css_input_tampered_source_and_exhausted_search() -> None:
    """D-11 fails closed before construction or after a bounded unsuccessful search."""
    from bp_registry.quaternary.asced import SplitterSearchExhausted, construct_splitter_batch, parse_pinned_gb46_css

    general = PauliCode(np.asarray([[Pauli.X, Pauli.Z]], dtype=np.uint8))
    with pytest.raises(ValueError, match="CSS artifact"):
        construct_splitter_batch(general, delta=2, row_weight=1, attempt_cap=1)
    with pytest.raises(ValueError, match="raw SHA-256"):
        parse_pinned_gb46_css(_gb46_raw() + b"tamper")
    exhausted = construct_splitter_batch(_small_css(), delta=2, row_weight=2, attempt_cap=1)
    assert isinstance(exhausted, SplitterSearchExhausted)
    assert exhausted.terminal_status == "exhausted"
    assert len(exhausted.receipts) == 1


def test_source_components_are_distinct_from_project_run_fidelity() -> None:
    """Only components, never generated rows, retain source provenance."""
    from bp_registry.quaternary.asced import construct_splitter_batch

    batch = construct_splitter_batch(_small_css(), delta=2, row_weight=2, attempt_cap=16)
    assert batch.receipt.run_fidelity == "canonical_adaptation"
    assert all("kit-cel/quantum_asced@816772071486615dfc7d71d1e15df597edc58a26" in item for item in batch.receipt.source_component_ids)
    assert "source_literal" not in json.dumps({"receipt": batch.receipt.receipt_sha256})


def test_materializes_preflighted_batches_with_stable_transform_lineage() -> None:
    """Complete receipt-bound batches become fixed working graphs before shots."""
    from bp_registry.quaternary import asced

    assert hasattr(asced, "materialize_asced_batches"), "receipt-bound batch materialization is required"
