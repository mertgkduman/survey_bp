# V3 contract fixes: completed in recommended order

The three findings from the [v3 audit](CANONICAL-KERNEL-V3-AUDIT.md) are fixed. Decoder equations, named-profile serialization, historical ledgers and compiled hot-loop bodies are preserved. Reserved profile identities remain protected; non-reserved study labels continue to work with complete validated numerical evidence. The changes tighten admission and verification; they do not introduce a new numerical default or a new speed claim.

| Order | Finding | Fix | Commit |
|---|---|---|---|
| 1 | V3-A01: implicit SPA accepted a min-sum profile | Scalar and compiled constructors reject the ambiguous profile, including nondefault saturation; explicit min-sum remains supported | `29a7023` |
| 2 | V3-A02: profile metadata could contradict execution | Validate fixed fields against implementation contracts; preserve implemented numerical parameters and all seven named-profile evidence snapshots | `59ea13b`, compatibility follow-up `a42a1d6` |
| 3 | V3-A03: altered summary claims passed replay | Compare all deterministic summary fields and JSON types, including missing/extra and nested claims; preserve historical accounting and relocatable bundles | `e16c508` |

## Evidence

- [016](016-scalar-admission-fix/README.md): reproduced two failures, then 76 focused tests passed.
- [017](017-profile-evidence-fix/README.md): reproduced 113 failures, then 247 focused tests passed, including fixed-field, numeric-domain and subclass-default cases. The broad suite subsequently exposed a historical alias dependency; 159 focused compatibility tests pass after preserving those aliases and custom study labels.
- [018](018-public-summary-fix/README.md): reproduced 17 failures, then 125 focused tests passed across schema versions, historical receipts and current policy paths.
- Combined independent qualification: **18 grouped checks passed, zero failed**. Includes 768 probability-domain recurrence sweeps, 16 exact-tree cases, 216 MAP patterns, 253,945 float16 boundaries, native ldpc/Relay and extracted aSCED checks, policy metamorphisms, 192 full-buffer comparisons, and corrected receipt counterexamples.
- Broad canonical/research regression: **1,162 passed, one existing notebook-related skip, zero failures**, recorded in `018-public-summary-fix/regression.xml` and `regression.log`. Focused and broad selections overlap and must not be added together.

The independent recurrence maximum error remains 4.44e-16 binary and 2.22e-16 Pauli. Full-buffer maximum error remains 4.44e-16. Saved qualification records source hashes and revision `a42a1d6`. Spikes 008–015 are unchanged historical evidence; their recorded failures are not overwritten as passes.

## Reproduce

```sh
OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=4 .venv/bin/python -m pytest -q tests/canonical tests/research --tb=short
OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONPATH=src:.planning/spikes .venv/bin/python .planning/spikes/018-public-summary-fix/qualify.py
PYTHONPATH=src .venv/bin/python .planning/spikes/018-public-summary-fix/verify_fixes.py
```

The independent script reuses pinned native dependencies from spike 013. The verifier checks current source hashes, regression artifacts, original audit preservation, and unchanged compiled functions/modules. Original audit and timing verifiers bind their original source revision; use the new verifier for this fixed revision.

## Remaining boundary

All three requested defects are resolved. Supported policies retain their existing compatibility boundaries. The `exact_unity` safeguard remains a documented finite approximation with nonmonotone behavior at very large LLRs. Changing that default would require separate numerical-policy qualification/versioning; these contract fixes do not silently change it. No blanket proof of arbitrary policy combinations, full source-curve reproduction or circuit-level qualification follows.

Phase 11 and publication gates are unchanged. HTML work was not performed.
