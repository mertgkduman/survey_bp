---
status: complete
date: 2026-10-30
commits:
  - 50d6371
  - 7eef1c5
---

# Bounded Yao non-OSD reproduction

Pinned the v2 TeX source and extracted every Figure 2–8 point and Table 1–2 setting outside BP-OSD. Added the published C2 code construction, a compiled binary SPA/BPGD path, deterministic per-shot manifests and ledgers, independent Type I/II classification, a fixed-error Table 2 surrogate, and a source-linked assessor. The executable policy is a canonical adaptation; no author-code identity is claimed.

The assessor verified the retained ledgers and produced `data/reproductions/yao-2312-10950-non-osd/results/{comparison.csv,comparison.png,comparison.pdf,REPORT.md}`. Across 164 plotted coordinates, 65 source values fall inside local two-sided 95% intervals and one falls inside an interrupted complete-prefix interval. Fourteen measured points have fewer than 30 failures, five are pilots, seven fall outside the local interval, 62 remain unmeasured, and ten BP-SI points are imported from another paper and source-mapped only. Repeated plotted coordinates count separately. Ordinary binary BP agrees at all B1/C2 p values. The B1/C2 guided T=10 high-rate points and A5/B2 Q-BPGD high-rate points are generally compatible; rare points remain count-limited.

Seven point-versus-interval exclusions are listed in `REPORT.md`: B1 guided T=1 at p=0.06, A5 QBP at p=0.10, and five B2 QBP points. The local B1 T=1 result is 100/12,358 versus the source 0.00606; uncertainty in the paper's 100-failure estimate overlaps the local interval. This remains a reproduction lead, not a diagnosed kernel defect. Earlier QBP v2 counts were imported from the vanilla study and their original ledgers were not revalidated here.

Exact low-rate coverage is not established: the B1 guided T=100 p=0.04 source rate of 10^-6 would require roughly 100 million shots to reach 100 failures. Figure 3/4 T=10 and Table 1 T wording conflict in the source. Table 2's fixed error bytes were not released, so the two local surrogates cannot be compared numerically to its 10,000-run statistic. BP-SI curves came from du Crest et al. and require a separate serial min-sum/inactivation reproduction. Phase 11 publication dispatch remains denied by its existing resource gate; this task used bounded interactive development runs only.

Verification: source extraction reproduced byte-identical JSON, `assess.py` verified manifests and ledgers, `git diff --cached --check` passed, and 18 focused decoder/source tests passed.
