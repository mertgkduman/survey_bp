"""Hostile boundary tests for canonical decoder-visible policy capabilities."""

from __future__ import annotations

from dataclasses import fields, is_dataclass

import numpy as np


def _walk(value, seen: set[int]) -> list[object]:
    if id(value) in seen:
        return []
    seen.add(id(value))
    found = [value]
    if is_dataclass(value):
        for item in fields(value):
            found.extend(_walk(getattr(value, item.name), seen))
    elif isinstance(value, (tuple, list, dict)):
        for item in (value.values() if isinstance(value, dict) else value):
            found.extend(_walk(item, seen))
    return found


def test_policy_capabilities_are_frozen_and_have_no_truth_or_engine_path(tmp_path):
    from bp_registry.canonical.execution import run_canonical_shot
    from bp_registry.css import fixture_code
    from bp_registry.sampling import DecoderObservation, HiddenTruth
    from tests.test_canonical_cli import _manifest

    code = fixture_code()
    truth = HiddenTruth(np.array([1, 0, 0], dtype=np.uint8), np.zeros(3, dtype=np.uint8))
    captured: list[object] = []
    def hostile(original, working, candidates):
        captured.extend(_walk((original, working, candidates), set()))
        assert original.hz.flags.writeable is False
        return candidates
    run_canonical_shot(_manifest(), code=code, observation=DecoderObservation("Z", code.hz @ truth.x % 2),
                       hidden_truth=truth, shot_id=0, ledger_path=tmp_path / "events.jsonl", policy=hostile)
    prohibited = {"ShotSample", "HiddenTruth", "LedgerWriter"}
    assert not any(type(item).__name__ in prohibited for item in captured)
    assert not any("evaluator" in type(item).__module__ for item in captured)


def test_identity_lift_and_stable_selection_have_typed_lineage():
    from bp_registry.canonical.lineage import LineageId, LineageEdge
    from bp_registry.canonical.problems import OriginalProblem, WorkingProblem, OriginalSpaceCandidate, select_stable_candidate

    original = OriginalProblem("original-a", np.array([[1, 0]], dtype=np.uint8), np.array([[1, 0]], dtype=np.uint8), np.array([1], dtype=np.uint8))
    working = WorkingProblem("working-a", original, LineageEdge("identity", LineageId("original", "original-a"), LineageId("working", "working-a")))
    first = OriginalSpaceCandidate("candidate-a", working, np.array([1, 0], dtype=np.uint8), local_order=0)
    second = OriginalSpaceCandidate("candidate-b", working, np.array([0, 0], dtype=np.uint8), local_order=1)
    assert select_stable_candidate([second, first]) is first
    assert select_stable_candidate([]) is None
    assert first.working.original is original
    assert first.candidate.flags.writeable is False


def test_empty_policy_selection_is_terminal_without_evaluator(tmp_path):
    from bp_registry.canonical.execution import run_canonical_shot
    from bp_registry.css import fixture_code
    from bp_registry.sampling import DecoderObservation, HiddenTruth
    from tests.test_canonical_cli import _manifest

    code = fixture_code()
    truth = HiddenTruth(np.array([1, 0, 0], dtype=np.uint8), np.zeros(3, dtype=np.uint8))
    called = False
    def evaluate(*_args, **_kwargs):
        nonlocal called
        called = True
    result = run_canonical_shot(_manifest(), code=code, observation=DecoderObservation("Z", code.hz @ truth.x % 2),
                                hidden_truth=truth, shot_id=0, ledger_path=tmp_path / "events.jsonl",
                                policy=lambda *_args: (), evaluate=evaluate)
    assert result.termination == "no_eligible_candidate"
    assert result.evaluation is None
    assert called is False
