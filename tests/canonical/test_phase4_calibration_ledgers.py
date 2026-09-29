"""Independent calibration-ledger audit over a real structural Relay shot."""

from __future__ import annotations

from hashlib import sha256
import importlib
import json
from pathlib import Path
import sys

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
audit = importlib.import_module("verify_phase4_calibration")


def test_calibration_ledger_audit_binds_real_relay_terminal_and_rejects_tampering(tmp_path, monkeypatch):
    from bp_registry.canonical.contracts import CanonicalManifestV4
    from bp_registry.canonical.execution import run_canonical_structural_shot
    from bp_registry.css import fixture_code
    from bp_registry.ledger import read_canonical_events
    from bp_registry.sampling import DecoderObservation, HiddenTruth

    run_id = "calibration-audit-fixture"
    policies = {
        "update": {"kind": "binary_spa", "binding_id": "update", "state_lifetime": "message"},
        "schedule": {"kind": "flooding", "binding_id": "schedule", "state_lifetime": "iteration"},
        "state_memory": {"kind": "identity", "binding_id": "memory", "state_lifetime": "leg"},
        "intervention": {"kind": "identity", "binding_id": "intervention", "state_lifetime": "search"},
        "stopping": {"kind": "syndrome_or_budget", "binding_id": "stopping", "state_lifetime": "iteration"},
        "selection": {"kind": "stable_first", "binding_id": "selection", "state_lifetime": "attempt"},
        "postprocessing": {"kind": "identity", "binding_id": "post", "state_lifetime": "attempt"},
    }
    manifest = CanonicalManifestV4.model_validate({
        "schema_version": 4, "run_id": run_id, "numerical_profile": "cpu-float64-spa-v1",
        "max_iterations": 2, "error_rate": 0.1, "policies": policies,
        "memory_bindings": [{"binding_id": "relay-prior", "kind": "affine_prior",
                             "target": "prior", "order": 0, "alpha": 0.5, "state_lifetime": "leg"}],
        "relay": {"total_leg_limit": 1, "legs": [{"max_iterations": 2}]},
    })
    code = fixture_code()
    hidden = np.asarray([1, 0, 0], dtype=np.uint8)
    calibration_dir = tmp_path / "calibration"
    cell = {"configuration_id": "fixture-cell", "code_id": "fixture-code",
            "preset_key": "canonical_default"}
    cell_root = calibration_dir / "runs" / "fixture-code" / "canonical_default" / audit.pilot._digest("fixture-cell")[:16]
    run_dir = cell_root / "run"
    run_dir.mkdir(parents=True)
    (cell_root / "manifest.json").write_text(json.dumps({"run_id": run_id}), encoding="utf-8")
    run_canonical_structural_shot(
        manifest, code=code, observation=DecoderObservation("Z", code.hz @ hidden % 2),
        hidden_truth=HiddenTruth(hidden, np.zeros(3, dtype=np.uint8)), shot_id=0,
        ledger_path=run_dir / "events.jsonl", sample_seed_identity="fixture-sample", context={},
    )
    raw = (run_dir / "events.jsonl").read_bytes()
    (calibration_dir / "events.jsonl").write_bytes(raw)
    terminal = next(event for event in read_canonical_events(run_dir / "events.jsonl") if event["kind"] == "termination")
    attempt = {"shot_id": 0, "status": "completed", "termination": terminal["termination"],
               "sample_identity": "fixture-sample", "outcome": terminal["data"]["outcome"],
               "work_vector": terminal["data"]["work_vector"],
               "aggregate_event_digest": sha256(raw).hexdigest()}
    result = {"codes": {"fixture-code": {"presets": {"canonical_default": {
        "configurations": [{"configuration_id": "fixture-cell", "attempts": [attempt]}],
    }}}}}
    calibration_path = calibration_dir / "result.json"
    calibration_path.write_text(json.dumps(result), encoding="utf-8")
    caps_path = tmp_path / "caps.json"
    caps_path.write_text(json.dumps({"design_amendment": {"path": "fixture", "sha256": "a" * 64}}), encoding="utf-8")
    (tmp_path / "base.json").write_text("{}", encoding="utf-8")
    active = importlib.import_module("run_phase4_active_benchmark")
    monkeypatch.setitem(active.CODE_MANIFESTS, "fixture-code", "base.json")
    monkeypatch.setattr(audit.pilot, "calibration_plan", lambda _root, _caps: {"cells": [cell]})
    monkeypatch.setattr(audit.pilot, "_calibration_manifest", lambda *_args, **_kwargs: {"run_id": run_id})
    monkeypatch.setattr(audit, "audit_terminal", lambda **_kwargs: {
        "status": "passed", "attempt_status_counts": {"completed": 1},
    })

    report = audit.audit_retained_ledgers(root=tmp_path, caps_path=caps_path, calibration_path=calibration_path)
    assert report["verified_terminal_shots"] == 1
    assert report["selection_permitted"] is True
    attempt["outcome"] = "logical_failure" if attempt["outcome"] != "logical_failure" else "exact"
    calibration_path.write_text(json.dumps(result), encoding="utf-8")
    with pytest.raises(ValueError, match="facts differ"):
        audit.audit_retained_ledgers(root=tmp_path, caps_path=caps_path, calibration_path=calibration_path)
