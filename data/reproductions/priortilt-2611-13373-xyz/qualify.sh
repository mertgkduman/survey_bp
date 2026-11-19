#!/usr/bin/env bash
set -euo pipefail
cd /hpc/group/pfisterlab/mg551/storage/survey_bp
export PYTHONPATH=src OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
export NUMBA_CACHE_DIR="${TMPDIR:-/tmp}/priortilt-xyz-qual-${SLURM_JOB_ID}"
mkdir -p "$NUMBA_CACHE_DIR"
trap 'rm -rf "$NUMBA_CACHE_DIR"' EXIT
exec .venv/bin/python data/reproductions/priortilt-2611-13373-xyz/qualify.py
