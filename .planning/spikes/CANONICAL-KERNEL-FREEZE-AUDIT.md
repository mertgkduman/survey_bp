# Canonical kernel freeze audit after stable SPA qualification

**The tested mathematical core is sound within the expanded envelope, but the complete kernel contract is not ready to freeze.** Three remaining configuration/state gaps need correction. Stable SPA itself passes the new exact-inference and native-alignment checks. Production remains unchanged from `be7286e`; this audit starts at `12cf2b1` and preserves spikes 008–026.

## Results in the approved order

| Spike | New evidence | Verdict |
|---|---|---|
| [027: mathematical stress](027-stable-spa-stress-audit/README.md) | 32 exact two-check tree cases, 120 mixed-scale check cases, 360 independent parity comparisons, 120 edge permutations, three Pauli-label permutations | PARTIAL: ordinary-range checks pass; C01 overflow guard gap |
| [028: upstream comparison](028-stable-upstream-audit/README.md) | 63 stable-SPA/native ldpc comparisons, eight high-confidence oracle cases, 84 NMS controls, 189 Relay inner-loop controls, five aSCED zero cases, six source-transcribed Sionna cases | VALIDATED for the stated correspondence scopes |
| [029: policy closure](029-schedule-policy-closure/README.md) | Schedule damping sensitivity, source-specific residual budget denial, public-policy and intervention exclusions | PARTIAL: C02 residual profile mismatch |
| [030: execution boundaries](030-freeze-execution-audit/README.md) | Alternate prior construction, full decode/batch overflow, noncontiguous inputs, empty batches, thread restoration and 12 ledger rows | PARTIAL: C03 admission gaps and C01 propagation |

**20 grouped checks: 15 pass and five fail.** The failures represent three findings: C01 twice, C02 once and C03 twice. **364 selected existing regressions pass.** These regressions do not assert the new counterexamples. The previous broad run remains 1,368 passes and one existing skip against identical production source; it was not rerun or counted as new evidence.

Tree marginals agree with exhaustive joint inference within 2.23e-16 (prespecified tolerance 2e-12). Mixed-message comparisons use a 600-digit independent parity partition oracle and 2e-11 tolerance. Stable SPA agrees with native ldpc moderate-range posteriors within 1.84e-15. These are bounded mathematical/implementation checks, not statistical curve reproduction.

## Findings and recommended correction order

### 1. C03 — validate the stored prior before any shortcut

[BoundBinaryFlooding](../../src/bp_registry/canonical/compiled.py) accepts dataclass replacement of its prior with NaN, positive infinity or negative infinity. With zero syndrome and zero iteration limit, the initial shortcut reports convergence instead of rejecting the invalid state.

The BP4 constructor checks finiteness before [float64 buffer conversion](../../src/bp_registry/compiled_contracts.py). On this host, finite float128 values of 1e400 become infinite float64 values and are stored without rejection. An initial shortcut can then report convergence. This requires alternate/direct construction; normal probability-based prior factories are not implicated by this counterexample.

**Acceptance:** normalize into the execution dtype, validate shape/type/finiteness, then own immutable state. Apply this to every bound/direct/replacement construction path and before zero-iteration or initial-convergence shortcuts. Retain valid custom profiles and ordinary binding performance. Do not merely suppress the cast warning.

### 2. C01 — fail before returning or committing nonfinite BP4 state

The [shared policy BP4 sweep](../../src/bp_registry/quaternary/compiled.py) lacks finite-state checks when resolution scope is `scalar_edges`. Finite incoming messages of 1e308 produce nonfinite beliefs, V2C and marginals in a valid redundant-check graph. The `all_messages` and `all_state` scopes reject the same overflow.

A companion graph with finite direct prior LLRs 1e308 demonstrates the same defect through full decode and CPU batch: both return an ordinary iteration-limit outcome after internal overflow. This is an extreme-state guard failure, not an ordinary-confidence accuracy failure or an observed publication-campaign failure.

**Acceptance:** validate all live state boundaries irrespective of rounding scope, including projected messages, beliefs, outgoing messages and marginals. Sweep, single-shot and batch must report numerical failure rather than an ordinary decoded result; thread masks and committed state/work must remain consistent. Use one shared guard contract, with performance measured outside the guard's failure path.

### 3. C02 — close residual schedule/profile admission

[SyndromeResidualSchedule](../../src/bp_registry/canonical/residual.py) accepts a profile declaring damping 0.6 but performs the undamped update. The retained fixture updates an edge to 5.3862943611 under both damping 0 and 0.6; the declared damped value would be 2.7545177444.

The conventional source procedure may intentionally be undamped. **Reject incompatible damped profiles first**, or define and independently qualify a distinct damped residual extension. Inserting damping without accounting for its effect on residual prediction, cache invalidation and source fidelity is insufficient. Public historical v1 residual behavior should remain source-scoped.

