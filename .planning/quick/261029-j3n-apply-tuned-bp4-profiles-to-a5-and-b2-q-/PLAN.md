---
status: in_progress
date: 2026-10-29
---

# Tuned BP4 inside Q-BPGD

Apply the frozen A5 and B2 BP4 priors and numerical profiles to the four-state Q-BPGD controller at physical depolarizing probability 0.06. Keep Q-BPGD's decimation settings and persistent-message semantics explicit. Run a paired, bounded comparison against the corresponding untuned Q-BPGD settings, retain per-shot evidence and independent logical outcomes, and document work and claim limits.

1. Identify the current Q-BPGD session binding and selected BP4 policy files.
2. Add a reproducible tuned Q-BPGD experiment with a frozen policy specification and event ledger.
3. Verify the tuned profile is used during all rounds, run bounded paired A5/B2 samples, and report counts and mean work.
4. Update project quick-task state and commit only owned files.
