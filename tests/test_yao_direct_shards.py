"""Direct iid shards combine only after the complete frozen plan is audited."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1] / "data/reproductions/yao-2312-10950-non-osd"
sys.path.insert(0, str(ROOT))
SPEC = importlib.util.spec_from_file_location("yao_non_osd_assess_shards", ROOT / "assess.py")
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def _fixture() -> tuple[dict, dict]:
    jobs = [{"code": "b1", "method": "bpgd_t1", "p": .04, "seed": 7,
             "start_shot": i * 10, "max_shots": 10, "target_failures": None,
             "output": f"data/reproductions/yao-2312-10950-non-osd/results/completion-rare-shard-example-s{i}"}
            for i in range(2)]
    plan = {"schema": "yao-completion-rare-shards-plan-v1", "jobs": jobs,
            "total_fixed_shots": 20}
    verified = {}
    for i, job in enumerate(jobs):
        verified[Path(job["output"]).name] = {
            "code": "b1", "method": "bpgd_t1", "physical_p": .04, "seed": 7,
            "start_shot": i * 10, "shots": 10, "stop_reason": "fixed_shots",
            "counts": {"type_i": i + 1, "type_ii": 0,
                       "exact_success": 9 - i, "stabilizer_success": 0,
                       "iterations": 10, "rounds": 10, "fixations": 0,
                       "elapsed_ns": 100}}
    return plan, verified


def test_fixed_shard_aggregate_requires_every_planned_shard() -> None:
    plan, verified = _fixture()
    assert MODULE.aggregate_fixed_shards(plan, dict(list(verified.items())[:1])) is None
    result = MODULE.aggregate_fixed_shards(plan, verified)
    assert result is not None
    assert (result["shots"], result["failures"], result["counts"]["type_i"]) == (20, 3, 3)
    assert result["stop_reason"] == "fixed_shots"
    assert MODULE.run_interval(result) == pytest.approx(MODULE.exact_interval(3, 20))


def test_fixed_shard_aggregate_rejects_overlap_and_policy_drift() -> None:
    plan, verified = _fixture()
    plan["jobs"][1]["start_shot"] = 9
    with pytest.raises(ValueError, match="overlapping/gapped"):
        MODULE.aggregate_fixed_shards(plan, verified)
    plan, verified = _fixture()
    verified[Path(plan["jobs"][1]["output"]).name]["seed"] = 8
    with pytest.raises(ValueError, match="manifest/summary"):
        MODULE.aggregate_fixed_shards(plan, verified)
