---
spike: 018
idea: canonical-kernel-audit
name: public-summary-fix
type: standard
validates: "Given replayable public evidence, when deterministic summary claims are altered, omitted or added, then verification rejects the receipt"
verdict: VALIDATED
related: [015-v3-execution-audit, 016-scalar-admission-fix, 017-profile-evidence-fix]
tags: [fix, replay, evidence, historical]
---

# Spike 018: Complete public summary verification

## Research and choice

Pure replay-contract logic. Inspected `run_quaternary`, preflight, historical receipts and all public schema branches; reused V3-A03.

| Approach | Benefit | Limitation |
|---|---|---|
| Compare the four discovered fields | Small patch | Leaves other altered/omitted claims unchecked |
| Compare all deterministic summary fields with replay | Complete claim/key/type coverage, including nested provenance | Must exclude relocatable path fields and select historical accounting explicitly |

Chose complete comparison through canonical JSON. Python equality alone would accept `True` in place of integer `1`. Only `output`, `ledger_path`, and `manifest_path` are excluded as locations; manifest content identity is checked separately and replay reads the requested output directory. Unknown summary claims are rejected. No new fields are added to historical results.

## Investigation and results

The initial regressions reported **17 failed, 3 passed**. The fix covers schemas v1–v4, each deterministic field altered or omitted, nested component fidelity, extra claims, numeric types, accounting downgrade attempts, and copied output bundles. Historical v2/v3 audit receipts still replay. Existing MBP4, Q-BPGD and aSCED public paths also pass.

Focused suite: **125 passed**. Scratch directories are cleaned on failed comparisons. Summary validation reuses the one deterministic replay; it does not add a second decoder pass. Decoder arithmetic and emitted ledgers are unchanged.

## Run and observability

```sh
OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=4 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_summary_verification.py tests/canonical/quaternary/test_public_execution.py tests/canonical/test_kernel_stabilization.py
```

`red.log`, `green.log`, and `green.xml` retain the before/after evidence. The final combined qualification script and evidence are stored here after all three fixes.
