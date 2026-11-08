---
quick_id: 261108-oq5
status: complete
baseline: 3e2381b
implementation_head: 5855049
---

# E03 → E01 → E02 complete

The user-authorized circuit contract fixes are implemented and committed in the
recommended order. Execution was inline through GSD quick, without subagents.
No ordinary BP equations, numerical profile identities, GPU kernels or old
evidence were changed. Publication gates and phase progress remain unchanged.

| Finding | Change | Commit | Before / after evidence |
|---|---|---|---|
| E03 | Validate binary matrix ranks/values, boolean convergence and nonnegative int64-representable iterations before lossless conversion. Bind the owned execution arrays to the ledger. | d6e8756 | e03-red.log: 26 failed, 1 passed; e03-green.log: 97 passed |
| E01 | Check the NMS scaled magnitude before saturation; compiled and auto raise the same NumericalFailure type and boundary as scalar. | 02d890a | e01-red.log: 5 failed, 12 passed; e01-green.log: 78 passed |
| E02 | Reject non-default solution_limit/relay_alpha outside Relay and bias outside guided/beam. Preserve shared defaults, active controls and model-copy revalidation. | 5855049 | e02-red.log: 8 failed, 7 passed; e02-green.log: 93 passed |

The intermediate counts refer to different selected suites. The final regression
suite passes **257 tests in 18.92 seconds**, with no failures or skips. It covers
all circuit tests, CPU batch evidence, ordinary memory and Relay controls. The
new regression file contains 59 cases spanning direct construction, replacement,
lossless normalization, immutability/replay, malformed shapes, empty batches,
overflow on unary/multi-edge checks, large finite parameters, initial stopping,
packed output publication, inactive settings and active controller operands.

## Independent requalification

`results.json` records current source hashes, package versions, git identity and
**12/12 passing groups**. The prior audit probes were imported with output paths
redirected into this task's `requalification/` directory; original source and
failure receipts were not overwritten.

- 1,152 circuit comparisons against independent factor calculations pass.
- 360 matched native ldpc comparisons and four Stim/Sinter affine/packing cases pass.
- 336 policy configurations pass the expected admission/execution checks: 188
  accepted, 148 rejected, 1,504 primary shots and 380 branching shots.
- 24 memory identities/compositions and nested-state ownership checks pass.
- All five original E03 invalid-value examples and all eight E02 inactive-control
  examples now reject; E01 scalar/compiled/auto report the same exception.
- Normal immutable outputs, exclusive export and independent replay pass.
- Factor, native and matrix JSON receipts match their original ordinary-domain
  baselines exactly. The 32 additional controller/rule/DEM ledger identities
  and both 64-shot benchmark ledgers are byte-identical before and after fixes.
- Source comparison establishes that only `circuit/policies.py` and
  `circuit/policy_compiled.py` changed in production. Code-capacity/GPU code and
  stored hardware qualification remain unchanged; no fresh GPU execution is claimed.

The full 2,285-pass suite and H200 qualification from the preceding implementation
remain historical evidence, not reruns on this revision. Affected regression and
independent audit checks passed, so no further full suite or GPU allocation was
needed for these two circuit-module guard changes.

## CPU timing scope

`compatibility.py` retains nine warmed decode measurements for each 64-shot,
32-check/64-fault fixture, including JSON encoding and immutable result binding,
excluding disk export. Final medians are 37.38 ms for SPA and 34.70 ms for NMS.
Baseline medians were 65.71 ms and 37.01 ms. The baseline ran concurrently with
the failing E03 test process, and the unchanged SPA arithmetic also shifted:
**these timings do not establish a speedup attributable to the fixes**. CPU
affinity and raw samples are retained; this is a bounded local timing observation,
not a scaling or universal throughput claim.

The ordinary decode loops remain compiled. E03 uses vectorized batch-boundary
validation; E01 adds a finite check only to the NMS scaling branch; E02 validates
configuration outside the message loop. A separate fresh Numba-cache check
(`first-call.json`) took 3.060 seconds including compilation on a four-shot
fixture, then approximately 0.59 ms per warm call, with identical result ledgers.
The `first_call_seconds` fields in the compatibility files are first calls on
their timing fixture after earlier qualification calls, not cold-JIT timings.

## Repeatable checks

From the repository root:

```sh
OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/circuit tests/canonical/test_batch_evidence.py tests/canonical/test_memory_execution.py tests/canonical/test_memory_composition.py tests/canonical/test_relay.py tests/canonical/test_relay_differential.py
OMP_NUM_THREADS=1 .venv/bin/python .planning/quick/261108-oq5-fix-circuit-contract-findings-e03-e01-e0/qualify.py
```

To produce a new timing receipt without overwriting the saved before/after files:

```sh
OMP_NUM_THREADS=1 .venv/bin/python .planning/quick/261108-oq5-fix-circuit-contract-findings-e03-e01-e0/compatibility.py /tmp/circuit-contract-compatibility.json
```

Spikes 047–049 record the individual closures. The original 043–046 audit stays
historical. These fixes close all three bounded pre-HTML findings; HTML can use
the documented admitted policy subset. Release packaging remains skipped and
scientific curve-reproduction/publication gates remain separate.
