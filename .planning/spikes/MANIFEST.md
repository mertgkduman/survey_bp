# Spike Manifest

## Ideas

### pfister-slide-bp-reproduction

Record the BP policies, settings, curves, and conclusions supplied in Dr. Pfister's presentation excerpt, then probe whether this project's fast decoders can reproduce the B1 and double-Gross code-capacity results on paired depolarizing errors.

**Requirements:**

- Keep presentation data distinct from newly simulated measurements.
- Place decoder-from-policy files, data, and plots under `from_dr_pfister_presentetations` (the requested spelling).
- Preserve the reported Q8, damping, stopping, work, and logical-failure meanings, with assumptions marked explicitly.
- Compare decoders on the same sampled errors and retain denominator and paired discordance counts.
- Compare uncapped and check-capped float64 BP4 on scaled, held-out same-error sweeps before choosing a canonical numerical default.
- Apply comparable numerical-policy ablations to binary BP and keep its outcome separate from BP4 selection.
- Preserve the frozen v1 canonical numerical profiles and their existing ledger semantics when adding a better-performing versioned default.

### canonical-kernel-audit

Audit the binary and quaternary canonical kernels before further HTML work, using independent mathematical oracles, pinned open-source implementations, policy composition probes, and execution-path consistency checks.

**Requirements:**

- Run spikes 008–011 in order, as explicitly approved by the user.
- Use exact small-graph inference and independently implemented recurrences; agreement between related backends alone is insufficient.
- Record repository revisions, settings, numerical tolerances, counterexamples, and intentional source-specific differences.
- Assess both correctness and extension contracts for BP-internal policies; retain incompatible combinations as explicit exclusions.
- Preserve frozen profile identities and existing evidence. This audit produces reproducible findings and a prioritized stabilization contract before any behavior migration.
- Reuse prior numerical evidence without treating curve proximity as an algebraic proof.

- Continue the approved four-part audit order on stabilized v3 as spikes 012–015, preserving prior evidence and testing new boundaries before a freeze decision.

- Fix V3-A01, V3-A02, then V3-A03 in that order as explicitly requested; preserve numerical execution and historical audit evidence.

- Continue post-fix verification in the approved mathematical, upstream, policy, execution order; target boundary and alternate-entry gaps as spikes 019–022 without changing production behavior.

- Fix B01 → B02 → B03, then qualify a separately versioned stable SPA policy; retain historical versions and evidence.

- Continue post-fix freeze assessment in the approved mathematical, upstream, policy and execution order; preserve production behavior and prior evidence while probing newly exposed boundaries.

- Fix C03 → C01 → C02 as approved; preserve historical evidence and source-scoped residual behavior, qualify finite-state failure handling and CPU throughput.

- Broaden the approved four-part audit to comprehension and completeness: explicit capability coverage, independent mathematical checks, upstream correspondence, and circuit/evidence boundaries before HTML. Preserve prior evidence and production behavior.

- Fix completeness findings D03 → D04 → D01 → D02 → D05 in the approved order; retain all historical evidence, explicit replay/version boundaries, and qualify CPU performance.

## Spikes

