#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
root="$PWD"
output="$root/data/results/fair-beam-relay-css-v2"
design="$root/data/studies/fair-beam-relay-css-v2.json"
python_bin=/hpc/group/pfisterlab/mg551/storage/survey_bp/.venv/bin/python
mkdir -p "$output/logs"

export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
"$python_bin" scripts/run_fair_beam_relay_campaign.py prepare --design "$design" --output "$output" >/dev/null

selection_job="$(sbatch --parsable --partition=common --array=0-5 --cpus-per-task=8 --mem=16G \
  --time=06:00:00 --job-name=fair-br-select --chdir="$root" \
  --output="$output/logs/selection-%A_%a.log" \
  --wrap='bash scripts/run_fair_beam_relay_campaign_slurm.sh selection')"
lock_job="$(sbatch --parsable --partition=common --dependency="afterok:$selection_job" \
  --cpus-per-task=6 --mem=16G --time=04:00:00 --job-name=fair-br-lock --chdir="$root" \
  --output="$output/logs/selection-lock-%j.log" \
  --wrap="$python_bin scripts/run_fair_beam_relay_campaign.py select --design data/studies/fair-beam-relay-css-v2.json --output data/results/fair-beam-relay-css-v2 --workers 6")"
evaluation_job="$(sbatch --parsable --partition=common --array=0-5 --dependency="afterok:$lock_job" \
  --cpus-per-task=8 --mem=16G --time=08:00:00 --job-name=fair-br-eval --chdir="$root" \
  --output="$output/logs/evaluation-%A_%a.log" \
  --wrap='bash scripts/run_fair_beam_relay_campaign_slurm.sh evaluation')"
report_job="$(sbatch --parsable --partition=common --dependency="afterok:$evaluation_job" \
  --cpus-per-task=6 --mem=32G --time=08:00:00 --job-name=fair-br-report --chdir="$root" \
  --output="$output/logs/report-%j.log" \
  --wrap="$python_bin scripts/run_fair_beam_relay_campaign.py report --design data/studies/fair-beam-relay-css-v2.json --output data/results/fair-beam-relay-css-v2 --workers 6")"

printf '{"selection_array":"%s","selection_lock":"%s","evaluation_array":"%s","report":"%s"}\n' \
  "$selection_job" "$lock_job" "$evaluation_job" "$report_job" | tee "$output/jobs.json"
