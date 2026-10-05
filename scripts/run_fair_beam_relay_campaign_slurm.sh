#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 || ( "$1" != selection && "$1" != evaluation ) ]]; then
  echo 'usage: run_fair_beam_relay_campaign_slurm.sh selection|evaluation' >&2
  exit 2
fi
if [[ ! "${SLURM_ARRAY_TASK_ID:-}" =~ ^[0-5]$ ]]; then
  echo 'SLURM_ARRAY_TASK_ID must be 0..5' >&2
  exit 2
fi

case "$SLURM_ARRAY_TASK_ID" in
  0) rate=p050; profile=i05 ;;
  1) rate=p050; profile=i10 ;;
  2) rate=p050; profile=i20 ;;
  3) rate=p080; profile=i05 ;;
  4) rate=p080; profile=i10 ;;
  5) rate=p080; profile=i20 ;;
esac

cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
/hpc/group/pfisterlab/mg551/storage/survey_bp/.venv/bin/python \
  scripts/run_fair_beam_relay_campaign.py run \
  --design data/studies/fair-beam-relay-css-v2.json \
  --output data/results/fair-beam-relay-css-v2 \
  --cohort "$1" --rate "$rate" --profile "$profile" --workers 8
