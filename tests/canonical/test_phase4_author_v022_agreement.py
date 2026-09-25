"""Source-matched memory draws and paired agreement accounting."""
from __future__ import annotations

from hashlib import sha256
import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]


def _module():
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "phase4_author_agreement_test", ROOT / "scripts/run_phase4_author_v022_agreement.py")
    assert spec and spec.loader
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def test_b1_later_leg_draw_matches_independently_retained_active_v4_digest(tmp_path):
    module = _module()
    from bp_registry.runner import canonical_public_shot_context

    design_path = ROOT / "data/evidence/phase4-author-v022-agreement-design-v1.json"
    design = module.low._read(design_path)
    module.validate_design(design)
    cell = design["code_rates"][1]
    manifest = module.manifest_for_cell(module.low._helper(), cell, sha256(design_path.read_bytes()).hexdigest())
    path = tmp_path / "b1.json"
    module.low._atomic(path, manifest)
    context = canonical_public_shot_context(path, shot_id=6)
    observation = {"check_matrix": context.code.hz.tolist(),
                   "sample_identity": context.sample_seed_identity}
    _, digests = module.explicit_gammas(manifest, observation, later_legs=2)
    assert digests[0] == "55a3ebfd8c00ebc192627c234fbce6f7212183b58bde10764e41e2ee203cfb24"


def test_pair_summary_retains_missingness_and_discordance():
    module = _module()
    pairs = [
        {"shot_id": 0, "executed_gamma_digests_checked": 1,
         "canonical": {"status": "completed", "diagnostic_cell": "valid_correct", "syndrome_valid": True,
                       "selection_status": "frozen_decoder_visible_candidate", "diagnostic_candidate_sha256": "a"},
         "native": {"status": "completed", "diagnostic_cell": "valid_correct", "syndrome_valid": True,
                    "success": True, "diagnostic_candidate_sha256": "b"}},
        {"shot_id": 1, "executed_gamma_digests_checked": 0,
         "canonical": {"status": "completed", "diagnostic_cell": "invalid_wrong_logical", "syndrome_valid": False,
                       "selection_status": "unavailable_due_to_stopping", "diagnostic_candidate_sha256": "c"},
         "native": {"status": "completed", "diagnostic_cell": "valid_correct", "syndrome_valid": True,
                    "success": True, "diagnostic_candidate_sha256": "d"}},
        {"shot_id": 2, "executed_gamma_digests_checked": 0,
         "canonical": {"status": "incomplete_interrupted"},
         "native": {"status": "completed"}},
    ]
    result = module.summarize(pairs, look=3, alpha=.05 / 36)
    assert result["complete_pairs"] == 2
    assert result["incomplete_pair_shot_ids"] == [2]
    assert result["paired_success_table"]["canonical_0_native_1"] == 1
    assert result["disagreement"]["all_shot_success"]["count"] == 1
    assert result["disagreement"]["diagnostic_cell"]["count"] == 1
    assert result["disagreement"]["exact_candidate"]["count"] == 2
    assert result["native_failures_or_timeouts"] == 0
