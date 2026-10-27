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
