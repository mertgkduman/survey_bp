"""Qualified aSCED overcomplete-map contracts."""

from __future__ import annotations

import importlib
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pytest

from bp_registry.quaternary.asced import ConstructedSplitterReceipt, SplitterSearchReceipt


FIXTURE = Path("data/fixtures/quaternary/asced-gb46-canonical-fixture.json")
MAP_FIXTURE = Path("data/fixtures/quaternary/asced-gb46-canonical-overcomplete-map.json")


def _digest(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _splitter_receipt(payload: dict[str, object]) -> ConstructedSplitterReceipt:
    receipt = payload["receipt"]
    assert isinstance(receipt, dict)
    searches = tuple(
        SplitterSearchReceipt(
            item["role"], item["attempt_cap"], item["candidates_examined"], item["accepted_ordinal"],
            item["rejected_cycle"], item["rejected_rank"], item["rejected_detectability"],
        )
        for item in receipt["search_receipts"]
    )
    return ConstructedSplitterReceipt(
        receipt["run_fidelity"], receipt["constructor_identity"], tuple(receipt["source_component_ids"]),
        receipt["artifact_sha256"], receipt["profile_sha256"], receipt["splitter_sha256"], receipt["h_ext_sha256"],
        receipt["terminal_status"], searches, receipt["constructed_receipt_sha256"],
    )


def test_generic_matrix_relation_and_syndrome_mapping() -> None:
    """A qualified GF(2) map applies identically to checks and syndromes."""
    try:
        module = importlib.import_module("bp_registry.quaternary.asced_overcomplete")
    except ModuleNotFoundError:
        module = None
    assert module is not None, "qualified aSCED overcomplete mapping module must exist"
    h_ext = np.array([[1, 0, 1], [0, 1, 1]], dtype=np.uint8)
    mapping = np.array([[1, 0], [0, 1], [1, 1]], dtype=np.uint8)
    h_oc = (mapping @ h_ext) % 2
    overcomplete = module.qualify_overcomplete_map(
        h_ext=h_ext,
        h_oc=h_oc,
        mapping=mapping,
        row_order=("H_X", "T_X", "H_Z", "T_Z"),
        row_origin_map=(("x", "original", 0), ("z", "original", 0)),
        fidelity="canonical_adaptation",
    )
    assert isinstance(overcomplete, module.AscedOvercompleteMap)
    z_ext = np.array([1, 0], dtype=np.uint8)
    assert np.array_equal(module.map_overcomplete_syndrome(overcomplete, z_ext), np.array([1, 0, 1], dtype=np.uint8))


def test_gb46_constructed_splitter_binding_exact_h_ext_digest_deterministic_nontrivial_m_search_order() -> None:
    """The canonical map consumes only the repaired Plan 10-10 receipt bytes."""
    from bp_registry.quaternary.asced_overcomplete import OvercompleteSearchExhausted, construct_overcomplete_map

    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    result = construct_overcomplete_map(
        h_ext=np.asarray(payload["h_ext"], dtype=np.uint8), h_ext_row_map=tuple(tuple(item) for item in payload["h_ext_row_map"]),
        constructed_splitter_receipt=_splitter_receipt(payload), pair_cap=1000,
    )
    assert not isinstance(result, OvercompleteSearchExhausted)
    overcomplete, receipt, searches = result
    assert overcomplete.mapping.shape == (48, 46)
    assert np.array_equal(overcomplete.mapping[:46], np.eye(46, dtype=np.uint8))
    assert receipt.run_fidelity == "canonical_adaptation"
    assert receipt.constructed_splitter_receipt_sha256 == payload["receipt"]["constructed_receipt_sha256"]
    assert tuple(search.role for search in searches) == ("x", "z")
    assert all(search.accepted_pair is not None and search.accepted_image is not None for search in searches)


def test_all_virtual_bits_syndrome_mapping_preserves_delta_two_paths() -> None:
    """Every [s_X,g_X,s_Z,g_Z] virtual path maps through the same M."""
    from bp_registry.quaternary.asced_overcomplete import (
        OvercompleteSearchExhausted, assemble_extended_syndrome, construct_overcomplete_map, map_overcomplete_syndrome,
    )

    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    result = construct_overcomplete_map(
        h_ext=np.asarray(payload["h_ext"], dtype=np.uint8), h_ext_row_map=tuple(tuple(item) for item in payload["h_ext_row_map"]),
        constructed_splitter_receipt=_splitter_receipt(payload), pair_cap=1000,
    )
    assert not isinstance(result, OvercompleteSearchExhausted)
    overcomplete, _receipt, _searches = result
    for g_x in (0, 1):
        for g_z in (0, 1):
            s_x = np.zeros(22, dtype=np.uint8)
            s_z = np.zeros(22, dtype=np.uint8)
            s_x[0], s_z[0] = 1, 1
            z_ext = assemble_extended_syndrome(
                overcomplete, s_x=s_x, g_x=np.array([g_x], dtype=np.uint8),
                s_z=s_z, g_z=np.array([g_z], dtype=np.uint8),
            )
            expected = (overcomplete.mapping @ z_ext) % 2
            assert np.array_equal(map_overcomplete_syndrome(overcomplete, z_ext), expected)
    with pytest.raises(ValueError, match="s_X"):
        assemble_extended_syndrome(
            overcomplete, s_x=np.zeros(1, dtype=np.uint8), g_x=np.zeros(22, dtype=np.uint8),
            s_z=np.zeros(22, dtype=np.uint8), g_z=np.zeros(1, dtype=np.uint8),
        )


def test_immutable_tampered_h_ext_or_block_permutation_rejected() -> None:
    """Receipt bytes and exact typed order prevent graph and observation substitution."""
    from bp_registry.quaternary.asced_overcomplete import construct_overcomplete_map

    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    h_ext = np.asarray(payload["h_ext"], dtype=np.uint8)
    h_ext[0, 0] ^= 1
    with pytest.raises(ValueError, match="receipt mismatch"):
        construct_overcomplete_map(
            h_ext=h_ext, h_ext_row_map=tuple(tuple(item) for item in payload["h_ext_row_map"]),
            constructed_splitter_receipt=_splitter_receipt(payload), pair_cap=1000,
        )
    swapped = tuple(tuple(item) for item in payload["h_ext_row_map"])
    swapped = swapped[:22] + (swapped[-1],) + swapped[23:-1] + (swapped[22],)
    with pytest.raises(ValueError, match="block order"):
        construct_overcomplete_map(
            h_ext=np.asarray(payload["h_ext"], dtype=np.uint8), h_ext_row_map=swapped,
            constructed_splitter_receipt=_splitter_receipt(payload), pair_cap=1000,
        )


def test_search_cap_exhaustion_has_no_runnable_partial_map() -> None:
    """A bounded search reports exhaustion instead of returning only identity rows."""
    from bp_registry.quaternary.asced_overcomplete import OvercompleteSearchExhausted, construct_overcomplete_map

    raw = np.array([[1, 0, 0], [0, 1, 0], [3, 0, 0], [0, 3, 0]], dtype=np.uint8)
    row_map = (("x", "original", 0), ("x", "splitter", 0), ("z", "original", 0), ("z", "splitter", 0))
    h_ext_sha = _digest({"rows": raw.tolist(), "row_map": [list(item) for item in row_map]})
    source = ConstructedSplitterReceipt(
        "canonical_adaptation", "test", ("source:x", "source:z"), "a" * 64, "b" * 64, "c" * 64,
        h_ext_sha, "completed", (), "d" * 64,
    )
    exhausted = construct_overcomplete_map(h_ext=raw, h_ext_row_map=row_map, constructed_splitter_receipt=source, pair_cap=1)
    assert isinstance(exhausted, OvercompleteSearchExhausted)
    assert exhausted.terminal_status == "exhausted"


def test_comparison_only_reject_unmatched_source_map_from_execution() -> None:
    """Pinned source triplets stay auditable without becoming canonical maps."""
    from bp_registry.quaternary.asced_overcomplete import map_overcomplete_syndrome, qualify_overcomplete_map

    h_ext = np.array([[1, 0], [0, 1]], dtype=np.uint8)
    comparison = qualify_overcomplete_map(
        h_ext=h_ext, h_oc=h_ext, mapping=np.eye(2, dtype=np.uint8), row_order=("H_X", "T_X", "H_Z", "T_Z"),
        row_origin_map=(("x", "original", 0), ("z", "original", 0)), fidelity="source_comparison",
    )
    assert comparison.comparison_only
    with pytest.raises(ValueError, match="comparison"):
        map_overcomplete_syndrome(comparison, np.array([1, 0], dtype=np.uint8))


def test_constructed_map_receipt_matches_the_frozen_gb46_fixture() -> None:
    """The checked-in canonical map is a replayable result, never a source map."""
    from bp_registry.quaternary.asced_overcomplete import OvercompleteSearchExhausted, construct_overcomplete_map

    splitter_payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    map_payload = json.loads(MAP_FIXTURE.read_text(encoding="utf-8"))
    result = construct_overcomplete_map(
        h_ext=np.asarray(splitter_payload["h_ext"], dtype=np.uint8),
        h_ext_row_map=tuple(tuple(item) for item in splitter_payload["h_ext_row_map"]),
        constructed_splitter_receipt=_splitter_receipt(splitter_payload), pair_cap=1000,
    )
    assert not isinstance(result, OvercompleteSearchExhausted)
    overcomplete, receipt, searches = result
    assert map_payload["run_fidelity"] == "canonical_adaptation"
    assert map_payload["constructed_splitter_receipt_sha256"] == splitter_payload["receipt"]["constructed_receipt_sha256"]
    assert map_payload["mapping"] == overcomplete.mapping.tolist()
    assert map_payload["h_oc"] == overcomplete.h_oc.tolist()
    assert map_payload["search_receipts"] == [
        {"role": item.role, "pair_cap": item.pair_cap, "pairs_examined": item.pairs_examined,
         "accepted_pair": list(item.accepted_pair) if item.accepted_pair else None,
         "accepted_image": list(item.accepted_image) if item.accepted_image else None,
         "rejected_zero": item.rejected_zero, "rejected_existing": item.rejected_existing,
         "terminal_status": item.terminal_status}
        for item in searches
    ]
    assert map_payload["receipt"] == {
        "run_fidelity": receipt.run_fidelity,
        "constructed_splitter_receipt_sha256": receipt.constructed_splitter_receipt_sha256,
        "h_ext_sha256": receipt.h_ext_sha256,
        "h_ext_row_map_sha256": receipt.h_ext_row_map_sha256,
        "construction_profile_sha256": receipt.construction_profile_sha256,
        "mapping_sha256": receipt.mapping_sha256,
        "h_oc_sha256": receipt.h_oc_sha256,
        "row_order_sha256": receipt.row_order_sha256,
        "qualification_sha256": receipt.qualification_sha256,
        "receipt_sha256": receipt.receipt_sha256,
    }


def test_gb46_and_toric_source_identities_are_comparison_only() -> None:
    """Pinned author triplets are retained as auditable, non-executable comparisons."""
    comparison = json.loads(Path("tests/canonical/quaternary/fixtures/asced-overcomplete.json").read_text(encoding="utf-8"))
    assert comparison["canonical_construction"]["run_fidelity"] == "canonical_adaptation"
    for fixture in comparison["source_comparisons"]:
        assert fixture["comparison_only"] and fixture["execution_status"] == "comparison_only"
        assert fixture["gf2_relation"] == "verified_on_pinned_checkout"
        assert fixture["h_ext"]["shape"][0] == fixture["mapping"]["shape"][1]
        assert fixture["h_oc"]["shape"] == [fixture["mapping"]["shape"][0], fixture["h_ext"]["shape"][1]]
        assert all(len(fixture[key]["sha256"]) == 64 for key in ("h_ext", "mapping", "h_oc"))
