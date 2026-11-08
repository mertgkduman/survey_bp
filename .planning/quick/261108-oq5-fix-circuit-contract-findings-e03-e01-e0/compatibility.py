"""Bounded valid-output and warm CPU control; run before and after the fixes."""
from pathlib import Path
from hashlib import sha256
from itertools import product
import importlib.util
import json
import os
import subprocess
import sys
import time
import numpy as np
import stim
from bp_registry.circuit import CircuitPolicy, PolicyBpSinterDecoder

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("audit_matrix", ROOT / ".planning/spikes/045-policy-admission/probe.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
identities = []
for (rule, parameter), controller, di in product(audit.RULES, ("single", "relay", "guided", "beam"), range(2)):
    policy = CircuitPolicy(rule=rule, parameter=parameter, controller=controller,
        max_attempts=1 if controller == "single" else 5, max_iterations=3,
        beam_width=2 if controller == "beam" else 1)
    result = PolicyBpSinterDecoder(policy).compile_decoder_for_dem(dem=audit.DEMS[di]).decode_detailed(audit.EVENTS)
    identities.append(dict(rule=rule, controller=controller, dem=di, ledger_sha256=sha256(result.ledger_json.encode()).hexdigest()))

rng = np.random.default_rng(261108)
h = np.zeros((32, 64), np.uint8)
for v in range(64):
    h[rng.choice(32, 4, replace=False), v] = 1
rates = rng.uniform(.05, .25, 64)
dem = stim.DetectorErrorModel("\n".join(f"error({p}) " + " ".join(f"D{c}" for c in np.flatnonzero(h[:, v]))
    + f" L{v % 3}" for v, p in enumerate(rates)))
events = rng.integers(0, 2, (64, 32), dtype=np.uint8)
timings = []
for rule, parameter in (("spa", 1.), ("normalized_min_sum", .8)):
    decoder = PolicyBpSinterDecoder(CircuitPolicy(rule=rule, parameter=parameter, max_iterations=8)).compile_decoder_for_dem(dem=dem)
    started = time.perf_counter()
    result = decoder.decode_detailed(events)
    first = time.perf_counter() - started
    times = []
    for _ in range(9):
        started = time.perf_counter()
        repeated = decoder.decode_detailed(events)
        times.append(time.perf_counter() - started)
        assert repeated.ledger_json == result.ledger_json
    timings.append(dict(rule=rule, shots=64, max_iterations=8, first_call_seconds=first,
        warm_seconds=times, median_seconds=float(np.median(times)),
        ledger_sha256=sha256(result.ledger_json.encode()).hexdigest(),
        scope="decode plus per-shot ledger encoding and immutable result binding; excludes disk export"))
output = dict(git_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
    cpu_affinity=sorted(os.sched_getaffinity(0)), output_identities=identities, timing=timings)
Path(sys.argv[1]).write_text(json.dumps(output, indent=2) + "\n")
print(json.dumps({"identical_output_cases": len(identities), "timing": [(t['rule'], t['median_seconds']) for t in timings]}))
