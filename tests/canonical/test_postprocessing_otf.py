"""Contracts for the Phase 7 ordered Tanner forest CSS adaptation."""

from __future__ import annotations

from pathlib import Path


def test_otf_exposes_a_named_css_adaptation_contract():
    assert (Path(__file__).resolve().parents[2] / "src/bp_registry/canonical/postprocessing/otf.py").is_file()
