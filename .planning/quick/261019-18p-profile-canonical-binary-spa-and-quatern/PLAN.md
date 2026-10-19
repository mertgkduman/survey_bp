---
id: 261019-18p
slug: profile-canonical-binary-spa-and-quatern
type: quick
status: complete
---

# Profile and advance canonical BP performance

Goal: identify measured hot-loop costs under matched work, then demonstrate a compiled path that preserves an explicit canonical policy contract and final decoding behavior.

1. Reprofile binary SPA and quaternary BP4 with setup, sweep, validation, and evaluation separated. Diagnose the existing min-sum and fixed-sweep BP4 output mismatches to avoid false speed claims. Retain a small, seeded workload and raw profiles.
2. Implement an optional compiled prototype for the highest-confidence hot loop, leaving the reference engine and publication path unchanged. Encode graph and policy inputs explicitly and keep the compiled code project-owned.
3. Compare intermediate messages and terminal decisions against the reference on targeted cases, then measure warm compiled throughput on the same work. Document compilation cost, scope, limitations, and the next engineering decision.

This is development evidence, not publication-campaign authorization or a source-faithful reproduction claim.
