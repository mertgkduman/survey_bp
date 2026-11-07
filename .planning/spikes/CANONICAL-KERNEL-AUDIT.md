# Canonical kernel audit and stabilization contract

**Date:** 2026-11-06  
**Scope:** User-approved spikes 008 → 009 → 010 → 011, before further HTML work.  
**Verdict:** **Not ready for a behavior freeze.** All four investigations are complete; all four have a PARTIAL scientific verdict. Production decoder behavior was not changed by this audit.

The core binary and scalar-quaternary message equations are supported by independent small-graph checks and native reference comparisons. The implementation nevertheless has concrete decision, composition, boundary, and evidence defects. Existing tests are not sufficient to establish readiness: all 398 selected regression tests pass while the new probes expose these issues.

## Evidence obtained

| Experiment | Executed evidence | Result |
|---|---|---|
| [008: mathematics](008-mathematical-correctness/README.md) | 192 binary and 192 Pauli probability-domain recurrence sweeps; exact tree marginals; 48 independently expressed damping sweeps | Maximum recurrence error ≤3.33e-16; hard-decision and finite-domain counterexamples |
| [009: upstream](009-open-source-cross-check/README.md) | 180 native ldpc comparisons, 189 native Relay inner-BP/memory comparisons, 29 unchanged extracted aSCED C++ function probes | Posteriors agree within fixed tolerances; native ties explained; aSCED decision defect confirmed |
| [010: policies](010-policy-extensibility/README.md) | 14 new grouped diagnostics and 238 existing regression tests | State isolation and compatibility protections pass; v2 damping is silently omitted in two lower-level schedule paths |
| [011: execution](011-execution-consistency/README.md) | 192 randomized scalar/compiled buffer comparisons, boundary cases, two complete public run/replay bundles, 160 existing tests | Buffers agree ≤4.44e-16; initial candidates and capped ledger work disagree with the intended contract |

Tolerance was specified before each experiment: 2e-12 for independent small-graph oracles; 2e-11 for native and backend differentials. Diagnostic results contain 51 grouped checks, 31 passing and 20 finding-bearing; several findings repeat the same root cause across profiles. These counts are not a scientific confidence level or a count of independent defects.

## Prioritized findings

### F01 — High: default BP4 v2 can select a nonmaximal posterior state

**Location:** `src/bp_registry/quaternary/numerics.py:244`, with corresponding compiled strict-decision branches.  
**Reproduction:** X/Y/Z LLRs `[-2,0,-2]` give maximal probability to X and Z, but v2 chooses Y. Three of 27 grid inputs fail the maximizing-set invariant; v1 passes that grid.  
**Exposure:** Generic/default scalar BP4 v2 and corresponding strict compiled paths. The alternative explicit `min_llr` policy has a different decision rule; this audit does not conflate them.  
**Evidence:** [008 results](008-mathematical-correctness/results.json), [009 results](009-open-source-cross-check/results.json).

