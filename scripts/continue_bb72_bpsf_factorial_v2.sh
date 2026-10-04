#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 || ! "$1" =~ ^[0-9]+$ || ! "$2" =~ ^[0-9]+$ ]]; then
  echo "usage: $0 SOURCE_RUN_JOB_ID ORIGINAL_PUBLISH_JOB_ID" >&2
  exit 2
fi

source_job_id="$1"
original_publish_job_id="$2"
cd "$(dirname "$0")/.."
source_state="$(sacct -X -j "$source_job_id" --format=State --noheader | head -n 1 | awk '{print $1}')"
echo "source job $source_job_id state: $source_state"

if [[ "$source_state" == "COMPLETED" ]]; then
  echo "original run completed; its dependent publication job owns publication"
  exit 0
fi
if [[ "$source_state" != "TIMEOUT" && "$source_state" != "FAILED" && "$source_state" != "CANCELLED" && "$source_state" != "OUT_OF_MEMORY" ]]; then
  echo "source job has no supported terminal failure state" >&2
  exit 1
fi

export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 BB72_V2_VERIFY_WORKERS=12
.venv/bin/python scripts/recover_bb72_bpsf_factorial_v2.py --source-job-id "$source_job_id"

# The original afterok dependency cannot fire after a failed source job.
scancel "$original_publish_job_id" || true
.venv/bin/python scripts/run_bb72_bpsf_factorial_v2.py report
.venv/bin/python scripts/render_bb72_bpsf_factorial_v2.py
.venv/bin/python scripts/package_bb72_bpsf_factorial_v2.py
.venv/bin/python scripts/publish_bb72_bpsf_factorial_v2.py
