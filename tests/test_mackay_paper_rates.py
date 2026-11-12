"""Published-rate coverage, exact pruning certificates and ordered parallel work."""

import copy
import gzip
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest

from bp_registry.unicycle import unicycle_checks

ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "data/reproductions/mackay-0304161-paper-rates"
spec = importlib.util.spec_from_file_location("_test_mackay_paper_rates", STUDY / "run.py")
campaign = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = campaign
spec.loader.exec_module(campaign)


def test_exact_published_grid_and_depolarizing_identity():
    plan = campaign.code_plan()
    assert [r["x_only"] for r in plan["matched_rates"]] == [.010, .013, .020, .030, .040]
    assert [r["depolarizing"] for r in plan["matched_rates"]] == [.015, .0195, .030, .045, .060]
    points = campaign.jobs(plan)
    assert len(points) == 30 and len({p["id"] for p in points}) == 30
    p = next(p for p in points if p["code"] == "unicycle274" and p["arm"] == "qbp" and p["matched_x_rate"] == .013)
    assert p["physical_p"] == .0195 and p["id"].endswith("p01950")
    assert plan["stop"]["target_block_failures"] == 20 and plan["stop"]["max_shots"] == 100_000_000
    assert all(p["decoder"]["max_iterations"] == 88200 for p in points)
    assert plan["parent_plan_sha256"] == campaign.sha(campaign.ORIGINAL / "plan.json")


