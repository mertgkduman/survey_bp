---
spike: 030
idea: canonical-kernel-audit
name: freeze-execution-audit
type: standard
validates: "Given the corrected kernel, when boundaries are exercised, then construction, public reachability, CPU execution and evidence agree across supported policy boundaries"
verdict: PARTIAL
related: [023, 024, 025, 026]
tags: [freeze-audit, boundaries]
---

# Freeze execution audit

## Research
Reuse the independent equations, pinned upstream identities and qualified contracts in spikes 019–026. Numerical and implementation agreement are tested separately.

## Investigation Trail
Baseline 12cf2b1, production be7286e. No production changes.

## Results
Two positive controls pass: CPU input isolation/empty batches/thread restoration (12 retained ledger rows), and stable-policy epsilon sensitivity confined to unary checks. 364 selected existing regressions pass.

Three failed assertions map to two findings:
- C03: replacing a valid bound binary prior with NaN or either infinity returns initial convergence at zero iterations. The bound-state dataclass has no admission guard.
- C03: finite float128 prior values 1e400 are checked before conversion, then stored as nonfinite float64 without rejection. The initial shortcut can report convergence from that invalid stored state. Validation must target the normalized execution dtype.
- C01: with finite direct prior LLRs 1e308, both full BP4 decode and CPU batch silently complete after the shared scalar-edge-resolution sweep overflow; they do not report numerical failure. The sweep counterexample in spike 027 supplies the internal-state witness.

## Run
`OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=4 PYTHONPATH=src:.planning/spikes .venv/bin/python .planning/spikes/030-freeze-execution-audit/probe.py`

Selected regressions: `tests/canonical/test_boundary_fixes.py`, `test_stable_spa_policy.py`, `test_residual_schedule.py`, and `test_kernel_contract_admission.py`.

## Investigation Trail
The first full-run overflow fixture had two redundant checks; its large prior offset prevented overflow. That harness assertion is retained in harness-first-run.log. Three redundant commuting checks produce the intended finite-input overflow, confirmed first through a visible sweep and then through full decode/batch. No malformed native CSR was executed. All prior changes use structurally valid graph replacement.
