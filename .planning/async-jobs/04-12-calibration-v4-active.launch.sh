#!/usr/bin/env bash
# Resume-safe one-worker launcher for the frozen active-memory calibration.
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT"
LOCK_DIR="data/results/phase4-memory-relay/calibration/.launcher-lock"
mkdir -p "$(dirname "$LOCK_DIR")"
if ! mkdir "$LOCK_DIR" 2>/dev/null; then
  OWNER_PID=$(cat "$LOCK_DIR/pid" 2>/dev/null || true)
  if [ -n "$OWNER_PID" ] && kill -0 "$OWNER_PID" 2>/dev/null; then
    printf 'refusing duplicate calibration launch: pid=%s still owns %s\n' "$OWNER_PID" "$LOCK_DIR" >&2
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

printf 'launching calibration pid=%s started_at=%s caps_commit=44201be\n' \
  "$$" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"

exec .venv/bin/python scripts/run_phase4_pilots.py \
  --run-calibration \
  --calibration-caps data/manifests/phase4-pilot-caps.json \
  --calibration-output data/results/phase4-memory-relay/calibration
