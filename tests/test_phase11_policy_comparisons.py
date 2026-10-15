"""Bounded, receipt-first Phase 11 policy-comparison regressions."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/run_phase11_policy_comparisons.py"


def _api():
    import importlib.util

    spec = importlib.util.spec_from_file_location("phase11_policy_comparisons", SCRIPT)
    assert spec and spec.loader, "policy comparison runner must be importable"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_tracer_mbp4_one_change_contract_and_replay(tmp_path: Path) -> None:
    """The first policy tracer changes only a qualified MBP4 recurrence."""
    module = _api()
    study = module.load_policy_study(ROOT)
    tracer = next(item for item in study["comparisons"] if item["comparison_id"] == "gb46-mbp4-alpha")
    assert "independence" in tracer["anchors"]
    assert tracer["declared_changed_field"] == "recurrence"
    assert tracer["baseline"]["schedule"] == tracer["variant"]["schedule"]
    assert tracer["baseline"]["initialization"] == tracer["variant"]["initialization"]
    assert tracer["baseline"]["stopping"] == tracer["variant"]["stopping"]
    assert tracer["variant"]["recurrence"] == "kuo-lai-2023-mbp4-fixed-inhibition-eq15-18"
    result = module.run_policy_comparisons(ROOT, tmp_path)
    assert result["status"] == "verified"
    assert result["comparison_count"] >= 1
    verification = module.verify_policy_comparisons(ROOT, tmp_path)
    assert verification["replayed_records"] >= 1
    record = json.loads((tmp_path / "records" / "gb46-mbp4-alpha" / "independence.json").read_text())
    assert record["sample_identity"] == record["baseline"]["sample_identity"] == record["variant"]["sample_identity"]
    assert record["baseline"]["terminal"] and record["variant"]["terminal"]
    assert record["baseline"]["work"] and record["variant"]["work"]
    assert record["baseline"]["runtime_ns"] >= 0 and record["variant"]["runtime_ns"] >= 0


def test_unsupported_or_multi_change_policy_is_rejected_before_output(tmp_path: Path) -> None:
    module = _api()
    study = module.load_policy_study(ROOT)
    bad = json.loads(json.dumps(study))
    comparison = bad["comparisons"][0]
    comparison["variant"]["alpha"] = 0.0
    with pytest.raises(ValueError, match="alpha"):
        module.validate_policy_study(ROOT, bad)
    bad = json.loads(json.dumps(study))
    bad["comparisons"][0]["variant"]["schedule"] = "qbp_variable_serial"
    with pytest.raises(ValueError, match="exactly one"):
        module.validate_policy_study(ROOT, bad)
    assert not list(tmp_path.rglob("*.json"))


def test_policy_record_writer_rejects_dangling_directory_symlink(tmp_path: Path) -> None:
    """Policy records use the Phase 11 no-follow writer for nested paths."""
    import pytest

    module = _api()
    (tmp_path / "records").symlink_to(tmp_path / "outside", target_is_directory=True)
    with pytest.raises(OSError):
        module._write_exact(tmp_path, ("records", "record.json"), {"schema": "test"})


def test_policy_replay_rejects_tampered_stored_record_digest(tmp_path: Path) -> None:
    """Replay validates the receipt before normalizing observational timing."""
    import pytest

    module = _api()
    module.run_policy_comparisons(ROOT, tmp_path)
    record_path = tmp_path / "records" / "gb46-mbp4-alpha" / "independence.json"
    changed = json.loads(record_path.read_text(encoding="utf-8"))
    changed["record_sha256"] = "0" * 64
    record_path.write_text(json.dumps(changed, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="record digest"):
        module.verify_policy_comparisons(ROOT, tmp_path)


def test_independence_cli_runs_and_replays_bounded_tracer(tmp_path: Path) -> None:
    run = subprocess.run(
        [sys.executable, str(SCRIPT), "run", "--output-root", str(tmp_path)],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    assert run.returncode == 0, run.stdout + run.stderr
    replay = subprocess.run(
        [sys.executable, str(SCRIPT), "replay", "--output-root", str(tmp_path)],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    assert replay.returncode == 0, replay.stdout + replay.stderr
    assert json.loads(replay.stdout)["replayed_records"] >= 1


def test_three_anchor_policy_rows_keep_asced_lanes_separate_and_native_unavailable() -> None:
    """D-14 requires all policy rows at exactly the frozen channel anchors."""
    module = _api()
    study = module.load_policy_study(ROOT)
    module.validate_policy_study(ROOT, study)
    assert all(item["anchors"] == ["lower_y", "independence", "higher_y"] for item in study["comparisons"])
    rows = {item["comparison_id"]: item for item in study["comparisons"]}
    assert set(rows) >= {"gb46-mbp4-alpha", "gb46-ordinary-asced", "gb46-overcomplete-asced"}
    assert rows["gb46-ordinary-asced"]["construction"] != rows["gb46-overcomplete-asced"]["construction"]
    assert rows["gb46-ordinary-asced"]["native_match_status"] == "unavailable"
    assert rows["gb46-overcomplete-asced"]["canonical_controlled_eligible"] is True


def test_policy_study_rejects_renamed_missing_or_fourth_anchor() -> None:
    module = _api()
    study = module.load_policy_study(ROOT)
    for anchors in (["lower_y", "independence"], ["lower_y", "independent", "higher_y"], ["lower_y", "independence", "higher_y", "extra"]):
        bad = json.loads(json.dumps(study))
        bad["comparisons"][0]["anchors"] = anchors
        with pytest.raises(ValueError, match="anchors"):
            module.validate_policy_study(ROOT, bad)


def test_complete_methods_keeps_canonical_asced_eligible_without_native_matching() -> None:
    module = _api()
    manifest = module.load_complete_methods(ROOT)
    module.validate_complete_methods(ROOT, manifest)
    methods = {row["method_id"]: row for row in manifest["methods"]}
    assert set(methods) == {"ordinary_bp4", "qbpgd", "mbp4", "canonical_asced"}
    asced = methods["canonical_asced"]
    assert asced["canonical_controlled_eligible"] is True
    assert asced["native_match_eligible"] is False
    assert asced["fidelity"] == "canonical_adaptation"
    assert all(row["status"] == "unavailable" for row in asced["native_lane"]) 
    assert methods["qbpgd"]["executable"] is False
