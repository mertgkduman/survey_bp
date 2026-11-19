#!/usr/bin/env bash
set -euo pipefail
study=/hpc/group/pfisterlab/mg551/storage/survey_bp/data/reproductions/priortilt-2611-13373-xyz
python=/hpc/group/pfisterlab/mg551/storage/survey_bp/.venv/bin/python
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
export NUMBA_CACHE_DIR="${TMPDIR:-/tmp}/priortilt-xyz-${SLURM_JOB_ID}-${SLURM_ARRAY_TASK_ID}"
mkdir -p "$NUMBA_CACHE_DIR"
child=''
cleanup() {
  if [[ -n "$child" ]]; then kill -TERM -- "-$child" 2>/dev/null || true; wait "$child" || true; fi
  rm -rf "$NUMBA_CACHE_DIR"
}
checkpoint() { trap '' USR1; cleanup; child=''; scontrol requeue "${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID}"; exit 0; }
trap cleanup EXIT
trap checkpoint USR1
trap 'exit 143' TERM INT
printf 'Running XYZ point %s with %s CPUs; validating inherited prefix before continuation\n' "$SLURM_ARRAY_TASK_ID" "$SLURM_CPUS_PER_TASK"
setsid "$python" "$study/parallel.py" --index "$SLURM_ARRAY_TASK_ID" &
child=$!;wait "$child";child=''
setsid "$python" "$study/parallel.py" --index "$SLURM_ARRAY_TASK_ID" --audit &
child=$!;wait "$child";child=''
