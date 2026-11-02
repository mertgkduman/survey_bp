---
status: in_progress
date: 2026-11-02
---

# B1/C2 depolarizing extension

1. Add a separate `depolarizing/` experiment under the cross-code study. Run
   plain binary v2 and joint QBP v2, T=100, no damping, float64 flooding SP,
   p=0.04,...,0.10. Decode identical errors, using binary q_X=q_Z=2p/3 and
   joint (1-p,p/3,p/3,p/3). Keep X-only results and frozen policies intact.
2. Freeze 2,000-shot pilots for all 14 points. Use pilot counts to fix a
   fresh independent cohort: N=min(1,000,000,max(20,000,ceil(200*2000/k)))
   where k is the smaller arm failure count; k=0 selects 1,000,000. Pilot
   samples do not enter final estimates. Shard fixed cohorts with disjoint
   deterministic PCG64 indices and at most 24 simultaneous one-CPU tasks.
   Exact fixed-N intervals and zero-failure one-sided 95% bounds are required;
   <100 failures remain explicitly marked as low-count estimates or bounds.
3. Independently audit manifests, code/implementation identities, every
   sample hash and aggregate, and selected correction replays with separate
   X/Z logical signatures. Combine with already audited A5/B2 depolarizing
   points into four-code tables/plots, record paired statistics and costs,
   document limitations, and commit completed evidence and GSD state.

The one-million-shot ceiling fixes the low-rate resolution prospectively;
this controlled comparison does not assert a measured nonzero LER when only
an upper bound is supported. This task runs inline under GSD quick.
