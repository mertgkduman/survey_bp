# Git workflow

`main` is the shared development and release branch. Start new work from an
up-to-date `main`; use a short-lived branch only when isolation or review needs
one. GSD is configured with `git.branching_strategy = "none"`, so a phase does
not require a permanent phase branch.

Before merging, check the decoder policy identities, retained evidence, and
appropriate regression tests. Preserve explicitly frozen numerical profiles in
historical experiments. A default change applies to new configurations; it must
not silently alter a replay or relabel an existing result.

Push the merged history to `main`, verify the remote commit, and retire the
completed branch. Inspect both untracked and ignored files before removing a
worktree. Campaign ledgers, notebooks, and interrupted evidence can exist
outside tracked files.

## Consolidation on 2 November 2026

The latest research history was combined with the two remaining unique lines
of work: Phase 6 candidate-list selection and the Phase 4 low-noise campaign
tools and diagnostic proposals. Merge commits retain their original histories.
The older BB72 and three fix branches already had equivalent patches in the
research history. Existing experiments and their assessments retain their
original identities.

Every former local and remote branch tip has a published annotated recovery tag:

```text
archive/2026-11-02/pre-consolidation/local/<branch>
archive/2026-11-02/pre-consolidation/remote/<branch>
```

The [branch inventory](../.planning/quick/261102-okz-consolidate-research-branches-into-main-/branch-inventory.json)
maps each original ref to its full commit and archive tag. Inspect or recover an
archived line without moving `main`:

```bash
git fetch origin --tags
git show archive/2026-11-02/pre-consolidation/local/phase6-beam-search
git switch -c recovery/phase6 archive/2026-11-02/pre-consolidation/local/phase6-beam-search
```

Five unverified local Yao report-refresh files were snapshotted separately as
`archive/2026-11-02/unverified-working-refresh`. This tag preserves the working
tree bytes for inspection; those files were not promoted to verified results.

Three evidence-bearing HPC worktrees are retained at their archived commits in
detached state:

| Directory | Retained material |
| --- | --- |
| `/hpc/group/pfisterlab/mg551/storage/survey_bp_low_noise_20260925` | Low-noise smoke manifests and ledgers |
| `/hpc/group/pfisterlab/mg551/storage/survey_bp_memory_integration_20260926` | Notebooks, plots, and HTML |
| `/hpc/home/mg551/gsd-workspaces/fair-beam-relay-campaign/survey_bp` | Campaign ledgers, logs, and results |

The primary checkout retains its untracked research data. Detailed local
inventories, file backups, and validation logs live in
`.git/consolidation-backups/2026-11-02/` in that checkout. These local files are
not supplied by GitHub archive tags.

## Regression environment

Run the full suite from the primary checkout using its qualified environment:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONPATH=src:. \
  .venv/bin/python -m pytest -q
```

Install the project entry points and optional analysis dependencies first; see
[environment pins](environment-pins.md). The notebook executor requires the
project `.venv/bin/python`. Some older campaign receipts contain absolute paths
to the primary checkout, and the Phase 4 cancelled-attempt inventory reads a
retained local `attempts.json`. Those integration tests require that evidence;
a fresh clone alone is insufficient.

Source-qualification tests also expect these externally obtained, pinned inputs:

| Local input | Source and identity |
| --- | --- |
| `/tmp/phase11-mbp4.pdf` | `https://arxiv.org/pdf/2104.13659`; SHA256 `37d3a734c1e617eecc45ed1cd641dd92b89adfd7e15390ef403d90637c547f23` |
| `/tmp/phase11-qbpgd-v2.pdf` | `https://arxiv.org/pdf/2312.10950v2`; SHA256 `cdc0af68a2edb55ab8c961989333258aac2cb8e30b7943a14c076dab4e719404` |
| `/tmp/phase10-asced-native/source/quantum_asced` | `https://github.com/kit-cel/quantum_asced.git`, commit `816772071486615dfc7d71d1e15df597edc58a26` |

Verify the pinned bytes when restoring these inputs. The source checkout is
used read-only for qualification; obtaining it does not authorize a new native
execution or change any source-fidelity assessment.
