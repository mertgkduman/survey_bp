"""Scientific qualification and durable stopping for Construction U campaigns."""

import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from bp_registry.css import gf2_rank, in_row_space
from bp_registry.unicycle import build_unicycle, singer_273, unicycle_checks


ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "data/reproductions/mackay-0304161-unicycle"
module_spec = importlib.util.spec_from_file_location("_test_unicycle_runner", STUDY / "run.py")
campaign = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(campaign)


@pytest.mark.parametrize("length,rank,logical,weight", [(74, 28, 18, 10), (274, 82, 110, 18)])
def test_source_constructions_and_independent_difference_property(length, rank, logical, weight):
    code = build_unicycle(length)
    check = unicycle_checks(length)
    assert np.array_equal(check, code.hx)
    assert np.array_equal(code.hx, code.hz)
    assert gf2_rank(check) == rank and code.k == logical
    assert np.all(check.sum(axis=1) == weight)
    assert np.all(check[:, -1] == 1)
    # Integer overlaps independently establish the projective-plane incidence
    # property, beyond simply re-running the constructor's difference test.
    overlap = check[:, :-1].astype(int) @ check[:, :-1].astype(int).T
    assert np.all(overlap[~np.eye(length - 1, dtype=bool)] == 1)
    assert np.all(np.diag(overlap) == weight - 1)
    assert np.array_equal((code.lx.astype(int) @ code.lz.astype(int).T) % 2, np.eye(logical))


def test_published_73_difference_set_and_frozen_273_order():
    assert tuple(np.flatnonzero(unicycle_checks(74)[0, :-1])) == (2, 8, 15, 19, 20, 34, 42, 44, 72)
    assert singer_273() == (39, 59, 78, 83, 89, 91, 118, 125, 156, 166, 178, 181, 182, 199, 227, 236, 250)


def test_unicycle_branch_selection_counts_invalid_branches_and_extra_bit_prior():
    calls = []

    class Graph:
        def run(self, syndrome, **kwargs):
            calls.append(syndrome.copy())
            # Extra=0 has weight 2, extra=1 has weight 1 including its extra
            # bit; choose the latter and count both independent runs.
            index = len(calls) - 1
            return SimpleNamespace(candidate=np.array([1, 1] if index == 0 else [0, 0], dtype=np.uint8),
                                   converged=True, iterations=(3, 7)[index])

    target = np.array([0, 1], dtype=np.uint8)
    candidate, valid, iterations = campaign.split_decode(Graph(), target, p=.1, limit=9)
    assert candidate.tolist() == [0, 0, 1] and valid and iterations == [3, 7]
    assert np.array_equal(calls[0], target) and np.array_equal(calls[1], target ^ 1)

    class InvalidLighter:
        def run(self, syndrome, **kwargs):
            extra = int(syndrome[0])
            return SimpleNamespace(candidate=np.array([0, 0] if extra == 0 else [1, 1], dtype=np.uint8),
                                   converged=bool(extra), iterations=8 if extra == 0 else 2)

    candidate, valid, iterations = campaign.split_decode(InvalidLighter(), np.zeros(2, dtype=np.uint8), p=.1, limit=8)
    assert candidate.tolist() == [1, 1, 1] and valid and iterations == [8, 2]


def test_likelihood_selection_uses_the_full_error_pattern_and_deterministic_ties():
    class Graph:
        def run(self, syndrome, **kwargs):
            extra = int(syndrome[0])
            return SimpleNamespace(candidate=np.array([1 - extra, 0], dtype=np.uint8), converged=True, iterations=1)

    candidate, valid, _ = campaign.split_decode(Graph(), np.zeros(2, dtype=np.uint8), p=.1, limit=1)
    # Both full candidates have weight 1; comparing only the cyclic component
    # would wrongly select the extra=1 branch.
    assert candidate.tolist() == [1, 0, 0] and valid


