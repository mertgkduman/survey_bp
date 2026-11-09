---
spike: 050
idea: canonical-kernel-audit
name: shared-mathematics
type: standard
validates: "Given heterogeneous signed priors, when ordinary and precision policies execute, then independent factors reproduce candidates, beliefs and stopping."
verdict: VALIDATED
related: [043, 044, 045, 046, 049]
tags: [shared-policies, completeness]
---

# Shared policy mathematical contracts

Baseline d031436. Continues the approved mathematics → upstream → policy → execution audit. User scope: existing/source-defined counterparts only; no new cross-family adaptations. Production and historical evidence remain unchanged during this audit.

## Research and approach
Independent mathematical oracles, aligned native execution, composition probes and evidence replay answer distinct questions. Prior qualification is carried only for matching source identities. CLI evidence is appropriate to this numerical question; HTML follows the audit.

## Research
Primary mathematical reference: [factor graphs and sum-product](https://web.stanford.edu/~montanar/TEACHING/Stat375/papers/sumprod.pdf). Factor enumeration and min-cost enumeration are independent of the production tanh/minimum loops; IEEE casts and integer rounding independently implement the declared precision boundaries. Cross-backend equality alone is not the oracle. Source-specific finite safeguards and early stopping are compared separately from exact marginal claims.

## Prespecified checks and run
Seeds 5001/5002, absolute/relative tolerance 2e-12. Signed heterogeneous priors on a two-check tree; four ordinary rules, zero/one/five sweeps; six formats, three rounding scopes, two precision rules, zero/one/four sweeps. Prior-decision shortcuts and exact stopping counts are included. Run `OMP_NUM_THREADS=1 .venv/bin/python .planning/spikes/050-shared-mathematics/probe.py`.

## Results
All three groups pass: 1,152 independent ordinary-factor comparisons and 1,728 independent precision-factor comparisons. Complete inputs, candidates, iteration counts and errors are retained in the case files. The precise maxima are recorded in results.json. Named Pauli and compiled/GPU mathematical evidence is carried only after matching the listed source hashes. No new GPU run is claimed.

## Investigation trail and limits
The expanded interfaces reproduce the declared finite recurrences. Reduced precision is rounding of float64 arithmetic, not native low-bit execution. Early stopping at a valid syndrome does not certify full convergence of posterior marginals, quantum logical success, or optimal coset decoding. No production behavior was changed. Diagnostic success and per-group verdicts remain distinct in results.json.
