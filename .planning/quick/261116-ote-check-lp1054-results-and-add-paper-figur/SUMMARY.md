---
id: 261116-ote
status: complete
campaign_status: running
implementation_commit: 781055fb
evidence_commit: 873c3724
phase_gates_changed: false
---

# Paper figure views and audited result check

Available experiment results now offers clickable paper titles and named, separate figure plots. The source-backed registry declares Yao Figs. 2–8, Roffe Fig. 3, MacKay Fig. 15, LP Example 4 and explicitly labelled controlled CSS comparisons. Each figure provides Paper reproductions and Additional curves group checkboxes below a scrollable individual curve list. Reproductions default on, additional curves off. Mixed selection, individual toggles, automatic ranges, table exports and figure-labelled settings receipts agree. Custom plots survive switching papers. New imports default to additional comparisons, while refresh removes stale paper, figure, code and decoder selections.

Classification uses explicit retained dataset/decoder-arm identities and source-figure scope before applying the same central evidence projection separately to each group. A foreign or additional point cannot make a reproduction eligible. Roffe OSD0/CS10 are additional because the source uses CS60. Canonical reproduction conventions remain explicit. MacKay's inferred cap and classical-versus-quantum metric distinction prevent an exact configuration claim; all local curves are additional. LP has no source LER figure, so no figure number or reproduced source curve is invented. The figure registry is validated and hashed on future catalog builds.

The unchanged frozen collectors publish audited snapshots only. Gamma80/60: **6/12 strata**, 24 distinct fresh policies, **6,525 shots / 480 logical failures**, 1,322 separate training measurements. Completed rates are p=.06/.08/.10 under both numerical backgrounds. At p=.06, source numerics select gamma0=0 and interval [0,.375]: fresh LER .0252207 versus continuous BP140 .0430108; mean sweeps 20.0958 versus 21.1226. Prior-tuned numerics select gamma0=0 and interval [-.375,.5]: .0178412 versus .0192123; mean sweeps 14.7244 versus 14.7483. Each fresh policy has 20 failures. Pointwise 95% intervals overlap within each comparison; no superiority claim. At p=.06 both selected first phases are zero-memory BP, leaving memory only in the disordered phase. At p=.08, source/tuned gamma LERs are .190476/.121951 versus BP140 .224719/.113636. At p=.10 they are .833333/.666667 versus .769231/.666667. All six comparison pairs have overlapping pointwise intervals; there is no consistent improvement. Six other strata continue with one CPU per point; no simulation design or stopping changes.

Original LP stack: **70/72 audited**, **11,236,743 fresh shots / 1,400 failures**, 1,960 separate training measurements. New p=.02 Beam32 LER 7.35187e-6 (95% [4.49072e-6,1.09068e-5], 2,720,397 shots) and Q-BP+CS10 8.12422e-6 ([4.96249e-6,1.20526e-5], 2,461,775 shots) have overlapping intervals. Two source strata remain incomplete or auditing. Raw data, frozen source/software/code/selection pins and kernels are preserved.

The public view changes from **443 curves / 3194 points / 13 codes / 0 circuits** to **448 / 3207 / 13 / 0**. All 1543 prior raw series retain every point and multiplicity; 18 new raw series are retained. Five exact-policy gamma-study curves now qualify at multiple rates; selected policies with only one rate remain in the report and are excluded from plots. One new LP policy is also a singleton; this does not weaken the two-rate rule.

Verification covers source scope, no cross-group qualification, bounds, retirement, new imports, metadata validation and rebuilds; Chromium covers paper/figure navigation, defaults, mixed state, scoped exports, empty groups, stale inputs, custom plots/inputs, mobile and v1. Two old catalog test assumptions were updated for optional source ordinates and plural dataset references. Missing normalized comparison experiment contexts are now derived centrally without inventing executable recipes. A duplicate-dataset diagnostic regression in that fallback was fixed by tracking generated coverage. No prior manifests, raw ledgers, frozen campaign files, canonical kernels, archived v1, model config or phase gates/counters change.

Validation result: 88 distinct relevant tests pass across the full run and focused fixes (the full run had 85 passing; its three failing cases and the updated context-contract test then passed as a four-test rerun). Fourteen Chromium workflow groups pass with zero page errors. Implementation 781055fb; audited snapshots 44262d66.

Additional workers completed during final checks. The unchanged collector refreshed the six-stratum snapshot and the public catalog after the initial push. `results-check.json` retains the first two-stratum check; `results-check-latest.json` records the superseding six-stratum assessment.

Superseding gamma snapshot: 873c3724. The latest seven real-data browser workflow groups pass at 448 curves / 3207 points / 13 codes / 0 circuits.
