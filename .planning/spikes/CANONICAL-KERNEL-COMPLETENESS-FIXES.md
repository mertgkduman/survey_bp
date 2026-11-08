# Canonical kernel completeness corrections

All five findings are corrected and committed in the recommended order:
**D03 → D04 → D01 → D02 → D05**. Re-executing the original audit produces
**32 passing groups, zero failures**; all **19 previously failing invariants**
now pass. Full repository regression completed with **2,251 passed, one existing
skip and 25 baseline fork/multithread warnings** in 1,390.32 seconds. See the
[verification receipt](042-batch-evidence-fix/verification.json).

| Order | Finding and change | Commit | Focused receipt |
|---|---|---|---|
| 1 | D03: shared direct/factory/replacement circuit admission before native execution | `630a934` | [038](038-circuit-admission-fix/README.md): 50 circuit tests |
| 2 | D04: immutable scientific inputs and audited state snapshots; DEM execution digest | `69498ab` | [039](039-model-ownership-fix/README.md): 340 tests |
| 3 | D01: versioned source-iteration dispatch and explicit unsupported group admission | `c3e24bb` | [040](040-update-context-fix/README.md): 116 tests |
| 4 | D02: exact committed serial posterior; redundant assembly removed | `b19d094` | [041](041-committed-posterior-fix/README.md): 91 tests |
| 5 | D05: immutable bound batch results, atomic export and stored-run replay | `502176b` | [042](042-batch-evidence-fix/README.md): 271 integration tests; 36 expanded evidence tests |

Focused suites overlap; their counts must not be added as unique tests.
Integration additionally caught an overbroad initial Hsu admission check. Follow-up
`7b763d2` preserves the historical plain-SPA profile while rejecting update-rule
overlays; 59 targeted route/context/group tests pass. The initial interrupted
run (1,584 passed, one skip, one failure) is retained under
`042-batch-evidence-fix/initial-integration`. The full suite subsequently passed on the
corrected source.

All 234 tracked historical files in spikes 008–037 remain byte-identical.
Only trailing whitespace in new human-readable diagnostic receipts was normalized.

Each fix retains its red/green receipts. The original failed audit remains
unchanged and continues to describe the historical implementation.

## Combined scientific and execution qualification

The [rerun](042-batch-evidence-fix/results.json) reuses the original probes with
outputs redirected into new directories:

- 192 nonuniform four-check Pauli-tree cases agree with independent enumeration;
  100 graph relabeling checks pass. The original 2e-12 tolerances are unchanged.
- 216 heterogeneous-prior circuit SPA/min-sum cases preserve native `ldpc`
  candidates, convergence and iteration counts. Its installed binary hash is
  recorded; the native build commit remains unknown.
- 432 binary/Pauli compiled configurations retain exact single/batch agreement
  across six formats, three scopes, two coefficient modes, two damping values
  and SPA/NMS/OMS. Stored replay checks all 2,592 grid event rows.
- Circuit affine parity, deterministic faults, ownership and export checks pass.
  A further 6,144 baseline/current benchmark rows pass stored replay, including
  historical v1 evidence.

The compiled configuration grid establishes the stated dispatch and backend
agreement. Independent equation checks and source comparisons retain their
separate scopes; the grid is not an independent mathematical proof of every
configuration.

## Performance

The [paired benchmark](042-batch-evidence-fix/cpu-comparison.json) compares
baseline `6f68961` with corrected source `502176b`. Persistent isolated processes
alternate execution order for 15 warm repetitions per case/worker count. Each
case has 512 fixed input shots and an iteration cap of 20. Batch timing includes
the new output copies, validation and digest binding, excluding graph setup,
first compilation and ledger I/O. Fresh-cache first-call timing is retained
separately; it includes compilation and execution, not pure compiler latency.

| Fixture | Workers | Shots/second | Batch speedup over repeated single shots | Throughput relative to baseline |
|---|---:|---:|---:|---:|
| Binary BB72 | 1 | 3,955 | 1.033× | 0.9953× |
| Binary BB72 | 2 | 5,650 | 1.474× | 0.9950× |
| Binary BB72 | 4 | 5,704 | 1.482× | 0.9949× |
| Pauli GB46 | 1 | 2,271 | 1.026× | 0.9985× |
| Pauli GB46 | 2 | 3,209 | 1.451× | 0.9939× |
| Pauli GB46 | 4 | 3,221 | 1.450× | 1.0000× |

The later `7b763d2` follow-up changes only Hsu admission, outside the benchmarked
compiled dependency paths. Candidate, iteration and convergence hashes match exactly. Warm throughput is
within 0.7% of baseline on these fixtures. The available CPUs 56 and 120 are
sibling hardware threads on one physical core; these measurements do not
establish physical-multicore scaling. The compiled arithmetic loops are
unchanged. D02 additionally eliminates one redundant Python belief assembly per
serial unit; no separate serial speed ratio is claimed.

## Versions, capability consolidation and remaining gates

The [contract guide](../../docs/canonical-kernel-contracts.md) consolidates
family, priors, update/assignment, numerical version, schedule, memory/controller,
backend and admission boundaries. Its [machine-readable evidence map](042-batch-evidence-fix/capability-contracts.json)
links the explicit compiled matrix, source authorities, fix commits and tests.
HTML availability must use existing runtime preflight/constructors and expose
these identities and evidence statuses; the catalog is not an admission override.

Corrected scalar dispatch is `source-iteration-v2`; `legacy-zero-v1` preserves
the former standalone/local index behavior. Complete historical evidence can be
replayed with pinned baseline source and environment. CPU export now identifies
`numba-cpu-batch-v2`; the verifier reads v1 without rewriting it. DEM source and
execution digests are distinct. Numerical profile identities, public manifest
defaults, phase position and publication gates remain unchanged.

These fixes close the demonstrated defects for the named tested contracts.
Arbitrary callback/controller combinations, zero-mass joint priors, compiled
indexed assignments, stable-policy circuit integration and published-curve
qualification retain their existing limits. A universal guarantee against any
future behavior change would exceed the evidence.

## Reproduction

Use the installed environment with `OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=4`.
Run `042-batch-evidence-fix/qualify.py`, the repository pytest suite, and
`042-batch-evidence-fix/verify.py`. Benchmark scripts `compare_cpu.py` then
`paired_cpu.py` use isolated baseline/current source trees and fresh caches.
The verifier checks source hashes, unchanged historical files, all stored grid
and benchmark rows, native comparison identity, and final regression receipts.