| # | Idea | Name | Type | Validates | Verdict | Tags |
|---|------|------|------|-----------|---------|------|
| 001 | pfister-slide-bp-reproduction | Slide evidence | standard | Given the supplied slides, when data and policies are transcribed, then every curve point and setting is attributable | VALIDATED | provenance, policies |
| 002 | pfister-slide-bp-reproduction | Policy kernel | standard | Given the existing fast decoders, when both code fixtures and slide knobs are applied, then numerical behavior is executable and qualified | PARTIAL | decoder, q8, codes |
| 003 | pfister-slide-bp-reproduction | Paired reproduction | standard | Given qualified code and policy variants, when shared errors are decoded, then measured LER and work can be compared with the slide | PARTIAL | simulation, statistics |
| 004 | pfister-slide-bp-reproduction | BP4 numerical scale-up | comparison | Given matched hold-out B1 and double-Gross errors, when capped and uncapped float64 BP4 variants decode a p sweep, then source proximity and work differences are measurable | VALIDATED | bp4, numerics, simulation |
| 005 | pfister-slide-bp-reproduction | Binary numerical scale-up | comparison | Given the same sampled errors, when binary SPA cap variants decode both CSS halves, then the effect on block LER and work is measurable | VALIDATED | binary, numerics, simulation |
| 006 | pfister-slide-bp-reproduction | Canonical numerical promotion | standard | Given held-out evidence and algebraic tests, when the best policy becomes a versioned canonical default, then new runs improve without changing frozen v1 replay | VALIDATED | canonical, compatibility |
| 007 | pfister-slide-bp-reproduction | Full v2 curve sweep | comparison | Given promoted v2 kernels, when every source probability is simulated on paired errors, then source proximity and uncertainty can be assessed point by point | IN_PROGRESS | canonical, reproduction, simulation |
| 008 | canonical-kernel-audit | Mathematical and numerical correctness | standard | Given small binary and Pauli graphs, when independently evaluated, then messages and decisions satisfy their declared mathematical contract | PARTIAL | mathematics, numerics |
| 009 | canonical-kernel-audit | Open-source cross-check | comparison | Given pinned upstream implementations and aligned settings, when matched inputs run, then agreement or discrepancies are explained | PARTIAL | upstream, provenance |
| 010 | canonical-kernel-audit | Policy extensibility | standard | Given supported policy compositions, when exercised, then order, state isolation, and compatibility are explicit | PARTIAL | policies, architecture |
| 011 | canonical-kernel-audit | Execution consistency | comparison | Given identical profiles and observations, when public, scalar, and compiled paths run, then behavior and evidence agree | PARTIAL | replay, accounting, backends |
| 012 | canonical-kernel-audit | V3 mathematical audit | standard | Given stabilized v3, when independently checked across priors, ties and numerical boundaries, then its declared mathematics holds | VALIDATED | mathematics, v3 |
| 013 | canonical-kernel-audit | V3 upstream audit | comparison | Given pinned upstream sources and explicit alignment, when current kernels run matched cases, then every discrepancy has evidence | VALIDATED | upstream, v3 |
| 014 | canonical-kernel-audit | V3 policy audit | standard | Given accepted compositions, when profile, lifecycle and numerical boundaries are varied, then execution matches the declared policy | PARTIAL | policies, admission |
| 015 | canonical-kernel-audit | V3 execution audit | comparison | Given the same contract and observation, when scalar, compiled, batch and public paths execute, then outputs and evidence remain consistent | PARTIAL | backends, work |
| 016 | canonical-kernel-audit | Scalar admission fix | standard | Given a min-sum profile without its update rule, when constructed, then scalar and compiled APIs reject ambiguity | VALIDATED | fixes, contracts |
| 017 | canonical-kernel-audit | Profile evidence fix | standard | Given a numerical profile, when admitted, then fixed semantic fields describe execution and supported knobs remain usable | VALIDATED | fixes, contracts |
| 018 | canonical-kernel-audit | Public summary fix | standard | Given replayable evidence, when result claims are altered, then verification rejects inconsistent summaries | VALIDATED | fixes, contracts |
| 019 | canonical-kernel-audit | Numerical envelope | standard | Given finite messages across scales and degrees, when independently evaluated, then error and adaptation boundaries are explicit | PARTIAL | boundary-audit |
| 020 | canonical-kernel-audit | Upstream numerical envelope | standard | Given aligned boundary inputs, when pinned native implementations run, then discrepancies and safeguards are explained | VALIDATED | boundary-audit |
| 021 | canonical-kernel-audit | Policy entry-point closure | standard | Given alternate constructors and composed updates, when admitted, then execution matches declared semantics | PARTIAL | boundary-audit |
| 022 | canonical-kernel-audit | CPU boundary and graph integrity | standard | Given qualified graphs and bounded observations, when execution is batched or state reused, then validity, work and graph identity agree | PARTIAL | boundary-audit |
| 023 | canonical-kernel-audit | Construction admission | standard | Given audited counterexamples, when corrected, then accepted construction paths enforce one contract | VALIDATED | fixes |
| 024 | canonical-kernel-audit | Local damping | standard | Given audited counterexamples, when corrected, then local schedule updates honor their active numerical profile | VALIDATED | fixes |
| 025 | canonical-kernel-audit | BP4 active cap | standard | Given audited counterexamples, when corrected, then compiled legacy BP4 honors the selected saturation | VALIDATED | fixes |
| 026 | canonical-kernel-audit | Stable SPA qualification | standard | Given audited counterexamples, when corrected, then a new stable log-domain policy agrees with independent exact inference | VALIDATED | fixes |
| 027 | canonical-kernel-audit | Stable SPA stress audit | standard | Given corrected kernels, when audited, then independent multi-check inference, mixed-scale messages and finite-state failure boundaries | PARTIAL | freeze-audit |
| 028 | canonical-kernel-audit | Stable upstream audit | standard | Given corrected kernels, when audited, then native and canonical comparisons use explicit mathematical and numerical alignment | VALIDATED | freeze-audit |
| 029 | canonical-kernel-audit | Schedule policy closure | standard | Given corrected kernels, when audited, then all advertised numerical controls remain active or are explicitly rejected across schedules | PARTIAL | freeze-audit |
| 030 | canonical-kernel-audit | Freeze execution audit | standard | Given corrected kernels, when audited, then construction, public reachability, CPU execution and evidence agree across supported policy boundaries | PARTIAL | freeze-audit |
| 031 | canonical-kernel-audit | prior-state-fix | standard | Given an admitted configuration, when executed, then normalized stored priors are finite before shortcuts | VALIDATED | fixes |
| 032 | canonical-kernel-audit | bp4-failure-fix | standard | Given an admitted configuration, when executed, then all BP4 scopes fail consistently on nonfinite state | VALIDATED | fixes |
| 033 | canonical-kernel-audit | residual-admission-fix | standard | Given an admitted configuration, when executed, then conventional residual scheduling rejects incompatible damping | VALIDATED | fixes |
| 034 | canonical-kernel-audit | Mathematical contract completeness | standard | Explicit contract coverage with executable evidence and exclusions | VALIDATED | completeness |
| 035 | canonical-kernel-audit | Upstream interface and algorithm comparison | standard | Explicit contract coverage with executable evidence and exclusions | VALIDATED | completeness |
| 036 | canonical-kernel-audit | Policy composition and capability coverage | standard | Explicit contract coverage with executable evidence and exclusions | PARTIAL | completeness |
| 037 | canonical-kernel-audit | Execution, circuit and evidence closure | standard | Explicit contract coverage with executable evidence and exclusions | PARTIAL | completeness |
| 038 | canonical-kernel-audit | D03 correction | standard | Fix and qualify the admitted contract boundary | VALIDATED | completeness, fixes |
| 039 | canonical-kernel-audit | D04 correction | standard | Fix and qualify the admitted contract boundary | VALIDATED | completeness, fixes |
| 040 | canonical-kernel-audit | D01 correction | standard | Fix and qualify the admitted contract boundary | VALIDATED | completeness, fixes |
| 041 | canonical-kernel-audit | D02 correction | standard | Fix and qualify the admitted contract boundary | VALIDATED | completeness, fixes |
| 042 | canonical-kernel-audit | D05 correction | standard | Fix and qualify the admitted contract boundary | IN_PROGRESS | completeness, fixes |
