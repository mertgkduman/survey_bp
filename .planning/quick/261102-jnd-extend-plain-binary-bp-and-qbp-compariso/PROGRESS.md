# Completed B1/C2 depolarizing study

All 14 fixed B1/C2 depolarizing points and their independent audits are complete.
See `261102-jnd-SUMMARY.md` for the final findings and verification. Final data
and four-code report commit: `b204164`.

Pilot array 60921180 completed 14 tasks; final array 60921740 completed 15
shards, with every task exiting zero. The 381,309 final paired samples exclude
all 28,000 pilot samples. Every new main estimate has at least 153 failures.

Results and frozen rerun instructions are under
`data/reproductions/yao-2312-10950-cross-code/depolarizing/`.
The full audit completed successfully, and the current report/plots were then
rebuilt through the hash-verifying `--render` route. No campaign jobs remain
active. The earlier X-only study and earlier rare-event reproduction task
retain their own status.
