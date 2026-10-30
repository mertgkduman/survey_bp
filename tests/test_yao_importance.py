"""Numerical qualification of the rare-event proposal and retained evidence."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1] / "data/reproductions/yao-2312-10950-non-osd"
sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location("yao_importance", ROOT / "run_importance.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
ASSESS_SPEC = importlib.util.spec_from_file_location("yao_importance_assess", ROOT / "importance_assess.py")
assert ASSESS_SPEC and ASSESS_SPEC.loader
ASSESS = importlib.util.module_from_spec(ASSESS_SPEC)
ASSESS_SPEC.loader.exec_module(ASSESS)


@pytest.mark.parametrize("depolarizing", [False, True])
def test_mixture_likelihood_ratio_reconstructs_target_probability(depolarizing: bool) -> None:
    """Enumerate the full small error space; no Monte Carlo tolerance is needed."""
    p, q, d, n = 0.04, 0.11, 0.1, 3
    alphabet = range(4 if depolarizing else 2)
    for states in np.ndindex(*(len(alphabet),) * n):
        weight = sum(state != 0 for state in states)
        pauli_factor = 3 ** weight if depolarizing else 1
        target = p ** weight * (1-p) ** (n-weight) / pauli_factor
        shifted = q ** weight * (1-q) ** (n-weight) / pauli_factor
        mixture = d * target + (1-d) * shifted
        ratio = MODULE._likelihood_weight(n, weight, p, q, d)
        assert mixture * ratio == pytest.approx(target, rel=2e-14, abs=1e-16)


def test_error_draw_is_deterministic_and_valid() -> None:
    first = MODULE._error_draw(21, 4000, 7000, 17, 20, .1, True)
    second = MODULE._error_draw(21, 4000, 7000, 17, 20, .1, True)
    assert np.array_equal(first[0], second[0])
    assert first[1:] == second[1:]
    assert first[1] == int(np.count_nonzero(first[0]))
    assert set(first[0]).issubset({0, 1, 2, 3})


def test_importance_run_retains_exact_weighted_shot_ledger(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output = tmp_path / "completion-importance-small"
    summary = MODULE.run(code_name="b1", method="bpgd_t1", p=.04, proposal_p=.06,
                         defensive_fraction=.1, seed=4, start_shot=100, shots=4,
                         output=output)
    events = [json.loads(line) for line in (output / "events.jsonl").read_text().splitlines()]
    assert [event["shot"] for event in events] == [100, 101, 102, 103]
    assert sum(event["importance_weight"] *
               (event["outcome"]["type_i"] or event["outcome"]["type_ii"])
               for event in events) == pytest.approx(summary["weighted_sums"]["failure"])
    assert sum(event["outcome"]["type_i"] or event["outcome"]["type_ii"]
               for event in events) == summary["counts"]["type_i"] + summary["counts"]["type_ii"]
    monkeypatch.setattr(ASSESS, "RESULTS", tmp_path)
    verified = ASSESS.verified_importance_runs()
    assert verified[("b1", "bpgd_t1", "0.04000")]["shots"] == 4
    assert verified[("b1", "bpgd_t1", "0.04000")]["rate"] == pytest.approx(
        summary["weighted_sums"]["failure"]/4)