@pytest.mark.parametrize("n,q,bound", [(74, 8, 10), (274, 16, 18)])
def test_independent_incidence_properties_establish_distance_lemma_prerequisites(n, q, bound):
    check = unicycle_checks(n)
    cyclic = check[:, :-1].astype(int)
    assert cyclic.shape == (q*q + q + 1,) * 2
    assert np.all(cyclic.sum(axis=0) == q + 1) and np.all(cyclic.sum(axis=1) == q + 1)
    overlap = cyclic.T @ cyclic
    assert np.all(overlap[~np.eye(n - 1, dtype=bool)] == 1)
    assert np.all(check[:, -1] == 1)
    assert bound == q + 2
    # A pattern within the certified radius cannot overturn syndrome majority.
    assert (bound//2 - 1) * (q + 1) == (n - 2)//2


@pytest.mark.parametrize("first", [0, 1])
def test_certified_branch_can_skip_either_hypothesis_without_truth(first):
    calls = []

    def run(syndrome, **kwargs):
        calls.append(syndrome.copy())
        assert len(calls) == 1
        candidate = np.zeros(273, dtype=np.uint8)
        candidate[:8-first] = 1
        return SimpleNamespace(candidate=candidate, converged=True, iterations=3)

    graph = SimpleNamespace(table=SimpleNamespace(variable_count=273), run=run)
    candidate, valid, work = campaign.certified_split(graph, np.full(273, first, dtype=np.uint8), p=.01, limit=5)
    assert valid and candidate[-1] == first and candidate.sum() == 8
    assert work == ([3, 0] if first == 0 else [0, 3])
    assert np.all(calls[0] == 0)


def test_distance_boundary_executes_both_and_keeps_extra_zero_tie_break():
    calls = []

    def run(syndrome, **kwargs):
        index = len(calls)
        calls.append(syndrome.copy())
        candidate = np.zeros(273, dtype=np.uint8)
        candidate[:8 if index == 0 else 9] = 1
        return SimpleNamespace(candidate=candidate, converged=True, iterations=index + 1)

    graph = SimpleNamespace(table=SimpleNamespace(variable_count=273), run=run)
    candidate, valid, work = campaign.certified_split(graph, np.ones(273, dtype=np.uint8), p=.01, limit=5)
    assert len(calls) == 2 and valid and candidate[-1] == 0 and candidate.sum() == 9
    assert work == [2, 1]


def test_invalid_low_weight_candidate_cannot_prune_a_valid_other_branch():
    calls = []

    def run(syndrome, **kwargs):
        index = len(calls)
        calls.append(syndrome.copy())
        return SimpleNamespace(candidate=np.zeros(73, dtype=np.uint8), converged=bool(index), iterations=2)

    graph = SimpleNamespace(table=SimpleNamespace(variable_count=73), run=run)
    candidate, valid, work = campaign.certified_split(graph, np.zeros(73, dtype=np.uint8), p=.01, limit=5)
    assert len(calls) == 2 and valid and candidate[-1] == 1 and work == [2, 2]


@pytest.mark.parametrize("code_id", ["unicycle74", "unicycle274"])
def test_real_kernel_pruning_and_order_preserve_original_selected_candidates(code_id):
    job = copy.deepcopy(next(j for j in campaign.jobs(campaign.code_plan()) if j["code"] == code_id and j["arm"] == "unicycle_sp"))
    job["decoder"]["iterations_per_branch"] = 4
    state = campaign.decoder_state(job)
    _, n, packed, graph = state
    for shot in range(16):
        truth = campaign.original.base._sample(job["seed"], 1000, shot, n, depolarizing=False)
        syndrome = campaign.original.base._syndrome(packed[1], truth)
        expected = campaign.original_split(graph, syndrome, p=.01, limit=4)
        candidate, valid, work = campaign.certified_split(graph, syndrome, p=.01, limit=4)
        assert np.array_equal(candidate, expected[0]) and valid == expected[1]
        assert sum(work) <= sum(expected[2])
        row = campaign.event(state, shot)
        assert row["iterations"] == sum(row["branch_iterations"])
        assert row["directed_edge_updates"] == 2 * job["graph_edges"] * row["iterations"]
        assert row["certified_branch_pruned"] == (0 in row["branch_iterations"])


def synthetic_event(state, shot):
    job = state[0]
    return {"shot": shot, "outcome": "type_ii" if shot in (1, 4) else "stabilizer_success" if shot == 3 else "exact_success",
            "iterations": 1, "branch_iterations": [1, 0], "certified_branch_pruned": True,
            "directed_edge_updates": 2 * job["graph_edges"], "decode_ns": 1,
            "error_sha256": "a"*64, "syndrome_sha256": "b"*64, "candidate_sha256": "c"*64}


def test_parallel_ordered_prefix_resume_work_and_classical_counter(tmp_path, monkeypatch):
    job = copy.deepcopy(next(j for j in campaign.jobs(campaign.code_plan()) if j["arm"] == "unicycle_sp"))
    job.update(max_shots=7, target_block_failures=2, workers=1)
    plan_path = tmp_path / "plan.json"
    plan_path.write_text("{}")
    monkeypatch.setattr(campaign, "PLAN", plan_path)
    monkeypatch.setattr(campaign, "CHUNK_SIZE", 2)
    monkeypatch.setattr(campaign, "event", synthetic_event)
    serial = campaign.run(job, tmp_path / "serial")
    parallel = campaign.run({**job, "workers": 2}, tmp_path / "parallel")
    assert serial["shots"] == parallel["shots"] == 5
    assert serial["failures"] == parallel["failures"] == 2
    assert serial["ledger_sha256"] == parallel["ledger_sha256"]
    assert serial["classical_block_errors"] == parallel["classical_block_errors"] == 3
    assert parallel["certified_branches_pruned"] == 5
    assert campaign.run({**job, "workers": 2}, tmp_path / "parallel") == parallel
    directory = tmp_path / "parallel" / job["id"]
    ledger = campaign.Ledger(directory, {**job, "workers": 2})
    bad = synthetic_event((job,), 5)
    bad["certified_branch_pruned"] = False
    with pytest.raises(ValueError, match="certified branch"):
        ledger.add(bad, b"bad")


def test_plot_ordinates_are_labelled_approximate_and_cover_every_planned_binary_rate():
    plot = campaign.code_plan()["source_plot"]
    assert [r["p"] for r in plot["points"].values()] == [.01, .013, .02, .03, .04]
    assert "approximated" in plot["ordinate_status"]
    assert plot["points"]["0.040"]["total_error_approx"] == pytest.approx(.18078419)
