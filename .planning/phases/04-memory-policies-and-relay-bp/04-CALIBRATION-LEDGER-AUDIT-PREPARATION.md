# Phase 4 terminal calibration ledger audit preparation

The isolated `verify_phase4_calibration.py --ledgers` path is ready to run once
the original calibration producer reaches a terminal result. It first performs
the frozen surface audit, then independently compares each configuration's
retained manifest with the frozen plan. It streams the aggregate ledger one
shot at a time, checks exact appended-byte digests, event grammar, Relay work,
sample identity, outcome, termination, and complete terminal-shot coverage.
The streaming design avoids loading the large aggregate ledger into memory.

Run from this isolated checkout after the main result is terminal:

```bash
OMP_NUM_THREADS=1 PYTHONPATH=src \
  /hpc/group/pfisterlab/mg551/storage/survey_bp/.venv/bin/python scripts/verify_phase4_calibration.py \
  --root /hpc/group/pfisterlab/mg551/storage/survey_bp --ledgers
```

The audit is read-only. It does not select settings or launch evaluation.
The live calibration remains running, so no terminal verdict has been claimed.
The real Relay fixture test passes, tampered outcomes are rejected, and one
completed and one budget-exhausted live shot were individually reconstructed.
The focused Phase 4 evidence/evaluation suite passed 46 tests with one skip.
