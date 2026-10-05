"""End-to-end campaign gates on independent matched cohorts and frozen selection."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_fair_beam_relay_campaign import prepare, report, run_shard, select  # noqa: E402
from package_fair_beam_relay_campaign_v2 import _package, _verify_package  # noqa: E402


def test_campaign_freezes_selection_before_evaluation_and_replays_terminal_evidence(tmp_path: Path):
    design = json.loads((ROOT / "data/studies/fair-beam-relay-css-v2.json").read_text())
    for rate in design["rates"].values():
        rate["selection_shots"] = 1
        rate["evaluation_shots"] = 1
    path = tmp_path / "design.json"
    path.write_text(json.dumps(design, sort_keys=True) + "\n")
    output = tmp_path / "result"
    prepare(path, output)
    with pytest.raises(ValueError, match="selection lock"):
        run_shard(path, output, "evaluation", "p050", "i05")
    for rate in design["rates"]:
        for profile in design["profiles"]:
            run_shard(path, output, "selection", rate, profile,
                      workers=2 if (rate, profile) == ("p050", "i05") else 1)
    lock = select(path, output, workers=2)
    assert set(lock["selected_profiles"]) == {"p050", "p080"}
    for rate in design["rates"]:
        for profile in design["profiles"]:
            run_shard(path, output, "evaluation", rate, profile)
    result = report(path, output, workers=2)
    assert result["assessment_status"] == "controlled_evaluation_complete"
    assert len(result["selected_paired_contrasts"]) == 4
    assert len(result["parameter_grid"]["p080"]["g0500"]) == 3
    assert (output / "study.html").is_file()
    assert (output / "REPORT.md").is_file()
    rows = [json.loads((output / "evaluation" / "p080" / profile / "events.jsonl").read_text().splitlines()[0])
            for profile in design["profiles"]]
    assert len({row["sample_identity"] for row in rows}) == 1
    assert all(row["arms"]["g0500"]["beam"]["initial"] == row["arms"]["g0500"]["relay"]["initial"]
               for row in rows)
    package = _package(path, output)
    assert len(package["files"]) == 42
    assert _verify_package(output) == package
    compressed = output / "evaluation/p080/i20/events.jsonl.gz"
    compressed.write_bytes(compressed.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="published file differs"):
        _verify_package(output)
    corrupted = json.loads((output / "selection-lock.json").read_text())
    current = corrupted["selected_profiles"]["p050"]["g0500"]["beam"]
    corrupted["selected_profiles"]["p050"]["g0500"]["beam"] = "i10" if current != "i10" else "i05"
    (output / "selection-lock.json").write_text(json.dumps(corrupted, sort_keys=True) + "\n")
    with pytest.raises(ValueError, match="selection lock"):
        report(path, output, workers=2)
