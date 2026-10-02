# Phase 5 p=0.05 damping pilot v1 invalidation

The original `b1-p005-damping-pilot` run is retained locally as historical diagnostic evidence only. It must not be published as a decoder comparison or used to claim a damping benefit.

An independent source audit on 2026-10-02 found that V2C damping stored the previous raw fresh message rather than the previous committed damped message required by Gökduman–Yao–Pfister Eq. 17. The BP-SF arm omitted first-iteration flips from the initial all-zero decision, and Restart Belief accepted every syndrome-valid root candidate without its source weight gate. Therefore the 14-arm table does not compare the intended policies. Any outcomes quoted from this v1 run are withdrawn.

The dependent verification job `57166513` and GitHub publication job `57166514` were cancelled before publishing. The corrected run uses `phase5-b1-p005-damping-pilot-v2.json`, new run/sample/decoder identities, and `b1-p005-damping-pilot-v2` output. The v1 ledger remains untouched to preserve provenance; no v1 shot may be resumed into v2.

This is a fixed 128-sample mechanism pilot on B1, not a statistically assessed decoder ranking, even after correction.

Sources: [Gökduman–Yao–Pfister damping Eq. 17](https://arxiv.org/html/2411.08177v2#S4.SS2), [BP-SF Algorithm 1](https://arxiv.org/html/2507.00254v1#S4), [Restart Belief Algorithm 1](https://arxiv.org/html/2511.13281v1#S3).
