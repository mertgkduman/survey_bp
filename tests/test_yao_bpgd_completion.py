"""The completion runner retains exactly the declared iid terminal prefix."""

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "data/reproductions/yao-2312-10950-bpgd-completion/run.py"
SPEC = importlib.util.spec_from_file_location("yao_bpgd_completion_run", RUN)
study = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(study)


def test_frozen_grid_matches_figures_and_marginals():
    plan = study.load_plan()
    points = study.jobs(plan)
    assert len(points) == len({point["id"] for point in points}) == 77
    assert {point["target_block_failures"] for point in points} == {20}
    assert {point["max_shots"] for point in points} == {100_000_000}
    for point in points:
        settings = point["decoder"]
        if point["arm"] == "qbp":
            assert point["physical_p"] == pytest.approx(1.5 * point["matched_x_rate"])
            assert settings["max_iterations"] == {"b1": 88200, "c2": 19220}[point["code"]]
            continue
        controller = settings["controller"]
        assert settings["max_iterations"] == controller["iterations_per_round"] * controller["round_limit"]
        for figure in settings["source_figures"]:
            arm = point["arm"].split("_r")[0] if figure != 6 else point["arm"]
            assert f'{point["physical_p"]:.5f}' in study.SOURCE["figures"][str(figure)]["curves"][arm]


def test_stopped_ledger_resumes_and_ignores_rows_past_target(tmp_path):
    job = {**study.jobs(study.load_plan())[0], "target_block_failures": 2, "max_shots": 5}

    def row(shot, outcome):
        return {"shot": shot, "outcome": outcome, "iterations": 100, "decode_ns": 10}

    ledger = study.Ledger(tmp_path, job)
    ledger.commit([row(0, "type_i"), row(1, "exact_success")])
    assert not ledger.complete
    ledger = study.Ledger(tmp_path, job)
    ledger.commit([row(2, "type_ii"), row(3, "type_i")])
    summary = study.Ledger(tmp_path, job).summary()
    assert (summary["shots"], summary["failures"], summary["stop_reason"]) == (3, 2, "target_block_failures")
    assert summary["counts"]["type_i"] == summary["counts"]["type_ii"] == 1
    assert 0 < summary["ci95_low"] < summary["rate"] < summary["ci95_high"] < 1


def test_zero_failures_at_cap_keeps_a_finite_upper_bound(tmp_path):
    job = {**study.jobs(study.load_plan())[0], "max_shots": 1}
    ledger = study.Ledger(tmp_path, job)
    ledger.commit([{"shot": 0, "outcome": "exact_success", "iterations": 10, "decode_ns": 5}])
    summary = ledger.summary()
    assert summary["stop_reason"] == "max_shots"
    assert summary["rate"] == summary["ci95_low"] == 0
    assert 0 < summary["ci95_high"] < 1


def test_joint_logical_signatures_do_not_cancel(monkeypatch):
    job = next(point for point in study.jobs(study.load_plan())
               if point["code"] == "b1" and point["arm"] == "qbp")
    code = study._code("b1")
    state = study.decoder_state(job)
    x, z = code.lx[0], code.lz[0]
    assert study._signature(x, state[4]) == study._signature(z, state[5]) != 0
    candidate = np.array([[0, 3], [1, 2]], dtype=np.uint8)[x, z]
    graph = SimpleNamespace(run=lambda *args, **kwargs:
                            SimpleNamespace(candidate=candidate, converged=True, iterations=1))
    monkeypatch.setattr(study, "_sample", lambda *args, **kwargs: np.zeros(code.n, dtype=np.uint8))
    assert study.event((*state[:-1], graph), 0)["outcome"] == "type_ii"


@pytest.mark.parametrize("index", [6, 56, 69, 70])
def test_real_decoder_checkpoint_and_replay(tmp_path, index):
    job = {**study.jobs(study.load_plan())[index], "max_shots": 2}
    summary = study.run(job, tmp_path)
    assert summary == study.run(job, tmp_path)
    ledger = study.Ledger(tmp_path / job["id"], job)
    assert ledger.shots == 2
    again = study.event(study.decoder_state(job), 1)
    assert {k: v for k, v in again.items() if k != "decode_ns"} == {
        k: v for k, v in ledger.last.items() if k != "decode_ns"
    }
