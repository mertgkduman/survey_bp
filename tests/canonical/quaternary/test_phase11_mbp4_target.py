"""Independent checks for the bounded Phase 11 MBP4 Figures 8--9 study.

The checks deliberately inspect frozen evidence only.  They do not import the
MBP4 kernel or recurrence helpers, so a change in the production recurrence
cannot update the expected trajectory at the same time.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
TARGET = ROOT / "data/source-targets/phase11-mbp4-figures8-9-five-qubit.json"
MANIFEST = ROOT / "data/manifests/phase11-mbp4-figures8-9-five-qubit.json"
ASSESSMENT = ROOT / "data/results/phase11-mbp4-figures8-9/assessment.json"
STUDY = ROOT / "scripts/run_phase11_source_studies.py"


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _syndrome(checks: list[list[int]], candidate: list[int]) -> list[int]:
    """Compute the original Pauli syndrome without calling production code."""
    return [
        sum(int(label != 0 and value != 0 and label != value) for label, value in zip(row, candidate, strict=True)) % 2
        for row in checks
    ]


def test_tracer_target_freezes_the_exact_figures_8_9_mechanism() -> None:
    target = _json(TARGET)
    assert target["schema"] == "phase11-mbp4-figures8-9-five-qubit-target-v1"
    assert target["target_id"] == "mbp4-figures8-9-five-qubit"
    assert target["paper"]["figures"] == ["Figure 8", "Figure 9"]
    assert target["source_settings"] == {
        "error": [0, 0, 0, 2, 0],
        "epsilon": 0.003,
        "schedule": "qbp_flooding",
        "beta": 0.0,
    }
    assert target["observation_horizon"]["kind"] == "frozen_sweeps"
    assert target["claim_scope"] == "deterministic_mechanism_only_not_a_curve_or_ranking"


def test_alpha_one_oscillation_is_independent_of_production_recurrence_helpers() -> None:
    target = _json(TARGET)
    path = target["paths"]["alpha_one"]
    assert path["alpha"] == 1.0
    assert path["expected_relation"] == "oscillatory"
    trajectory = path["expected_trajectory"]
    candidates = [step["candidate"] for step in trajectory]
    assert len(candidates) == target["observation_horizon"]["sweeps"]
    assert len({tuple(candidate) for candidate in candidates}) < len(candidates)
    assert candidates[0] != candidates[1]
    assert _syndrome(target["problem"]["checks"], candidates[-1]) != target["problem"]["syndrome"]


def test_alpha_one_point_five_convergence_uses_original_problem_evaluation() -> None:
    target = _json(TARGET)
    path = target["paths"]["alpha_one_point_five"]
    assert path["alpha"] == 1.5
    assert path["expected_relation"] == "correct_convergence"
    candidate = path["expected_trajectory"][-1]["candidate"]
    assert _syndrome(target["problem"]["checks"], candidate) == target["problem"]["syndrome"]
    assert candidate == target["source_settings"]["error"]


def test_alpha_only_contrast_holds_all_non_alpha_settings_and_work_evidence_fixed() -> None:
    target = _json(TARGET)
    assessment = _json(ASSESSMENT)
    expected = {
        "varying_field": "alpha",
        "held_constant": ["five_qubit_checks", "IIIYI_error", "epsilon", "schedule", "beta", "numerical_profile", "observation_horizon"],
    }
    assert target["alpha_only_contrast"] == expected == assessment["alpha_only_contrast"]
    paths = assessment["ledger"]["paths"]
    assert set(paths) == {"alpha_one", "alpha_one_point_five"}
    assert paths["alpha_one"]["work"]["bp_calls"] == 20
    assert paths["alpha_one_point_five"]["work"]["bp_calls"] == 13


def test_replay_and_digest_bind_target_manifest_ledger_and_assessment() -> None:
    target = _json(TARGET)
    manifest = _json(MANIFEST)
    assessment = _json(ASSESSMENT)
    target_bytes = TARGET.read_bytes()
    assert manifest["target_document_sha256"] == sha256(target_bytes).hexdigest()
    assert assessment["target_receipt_sha256"] == target["target_receipt_sha256"]
    assert assessment["deterministic_replay"]["ledger_sha256"] == assessment["deterministic_replay"]["replay_ledger_sha256"]
    assert assessment["assessment_sha256"] == sha256(_canonical_bytes({
        key: value for key, value in assessment.items() if key != "assessment_sha256"
    })).hexdigest()


def test_figure6_remains_blocked_and_never_inherits_the_mechanism_verdict() -> None:
    assessment = _json(ASSESSMENT)
    figure6 = assessment["blocked_targets"]["figure6"]
    assert figure6["status"] == "blocked_metadata"
    assert set(figure6["missing_metadata"]) == {
        "iteration_cap", "denominator", "stopping_rule", "exact_coordinates", "interval_method",
    }
    assert figure6["assessment"] == "not_admitted"
    assert assessment["claim_scope"] == "deterministic_mechanism_only_not_a_curve_or_ranking"
