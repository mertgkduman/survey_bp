"""Real Sinter worker qualification of observation-v2, not a curve study."""
import json
from pathlib import Path

import numpy as np
import sinter
import stim

from bp_registry.canonical.policy_decoder import BinaryPolicy
from bp_registry.canonical.contracts import MemoryCompositionSpec
from bp_registry.circuit import SharedPolicySinterDecoder


def main():
    out = Path(__file__).parent / "sinter-smoke"
    out.mkdir(exist_ok=True)
    circuit = stim.Circuit.generated("surface_code:rotated_memory_x", distance=3, rounds=2,
                                     after_clifford_depolarization=.005)
    memory = MemoryCompositionSpec.model_validate(dict(bindings=[dict(
        binding_id="prior", kind="affine_prior", target="prior", parameters=dict(alpha=.5),
        order=0, history_owner="history:prior", state_lifetime="attempt",
        advance_boundary="source_iteration", refresh_boundary="attempt_start",
        source_status="canonical_adaptation",
        assignment=dict(mode="uniform", low=.2, high=.8, root_seed_identity="b" * 64))]))
    policies = {
        "serial-observation-v2": BinaryPolicy(schedule="check_node_serial", randomized="attempt", max_iterations=4),
        "group-observation-v2": BinaryPolicy(schedule="group_shuffled", max_iterations=4),
        "memory-observation-v2": BinaryPolicy(schedule="check_node_serial", memory=memory, max_iterations=4),
    }
    (out / "circuit.stim").write_text(str(circuit))
    (out / "policies.json").write_text(json.dumps({k: p.model_dump(mode="json") for k, p in policies.items()}, indent=2) + "\n")
    decoders = {name: SharedPolicySinterDecoder(p, str(out / name)) for name, p in policies.items()}
    results = sinter.collect(num_workers=1, tasks=[sinter.Task(circuit=circuit, decoder=name,
        json_metadata=dict(qualification="development_smoke", identity_version="observation-v2",
                           policy=policy.model_dump(mode="json"))) for name, policy in policies.items()],
        custom_decoders=decoders, max_shots=8, start_batch_size=4, max_batch_size=4)
    (out / "results.csv").write_text(sinter.CSV_HEADER + "\n" + "\n".join(r.to_csv_line() for r in results) + "\n")
    counts = {}
    for name, policy in policies.items():
        # Verification must not emit extra worker ledgers.
        compiled = SharedPolicySinterDecoder(policy).compile_decoder_for_dem(
            dem=circuit.detector_error_model(decompose_errors=True))
        count = 0
        for path in sorted((out / name).glob("*.jsonl")):
            count += compiled.verify_ledger(path)["shots"]
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            assert rows[0]["random_identity"]["version"] == "observation-v2"
            for row in rows[1:]:
                single = compiled.decode_detailed(np.array([row["detectors"]], dtype=np.uint8))
                assert single.ledger[1]["binary_execution"] == row["binary_execution"]
        counts[name] = count
    assert all(count == 8 for count in counts.values()), counts
    (out / "verification.json").write_text(json.dumps(dict(verified_shots=counts,
        source="real Sinter collect worker", per_shot_rebatching="exact binary execution",
        interpretation="API/ledger qualification only; no curve or decoder ranking claim"), indent=2) + "\n")
    print(json.dumps(counts))


if __name__ == "__main__":
    main()
