"""Public lifecycle regressions for the Phase 11 controlled GB46 calibration."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def test_installed_cli_exposes_phase11_controlled_lifecycle() -> None:
    """The public wrapper advertises every lifecycle operation before a run starts."""
    result = subprocess.run(
        [sys.executable, "scripts/run_phase11_controlled.py", "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "preflight" in result.stdout
    assert "run" in result.stdout
    assert "resume" in result.stdout
    assert "replay" in result.stdout
    assert "verify" in result.stdout
    assert "assess" in result.stdout


def test_bounded_public_lifecycle_evidence_integrity(tmp_path: Path) -> None:
    """The shipped wrapper seals complete matched pairs before assessment."""
    output = tmp_path / "phase11-controlled"
    run = subprocess.run(
        [sys.executable, "scripts/run_phase11_controlled.py", "run", "--output-root", str(output)],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    assert run.returncode == 0, run.stderr
    assert '"complete_pairs": 6' in run.stdout

    for command in ("replay", "verify"):
        result = subprocess.run(
            [sys.executable, "scripts/run_phase11_controlled.py", command, "--output-root", str(output)],
            cwd=ROOT, text=True, capture_output=True, check=False,
        )
        assert result.returncode == 0, result.stderr
        assert '"publication_authorization": "deny"' in result.stdout

    pair = output / "pairs" / "lower_y" / "0.json"
    pair.write_text(pair.read_text(encoding="utf-8").replace('"joint"', '"tampered"', 1), encoding="utf-8")
    tampered = subprocess.run(
        [sys.executable, "scripts/run_phase11_controlled.py", "verify", "--output-root", str(output)],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    assert tampered.returncode == 2
    assert "error" in tampered.stdout


def test_verifier_rejects_resigned_pair_with_changed_arm_evidence(tmp_path: Path) -> None:
    """A pair's self-digest cannot replace its deterministic replay binding."""
    from bp_registry.campaigns.controlled_execution import _matched_digest, run_phase11_controlled, verify_phase11_controlled

    output = tmp_path / "phase11-controlled"
    design = ROOT / "data/studies/phase11-gb46-joint-separate.json"
    run_phase11_controlled(root=ROOT, design_path=design, output_root=output)
    pair_path = output / "pairs" / "lower_y" / "0.json"
    changed = json.loads(pair_path.read_text(encoding="utf-8"))
    changed["joint"]["terminal_status"] = "wrong_logical_action"
    changed["joint"]["all_shot"] = "failure"
    changed["joint"]["evaluation"]["outcome"] = "wrong_logical_action"
    changed["record_sha256"] = _matched_digest({key: value for key, value in changed.items() if key != "record_sha256"})
    pair_path.write_text(json.dumps(changed, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")

    import pytest

    with pytest.raises(ValueError, match="deterministic arm evidence"):
        verify_phase11_controlled(root=ROOT, design_path=design, output_root=output)


def test_gb46_three_point_design_has_disjoint_calibration_ranges() -> None:
    """The public design preserves all three exact rows without a source lane."""
    from bp_registry.campaigns.controlled_execution import preflight_phase11_controlled_design

    receipt = preflight_phase11_controlled_design(
        root=ROOT, design_path=ROOT / "data/studies/phase11-gb46-joint-separate.json",
    )
    assert receipt["point_order"] == ["lower_y", "independence", "higher_y"]
    ranges = receipt["sample_ranges"]
    assert {item for lower, upper in ranges.values() for item in range(lower, upper + 1)} == set(range(6))
    assert receipt["publication_authorization"] == "deny"


def test_gb46_empty_shard_is_explicitly_incomplete(tmp_path: Path) -> None:
    """An empty valid shard cannot be silently turned into an assessment."""
    result = subprocess.run(
        [sys.executable, "scripts/run_phase11_controlled.py", "run", "--output-root", str(tmp_path / "empty"),
         "--shard", "lower_y:1:0"],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    assert '"assessment_status": "incomplete_shard"' in result.stdout


def test_bb72_tracer_preflight_binds_artifact_provenance_and_qualifications() -> None:
    """The second-code tracer retains source limits as qualified metadata."""
    from bp_registry.campaigns.controlled_execution import preflight_phase11_controlled_design

    receipt = preflight_phase11_controlled_design(
        root=ROOT, design_path=ROOT / "data/studies/phase11-bb72-joint-separate.json",
    )

    assert receipt["code_id"] == "BB72"
    assert receipt["code_artifact_sha256"]
    assert receipt["code_provenance_sha256"]
    assert receipt["distance_qualification"] == "source_reported_distance_6_not_platform_verified"
    assert receipt["logical_operator_qualification"] == "project_derived_logicals_not_independent_distance_verification"
    assert receipt["publication_authorization"] == "deny"


def test_bb72_three_point_calibration_replays_named_work_and_wall_runtime(tmp_path: Path) -> None:
    """All frozen rows use the same public lifecycle and retain native units."""
    from bp_registry.campaigns.controlled_execution import (
        assess_phase11_controlled,
        replay_phase11_controlled,
        run_phase11_controlled,
    )

    design = ROOT / "data/studies/phase11-bb72-joint-separate.json"
    output = tmp_path / "bb72"
    run = run_phase11_controlled(root=ROOT, design_path=design, output_root=output)
    replay = replay_phase11_controlled(root=ROOT, design_path=design, output_root=output)
    assessment = assess_phase11_controlled(root=ROOT, design_path=design, output_root=output)

    assert run["complete_pairs"] == 6
    assert replay["complete_pairs"] == 6
    assert assessment["publication_authorization"] == "deny"
    assert "joint:check_to_variable_updates" in run["arm_work"]
    assert "joint:variable_to_check_updates" in run["arm_work"]
    assert "separate:x_canonical_spa_iterations" in run["arm_work"]
    assert "separate:z_canonical_spa_iterations" in run["arm_work"]
    assert run["arm_runtime_ns"]["joint"] > 0
    assert run["arm_runtime_ns"]["separate"] > 0
    assert run["timing_boundary"] == "decoder_callback_wall_v1"
