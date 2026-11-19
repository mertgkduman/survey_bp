#!/usr/bin/env bash
set -euo pipefail
study=data/reproductions/priortilt-2611-13373-advanced-tuning
export PYTHONPATH="$PWD/src" OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
export NUMBA_CACHE_DIR="${TMPDIR:-/tmp}/adv-bp-${SLURM_JOB_ID}-${SLURM_ARRAY_TASK_ID:-0}"
mkdir -p "$NUMBA_CACHE_DIR"
child=''
cleanup() {
    if [[ -n "$child" ]]; then
        kill -TERM -- "-$child" 2>/dev/null || true
        wait "$child" || true
    fi
    rm -rf -- "$NUMBA_CACHE_DIR"
}
checkpoint() {
    trap '' USR1
    cleanup
    child=''
    scontrol requeue "$SLURM_JOB_ID"
    exit 0
}
trap cleanup EXIT
trap checkpoint USR1
trap 'exit 143' TERM INT
step() {
    setsid .venv/bin/python "$study/$1" "${@:2}" &
    child=$!
    wait "$child"
    child=''
}
case "$1" in
    screen) step screen.py "$2" ;;
    tune) step tune.py "$SLURM_ARRAY_TASK_ID" ;;
    confirm)
        step confirm.py "$SLURM_ARRAY_TASK_ID"
        step confirm.py "$SLURM_ARRAY_TASK_ID" --audit
        ;;
    collect) step report.py ;;
    *) exit 2 ;;
esac
