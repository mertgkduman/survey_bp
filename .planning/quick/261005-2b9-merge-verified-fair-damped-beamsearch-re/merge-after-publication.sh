#!/usr/bin/env bash
set -euo pipefail

source_worktree=/hpc/home/mg551/gsd-workspaces/fair-damped-beam-relay/survey_bp
merge_worktree=/hpc/home/mg551/gsd-workspaces/integration-fair-beam-relay-main/survey_bp
python_bin=/hpc/group/pfisterlab/mg551/storage/survey_bp/.venv/bin/python
old_main=51e6317095ad73158331bcf921c2e25297480753

cd "$source_worktree"
if [[ -n "$(git status --porcelain)" ]]; then
  echo 'Feature worktree has uncommitted changes' >&2
  exit 1
fi
git fetch origin main feat/fair-damped-beam-relay
published_main="$(git rev-parse origin/main)"
if [[ "$published_main" == "$old_main" ]]; then
  echo 'BB72 v2 publication is absent from origin/main' >&2
  exit 1
fi
git cat-file -e "$published_main:data/results/bb72-bpsf-factorial-v2/publication-manifest.json"
git cat-file -e "$published_main:data/results/bb72-bpsf-factorial-v2/study.html"
if [[ -e "$merge_worktree" ]]; then
  echo 'Integration worktree already exists; inspect before retry' >&2
  exit 1
fi
mkdir -p "$(dirname "$merge_worktree")"
git worktree add -b integration/fair-beam-relay-main "$merge_worktree" origin/main
cd "$merge_worktree"
git merge --no-ff -m 'Merge fair damped BeamSearch and RelayBP after BB72 v2 publication' origin/feat/fair-damped-beam-relay
git diff --check "$published_main"..HEAD

export PYTHONPATH="$PWD/src"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
"$python_bin" -m pytest -q \
  tests/canonical/test_fair_legs.py \
  tests/test_run_fair_beam_relay_css.py \
  tests/canonical/test_relay.py \
  tests/canonical/test_memory_policies.py
"$python_bin" scripts/run_fair_beam_relay_css.py verify \
  --design data/studies/fair-beam-relay-css-v1.json \
  --output data/results/fair-beam-relay-css-v1-smoke

if [[ -n "$(git status --porcelain)" ]]; then
  echo 'Integration worktree changed during verification' >&2
  exit 1
fi
git push origin HEAD:main
merged_head="$(git rev-parse HEAD)"
remote_main="$(git ls-remote origin refs/heads/main | awk '{print $1}')"
if [[ "$remote_main" != "$merged_head" ]]; then
  echo 'Remote main does not equal verified merge commit' >&2
  exit 1
fi
printf 'Published BB72 v2 base: %s\nMerged main: %s\n' "$published_main" "$merged_head"
