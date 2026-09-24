"""Public, bounded evidence checks for the Phase 3 matched pilot matrix."""

from __future__ import annotations

import importlib.util
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PILOT_SCRIPT = REPOSITORY_ROOT / "scripts" / "run_phase3_pilots.py"


def _pilot_module():
    spec = importlib.util.spec_from_file_location("phase3_pilots", PILOT_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_bb144_tracer_runs_through_public_preflight_run_and_verify(tmp_path):
    """The first matched lane is durable public evidence, not an internal shortcut."""
    assert PILOT_SCRIPT.is_file(), "Phase 3 needs a public BB-144 pilot runner"
    module = _pilot_module()
    report = module.run_pilots(
        repository_root=REPOSITORY_ROOT,
        output_root=tmp_path / "phase3-pilots",
        manifest_names=("phase3-pilot-bb144.json",),
    )
    assert report["code_ids"] == ["gross-bb-144"]
    assert report["labels"] == {"relation": "pilot_adaptation", "assessment_status": "not_assessed"}
    assert report["matched_sample_identities"] is True
    assert report["verified_terminals"]
    assert (tmp_path / "phase3-pilots" / "events.jsonl").is_file()
    assert (tmp_path / "phase3-pilots" / "result.json").is_file()
