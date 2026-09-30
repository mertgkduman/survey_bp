#!/usr/bin/env bash
# Run the bounded Phase 4 production sequence inside the declared allocation.
set -euo pipefail

if [ "${SLURM_JOB_ID:-}" != "55938300" ]; then
  echo "Phase 04-13 requires the frozen one-worker allocation 55938300." >&2
  exit 2
fi

cd /hpc/group/pfisterlab/mg551/storage/survey_bp
export OMP_NUM_THREADS=1
export PYTHONPATH=src

.venv/bin/python scripts/run_phase4_evaluation.py --run \
  --output data/results/phase4-memory-relay/evaluation
.venv/bin/python scripts/run_phase4_evaluation.py --run-native \
  --output data/results/phase4-memory-relay/evaluation
.venv/bin/python scripts/run_phase4_factorial.py --run \
  --evaluation data/results/phase4-memory-relay/evaluation/result.json \
  --output data/results/phase4-memory-relay/factorial
