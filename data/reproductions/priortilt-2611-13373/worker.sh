#!/usr/bin/env bash
set -euo pipefail
study=/hpc/group/pfisterlab/mg551/storage/survey_bp/data/reproductions/priortilt-2611-13373
python=/hpc/group/pfisterlab/mg551/storage/survey_bp/.venv/bin/python
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
export NUMBA_CACHE_DIR="${TMPDIR:-/tmp}/priortilt-${SLURM_JOB_ID}-${SLURM_ARRAY_TASK_ID}"
mkdir -p "$NUMBA_CACHE_DIR"
child=''
cleanup() { rm -rf "$NUMBA_CACHE_DIR"; }
checkpoint() {
  trap '' USR1
  if [[ -n "$child" ]]; then kill -TERM "$child" 2>/dev/null || true; wait "$child" || true; fi
  scontrol requeue "${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
  exit 0
}
trap cleanup EXIT
trap checkpoint USR1
"$python" "$study/run.py" --index "$SLURM_ARRAY_TASK_ID" &
child=$!
wait "$child"
child=''
# A fresh interpreter validates the entire retained ledger in the same CPU allocation.
"$python" "$study/run.py" --index "$SLURM_ARRAY_TASK_ID" --audit &
child=$!
wait "$child"
child=''
