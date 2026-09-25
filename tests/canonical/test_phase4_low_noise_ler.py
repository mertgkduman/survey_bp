"""Statistical and identity contracts for the finite lower-noise campaign."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/run_phase4_low_noise_ler.py"
SPEC = importlib.util.spec_from_file_location("phase4_low_noise_ler", SCRIPT)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def test_frozen_design_and_distinct_matched_source_canonical_manifests():
    design = json.loads((ROOT / "data/evidence/phase4-low-noise-ler-design-v1.json").read_text())
    runner.validate_design(design)
    helper = runner._helper()
    base = json.loads((ROOT / "data/manifests/phase4-memory-relay-bb144.json").read_text())
    source = runner._manifest(helper, base, arm_name="source_relay", preset="source_procedure",
                              arm="canonical_relay_31", rate=.06, design_digest="a" * 64, max_shots=8192)
    canonical = runner._manifest(helper, base, arm_name="canonical_relay", preset="canonical_default",
                                 arm="canonical_relay_31", rate=.06, design_digest="a" * 64, max_shots=8192)
    assert source["randomness"]["physical_sample_identity"] == canonical["randomness"]["physical_sample_identity"]
    assert source["randomness"]["physical_sample_identity"] != base["randomness"]["physical_sample_identity"]
    assert source["policies"]["update"]["kind"] == "min_sum"
    assert canonical["policies"]["update"]["kind"] == "binary_spa"
    assert source["budgets"]["max_shots"] == canonical["budgets"]["max_shots"] == 8192
    assert source["relay"]["memory_tuning"] == canonical["relay"]["memory_tuning"]
    drifted = {**design, "precision": {**design["precision"], "no_recovery_policy": "conditional_ler"}}
    with pytest.raises(ValueError, match="no-recovery"):
        runner.validate_design(drifted)


def test_exact_sequential_precision_and_no_recovery_denominator():
    alpha = .05 / (6 * 2)
    assert runner.exact_interval(0, 256, alpha=alpha)[1] > 0
    rows = {shot: {"status": "completed", "selection_status": "frozen_decoder_visible_candidate" if shot >= 80 or shot < 70 else "unavailable_due_to_stopping",
                   "diagnostic_cell": "valid_wrong_logical" if shot < 70 else
                   "invalid_correct" if shot < 80 else "valid_correct"} for shot in range(256)}
    summary = runner.summarize(rows, planned_shots=256, alpha=alpha,
                               min_failures=50, max_relative_half_width=.35,
                               no_recovery_policy="count_as_failure")
    assert summary["primary"]["failures"] == 80
    assert summary["primary"]["denominator"] == 256
    assert summary["strict_logical_error"]["failures"] == 70
    assert summary["strict_logical_error"]["valid_syndrome_selected_denominator"] == 246
    assert summary["diagnostic_cells"]["invalid_correct"] == 10
    assert summary["diagnostic_cell_estimates"]["invalid_correct"]["denominator"] == 256
    assert sum(summary["diagnostic_cells"].values()) == 256
    assert summary["selection"]["no_selected_recovery"] == 10
    assert summary["primary"]["precision_met"] is True
    assert summary["strict_logical_error"]["precision_met"] is True
    assert summary["precision_met"] is True
    rows[255] = {"status": "incomplete_public_boundary", "outcome": None}
    incomplete = runner.summarize(rows, planned_shots=256, alpha=alpha,
                                  min_failures=50, max_relative_half_width=.35,
                                  no_recovery_policy="count_as_failure")
    assert incomplete["primary"]["precision_met"] is False
    assert incomplete["incomplete_shots"] == 1
    rows[255] = {"status": "completed", "selection_status": "frozen_decoder_visible_candidate", "diagnostic_cell": "invalid_correct"}
    with pytest.raises(ValueError, match="selected recovery"):
        runner.summarize(rows, planned_shots=256, alpha=alpha, min_failures=50,
                         max_relative_half_width=.35, no_recovery_policy="count_as_failure")


def test_four_diagnostic_cells_on_pinned_bb144_original_problem():
    from bp_registry.runner import canonical_public_shot_context

    manifest_path = ROOT / "data/manifests/phase4-memory-relay-bb144.json"
    context = canonical_public_shot_context(manifest_path, shot_id=0)
    code = context.code.validate()
    truth = context.hidden_truth.x.astype(np.uint8)
    logical_x = code.lx[0].astype(np.uint8)
    invalid_even = next(
        (np.eye(code.n, dtype=np.uint8)[j] for j in range(code.n)
         if np.any(code.hz[:, j]) and not np.any(code.lz[:, j])), None,
    )
    assert invalid_even is not None
    candidates = {
        "valid_correct": truth,
        "valid_wrong_logical": truth ^ logical_x,
        "invalid_correct": truth ^ invalid_even,
        "invalid_wrong_logical": truth ^ invalid_even ^ logical_x,
    }
    for expected, candidate in candidates.items():
        got = runner.classify_diagnostic_candidate(manifest_path, shot_id=0, candidate=candidate.tolist())
        assert got["diagnostic_cell"] == expected
    assert runner.classify_diagnostic_candidate(manifest_path, shot_id=0, candidate=None)["diagnostic_cell"] == "no_proposal"
