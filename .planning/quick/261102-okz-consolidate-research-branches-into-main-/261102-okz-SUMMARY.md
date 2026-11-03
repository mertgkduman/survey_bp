---
status: complete
date: 2026-11-02
validated_commit: 8ec6d14bf247c0857bbb6224b32d1ab9dd15d321
published_validation_commit: 22f881f19d354f4f4f027f1ebb669915379d53e7
milestone_tag: consolidated/2026-11-02
---

# Consolidate research development onto main

The latest research line and both remaining unique branches are integrated into
`main`. GitHub main was fast-forwarded without rewriting history. Only `main`
remains active locally and remotely; its upstream is `origin/main`.

- Merged Phase 6 candidate-list selection with its two original commits.
- Merged the three low-noise campaign commits, including diagnostic proposals
  kept separate from selected recoveries.
- Confirmed the BB72 and three fix lines already had equivalent patches.
- Retired seven remote and twenty local branches, including the temporary
  integration branch. Published annotated archive tags preserve all 28 original
  local/remote tips. A separate tag retains the five unverified report refreshes.
- Removed nine clean worktrees after archiving their ignored files, and pruned
  one missing temporary registration. Retained three evidence worktrees at
  detached archived commits. All 14,319 original primary untracked paths and
  all 93 untracked paths in those retained worktrees remained present.
- Preserved the Git trees for reproduction data, code artifacts, manifests,
  literature policies, and `from_dr_pfister_presentetations` exactly.

## Validation

The final primary-checkout regression passed **1,514 tests, with one existing
skip** (2,317.81 seconds). The skip is the deferred Wave 1 notebook evidence
check, recorded verbatim in `validation.json`. The existing 25 warnings were
not test failures.

The initial isolated baseline had 1,476 passes, 26 failures, and one skip.
Twenty-four failures came from missing external/local fixtures, notebook or CLI
environment prerequisites, and historical absolute paths. The three retained
replay tests passed in the primary checkout. The other two failures exposed a
historical Q-BPGD qualification inheriting v2 execution but v1 replay: both are
now explicitly pinned to its original v1 profile. New canonical defaults remain
v2. The merged-feature and source-study checks also passed (20 tests).

No scientific assessment status was upgraded. The current Phase 11 work and its
open publication gates remain as recorded in project state.

## Records and recovery

- `branch-inventory.json`: original refs, commits, and recovery tags.
- `validation.json`: exact test counts, commands, log hashes, fixture requirements,
  and unchanged research-tree identities.
- `retirement.json`: retired refs, retained worktrees, and local backup archives.
- `docs/git-workflow.md`: ongoing main workflow, recovery commands, and full-suite
  environment requirements.
- Local inventories, raw validation logs, ignored-file tar archives, and the
  report-refresh backup: `.git/consolidation-backups/2026-11-02/` in the primary
  checkout. Untracked research data remains local and is not supplied by tags.

Execution was inline under the quick workflow. No subagents, model escalation,
or model/workflow preference changes were used.
