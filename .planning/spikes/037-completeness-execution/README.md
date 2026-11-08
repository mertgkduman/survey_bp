---
spike: 037
idea: canonical-kernel-audit
name: completeness-execution
type: standard
validates: "Execution, circuit and evidence closure"
verdict: PARTIAL
related: [027, 028, 029, 030, 031, 032, 033]
tags: [completeness]
---

# Execution, circuit and evidence closure

## Investigation Trail
Continues the already approved mathematics → upstream → policy → execution order. Production baseline 4cce08e. Historical spikes 008–033 remain unchanged. This is an audit, not a behavior migration.

## Research and approach
Extend alternate-construction and immutable-state checks to circuit/model/original-problem surfaces. Avoid executing malformed buffers in bounds-unchecked native code. Use ordinary NumPy write-flag mutation to test ownership claims, then compare exported evidence with independently computed parity. Interpret [Stim DEM semantics](https://github.com/quantumlib/Stim/blob/main/doc/file_format_dem_detector_error_model.md) independently on an eight-assignment affine fixture.

## Results
Four controls pass and nine invariants fail: **D03** five circuit construction bypasses, **D04** three mutable original/model boundaries, and **D05** one stale batch evidence export. The valid batch control and deliberately invalid exported event are stored separately. The latter is a counterexample, never an accepted scientific run.

The DEM fixture preserves deterministic biases, separator-linked single faults and an undetected logical mechanism. Existing corrected flooding graph ownership is a passing control. Full regression results are retained in `full-regression.log` and `full-regression.xml`; the consolidated verification receipt reports exact counts and skip reasons.

## Run and observability
`NUMBA_NUM_THREADS=4 .venv/bin/python .planning/spikes/037-completeness-execution/probe.py`

`results.json` retains inputs/details, source hashes, package versions, grouped verdicts and failing assertions. A zero process exit means the audit completed, not that every invariant passed. See [the consolidated report](../CANONICAL-KERNEL-COMPLETENESS-AUDIT.md) for fixes, limitations and freeze gates.

## Full regression receipt
`NUMBA_NUM_THREADS=4 OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests --junitxml=.planning/spikes/037-completeness-execution/full-regression.xml` completed with **2109 passed, 1 existing skip, 25 fork/multithread deprecation warnings** in 1400.71 seconds. No source/test fixes were made. The full suite passing does not close the nine newly demonstrated execution invariants. The retained collection lists 2110 tests; slow public CLI and resource-gate sections completed normally.
