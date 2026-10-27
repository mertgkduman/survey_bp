---
quick_id: 261027-l1l
date: 2026-10-27
status: verified
---

# Promote float64 v2 defaults and compare numerical profiles

New plain flooding binary SPA and scalar BP4 constructors and numerical helpers
default to their float64 v2 profiles. Binary SPA schema 9 and quaternary schema
`quaternary_experiment_v3` make v2 the public default, including preflight,
execution, and replay verification. The binary Python and compiled flooding
sweeps apply the same V2C damping boundary. The BP4 v2 public resolver records
the new numerical policy as a `canonical_adaptation` rather than presenting it
as a source-faithful numerical implementation.

Historical public schemas and result ledgers remain pinned to v1. Min-sum,
memory, intervention, Q-BPGD, MBP4, Relay, and circuit routes retain their
declared profiles until independently qualified. New v2 public schemas admit
only plain flooding BP. The documentation identifies these compatibility
boundaries. Runnable new-schema examples and regenerated public JSON schemas
are included.

The version comparison is available as a two-column
`docs/decoder-numerics-v1-v2.html` and two-page
`docs/decoder-numerics-v1-v2.pdf`, generated from the shared content in
`scripts/build_decoder_profile_comparison.py`. It states the prior, check,
posterior, extrinsic, damping, tie, and stopping differences for binary SPA
and BP4.

Verification: the affected canonical and CLI suite passed 829 tests with one
skip under `OMP_NUM_THREADS=1`; the two external-fixture modules
`test_phase11_mbp4_target.py` and `test_phase11_native_asced.py` were excluded
because their `/tmp` inputs are absent. The focused v2 tests passed 3/3 and
circuit tests passed 7/7. Both example manifests passed public preflight.
The generated schemas match `model_json_schema()` exactly; the PDF has two
page objects and the HTML has two comparison sections. `git diff --check`
passed. Historical evidence files and running experiment outputs were not
modified or staged.