The flooding, check-serial, variable-serial and layered controls now honor damping in the tested cases. BPGD and Q-BPGD correctly reject the unqualified stable flooding policy. The residual v1 budget-denial probe preserves state. This finding is specific to numerical compatibility admission, not evidence that the entire residual lifecycle is wrong.

## Policy coverage and boundaries before HTML

| Capability | Current position | Required treatment |
|---|---|---|
| Binary and joint-Pauli stable SPA flooding | Explicit policy v3 in compiled API and CPU batches; expanded ordinary-range oracle checks pass | Keep version and reduction order explicit; close finite-state gaps |
| Floating/fixed-point resolution, damping, MS/NMS/OMS | Existing explicit policy contracts and prior qualification; MS/NMS native controls reconfirmed here | Expose only qualified parameter/scope combinations; boundary formats still use float64 internal storage/arithmetic |
| Binary flooding, layered, check-/variable-serial | Tested damping controls pass | Preserve local-unit/read-write/stopping semantics |
| Conventional syndrome-residual schedule | v1 lifecycle control passes; damped v3 admission is inconsistent | Fix C02 before advertising that composition |
| Pauli serial/ordered transformations | Prior independently qualified scope remains; this turn adds label covariance | Do not infer that compiled stable-policy support automatically extends to these paths |
| BPGD/Q-BPGD, Relay, branching and restart | Source- and version-specific contracts remain; new stable-policy BPGD/Q-BPGD calls are rejected | Qualify controller composition explicitly before extending it; Relay native comparison covers only its inner BP/memory correspondence |
| Clustered RL schedule | External-artifact admission exists; no substitute learned traversal is implemented | Continue to expose it as gated/unavailable without qualified author artifacts |
| Public research manifests/defaults | Frozen research contract rejects stable policy v3; generic profile defaults retain their earlier approximation | Either retain clearly named historical choices or introduce a new public contract; never silently rewrite v1 evidence |
| Correlated code capacity and circuit regimes | Distinct observation/evaluation contracts remain mandatory | Do not infer a universal freeze from binary/Pauli flooding tests; all three publication regimes remain in scope |

The architecture can express a broad range of mathematically compatible policies. Its weak point is that admission knowledge is distributed among factories, dataclasses, schedules and controllers. Before a freeze, consolidate a capability matrix keyed by kernel family, policy version, numerical profile, schedule, controller and backend. Derive negative admission tests and UI availability from that matrix. Every accepted parameter must either act at its declared boundary or have an explicitly documented scope where it is inactive; stable epsilon's unary-only effect is a passing example.

## Primary-source comparison

[ldpc's BP interface](https://software.roffe.eu/ldpc/ldpc/bp_decoder.html) supplies native parallel SPA/NMS correspondence. The installed binary is hashed; its exact build commit is not established. High-confidence native SPA nonfinite results are retained as discrepancies, while independent parity inference determines correctness.

[Pinned Relay](https://github.com/trmue/relay/blob/14cb31a18f9b9d7d099791b793e35b8a2951f8f3/crates/relay_bp/src/bp/min_sum.rs) and [pinned aSCED](https://github.com/kit-cel/quantum_asced/blob/816772071486615dfc7d71d1e15df597edc58a26/src/Decoder/BP/BP_CN_Processing/BP_SPA.cpp) are executed within their recorded inner-function correspondence scopes. Full native pipelines and published curves are not claimed.

[Sionna v2.1.0 source](https://github.com/NVlabs/sionna/blob/v2.1.0/src/sionna/phy/fec/ldpc/decoding.py) provides a useful comparison for callable node updates, ordered callbacks and scheduling/state interfaces. Its float64 phi operation applies internal argument bounds even without optional output clipping. This audit records a source hash and six explicitly labeled NumPy transcriptions; Sionna/PyTorch was not executed. The tag's commit was not independently resolved.

No repository is treated as a universal numerical authority. Exact inference, extrinsic-message equations, algebraic syndrome validity, declared quantization/ordering, scoped work and provenance are separate acceptance requirements.

## Reproduction and freeze decision

Run each numbered probe using its README, then run `verify_freeze_audit.py`. `FREEZE-AUDIT-VERIFICATION.json` checks current production hashes, unchanged historical evidence, exact finding counts, native identities, selected-test receipts and ledger contents.

Close C03 → C01 → C02, repeat their counterexamples as passing regressions, and explicitly settle public stable-policy exposure before committing HTML labels/defaults. Freeze those **versioned, bounded contracts**; future policies and regimes should extend them through new qualified versions rather than changing historical behavior. No finite audit can guarantee that no future defect or extension will require a new version.
