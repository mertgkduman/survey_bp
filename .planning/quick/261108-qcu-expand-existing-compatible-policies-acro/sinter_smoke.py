"""Bounded real Sinter worker smoke; not a scientific reproduction campaign."""
import json
from pathlib import Path
import sinter
import stim
from bp_registry.canonical.policy_decoder import BinaryPolicy
from bp_registry.circuit import SharedPolicySinterDecoder
from bp_registry.resolution import BpFloodingPolicy, ResolutionPolicy


def main():
    out = Path(__file__).parent / "sinter-smoke"
    out.mkdir(exist_ok=True)
    circuit = stim.Circuit.generated("surface_code:rotated_memory_x", distance=3, rounds=2,
                                     after_clifford_depolarization=.005)
    policies = {
        "serial": BinaryPolicy(schedule="check_node_serial", max_iterations=4),
        "impulse": BinaryPolicy(controller="impulse", options=dict(realization="exact_shortening",
            selection="first_convergence", baseline_sweeps=2, attempt_sweeps=2, attempt_cap=2)),
        "precision": BinaryPolicy(max_iterations=4, flooding_policy=BpFloodingPolicy(
            check_rule="min_sum", resolution=ResolutionPolicy("int8", 16, "all_messages"),
            alpha=.875, version="bp-flooding-policy-v2", check_stabilization="exact_unity", product_epsilon=1e-10)),
    }
    (out / "circuit.stim").write_text(str(circuit))
    (out / "policies.json").write_text(json.dumps({k: p.model_dump(mode="json") for k, p in policies.items()}, indent=2))
    decoders = {name: SharedPolicySinterDecoder(p, str(out / name)) for name, p in policies.items()}
    results = sinter.collect(num_workers=1,
        tasks=[sinter.Task(circuit=circuit, decoder=name, json_metadata=dict(qualification="development_smoke")) for name in policies],
        custom_decoders=decoders, max_shots=8, start_batch_size=4, max_batch_size=4)
    (out / "results.csv").write_text(sinter.CSV_HEADER + "\n" + "\n".join(r.to_csv_line() for r in results) + "\n")
    counts = {}
    for name, factory in decoders.items():
        compiled = factory.compile_decoder_for_dem(dem=circuit.detector_error_model(decompose_errors=True))
        count = 0
        for path in sorted((out / name).glob("*.jsonl")):
            count += compiled.verify_ledger(path)["shots"]
        counts[name] = count
    assert all(count == 8 for count in counts.values()), counts
    (out / "verification.json").write_text(json.dumps(dict(verified_shots=counts, source="real Sinter collect worker",
        interpretation="API/ledger qualification only; no curve or decoder ranking claim"), indent=2) + "\n")
    print(json.dumps(counts))


if __name__ == "__main__":
    main()
