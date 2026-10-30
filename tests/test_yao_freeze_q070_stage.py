"""The automated rare-event follow-up excludes screen shots and prior stages."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1] / "data/reproductions/yao-2312-10950-non-osd"
sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location("yao_freeze_q070", ROOT / "freeze_t10_q070_stage.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


def _setup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    results = tmp_path / "results"
    results.mkdir()
    monkeypatch.setattr(MODULE, "REPO", tmp_path)
    monkeypatch.setattr(MODULE, "RESULTS", results)
    rows = {0.05: 0.0001, 0.055: 0.00008, 0.07: 0.0003}

    def fake_assess(path: Path) -> dict:
        qs = [0.07] if "q070" in path.name else [0.05, 0.055]
        return {"plan_sha256": path.name, "rows": [
            {"proposal_p": q, "failure_ess_per_shot": rows[q]} for q in qs]}

    monkeypatch.setattr(MODULE, "assess", fake_assess)
    first = {"code": "b1", "method": "bpgd_t10", "p": .04, "start_shot": 0,
             "shots": 10000}
    _write(results / "completion-importance-plan.json", {"jobs": [first]})
    _write(results / "completion-importance-extension-stage1.json", {"jobs": [
        {**first, "start_shot": 10000, "shots": 20000}]})
    for stage in range(2, 8):
        _write(results / f"completion-importance-extension-stage{stage}.json", {"jobs": []})
    jobs = []
    for shard in range(10):
        output = results / f"prior-stage8-s{shard+1:02d}"
        _write(output / "summary.json", {"shots": 50000})
        jobs.append({**first, "start_shot": 30000 + 50000*shard,
                     "shots": 50000, "output": str(output.relative_to(tmp_path))})
    _write(results / "completion-importance-extension-stage8.json", {"jobs": jobs})
    return results


def test_freeze_selects_audited_best_arm_and_disjoint_future_shots(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    results = _setup(tmp_path, monkeypatch)
    stage_path, receipt_path = MODULE.freeze()
    stage, receipt = json.loads(stage_path.read_text()), json.loads(receipt_path.read_text())
    assert receipt["selected_proposal_p"] == .07
    assert receipt["screen_shots_excluded_from_final_estimate"] is True
    assert len(stage["jobs"]) == 10
    assert [job["start_shot"] for job in stage["jobs"]] == [530000 + 50000*i for i in range(10)]
    assert all(job["proposal_p"] == .07 and job["seed"] == 20261035 for job in stage["jobs"])
    with pytest.raises(FileExistsError):
        MODULE.freeze()


def test_freeze_requires_complete_prior_stage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    results = _setup(tmp_path, monkeypatch)
    (results / "prior-stage8-s09" / "summary.json").unlink()
    with pytest.raises(ValueError, match="must finish"):
        MODULE.freeze()
    assert not (results / "completion-importance-extension-stage9.json").exists()
