---
quick_id: 261119-kxq
status: complete
commit: d105c23f
---

# Paper-reported reference markers

The catalog extracts 307 distinct source points and records the four archival
input hashes. Figure views pair them with eligible curves by scoped dataset,
decoder arm, code and noise. The rate plots show separate same-color stars,
fit axes to the displayed values, and expose source metrics in marker
tooltips and settings downloads.

| Source | Figure | Points | Evidence |
| --- | --- | ---: | --- |
| Yao et al. | 2–8 | 154 | Author TeX coordinates. The conflicting Fig. 3 and Fig. 4 T=10 ordinates retain their separate values. |
| Roffe et al. | 3 | 109 | Approximate vector ordinates for regular BP on four toric codes. CS-60 has no corresponding local curve. |
| MacKay et al. | 16 | 5 | Approximate length-274 classical block error, paired with the inferred-budget unicycle comparison. Length 74 has no corresponding published multi-rate grid. |
| Ye and Delfosse | 1 | 39 | Author-derived LER per cycle for PriorTilt, Relay-BP and Beam Search. The Relay-BP and Beam Search guest views reuse 13 points each. |

The lifted-product Example 4 has no published LER figure. Paper data remain
separate from measured results and never affect eligibility, saved decoder
choices or CSV rows. The committed static file contains the marker data over
the previous committed measurements. Other in-progress catalog updates remain
in the worktree.

Verification passed for 64 focused tests and 10 Chromium workflow checks.
Chromium also checked the exact marker counts against the committed catalog,
including the guest views. Freshly built reference data matched the checked-in
values, and both catalogs validated against the updated schema.