def test_quantum_outcomes_cover_logicals_above_63_and_y_does_not_cancel():
    code = build_unicycle(274)
    packed = tuple(np.packbits(m, axis=1, bitorder="little") for m in (code.hx, code.hz, code.lx, code.lz))
    zero = np.zeros(code.n, dtype=np.uint8)
    residual = code.lx[100]
    assert not in_row_space(code.hx, residual)
    assert campaign.outcome(*packed, residual, zero, joint=False)[0] == "type_ii"
    assert campaign.outcome(*packed, code.hx[0], zero, joint=False)[0] == "stabilizer_success"
    # Equal nonzero X/Z logical signatures must not cancel each other. Pauli
    # labels are I,X,Y,Z, so overlapping X/Z support maps to label 2.
    x, z = code.lx[100], code.lz[100]
    pauli = np.where(x, np.where(z, 2, 1), np.where(z, 3, 0)).astype(np.uint8)
    assert np.array_equal(campaign.base._syndrome(packed[3], x), campaign.base._syndrome(packed[2], z))
    assert campaign.outcome(*packed, pauli, zero, joint=True)[0] == "type_ii"
    bit = zero.copy()
    bit[0] = 1
    assert campaign.outcome(*packed, bit, zero, joint=False)[0] == "type_i"


@pytest.mark.parametrize("arm", ["binary_sp", "unicycle_sp", "qbp"])
def test_real_kernel_shots_replay_and_record_full_directed_work(arm):
    plan = campaign.code_plan()
    job = next(j for j in campaign.jobs(plan) if j["arm"] == arm and j["code"] == "unicycle74")
    job = copy.deepcopy(job)
    job["decoder"]["iterations_per_branch"] = 3
    job["decoder"]["max_iterations"] = 3 * job["decoder"]["branch_count"]
    state = campaign.decoder_state(job)
    for shot in range(2):
        left, right = campaign.event(state, shot), campaign.event(state, shot)
        assert {k: v for k, v in left.items() if k != "decode_ns"} == {k: v for k, v in right.items() if k != "decode_ns"}
        assert left["iterations"] == sum(left["branch_iterations"])
        assert left["directed_edge_updates"] == 2 * job["graph_edges"] * left["iterations"]


def test_stopping_prefix_resume_corruption_and_zero_failure_interval(tmp_path):
    job = copy.deepcopy(campaign.jobs(campaign.code_plan())[0])
    job.update(target_block_failures=2, max_shots=8)

    def row(index, failure=False):
        branches = [1] * job["decoder"]["branch_count"]
        return {"shot": index, "outcome": "type_i" if failure else "exact_success",
                "iterations": sum(branches), "branch_iterations": branches, "decode_ns": 1,
                "directed_edge_updates": 2 * job["graph_edges"] * sum(branches)}

    ledger = campaign.Ledger(tmp_path, job)
    ledger.commit([row(0), row(1, True)])
    resumed = campaign.Ledger(tmp_path, job)
    assert resumed.shots == 2 and resumed.failures == 1
    resumed.commit([row(2), row(3, True), row(4)])
    summary = resumed.summary()
    assert summary["shots"] == 4 and summary["failures"] == 2
    assert summary == campaign.Ledger(tmp_path, job).summary()
    assert summary["ci95_low"] <= .5 <= summary["ci95_high"]
    bad = row(4)
    bad["directed_edge_updates"] += 1
    with pytest.raises(ValueError, match="branch work"):
        resumed.add(bad, b"bad")
    zero_dir = tmp_path / "zero"
    zero_dir.mkdir()
    capped = campaign.Ledger(zero_dir, {**job, "max_shots": 2})
    capped.commit([row(0), row(1)])
    upper = capped.summary()
    assert upper["rate"] == 0 and upper["ci95_low"] == 0 and 0 < upper["ci95_high"] < 1


def test_full_grid_and_frozen_artifact_identities():
    plan = campaign.code_plan()
    assert len(campaign.jobs(plan)) == 42
    assert plan["stop"] == {"target_block_failures": 20, "max_shots": 100_000_000, "failure_events": ["type_i", "type_ii"]}
    for job in campaign.jobs(plan):
        assert job["decoder"]["branch_count"] * job["decoder"]["iterations_per_branch"] == 88200
        expected = job["matched_x_rate"] * (1.5 if job["arm"] == "qbp" else 1)
        assert job["physical_p"] == pytest.approx(expected)
    for name, receipt in plan["codes"].items():
        code = campaign.load_artifact(STUDY, receipt["artifact"], expected_raw_sha256=receipt["raw_sha256"],
                                      expected_semantic_sha256=receipt["semantic_sha256"]).code
        assert code.k == receipt["k"]
        assert int(code.hx.sum()) == receipt["edges_per_component"]
