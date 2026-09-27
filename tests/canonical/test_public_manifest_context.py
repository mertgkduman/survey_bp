"""Equivalence coverage for request-scoped canonical public context reuse."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from bp_registry import evaluator
from bp_registry.ledger import CanonicalEventWriter, read_canonical_events, read_canonical_events_bytes
from bp_registry.runner import canonical_public_manifest_context, canonical_public_shot_context


ROOT = Path(__file__).resolve().parents[2]


def _ordinary_memory_manifest(tmp_path: Path) -> Path:
    value = json.loads((ROOT / "data/manifests/canonical-three-qubit-development.json").read_text())
    value.update({
        "schema_version": 4,
        "run_id": "public-context-ordinary-memory",
        "memory": {"bindings": [{
            "binding_id": "memory", "kind": "posterior_momentum", "target": "posterior",
            "parameters": {"alpha": 0.1, "gamma": 0.9}, "order": 0,
            "history_owner": "context:memory", "state_lifetime": "attempt",
            "advance_boundary": "source_iteration", "refresh_boundary": "attempt_start",
            "source_status": "canonical_adaptation", "retain_history": False,
        }]},
    })
    path = tmp_path / "ordinary-memory.json"
    path.write_text(json.dumps(value), encoding="utf-8")
    return path


def _context_bytes(context) -> bytes:
    """Serialize every public/static and per-shot fact relevant to replay."""
    code = context.code.validate()
    payload = {
        "manifest_sha256": context.manifest_sha256,
        "artifact_raw_sha256": context.artifact_raw_sha256,
        "artifact_semantic_sha256": context.artifact_semantic_sha256,
        "compact_manifest": context.compact_manifest,
        "sample_seed_identity": context.sample_seed_identity,
        "run_id": context.run_id,
        "shot_id": context.shot_id,
        "check_type": context.check_type,
        "syndrome": context.syndrome,
        "code_id": context.code_id,
        "evidence_relation": context.evidence_relation,
        "fixture": context.fixture,
        "assessment_status": context.assessment_status,
        "decoder_seed_identity": context.decoder_seed_identity,
        "error_rate": context.error_rate,
        "max_iterations": context.max_iterations,
        "work_limits": context.work_limits,
        "composition_identity": context.composition_identity,
        "policy_effects": context.policy_effects,
        "profile_plan": context.profile_plan,
        "trace_plan": context.trace_plan,
        "update_kind": context.update_kind,
        "schedule_kind": context.schedule_kind,
        "execution_identity": context.execution_identity,
        "memory_execution_context": context.memory_execution_context,
        "code": {"hx": code.hx.tolist(), "hz": code.hz.tolist(), "lx": None if code.lx is None else code.lx.tolist(), "lz": None if code.lz is None else code.lz.tolist()},
        "hidden_truth": {"x": context.hidden_truth.x.tolist(), "z": context.hidden_truth.z.tolist()},
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def test_manifest_base_derives_byte_identical_v2_v3_and_v4_contexts(tmp_path):
    """Static preflight reuse cannot change public identities or classification."""
    manifests = (
        ROOT / "data/manifests/canonical-three-qubit-development.json",
        ROOT / "data/manifests/phase3-hsu-group-pilot.json",
        ROOT / "data/manifests/phase4-memory-relay-b1.json",
        _ordinary_memory_manifest(tmp_path),
    )
    for path in manifests:
        base = canonical_public_manifest_context(path)
        snapshot_base = canonical_public_manifest_context(path, manifest_bytes=path.read_bytes())
        assert base.manifest_sha256 == canonical_public_manifest_context(path).manifest_sha256
        for shot_id in range(min(2, base.manifest.budgets.max_shots)):
            derived = base.shot_context(shot_id)
            snapshot_derived = snapshot_base.shot_context(shot_id)
            wrapped = canonical_public_shot_context(path, shot_id=shot_id)
            assert _context_bytes(derived) == _context_bytes(wrapped)
            assert _context_bytes(snapshot_derived) == _context_bytes(wrapped)
            candidate = np.zeros(derived.code.n, dtype=np.uint8)
            assert evaluator.evaluate_candidate(
                derived.code, true_x=derived.hidden_truth.x, true_z=derived.hidden_truth.z, candidate_x=candidate,
            ) == evaluator.evaluate_candidate(
                wrapped.code, true_x=wrapped.hidden_truth.x, true_z=wrapped.hidden_truth.z, candidate_x=candidate,
            )
        with pytest.raises(ValueError, match="shot_id is outside"):
            base.shot_context(-1)
        with pytest.raises(ValueError, match="shot_id is outside"):
            canonical_public_shot_context(path, shot_id=base.manifest.budgets.max_shots)


def test_manifest_base_is_frozen_and_samples_each_shot_independently(tmp_path):
    base = canonical_public_manifest_context(_ordinary_memory_manifest(tmp_path))
    with pytest.raises((AttributeError, TypeError)):
        base.manifest_sha256 = "not-allowed"  # type: ignore[misc]
    first, second = base.shot_context(0), base.shot_context(1)
    assert first.shot_id != second.shot_id
    assert first.sample_seed_identity != second.sample_seed_identity
    assert first.memory_execution_context["decoder_identity"] != second.memory_execution_context["decoder_identity"]


def test_manifest_base_and_derived_contexts_do_not_share_mutable_statics(tmp_path):
    path = _ordinary_memory_manifest(tmp_path)
    base = canonical_public_manifest_context(path)
    expected_next = base.shot_context(1)
    first = base.shot_context(0)

    # Mutate every returned mutable boundary: none may poison the cached base
    # or a separately derived public context.
    first.work_limits["shot"]["injected"] = 1
    first.compact_manifest["injected"] = {"control": True}
    first.policy_effects["injected"] = {"control": True}
    first.profile_plan["injected"] = True
    first.code.hx[0, 0] ^= 1
    base.work_limits["shot"]["injected"] = 1
    base.compact_manifest["injected"] = {"control": True}
    base.policy_effects["injected"] = {"control": True}
    base.profile_plan["injected"] = True
    base.code.hx[0, 0] ^= 1
    base.manifest.memory.bindings[0].parameters["alpha"] = 0.2

    next_context = base.shot_context(1)
    wrapped = canonical_public_shot_context(path, shot_id=1)
    assert _context_bytes(next_context) == _context_bytes(expected_next)
    assert _context_bytes(next_context) == _context_bytes(wrapped)
    assert "injected" not in next_context.work_limits["shot"]
    assert "injected" not in next_context.compact_manifest
    assert "injected" not in next_context.policy_effects
    assert "injected" not in next_context.profile_plan


def test_ledger_snapshot_parser_has_the_same_validation_as_the_path_api(tmp_path):
    path = tmp_path / "canonical-events.jsonl"
    with CanonicalEventWriter(path) as writer:
        writer.begin(run_id="snapshot", shot_id=0, sample_seed_identity="sample")
        writer.event(run_id="snapshot", shot_id=0, kind="attempt", data={"attempt": 0})
        writer.terminal(run_id="snapshot", shot_id=0, termination="completed")

    snapshot = path.read_bytes()
    assert read_canonical_events_bytes(snapshot) == read_canonical_events(path)
    with pytest.raises(ValueError, match="invalid event_id"):
        read_canonical_events_bytes(snapshot.replace(b'"event_id":"', b'"event_id":"forged', 1))
