---
spike: 045
idea: canonical-kernel-audit
name: policy-admission
type: standard
validates: "Every admitted policy has explicit effective controls, compatible operands and owned attempt state."
verdict: PARTIAL
related: [036, 040, 044]
tags: [policies, admission]
---

# Policy composition and admission

Regrounded in MANIFEST.md and CONVENTIONS.md after 044. Extend the historical
capability matrix with the new circuit policy interface, without implying that
every CPU policy is compiled or GPU compatible. Primary interface comparisons
are recorded in 044; mathematical recurrence checks are in 043.

## Approach and prespecified checks

Exercise four check rules, four controllers, seven memory configurations and
three backend requests (336 configurations). Admission expectations are specified
independently. Use both heterogeneous affine mechanisms and inconsistent duplicate
checks, all four detector patterns, repeated calls and repeated shots. Verify
original-problem validity, logical projection, work, attempt limits, lineage,
memory resets and supported backend parity (posterior tolerance 2e-12).

Separately check five identity memories for every rule and the full ordered
identity chain. Probe non-default controller-specific controls with static operand
inspection as well as execution: lack of effect on a single convergent shot alone
would not establish that a parameter is ignored.

## Run

`OMP_NUM_THREADS=1 .venv/bin/python .planning/spikes/045-policy-admission/probe.py`

Records include accepted/rejected configurations and concrete ineffective-control
examples. Process exit zero means the audit ran; failed invariant counts remain
visible in results.json.

## Investigation trail and results

The first identity probe incorrectly assumed all gamma parameters weight history.
Inspection and isolated runs established that V2C damping gamma weights the fresh
message, so its identity is gamma=1. The initial failed probe is retained as
initial-probe-results.json and initial-probe.log; it is not a production finding.
After correcting that test assumption, 24 identity/composed-identity cases and
caller/accessor ownership checks pass.

The 336-configuration matrix passes its admission, backend, state and work checks.
There are 188 accepted configurations and 148 expected rejections, with 1,504
primary shots plus repeated-call and individual-shot checks.

**E02:** eight non-default controller settings are accepted but never consumed:
solution_limit and relay_alpha outside Relay; bias outside guided/beam. Static
operand inspection and identical complete per-shot attempt evidence agree. This
can make a policy sweep or HTML control appear effective while only its recorded
configuration changes. Reject non-default inapplicable controls, or expose their
inactivity explicitly in a capability contract. Default-valued shared fields may
remain for backward compatibility. This does not invalidate active memory or
controller behavior.

Two invariant groups pass; the inactive-control group fails.
