# Spike Manifest

## Ideas

### pfister-slide-bp-reproduction

Record the BP policies, settings, curves, and conclusions supplied in Dr. Pfister's presentation excerpt, then probe whether this project's fast decoders can reproduce the B1 and double-Gross code-capacity results on paired depolarizing errors.

**Requirements:**

- Keep presentation data distinct from newly simulated measurements.
- Place decoder-from-policy files, data, and plots under `from_dr_pfister_presentetations` (the requested spelling).
- Preserve the reported Q8, damping, stopping, work, and logical-failure meanings, with assumptions marked explicitly.
- Compare decoders on the same sampled errors and retain denominator and paired discordance counts.

## Spikes

| # | Idea | Name | Type | Validates | Verdict | Tags |
|---|------|------|------|-----------|---------|------|
| 001 | pfister-slide-bp-reproduction | Slide evidence | standard | Given the supplied slides, when data and policies are transcribed, then every curve point and setting is attributable | VALIDATED | provenance, policies |
| 002 | pfister-slide-bp-reproduction | Policy kernel | standard | Given the existing fast decoders, when both code fixtures and slide knobs are applied, then numerical behavior is executable and qualified | PARTIAL | decoder, q8, codes |
| 003 | pfister-slide-bp-reproduction | Paired reproduction | standard | Given qualified code and policy variants, when shared errors are decoded, then measured LER and work can be compared with the slide | PARTIAL | simulation, statistics |
