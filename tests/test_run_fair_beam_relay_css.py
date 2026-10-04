"""The fair CSS fixture remains matched and replayable after publication."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_fair_beam_relay_css import execute  # noqa: E402


def _tiny_design(tmp_path: Path) -> Path:
    value = json.loads((ROOT / "data/studies/fair-beam-relay-css-v1.json").read_text())
    value["shots"] = 2
    target = tmp_path / "design.json"
    target.write_text(json.dumps(value, sort_keys=True) + "\n")
    return target


def test_matched_runner_replays_all_structural_evidence_and_detects_tampering(tmp_path: Path):
    design = _tiny_design(tmp_path)
    output = tmp_path / "result"
    produced = execute(design, output)
    assert produced["shots"] == 2
    assert execute(design, output, check_only=True) == produced
    rows = [json.loads(line) for line in (output / "events.jsonl").read_text().splitlines()]
    assert len(rows) == 2
    assert all(set(row["arms"]) == {"g1000", "g0500"} for row in rows)
    assert all(arm["beam"]["initial"] == arm["relay"]["initial"] == arm["initial"]
               for row in rows for arm in row["arms"].values())
    assert all(row["sample_identity"] for row in rows)
    rows[0]["arms"]["g0500"]["beam"]["initial"]["candidate"][0] ^= 1
    (output / "events.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
    with pytest.raises(ValueError, match="deterministic replay"):
        execute(design, output, check_only=True)


def test_design_change_is_rejected_after_first_shot(tmp_path: Path):
    design = _tiny_design(tmp_path)
    output = tmp_path / "result"
    execute(design, output)
    value = json.loads(design.read_text())
    value["controls"]["v2c_gamma"] = 1.0
    design.write_text(json.dumps(value, sort_keys=True) + "\n")
    with pytest.raises(ValueError):
        execute(design, output, check_only=True)


def test_runtime_method_and_values_are_checked_even_though_time_is_not_replayed(tmp_path: Path):
    design = _tiny_design(tmp_path)
    output = tmp_path / "result"
    execute(design, output)
    rows = [json.loads(line) for line in (output / "events.jsonl").read_text().splitlines()]
    rows[0]["arms"]["g0500"]["runtime_ns"]["beam_extra"] = -1
    (output / "events.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
    with pytest.raises(ValueError, match="runtime evidence"):
        execute(design, output, check_only=True)
