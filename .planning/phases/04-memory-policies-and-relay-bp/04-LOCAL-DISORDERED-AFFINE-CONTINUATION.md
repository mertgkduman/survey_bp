---
phase: 04-memory-policies-and-relay-bp
scope: local deterministic disordered affine-prior execution
status: implementation_slice_complete
commits: [3a3bb8c]
date: 2026-09-27
---

# Local disordered affine-prior continuation

`3a3bb8c` admits the existing uniform PCG64 affine-prior assignment for the
implemented deterministic local schedules: `layered`, `check_node_serial`, and
`variable_node_serial`. The controller stages each assignment, its history
proposal, and optional trace payload at the start of a source iteration, then
commits them only after every local unit in that traversal has committed.

The public runner and independent semantic replayer now supply the same
decoder-local execution identity to the local controller. Trace configuration
does not affect the identity or assignment stream. A trace records assignment
evidence only after a completed source iteration; denied partial traversals and
injected numerical failures retain no staged assignment evidence.

## Validation

- `OMP_NUM_THREADS=1 PYTHONPATH=src /hpc/group/pfisterlab/mg551/storage/survey_bp/.venv/bin/python -m pytest -q tests/canonical/test_local_memory_execution.py` — 22 passed.
- `OMP_NUM_THREADS=1 PYTHONPATH=src /hpc/group/pfisterlab/mg551/storage/survey_bp/.venv/bin/python -m pytest -q tests/canonical/test_local_memory_execution.py -k 'disordered or numerical_failure or ordered_affine'` — 10 passed, 12 deselected.
- `OMP_NUM_THREADS=1 PYTHONPATH=src /hpc/group/pfisterlab/mg551/storage/survey_bp/.venv/bin/python -m pytest -q tests/canonical/test_memory_trace.py -k 'public_v4_trace_links_committed_memory_and_keeps_assignment_rng_observational'` — 1 passed, 8 deselected.

## Limits

- Lifetime remains `attempt`; refresh remains `attempt_start`; history retention remains disabled.
- This slice does not admit residual, randomized, group-shuffled, Relay-leg, search-member, or retained-history local execution.
- Assignment remains a decoder-local uniform PCG64 affine-prior mechanism; it has no access to physical hidden truth.
- No production sampling, calibration/evaluation artifacts, phase summary, or completion state was created or changed.
