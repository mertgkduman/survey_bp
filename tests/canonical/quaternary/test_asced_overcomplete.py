"""Qualified aSCED overcomplete-map contracts."""

from __future__ import annotations

import importlib

import numpy as np


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
        row_origin_map=(("H_X", 0), ("H_Z", 0)),
        fidelity="canonical_adaptation",
    )
    assert isinstance(overcomplete, module.AscedOvercompleteMap)
    z_ext = np.array([1, 0], dtype=np.uint8)
    assert np.array_equal(module.map_overcomplete_syndrome(overcomplete, z_ext), np.array([1, 0, 1], dtype=np.uint8))
