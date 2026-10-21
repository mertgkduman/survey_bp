---
id: 261021-njt
slug: optimize-policy-composable-quaternary-bp
type: quick
status: complete
---

# Policy-bearing quaternary BP optimization

Preindexed graph incidence for transformed BP4 and fixed-alpha MBP4 flooding and serial execution, and computed old-edge scalar quantization once per complete flooding pass. The same-core GB46 sweep profile improved transformed flooding 2.40× and MBP4 flooding 2.34×; serial paths were essentially flat. All retained before/after numerical buffers, work records, and final state digests matched exactly. Focused tests passed 48/48. The broader quaternary suite passed 188 tests and had seven failures caused by missing external source fixtures. See `REPORT.md` for methods and limits.
