---
spike: 053
idea: canonical-kernel-audit
name: shared-evidence
type: standard
validates: "Given the same decoding problem, when public transports and replay execute, then outputs and evidence preserve their declared identities."
verdict: PARTIAL
related: [043, 044, 045, 046, 049]
tags: [shared-policies, completeness]
---

# Shared execution and evidence closure

Baseline d031436. Continues the approved mathematics → upstream → policy → execution audit. User scope: existing/source-defined counterparts only; no new cross-family adaptations. Production and historical evidence remain unchanged during this audit.

## Research and approach
Independent mathematical oracles, aligned native execution, composition probes and evidence replay answer distinct questions. Prior qualification is carried only for matching source identities. CLI evidence is appropriate to this numerical question; HTML follows the audit.

## Research and approach
The [Sinter v1.15.0 API](https://github.com/quantumlib/Stim/blob/v1.15.0/doc/sinter_api.md) supplies packed detector batches, not stable global shot IDs. Its sampler interface also permits variable batch sizes. The [Stim DEM specification](https://github.com/quantumlib/Stim/blob/v1.15.0/doc/file_format_dem_detector_error_model.md) defines affine detector/observable effects and separator-linked mechanisms. These transport semantics are distinct from a BP mathematical oracle.

Check independent affine projection, multi-byte packing/padding, empty batches, immutable result columns, invalid pre-cast values, stale binding rejection and exclusive ledger export. For randomness, compare one eight-shot call with eight one-shot calls on identical bytes and fixed policy/seed. Hash-check existing full regression, legacy parity and hardware receipts before carrying them.

Run `OMP_NUM_THREADS=1 .venv/bin/python .planning/spikes/053-shared-evidence/probe.py`.

## Results
Normal evidence and transport checks pass. All 14 shared implementation source hashes and 28 evidence hashes still match the prior qualification. Four stored H200 batch ledgers (4,096 shots) pass fresh content/result binding validation; the CPU replay and H200 execution are carried evidence, not new hardware runs. Prior qualification remains 2,462 broad passes / 20 skips, 387 final affected passes, 82 byte-identical legacy receipts and 24 real Sinter worker smoke shots.

Fresh focused regression: **290 passed in 16.80 seconds**, covering the shared decoder, local memory and all circuit tests. These regressions do not cover the new counterexamples; the diagnostic probe correctly reports two passing groups and one failed group.

**F02 — transport-dependent random identity:** `SharedCompiledPolicyDecoder.decode_detailed` assigns `shot_identity=f"circuit:{index}"`, where index restarts at zero for every call. That value feeds the execution identity and attempt/sweep random streams. Changing batch partition therefore changes the effective randomized decoder despite identical model, policy, root seed and observation bytes.

## Investigation trail
A deterministic search (seed 5302, trial 2) found a four-check/eight-fault DEM. Eight copies of syndrome [0,1,1,1] all return valid candidates. Attempt-randomized variable-serial min-sum changes the prediction at row 3 between one batch and single-shot calls; sweep randomization changes row 2. Deterministic and configuration-randomized controls remain identical. Full ledgers, input DEM/rates, output bytes and differing rows are retained. The emitted ledgers replay correctly: replay confirms the transport-dependent choice rather than correcting it.

This is a project reproducibility defect, not a claim that the Sinter interface forbids stochastic decoders. Randomization needs an explicit stable identity contract, rather than an accidental dependency on transport chunking. It can affect logical-error counts and makes batch tuning a scientific setting.

## Recommended correction and impact
Define and version the shared Sinter random identity. The stateless Sinter adapter can derive a deterministic attempt key from model/policy/observation content and the declared seed; CPU APIs can retain explicit caller-provided trial identities. If independent random replicas per identical syndrome are required, provide a higher-level sampler with stable sample IDs instead. A mutable global counter alone does not solve worker/resume ordering. Preserve old shared-v1 receipt replay and test chunking, permutation, separate decoder instances, packed transport and all identity-consuming policy families.

No tracked campaign under data/manifests/experiments/presentation results uses the new shared schema. The tracked PD-prime search finds design/schema documents but no explicit affected binding chain. result-impact.json records the scope and exact matches; untracked/private campaigns are not exhaustively assessed. This audit changed no production code, so existing results are not changed by the audit. After correction, rerun only experiments actually using an affected composition or randomized shared Sinter policy; retain all historical kernel/version identities.

