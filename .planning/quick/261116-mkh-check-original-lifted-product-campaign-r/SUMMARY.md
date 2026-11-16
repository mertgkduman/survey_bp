---
id: 261116-mkh
status: complete
data_commit: a75222da
campaign_status: running
workers_completed: 68
workers_audited: 68
workers_planned: 72
phase_gates_changed: false
---

# Original lifted-product results checked

Original LP1054 campaign now has68/72 completed simulation workers and68 fully audited confirmations. The remaining simulations are Q-BP+CS10, tuned Q-BP, beam32 and beam128, all at p=.02. Their last checked committed prefixes were about1.7–2.0M shots each; no provisional LER or upper bound is published. Both long audits for tuned BP and Relay128 at p=.02 completed during this check; the final refresh includes them. All point simulations and audits retain one CPU. No worker/audit error log was found.

Eight completed-source audit dependencies were released only after Slurm COMPLETED0:0, matching plan/completion/selection hashes and pending audit status. The separate audit-release-261116-mkh.json preserves this scheduling-only action. Earlier dependency-release evidence and all scientific settings remain unchanged. Frozen full point auditors and collector were reused without modification; automatic final collector61930188 remains pending until all72 audits complete.

The published snapshot contains68 fresh confirmation measurements,6,054,571 decoder shots and1,360 logical failures, plus1,892 separate training measurements. Every confirmation stopped at20 failures. The unchanged auditors check every row and both endpoints of each64-shot chunk. Independent check.py additionally reconciles all1,960 summaries/manifests, source identities, counts/rates, stopping-aware95% intervals, work ceilings, coarse/finalist/fresh seeds and original LER-first selection. Source/software/code hashes still match the frozen plan. CHECKED-RESULTS.json retains every input summary hash and numerical comparison.

At p=.04/.06/.08, tuned Q-BP gives5.46e-5/1.71e-3/1.09e-2 versus Q-BP+CS10 at7.15e-5/3.17e-4/6.68e-4. At .04 the tuned point estimate is lower but95% intervals overlap. At .06/.08 joint CS10 point estimates are5.38x/16.33x lower, with nonoverlapping pointwise intervals. Binary BP+CS10 is6.58x/169.08x higher at those latter rates. These20-failure pointwise comparisons do not establish simultaneous superiority. At .10 OSD0 and CS10 joint intervals overlap; do not claim CS10 is conclusively better there.

The two late audit receipts add tuned BP at p=.02:20/1,669,781=1.19776e-5,95% interval[7.316e-6,1.777e-5], with damping.3/scale.8/offset.2 and32 sweeps per component. Its point estimate is113.09x below untuned BP, with slightly fewer mean edge updates(30,692 versus31,542). Relay128 is20/1,339,641=1.49294e-5; joint OSD0 is20/1,083,988=1.84504e-5. All three latter intervals overlap; equivalence or superiority is not established. Joint CS10 and the remaining rare search/QBP points are still pending.

Tuning improves plain BP/Q-BP at useful rates, but the current binary beam/Relay searches do not match joint OSD at the middle rates. Even beam128 gives LER.0104/.169 at .06/.08; Relay128 gives.0174/.227. Their128 caps permit4x the baseline directed-edge work ceiling. Binary search ignores X/Z correlations; no search-family impossibility or globally optimal tuning claim follows. Four rare p=.02 confirmations remain unresolved. Mean iterations/edge counts and provenance-instrumented timings remain separate; no uninstrumented runtime or native speedup is claimed.

Saved and visually inspected a three-panel scientific PNG/PDF showing ordinary/tuned BP, OSD variants and search variants with95% intervals; pending points are omitted. Only fixed profiles are connected; pointwise-tuned/search measurements are separate markers because their concrete settings can differ between rates. The paper has no numerical LER curve/grid/cap for1054, so source agreement is not applicable. The32/.625 baseline remains borrowed from the cited BP-OSD paper, with its layered schedule versus canonical flooding explicitly documented.

Normalized results and refreshed the workbench:440→443 curves,3178→3194 displayed points,13 codes/0 circuits unchanged. The LP study retains23 exact configurations/68 raw points;15 compatible multi-rate curves/60 points are displayed. Eight singleton/incompatible exact settings stay in the full result table. All1538 previous raw series retain every old point, including multiplicity.55 catalog/projection/label regressions and11 Chromium workflow groups pass on actual/synthetic LP data, exports/settings, empty/stale selections, custom matrix/Stim and archivedv1. Browser receipts are under browser/; scratch downloads/screenshots remain local.

No additional simulation was launched. No canonical policy/kernel change, prior frozen source/manifest/raw result edit, v1 change, model/config edit or phase counter/gate change was made. The campaign remains running; this result-check task is complete.
