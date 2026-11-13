# Verification — implementation tests pass; measurements pending

- 165 runtime/research regressions pass. Final10 display-label checks also pass
  (overlapping suites), including separate X/Z, depolarizing, p0=2p/3 and d=0.
- Real canonical kernels: identical Pauli/syndrome hashes across both methods,
  Y and Z samples, nontrivial Z logical failure, actual component work,
  counter-tampering rejection, serial/parallel equality, resume and endpoint
  collection all pass. No hidden truth is supplied to either decoder.
- Complete-audit gate and scheduler dependency tests prevent publishing or
  Roffe dispatch before old40 and new20 points complete. Submission is locked
  and idempotent. Old pending advance61773603 was canceled (Slurm confirmed).
- New frozen plan:20 points,40 pins, SHA256
  1981707650adf4b9a04730a2bd58594bd016dd67695252086d3391aacc2bf1bb.
  Existing baseline/tuning/confirmation/Roffe plans still verify unchanged pins.
- Scheduler --test-only accepts the new0–19 array with eight one-CPU workers.
  No production measurements are claimed from this check.
- Three source inventories preserve missing length74 ordinates as null and
  distinguish the actual fixed-target summary. No canonical/source/v1 edits.

Remaining: production controls, full-ledger audit, measured catalog/browser
verification, and updated source/comparison report. Existing rare confirmation
point continues separately and remains a prerequisite for Roffe.
