# Canonical kernel: boundary audit before HTML

**Do not freeze the full kernel contract yet.** The previously fixed findings remain fixed on their tested entry paths. This expanded audit finds three additional gaps in accepted low-level configurations and demonstrates why the already documented numerical approximation needs a deliberate default-policy decision. Production source is unchanged from the fixes qualified at `a42a1d6` and documented by `e7a0387`.

The architecture remains suitable for compatible policy compositions. The missing protection is systematic agreement between every admitted configuration and every construction/execution path, including dataclass replacement used by research callers.

## Results in the approved order

| Spike | Evidence | Verdict |
|---|---|---|
| [019: numerical envelope](019-numerical-envelope/README.md) | 600-digit parity oracle; 100 degree/scale/sign cases; exact-tree counterexample | PARTIAL: stable primitive passes; default approximation is not globally exact SPA |
| [020: upstream boundaries](020-upstream-envelope/README.md) | 9 high-confidence native ldpc SPA cases, 10 min-sum cases, 5 extracted aSCED checks, 189 pinned Relay inner-loop cases | VALIDATED: discrepancies classified, not treated as correctness targets |
| [021: entry-point closure](021-policy-entry-closure/README.md) | Factory versus replacement, kernel/schedule mismatch, budgeted serial steps, qualified Pauli controls | PARTIAL: B01 and B02 |
| [022: CPU/graph integrity](022-cpu-graph-integrity/README.md) | 840 ledger rows in 210 batches, independent stopping/work/validity checks, nondefault v1 cap | PARTIAL: B03; qualified CPU matrix passes |

Totals: **15 grouped checks, 10 passing and 5 failed assertions**. The five failures represent one known numerical limitation, two manifestations of B01, B02, and B03. Selected existing regressions pass **183 tests**; these do not assert the new counterexamples. Previous broad qualification remains 1,162 passes and one existing skip against identical production source; it was not counted as a new run.

## Numerical default: decide before freezing

On the tree `H=[[1,1,1]]`, syndrome `[1]`, prior LLR 40, exact SPA posterior LLR is approximately **0.693147** for each variable. Current v3 yields **16.281002**. The tanh product rounds toward unity and triggers the finite safeguard. This is a large posterior-confidence distortion, not just a harmless final-digit difference. The input is a stress fixture, not a claimed campaign probability or error-rate measurement; high LLRs can also arise as internal messages.

The 100-case envelope spans 1/2/4/16/64 incoming neighbors and magnitudes 1e-12–1000. The default exceeds the prespecified 2e-11 exact-SPA tolerance in 60 cases. Existing scalar stable log-domain box-plus primitives agree with the independent oracle across all 100 cases. Their availability does **not** qualify an entire replacement scalar/compiled engine, all policies or CPU speed.

**Recommendation:** qualify a separately versioned stable log-domain SPA policy for the generic default, retaining v3/exact-unity as an explicit reproducibility option. Define check reduction, unary behavior, optional clipping and quantization boundaries together. Promote only after independent tree/recurrence checks, full-buffer parity, stopping/work checks, historical replay and matched CPU measurements. If retaining the present default instead, its approximate numerical envelope must remain part of the public contract; it cannot be described as globally exact SPA.

## New findings

### B01 — Alternate construction and binding bypass admission (high for extension readiness)

Normal factories reject unsupported pairings, but `dataclasses.replace` on a valid compiled graph bypasses those checks. A binary graph can declare min-sum while executing SPA. A Pauli graph can declare box-plus while executing tanh-product, producing C2V about 23.719 instead of the declared rule's 48.614. `FloodingSchedule` can also accept a profile different from its kernel and silently change clipping/damping behavior.

These examples use valid graph shapes and ordinary public construction APIs. They do not require malicious mutation of frozen objects. Existing reproduction scripts legitimately use replacement, so simply banning all replacement would break supported work.

**Acceptance:** one shared invariant validator runs for factories, direct initialization/replacement and schedule/session binding. It validates the effective rule/profile/policy/backend tuple and graph buffer structure before compiled execution. Supported historical replacements remain valid; incompatible replacements fail before returning a graph. Metadata describes the one effective rule actually executed.

### B02 — Binary serial schedules accept but ignore v3 damping (medium; low-level API)

