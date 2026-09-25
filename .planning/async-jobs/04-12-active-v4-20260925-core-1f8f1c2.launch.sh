#!/usr/bin/env bash
# Resume-safe detached launcher for the identified Plan 04-12 active-memory v4 benchmark.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT"
LOCK_DIR="data/results/phase4-memory-relay/benchmark-artifacts/04-12-active-v4-20260925-core-1f8f1c2/.launcher-lock"
mkdir -p "$(dirname "$LOCK_DIR")"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  OWNER_PID=$(cat "$LOCK_DIR/pid" 2>/dev/null || true)
  if [ -n "$OWNER_PID" ] && kill -0 "$OWNER_PID" 2>/dev/null; then
    printf 'refusing duplicate active campaign launch: pid=%s still owns %s\n' "$OWNER_PID" "$LOCK_DIR" >&2
    exit 75
  fi
  rm -f "$LOCK_DIR/pid"
  rmdir "$LOCK_DIR"
  mkdir "$LOCK_DIR"
fi
printf '%s\n' "$$" > "$LOCK_DIR/pid"
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
