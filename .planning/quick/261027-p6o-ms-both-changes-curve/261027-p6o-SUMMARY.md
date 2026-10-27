---
status: complete
quick_id: 261027-p6o
date: 2026-10-27
---

# BP4 min-sum both-changes curve check

Ran the diagnostic hybrid at all nine reported vanilla BP4 MS positions,
10,000 shots per point. It retains Q8 scalar projected and check messages at
scale 16, with unbounded float64 three-coordinate V2C and an exact
commuting-minus-anticommuting log-sum-exp projection before scalar
quantization. The decoder prior was `p0=p`, damping was zero, and `T=1000`.

All nine reported reference point estimates fell inside the local exact
pointwise 95% intervals. On identical errors, the hybrid reduced original
Q8 MS failures from 1,910 to 109 on B1 at `p=.06`, 8,622 to 87 on B1 at
`p=.10`, and 2,153 to 50 on double-Gross at `p=.08` (each out of 10,000).
The local high-p rates were also close: B1 `p=.14` was 0.584 versus 0.581;
double-Gross `p=.12` was 0.2173 versus 0.21935.

An independent 50,000-shot holdout at double-Gross `p=.06` gave 154/50,000
= 0.00308, exact 95% interval [0.002613, 0.003606], above the reported
point estimate 0.00245. This is a remaining low-p discrepancy. The source
denominator is unknown, so its own sampling uncertainty cannot be included
in a formal two-sample comparison. The hybrid is not proven source-faithful
Q8 even where rates agree.

The nine point ledgers, independent holdout, CSV, Markdown report, and
PNG/PDF plot are in `from_dr_pfister_presentetations/results/ms_both_changes_curve/`.
The diagnostic policy is recorded in
`from_dr_pfister_presentetations/decoders/bp4_ms_both_changes_diagnostic.json`.
The analyzer audited all new ledger SHA-256 values, outcome partitions,
denominators, and intervals, and matched each point's 10,000 error hashes
against the original Q8 campaign prefix. B1 `p=.14` was merged from five
contiguous 2,000-shot shards after checking their ranges and hashes. The
first unsharded attempt was canceled for throughput before it emitted a
result and is retained as interrupted evidence.

No canonical decoder default or historical result was changed.
