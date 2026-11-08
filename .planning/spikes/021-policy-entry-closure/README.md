---
spike: 021
idea: canonical-kernel-audit
name: policy-entry-closure
type: standard
validates: "Given alternate constructors and schedule composition, accepted execution preserves declared numerical semantics"
verdict: PARTIAL
related: [016-scalar-admission-fix, 017-profile-evidence-fix, 022-cpu-graph-integrity]
tags: [admission, composition, constructors]
---

# Spike 021: Close every policy entry point

## Research and approach

Pure local API/contract investigation; reused the validated policy metamorphisms. [Sionna's extension interface](https://nvlabs.github.io/sionna/v2.2.0/phy/api/fec/ldpc/sionna.phy.fec.ldpc.LDPCBPDecoder.html) remains an architectural comparison, not an execution oracle.

| Approach | Choice | Reason |
|---|---|---|
| Retest only normal factories | Control | Those guards were already fixed |
| Exercise dataclass replacement and composed schedule APIs | Primary | These are used by real research callers |
| Execute malformed CSR buffers | Excluded | Unnecessary native memory-safety risk; valid-shape examples suffice |

## Results

Two positive grouped controls pass; three contract checks fail, grouped into two root findings.

**B01 — admission is not closed across construction paths.** Normal factories reject min-sum/SPA and BP4 box-plus/compiled pairings. `dataclasses.replace` accepts both. Binary execution uses SPA under a min-sum profile. BP4 execution declares box-plus but emits about 23.719 where the declared box-plus result is about 48.614. A flooding schedule also accepts a numerical profile different from its kernel and consequently bypasses declared v3 damping. These are ordinary API constructions, not mutation of frozen objects through Python internals.

**B02 — low-level binary serial schedules accept v3 damping but ignore it.** Budgeted public `execute_local_step` calls for both check-node and variable-node serial schedules produce identical buffers at damping 0 and .6. The chosen inputs require a different damped result. Public v3 binary manifest admission is flooding-only, so this does not demonstrate corruption of a qualified public serial run. The low-level extension API should reject the pairing until semantics are qualified, or implement its declared recurrence.

Qualified Pauli neutral-transform, damping sensitivity, ordering and state-isolation controls still pass. The defects concern configuration/entry-point closure, not rejection of the policy architecture itself.

## Recommended boundary

Use one composition validator from normal factories, direct dataclass initialization/replacement, and schedule/session binding. It should validate rule, profile, policy and backend together; incompatible combinations fail before execution. Extend the qualification matrix with a source-grounded oracle for each newly supported schedule/profile pair. Preserve supported historical graph replacements used by reproduction studies.

## Run and evidence

```sh
OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONPATH=src:.planning/spikes .venv/bin/python .planning/spikes/021-policy-entry-closure/probe.py
```

`results.json` contains full profiles, actual/expected buffers, factory rejection controls, source hashes and the independently budgeted serial calls. Production and historical evidence are unchanged.
