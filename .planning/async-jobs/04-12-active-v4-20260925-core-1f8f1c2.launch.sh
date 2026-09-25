#!/usr/bin/env bash
# Resume-safe detached launcher for the identified Plan 04-12 active-memory v4 benchmark.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT"
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

printf 'launching campaign=04-12-active-v4-20260925-core-1f8f1c2 pid=%s started_at=%s omp=%s\n' \
  "$$" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$OMP_NUM_THREADS"

exec .venv/bin/python scripts/run_phase4_active_campaign.py \
  --run \
  --output data/results/phase4-memory-relay/benchmark-v4-active-04-12-active-v4-20260925-core-1f8f1c2.json \
  --slurm-job-id 55938300 \
  --campaign-id 04-12-active-v4-20260925-core-1f8f1c2