The pinned aSCED source contains this same strict comparison ladder. Its reproduction is source-faithful, but [Lai–Kuo Algorithm 1](https://arxiv.org/html/2104.00304v3#S3) specifies a minimum-LLR decision. A fallback outside the minimum set is not just a tie preference.

**Required stabilization:** Separate a named aSCED source-compatibility decision from a generic maximizing-set decision. Promote a corrected generic default under a new profile identity; retain v1/v2 replay. Exhaustively check every equality pattern across I/X/Y/Z, including cases where only X and Z tie, in scalar and compiled paths. Do not erase the existing regression that records historical behavior; scope it to the historical profile.

### F02 — High: capped public quaternary ledgers lose already executed work

**Locations:** `quaternary/kernel.py:273`, analogous terminal constructions in `quaternary/schedules.py:195` and `:277`, and `quaternary/execution.py` serialization of `sweep.work`.  
**Reproduction:** Permit one BP call, execute it, then attempt a second. The budget tree records one call, while the capped snapshot reports an all-zero work vector.  
**Exposure:** Direct v1/v2 sessions and both tested public scalar schemas. The full public API emits zero work and its replay verifier accepts it.  
**Evidence:** [Numerical-v1 public bundle](011-execution-consistency/quaternary_experiment_v2-budget-counterexample/input.json), [numerical-v2 public bundle](011-execution-consistency/quaternary_experiment_v3-budget-counterexample/input.json), each with retained `events.jsonl`, `manifest.json`, and `result.json`.

**Required stabilization:** Distinguish zero incremental work for a denied request from cumulative committed work. Every terminal snapshot must retain the committed cumulative vector. Independently reconcile ledger totals with admitted work; replaying the same implementation is insufficient. Apply this to cap and numerical-failure terminals in plain, transformed, serial, and policy-specific sessions. Preserve historical evidence and version the corrected evidence interpretation rather than rewriting old ledgers. Audit retained capped results before using their work statistics; this investigation does not establish how many historical results are affected.

### F03 — High for extension readiness: two BP4 schedule paths ignore v2 damping

**Locations:** `quaternary/schedules.py:185` and `:266`; compare `quaternary/kernel.py`'s ordinary sweep.  
**Reproduction:** Adding normalization by 1 changes V2C by 0.10986122886681093. Changing serial damping from 0 to 0.6 produces no change.  
**Exposure:** Direct lower-level v2 sessions and the compatibility resolver. **The public schema-v3 validator correctly blocks transformed and serial v2**, limiting current exposure.  
**Evidence:** [010 results](010-policy-extensibility/results.json).

**Required stabilization:** Either reject these combinations consistently at every admission boundary or execute the declared damping at a precisely specified schedule-local boundary. Require identity-transform invariance, nonidentity parameter sensitivity, and a probability-domain serial oracle before enabling public support. Centralize shared update stages so adding a transform cannot select a different, incomplete sweep implementation.

### F04 — Medium: compiled initial candidates do not reflect supported priors

**Locations:** `canonical/compiled.py:125` and `:191`; `quaternary/compiled.py:178` and `:280`.  
**Reproduction:** Binary p=.8 with cap zero or an edgeless graph yields ones in scalar initialization but zeros in compiled initialization. BP4 prior `[.1,.6,.2,.1]` on an XX check yields `[X,X]` in scalar v1 but `[I,I]` in compiled v1's zero-syndrome shortcut, including with a positive cap. At cap zero, Pauli v2 also differs in convergence flag.  
**Evidence:** [011 results](011-execution-consistency/results.json).

**Required stabilization:** Compute the initial candidate using the selected prior/decision rule, or explicitly name an all-zero/all-I shortcut as a separate policy with its eligibility restriction. Specify initial checking, final candidate validity, and termination reason separately. Test biased/nonuniform priors, disconnected variables, edgeless binary graphs, zero iterations, and both stopping modes. Corrected compiled behavior requires an explicit backend/profile migration for any historical result that depended on the old shortcut.

### F05 — Medium contract gap: explicit float64 SPA has a second stabilization rule

**Location:** `canonical/compiled.py:327`, versus `_v2_check` and scalar numerics; analogous duplicated policy/plain paths exist in BP4.  
**Reproduction:** With identical float64 SPA, damping .1 and no shortcut, excluded-neighbor LLR 30 gives C2V 29.9998336 in plain v2 but 23.7189980 through `BpFloodingPolicy`.  
**Cause:** Plain v2 changes only products rounded to exact ±1; the policy route clamps all products outside ±(1−1e-10).  
**Evidence:** [011 results](011-execution-consistency/results.json).

The explicit policy has its own version ID; this is not an assertion that two differently named implementations must be bitwise identical. The problem is that the epsilon/clamp boundary is not a selectable, complete numerical contract in the policy object. Choosing float64 and SPA does not identify the plain canonical v2 recurrence.

**Required stabilization:** Expose the check stabilization rule and epsilon as named numerical settings, compose them explicitly, and share that primitive across plain and policy paths. Test neutral-policy equivalence only when **all** effective settings match. Until then, label these as different numerical adaptations.

### F06 — Medium numerical robustness: finite binary priors can fail in an intermediate ratio

**Locations:** `canonical/numerics.py:95` and `:115`.  
**Reproduction:** `p=np.nextafter(0.,1.)` is accepted by the strictly-positive domain check, and its true float64 log odds is finite (~744.44), but v2 forms `(1-p)/p` first and overflows. Both helpers fail.  
**Evidence:** [008 results](008-mathematical-correctness/results.json).

**Required stabilization:** Use a stable difference of logarithms under a new numerical contract, or explicitly bound the admissible probability domain before decoding. Test subnormals, probabilities near one, and invalid/nonfinite inputs. Avoid silently changing the frozen single-ratio profile's trajectory or evidence.

### F07 — Medium admission gap: direct update/profile combinations are ambiguous

**Location:** `canonical/kernel.py:36` constructor and `canonical/updates.py:46`.  
**Reproduction:** `BinarySpaKernel(update_rule=MinSumUpdate())` accepts a clipped v1 min-sum primitive inside the default damped/unclipped SPA-v2 surrounding state.  
**Exposure:** Low-level constructor; public closed registries impose separate restrictions.  
**Evidence:** [010 results](010-policy-extensibility/results.json).

**Required stabilization:** Validate the complete update/profile/schedule combination or require an explicitly named mixed adaptation. Kernel-family identity must not imply SPA when a supplied check update is min-sum. Test rejection and explicit admission at low-level and public boundaries.

## Intentional differences to retain explicitly

- **Exact-unity safeguard:** In both v2 families, one-neighbor input 38 produces ≈37.43, while 40 produces ≈23.72. This follows the selected source-style rule, but it is nonmonotonic and not exact SPA in the saturated domain. Decide deliberately whether the generic default should retain it; do not change it merely because a smoother rule looks attractive. Prior held-out numerical results belong to their existing profile.
- **Native zero ties:** ldpc and Relay choose bit one for zero beliefs; the canonical binary rule chooses zero. The 58 ldpc and 60 Relay candidate discrepancies in these experiments are confined to zero/near-zero beliefs. They are explained policy differences, not unexplained posterior errors.
- **Saturation and quantization:** Clipping boundaries, quantization scope, coefficient rounding, and damp-before/after-round order are algorithmic settings. Float64 storage of quantized messages does not demonstrate native low-precision arithmetic performance.
- **Kernel families:** Binary X/Z inference, correlated four-state inference, and circuit fault/detector factorization remain separate mathematical contracts. The audit does not qualify new circuit models or arbitrary binary-to-quaternary ports.

## Contract to stabilize before extending the interface

| Boundary | Required explicit choice | Acceptance evidence |
|---|---|---|
| Problem and prior | Immutable observed problem, Pauli order, positive-domain/smoothing rule, per-variable priors | Exact algebra and malformed-input probes; no hidden truth in policy views |
| Check update | SPA/MS/NMS/OMS, reduction order, degree-zero/one behavior, stabilization, normalization/offset order | Independent local-factor oracle and pinned native comparisons |
| Variable update | Prior/memory source, excluded-neighbor operation, posterior clipping, edge feedback | Probability-domain oracle, memory and exclusion fixtures |
| Decision | Maximizing-set rule and deterministic tie order or named source-compatible variant | Exhaustive ties and scalar/compiled parity |
| Schedule | Unit, read freshness, commit boundary, seeded order, local versus iteration memory advance | Identity/sensitivity tests, noncommuting-order tests, denied-update rollback |
| Intervention | Finite prior change versus exact fixation, graph transform, reset/continue/clone semantics | Original-problem invariance, branch isolation, replayed lineage |
| Numerical policy | Every clip, epsilon, rounding boundary, coefficient orientation, dtype/intermediate convention | Exact profile evidence plus same-setting cross-backend comparisons |
| Stopping and work | Initial check, fixed-budget versus first-valid, terminal validity, leaf and cumulative counters | Zero-budget and cap-after-progress tests; independent ledger reconciliation |
| Backend | Shared semantic stages; explicit supported matrix | Complete-buffer, candidate, stopping, and work agreement; unsupported combinations fail closed |
| Migration | Historical replay identity versus corrected default/evidence version | Frozen v1/v2 fixtures continue to replay; new profiles pass the new invariants |

This supports many policies without making arbitrary combinations automatically valid. A new policy should provide equations, capabilities, private state ownership, advance/reset/clone boundaries, compatibility predicates, and work charges. It should not require copying another full BP loop. The existing architecture already supplies much of this; the duplicated schedule/numerical paths are the main implementation weakness exposed here.

## Reproduction and limits

Run each `probe.py` in numerical order using its README command. Each writes a deterministic-case result file with environment versions, tested production-source hashes, and a Git HEAD. Probe process exit success means the investigation ran; inspect the result's `failed` count. The two pytest XML/log pairs preserve the 398 passing existing tests.

Run `.venv/bin/python .planning/spikes/verify_kernel_audit.py` to check retained counts, regression outcomes, manifest verdicts, counterexample structure, and unchanged production-source hashes without rerunning decoders. It verifies artifact integrity, not kernel correctness. Public bundles preserve original receipts separately and relocate only filesystem metadata in the replayable receipt; their manifest and ledger bytes are unchanged.

Native details: ldpc is pinned to installed release 2.4.1 plus binary hashes; its exact upstream build commit was not established. Relay source is pinned to `14cb31a18f9b9d7d099791b793e35b8a2951f8f3`, with an existing isolated F64 binary identified by hash. aSCED source is pinned to `816772071486615dfc7d71d1e15df597edc58a26`; its two original C++ function bodies were compiled unchanged in a disposable host. These are three different evidence strengths, documented separately. Full native aSCED matched-shot access remains unqualified by this audit.

No new Monte Carlo publication campaign or Slurm job was run. These deterministic tests establish counterexamples and bounded mechanism agreement, not published-curve reproduction, decoder superiority, or the frequency/impact of each defect on realistic codes. There is no claim that a finite test suite can guarantee no future behavior changes. The actionable endpoint is a versioned, independently tested contract with explicit exclusions.

**Recommended next work:** Stabilize F02 and F01 first; resolve F03–F07 against the contract above; then rerun these probes and the frozen regression fixtures before resuming HTML integration. Existing scientific phase gates and campaign authorization remain unchanged.
