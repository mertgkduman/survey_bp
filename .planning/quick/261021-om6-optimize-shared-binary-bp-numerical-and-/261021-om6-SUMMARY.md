---
id: 261021-om6
slug: optimize-shared-binary-bp-numerical-and-
type: quick
status: complete
---

# Shared binary BP path optimization

Optimized the production scalar box-plus pair and cached binary flooding exclusions without bypassing update-rule callbacks or changing numerical profile and work semantics. On a pinned BB72 three-sweep workload, SPA improved 2.52× and three min-sum variants improved 1.09–1.14×. All before/after scalar output bits and sweep buffer/work hashes matched; 196 focused and adjacent binary policy tests passed. See `REPORT.md` and retained JSON artifacts for measurement and qualification limits.
