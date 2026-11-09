"""Bounded matched CPU timing; all decoder receipts retained beside timings."""
import json
from pathlib import Path
from time import perf_counter

import numpy as np
from bp_registry.canonical.policy_decoder import BinaryPolicy, BinaryPolicyDecoder

out = Path(__file__).parent
rng = np.random.default_rng(1082026)
h = np.zeros((64, 128), dtype=np.uint8)
for row in h:
    row[rng.choice(128, 5, replace=False)] = 1
priors = rng.uniform(0.4, 3.5, 128)
events = rng.integers(0, 2, (12, 64), dtype=np.uint8)
results, timings = {}, {}
for backend in ("compiled", "scalar"):
    decoder = BinaryPolicyDecoder(h, BinaryPolicy(backend=backend, max_iterations=10))
    warm = decoder.decode(events[0], prior_llrs=priors, shot_identity="warmup")
    (out / f"timing-{backend}-warmup.json").write_text(warm.ledger_json + "\n")
    start = perf_counter()
    batch = [decoder.decode(s, prior_llrs=priors, shot_identity=f"timing:{i}") for i, s in enumerate(events)]
    timings[backend] = perf_counter() - start
    results[backend] = batch
    (out / f"timing-{backend}.jsonl").write_text("".join(r.ledger_json + "\n" for r in batch))
for a, b in zip(results["compiled"], results["scalar"], strict=True):
    np.testing.assert_array_equal(a.candidate, b.candidate)
    assert (a.iterations, a.converged) == (b.iterations, b.converged)
report = dict(shots=12, checks=64, variables=128, edges=int(h.sum()), max_iterations=10,
              seconds=timings, scalar_over_compiled=timings["scalar"] / timings["compiled"],
              agreement="exact candidates, iterations and convergence",
              includes="decoding and complete detailed result/ledger serialization",
              excludes="JIT warmup, graph construction and file I/O",
              interpretation="bounded local engineering timing; not a publication scaling result")
(out / "timing.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
