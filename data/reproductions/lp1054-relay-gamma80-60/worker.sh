#!/usr/bin/env bash
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
export NUMBA_CACHE_DIR="/tmp/lp1054-gamma-${SLURM_JOB_ID}"
mkdir -p "$NUMBA_CACHE_DIR"
child_pid=''
resume_later() {
  if [[ -n "$child_pid" ]]; then
    kill -TERM "$child_pid" 2>/dev/null || true
    wait "$child_pid" 2>/dev/null || true
  fi
  scontrol requeue "$SLURM_JOB_ID"
  exit 0
}
trap resume_later USR1
.venv/bin/python data/reproductions/lp1054-relay-gamma80-60/run.py --index "$SLURM_ARRAY_TASK_ID" &
child_pid=$!
wait "$child_pid"
child_pid=''
.venv/bin/python data/reproductions/lp1054-relay-gamma80-60/run.py --audit --index "$SLURM_ARRAY_TASK_ID" &
child_pid=$!
wait "$child_pid"
