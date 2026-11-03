---
status: complete
date: 2026-11-02
---

# Consolidate research development onto main

1. Refresh refs and record live branch/worktree inventories. Annotate recovery
   tags for every branch/ref being retired; snapshot the five unverified local
   refresh files separately. Preserve untracked evidence in place and remove
   only clean obsolete worktrees after recording their state.
2. Create an isolated integration worktree from the current research tip.
   Establish baseline regression results, merge the two Phase 6 candidate-list
   commits and three low-noise campaign commits with their histories intact,
   review compatibility and fix concrete failures. Record any baseline failures
   separately; do not relabel scientific reproduction or publication gates.
3. Validate the final tree, document the single-main workflow and archive map,
   fast-forward local/remote main without rewriting history, tag the consolidated
   state, verify remote identities, retire represented branch refs and clean
   obsolete worktrees. Keep dirty/evidence worktrees detached at archived tips.

User authorized this consolidation, remote publication and retirement after
review. Execution is inline; no subagents or automatic model escalation.