Check-node and variable-node serial schedules accept kernels with damping 0 and .6 and produce identical committed message buffers on inputs requiring a damped difference. The probe uses budgeted public `execute_local_step`, not an internal bypass. Public v3 binary manifests remain flooding-only, so no qualified public serial execution is shown corrupted.

**Acceptance:** either reject those profile/schedule pairs at the shared admission boundary or implement and independently qualify their local-update recurrence, message freshness, damping stage and stopping boundaries. Tests must include parameter sensitivity, not only determinism.

### B03 — Compiled BP4 ignores an accepted v1 saturation parameter (medium)

The ordinary factory accepts `replace(QBP4_F64_V1, saturation=1)`. Prior conversion honors the selected cap, but compiled v1 update/decode calls use the constant default limit. Scalar output caps at 1 while compiled beliefs reach 1.6201145 on the retained fixture. Standard v1/v3 defaults are unaffected by this example.

**Acceptance:** propagate the selected parameter through all compiled v1 sweep/decode paths, or reject unsupported values explicitly. Check full messages, beliefs, decisions and stopping across nondefault caps; preserve standard historical behavior.

Resolve B01's shared validation boundary first, include B02's compatibility rule there, then qualify B03's backend parameter handling. The numerical-default work is a separate versioned behavior change and should be completed before a final freeze claim.

## What remains supported

| Surface | Evidence | Boundary |
|---|---|---|
| Binary and Pauli default recurrences in the prior tested envelope | Independent probability-domain and exact-tree evidence, source hashes unchanged | Expanded high-confidence exactness fails as above |
| Explicit min-sum and normalized min-sum | New high-confidence native agreement; existing offset/quantization contracts | No claim that every memory/schedule combination is admitted |
| Pauli flooding, serial damping and ordered transforms | Prior independent serial oracle plus repeated identity/sensitivity/isolation controls | Binary serial-v3 mismatch is separate |
| CPU flooding | New 840-row matrix, workers 1/2, caps 0/1/4, unary/isolated/empty-binary cases | No arbitrary controller or serial batching |
| Failure handling | Overflow rejects outputs and restores thread count | Parallel overflow exposes Numba SystemError rather than a normalized numerical-failure exception |
| Circuit/detector semantics and full source curves | Not evaluated here | Existing staged scientific gates remain open |

## Open-source comparison is not an infallible standard

Installed [ldpc BP](https://software.roffe.eu/ldpc/ldpc/bp_decoder.html) 2.4.1 returns negative-infinite posteriors in the retained LLR-40/100/500 SPA fixtures. Its explicit min-sum cases agree with the independent linear result. The package binary is hashed; an exact build commit is not established.

Pinned [aSCED SPA](https://github.com/kit-cel/quantum_asced/blob/816772071486615dfc7d71d1e15df597edc58a26/src/Decoder/BP/BP_CN_Processing/BP_SPA.cpp) uses a total-product division that produces zero/zero NaNs in extracted function probes. Pinned [Relay](https://github.com/trmue/relay/blob/14cb31a18f9b9d7d099791b793e35b8a2951f8f3/crates/relay_bp/src/bp/min_sum.rs) retains the tested inner-BP/affine-memory correspondence. Neither comparison establishes full decoder or curve reproduction.

[Sionna's phi-domain check update](https://nvlabs.github.io/sionna/v2.2.0/phy/api/fec/ldpc/sionna.phy.fec.ldpc.cn_update_phi.html) is an additional primary design reference for stable check arithmetic; Sionna/PyTorch was not installed or executed. Mathematical oracles and explicitly aligned numerical contracts take precedence over copying another implementation's defects.

## Freeze gate and reproducibility

Establish an executable matrix of admitted family × rule × profile × schedule × backend combinations. Every admitted numerical parameter needs a sensitivity/equivalence check; every construction path must enforce the same matrix. Add independent oracles for each newly admitted recurrence, preserved historical replay, complete evidence validation, and explicit unsupported-pair rejection. This gives a maintainable freeze gate; repeated passing happy-path regressions cannot certify untested combinations.

Run the probe command in each README in order. Then run:

```sh
PYTHONPATH=src .venv/bin/python .planning/spikes/verify_boundary_audit.py
```

This checks source identity, retained findings, original-problem validity of the compressed CPU ledger, regression totals and absence of production changes. It intentionally retains failed audit assertions. All prior spikes and scientific-phase statuses are preserved; no HTML changes were made.
