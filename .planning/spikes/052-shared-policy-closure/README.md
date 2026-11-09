---
spike: 052
idea: canonical-kernel-audit
name: shared-policy-closure
type: standard
validates: "Given accepted policies, when combined and reused, then operands, state lifetime, admission and source semantics remain coherent."
verdict: PARTIAL
related: [043, 044, 045, 046, 049]
tags: [shared-policies, completeness]
---

# Shared policy composition closure

Baseline d031436. Continues the approved mathematics → upstream → policy → execution audit. User scope: existing/source-defined counterparts only; no new cross-family adaptations. Production and historical evidence remain unchanged during this audit.

## Research and approach
Independent mathematical oracles, aligned native execution, composition probes and evidence replay answer distinct questions. Prior qualification is carried only for matching source identities. CLI evidence is appropriate to this numerical question; HTML follows the audit.

## Approach and run
Prespecified 432 combinations of six schedules, four check rules, six memory choices (including none) and three backend requests. Expected admission is specified independently of constructors. Four syndromes include inconsistent duplicate checks; signed heterogeneous priors expose lost channel information. Check original parity, replay, reset isolation, work leaf sums and unique leaf identities. Then exercise all nine controllers on two graphs, three signed channel vectors and every syndrome, plus declared randomized refresh boundaries.

Run `OMP_NUM_THREADS=1 .venv/bin/python .planning/spikes/052-shared-policy-closure/probe.py`.

## Results
Three groups pass: 200 supported configurations and 232 expected rejections; 800 primary shots plus 1,600 repeated/replayed calls; 216 controller cases and replay; nine randomized schedule/scope checks. Graph validity, deterministic replay, supported admission, ordinary work and reset isolation hold for these fixtures. capabilities.json captures the complete public family inventory and exclusions.

**F01 — local fixed-prior composition admission:** layered, check-serial and variable-serial execution all accept affine-prior memory followed by PD-prime. PD-prime's source recurrence uses its old field and the difference of C2V sums; it has no changing-prior operand. The local composition validator only checks its position among field transforms, whereas flooding also rejects preceding prior transforms.

## Investigation trail
The independent liveness probe changes affine alpha from 0 to .9 on an inconsistent graph, observes every incoming fresh field and every committed PD-prime field, and forces four complete source traversals. For all three schedules the incoming field changes, but every output field remains identical. This confirms a silently ineffective declared policy rather than just equal final candidates. Full observations and memory receipts are retained in fixed-prior-counterexample.json.

## Recommended correction and impact
Reject affine-prior + PD-prime combinations in local admission, matching the existing flooding rule. A changing-prior PD-prime recurrence would require a separately defined policy; the user's source-defined-counterpart boundary rules out inventing it here. Add an admission regression for each local schedule and a fixed-prior PD-prime control. Ordinary individual memory policies are unaffected. Existing results require investigation only if they actually used this previously admitted combination; no historical rerun is justified solely by this finding.

This is an audit; production behavior remains unchanged. The diagnostic process exit succeeds while results.json explicitly records the failed invariant.
