---
phase: 09-css-reproduction-and-controlled-comparisons
plan: "11"
subsystem: campaigns
tags: [paired-design, measured-cost, controlled-comparison, ordered-work]
status: complete
dependency_graph:
  requires: [09-08, 09-09, 09-18]
  provides: [exact paired sizing, distinct mechanism profiles, frozen positive-N controlled design]
  affects: [09-19, 09-12, 09-13, 09-14]
key_files:
  created: [src/bp_registry/campaigns/sizing.py, scripts/phase9_control_profiles.py, data/studies/phase9-control-profiles-v1.json, data/studies/phase9-controlled-design-v1.json, data/results/phase9-control-profiles-v1, data/results/phase9-controlled-design-v1, tests/test_campaign_sizing.py]
  modified: [src/bp_registry/campaigns/cli.py, docs/campaigns.md]
actuals:
  tasks: 2
  commits: 2
---

# Phase 09 Plan 11: Measured Controlled Design

## Delivered

- Added exact unconditional paired McNemar sizing with a two-sided three-question alpha allocation, explicit disjoint calibration/evaluation namespaces, minimal powered N, and a blocked-precision result. The prospective 0.05 all-shot risk difference, 0.80 target power, and conservative q=1 planning assumption require 4,188 pairs. q=1 is not presented as an estimate from the tiny calibration samples.
- Measured and independently replayed separate Beam, Relay, MBBP, SPA flooding, and SPA check-node serial profiles. Beam and Relay have distinct inner wall/work fields and conservative full shared-process wall/CPU/RSS/storage bounds. MBBP's two-shot member ledger supports a separate 75-work-unit per-pair upper bound. Schedule profiles were rerun from the tracked Phase 3 manifests because the older Phase 3 run ledgers fail the current manifest-digest verifier; those old ledgers do not authorize cost projections.
- Froze the three families in `data/studies/phase9-controlled-design-v1.json` before evaluative sampling. The local matched denominators are schedule **3** at B1 p=0.10, Beam/Relay **16** at BB72 p=0.08, and MBBP list/vote **2** at B1 p=0.000001. Achieved exact powers at these caps are 0, approximately 0.004897, and 0. The design therefore labels all three exploratory and leaves EVAL-03 incomplete pending their frozen evaluative pairs.
- Published a public `OrderedCampaignWorkSpecV1` plan for each complete arm sequence and sample-major group order. Their plan digests are `439e5b745bdbc915df755a6e7eb47f8a0780788ef49bf7fd36797404c9308760`, `0d3e947f54da233582ce4db2cab4a8f72bb80ade2461cf82ffb41eaf38e835bb`, and `30a113e8b15944af0637e9aaa906fb196fef6545943b1012c234231587b1b306`. The generic ordered runner rejects these planning-only controlled targets; Plan 09-19 supplies their dedicated execution route.
- Kept site wall/core/memory/storage/accounting ceilings unavailable and publication Slurm denied. No profile sample belongs to an evaluation namespace. Production commits: `d52aec4`, `585d742`.

## Verification

- `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/test_campaign_sizing.py -x`: **14 passed**.
- `scripts/phase9_control_profiles.py verify` independently replayed all five mechanism profile chains and returned `status=verified`, `publication_slurm_authorization=deny`.
- Public `bp-registry-campaign plan` accepted all three prospective ordered work documents with complete groups. The design test recomputes the plan digests, profile file hashes, positive N, disjoint namespaces, and bounded projections.

## Self-Check: PASSED

Every family has a distinct measured cost basis, a positive bounded local N, and a sealed complete arm order. The statistical claim remains exploratory and no controlled evaluation has started.
