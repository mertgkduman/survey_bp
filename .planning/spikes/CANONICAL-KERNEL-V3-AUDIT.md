# Canonical kernel v3: follow-up audit before HTML

**Decision: retain the kernel architecture, but do not freeze the extension/evidence contract yet.** The tested default mathematics and qualified CPU paths pass. Three reproducible contract gaps remain. This audit changed no production behavior and does not advance any scientific/publication phase gate.

Audited production source is identical to stabilization commit `dfe0306` (documentation commit `21a7c48` followed it). Every probe records hashes of all Python production files. The earlier [008–011 audit](CANONICAL-KERNEL-AUDIT.md) remains historical evidence; its seven fixes are not retroactively rewritten by this report.

## Ordered experiments

| Spike | Evidence | Verdict |
|---|---|---|
| [012: mathematics](012-v3-mathematical-audit/README.md) | 768 independent probability-domain recurrence sweeps, 16 exact trees, 216 MAP patterns, 1,003 prior boundaries, 253,945 float16 rounding checks | VALIDATED within tested domain |
| [013: upstream](013-v3-upstream-audit/README.md) | 264 native ldpc comparisons, 189 pinned Relay inner-BP comparisons, extracted aSCED projection/decision/check functions | VALIDATED with explicit source differences |
| [014: policy interfaces](014-v3-policy-audit/README.md) | Composition metamorphisms, direct admission/evidence counterexamples, 49 existing regressions | PARTIAL: two gaps |
| [015: execution/evidence](015-v3-execution-audit/README.md) | 192 full-buffer comparisons, public replay/tamper probes, 114 existing regressions, revalidation of 2,048 CPU ledger rows | PARTIAL: one gap |

The two regression selections total 163 passing tests. They do not assert the three new counterexamples. New probe totals are 18 grouped checks: 15 pass, three intentionally remain failed in the saved evidence. A successful probe process is not equivalent to a passing audit.

## Fix order before freezing

1. **V3-A01 — scalar update/profile admission (medium).** `BinarySpaKernel(profile=MIN_SUM_CPU_F64)` accepts a min-sum profile but executes SPA: incoming `[1,2]` produces approximately 0.735 rather than 1. The compiled constructor rejects this pairing; explicit `MinSumUpdate()` works. Reject the ambiguous scalar construction or resolve its update explicitly, using the same admission contract across backends. Acceptance: symmetric constructor tests, explicit min-sum preserved, no default or historical arithmetic change.
2. **V3-A02 — numerical evidence can misdescribe execution (medium).** Custom dataclass profiles can declare float32, a different exact-zero decision, or a different Pauli tie order while retaining float64/default decisions. Fixed descriptive fields should be derived or validated. Supported variations must have implemented policy parameters and complete resolved evidence. Acceptance: every accepted field is either executed or rejected when inconsistent; legal cap/epsilon/damping variations and historical profile identities remain usable. Public literal-profile schemas are narrower and are not shown vulnerable by these examples.
3. **V3-A03 — result-summary replay validation (high for evidence consumers).** Public quaternary verification returns success after `termination`, `outcome`, `numerical_profile` or `run_fidelity` is individually replaced by fabricated text. Manifest/ledger identity and ledger replay still pass, and work tampering is rejected. Validate deterministic summary fields against replay/preflight; handle output locations separately. Acceptance: one-field mutations of scientific and contract claims fail, normal and historical replay remain valid, scratch cleanup still works.

This order first establishes executable semantics and truthful configuration evidence, then binds public summaries to them. None of these counterexamples demonstrates incorrect default v3 posterior arithmetic. All three matter to a policy research platform and to an HTML layer that may display verified summaries.

## Numerical decision that must remain explicit

The default `exact_unity` safeguard is a declared finite approximation, not globally exact or monotone SPA. A one-neighbor LLR of 38 produces about 37.43; 40 produces about 23.72 because the tanh product rounds to unity and triggers the safeguard. The current independent recurrence checks cover moderate messages; they do not erase this boundary behavior.

