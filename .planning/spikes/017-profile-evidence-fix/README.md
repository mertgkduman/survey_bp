---
spike: 017
idea: canonical-kernel-audit
name: profile-evidence-fix
type: standard
validates: "Given an admitted numerical profile, when evidence is serialized, then fixed fields describe execution and implemented parameters remain configurable"
verdict: VALIDATED
related: [014-v3-policy-audit, 016-scalar-admission-fix, 018-public-summary-fix]
tags: [fix, profiles, evidence]
---

# Spike 017: Executable profile evidence

## Research and choice

Pure dataclass/contract logic. Reused V3-A02, existing profile definitions and current numerical parameter consumption; no external dependency changes.

| Approach | Benefit | Limitation |
|---|---|---|
| Remove fixed fields from constructor | Prevents overrides | Larger API and serialization migration |
| Validate fixed fields during construction | Preserves serialization and explicit errors | Must distinguish implemented parameters from descriptive fields |

Chose construction-time validation against implementation-class defaults. Subclass defaults cannot silently redefine precision. All named identities and serialized values are unchanged. Inactive v2/v3 saturation is fixed; active v1 saturation remains configurable. Existing cap/epsilon/damping and Pauli check-rule choices remain available. Unsupported formats and tie rules must use a separately implemented/versioned policy rather than relabel these profiles.

## Investigation and results

Initial regressions: 113 failed, 33 passed. Validation now rejects inconsistent fixed fields across seven profiles, invalid numeric types/bounds, and changed subclass precision defaults. Evidence snapshots prove all seven existing named profiles serialize identically. Current kernels and compiled paths retain their numerical results.

Final focused suite: **247 passed**. This includes stabilization, active-parameter/kernel and compiled BP4 regressions. Constructor validation adds no message-loop work. Deliberate mutation of frozen objects via Python internals is not an API guarantee.

## Run and observability

```sh
OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=4 .venv/bin/python -m pytest -q tests/canonical/test_kernel_contract_admission.py tests/canonical/test_kernel_stabilization.py tests/canonical/test_numerics.py tests/canonical/quaternary/test_kernel.py tests/canonical/quaternary/test_compiled_bp4.py
```

`frozen-profiles.json` was captured before the fix. `red.log`, `green.log`, and `green.xml` preserve evidence; prior audit failures remain historical records.
