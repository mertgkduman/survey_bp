"""Public-path tracer contracts for the Phase 4 Relay-BP adaptation."""

from __future__ import annotations

import numpy as np


def _policies() -> dict[str, object]:
    return {
        "update": {"kind": "binary_spa", "binding_id": "update", "state_lifetime": "message"},
        "schedule": {"kind": "flooding", "binding_id": "schedule", "state_lifetime": "iteration"},
        "state_memory": {"kind": "identity", "binding_id": "memory", "state_lifetime": "leg"},
        "intervention": {"kind": "identity", "binding_id": "intervention", "state_lifetime": "search"},
        "stopping": {"kind": "syndrome_or_budget", "binding_id": "stopping", "state_lifetime": "iteration"},
        "selection": {"kind": "stable_first", "binding_id": "selection", "state_lifetime": "attempt"},
        "postprocessing": {"kind": "identity", "binding_id": "post", "state_lifetime": "attempt"},
    }


def test_tracer_two_leg_relay_is_public_truth_blind_and_transfers_only_posterior(tmp_path):
    """The persisted Relay composition reaches the structural engine and freezes selection before truth."""
    from bp_registry.canonical.contracts import CanonicalManifestV4
    from bp_registry.canonical.execution import run_canonical_structural_shot
    from bp_registry.css import fixture_code
    from bp_registry.sampling import DecoderObservation, HiddenTruth

    code = fixture_code()
    hidden_x = np.asarray([1, 0, 0], dtype=np.uint8)
    observation = DecoderObservation("Z", code.hz @ hidden_x % 2)
    manifest = CanonicalManifestV4.model_validate({
        "schema_version": 4,
        "run_id": "phase4-relay-tracer",
        "numerical_profile": "cpu-float64-spa-v1",
        "max_iterations": 4,
        "error_rate": 0.1,
        "policies": _policies(),
        "memory_bindings": [{
            "binding_id": "relay-prior", "kind": "affine_prior", "target": "prior",
            "order": 0, "alpha": 0.5, "state_lifetime": "leg",
        }],
        "relay": {"total_leg_limit": 2, "legs": [{"max_iterations": 4}, {"max_iterations": 4}]},
    })

    result = run_canonical_structural_shot(
        manifest, code=code, observation=observation,
        hidden_truth=HiddenTruth(hidden_x, np.zeros(3, dtype=np.uint8)), shot_id=0,
        ledger_path=tmp_path / "events.jsonl", sample_seed_identity="sample-0", context={"tracer": True},
    )

    assert result.termination == "completed"
    events = (tmp_path / "events.jsonl").read_text(encoding="utf-8")
    assert "relay_transfer" in events
    assert "llr_log_p0_over_p1" in events