Keep this visible in numerical evidence and any interface. If mathematical exactness over the full finite-LLR range is intended as the default standard, qualify a separately versioned stable log-domain check policy before freezing that choice. Do not silently change v3 or historical source-compatible profiles. Standardizing this decision is separate from the three newly discovered API/evidence defects.

## Policy breadth and CPU boundary

| Policy surface | Evidence/extension model | Qualification boundary |
|---|---|---|
| Binary and scalar commuting-Pauli SPA | Independent local factors and exact trees | Distinct compatible mathematical families |
| Min-sum, normalized/offset variants | Explicit check rule and ordered coefficients; native ldpc correspondence | New explicit flooding policy v2; not every schedule/intervention combination |
| Damping and ordered check transforms | Neutral identity, sensitivity, transform order and independent serial oracle in regressions | Public BP4 v4 permits qualified plain/normalized/offset flooding and variable serial with identity intervention |
| Memory, MBP4 and controller policies | Existing state/ownership and named-policy regressions; pinned Relay affine-memory inner loop | Source versions, lifecycle and admission stay explicit; no blanket v3 migration |
| Resolution | Six formats, three rounding scopes, explicit coefficient rounding | Float64 storage/intermediates with boundary quantization; no native low-precision SIMD claim |
| CPU batches | Same compiled per-shot functions; worker restoration, output/work/ledger checks | Qualified flooding only; no arbitrary serial, relay, branch or intervention batching |
| Circuit/detector decoding | Later separate semantic contract | Not validated by this CSS/Pauli audit |

The architecture supports a broad policy vocabulary. It does not need arbitrary callbacks everywhere to be extensible: policies need explicit inputs, mathematical meaning, state ownership, stage order, compatibility and evidence. [Sionna's documented update/schedule/callback/state separation](https://nvlabs.github.io/sionna/v2.2.0/phy/api/fec/ldpc/sionna.phy.fec.ldpc.LDPCBPDecoder.html) is a useful interface comparison; Sionna was not executed here.

## Primary sources and interpretation

- [Lai–Kuo BP4/MBP4 mathematics](https://arxiv.org/html/2104.00304v3): scalar commutation messages and posterior decisions inform independent checks; numerical safeguards are separately identified adaptations.
- [ldpc BP API](https://software.roffe.eu/ldpc/ldpc/bp_decoder.html): executed installed 2.4.1 with binary hash, explicit syndrome input, parallel schedule and aligned damping/scaling. Its exact build commit is not established.
- [Relay min-sum at 14cb31a](https://github.com/trmue/relay/blob/14cb31a18f9b9d7d099791b793e35b8a2951f8f3/crates/relay_bp/src/bp/min_sum.rs): executed isolated native F64 inner BP with affine prior memory; no full Relay control-flow equivalence claim.
- [aSCED at 8167720](https://github.com/kit-cel/quantum_asced/blob/816772071486615dfc7d71d1e15df597edc58a26/src/Decoder/BP/BP4_Decoder.cpp): unchanged extracted C++ functions confirm source decision differences. Its [SPA check update](https://github.com/kit-cel/quantum_asced/blob/816772071486615dfc7d71d1e15df597edc58a26/src/Decoder/BP/BP_CN_Processing/BP_SPA.cpp) exhibits zero/zero NaNs absent from canonical exclusion. Source agreement is evidence, not an infallible mathematical standard.

Prior [CPU timing evidence](../../docs/kernel-stabilization-and-cpu.md) remains tied to unchanged source, and its ledger verification passed again. This audit adds no timing result or statistical decoding-performance claim. Complete aSCED/Relay reproduction, large campaigns, all policy combinations and formal correctness proofs remain outside its scope.

## Reproduction and continuation

Run the four commands in their READMEs in order; pinned native dependencies must remain available. Run `PYTHONPATH=src .venv/bin/python .planning/spikes/verify_v3_audit.py` to verify source hashes, expected recorded findings and regression totals. This validates saved evidence without suppressing unresolved failures.

Complete V3-A01–A03 and decide the documented numerical default before claiming the contract frozen or promoting HTML verification badges. Keep phase 11 status, historical evidence and publication restrictions unchanged.
