#!/usr/bin/env bash
set -euo pipefail
study=data/reproductions/priortilt-2611-13373-bp
export PYTHONPATH="$PWD/src" OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
export NUMBA_CACHE_DIR="${TMPDIR:-/tmp}/priortilt-bp-${SLURM_JOB_ID}-${SLURM_ARRAY_TASK_ID:-0}"
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
run_step() {
    setsid .venv/bin/python "$study/$1" "${@:2}" &
    child=$!
    wait "$child"
    child=''
}
case "$1" in
    tune) run_step tune.py "$2" ;;
    evaluate)
        run_step evaluate.py "$SLURM_ARRAY_TASK_ID"
        run_step evaluate.py "$SLURM_ARRAY_TASK_ID" --audit
        ;;
    collect) run_step report.py ;;
    qualify) run_step qualify.py ;;
    *) exit 2 ;;
esac
