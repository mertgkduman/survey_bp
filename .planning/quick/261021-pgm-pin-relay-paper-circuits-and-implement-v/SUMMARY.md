---
status: complete
type: quick
date: 2026-10-21
commit: 93757e2
---

# Pinned circuit fixtures and canonical Sinter BP adapter

Imported 672 Relay-BP v0.2.2 and 38 BeamSearch author `.stim` circuits into separate source archives with exact upstream commits, retained licenses, per-file SHA-256 inventories, and directly usable representatives. Added a Stim DEM to independent binary-fault graph projection and an opt-in Numba CPU decoder implementing Sinter's bit-packed observable interface. It uses canonical numerical/check primitives, plain flooding SPA or min-sum, and an explicit zero-belief tie policy.

The matched-input, warm CPU profile used 4,096, 2,048, 1,024, 128, and 512 shots on five pinned circuit fixtures. With Relay's tie policy, every observable prediction matched the isolated author v0.2.2 Rust build and the installed local fork. The canonical CPU path took 0.0206–1.4449 seconds versus author Rust 0.0402–2.0946 seconds across those batches. These are bounded local timings, not paper-curve reproduction or stable speed ratios. The eight-iteration BB144 diagnostics had zero converged shots. The canonical default tie rule disagreed with author Rust on one surface-code shot; explicit Relay tie policy resolved that difference.

Added a cross-regime paper index, non-runnable source policy files for aSCED, Q-BP/Q-BPGD, MBP4, Relay-BP circuits, and BeamSearch circuits, and refreshed both READMEs. Paper-specific circuit source settings and statistical gates remain unqualified. CPU only: the login node exposed no GPU device or backend, while Slurm advertises GPU partitions; no GPU performance claim was made.

Verification: 42 focused tests passed; all 24 `.spec.toml` records parsed as non-runnable; 710 archived circuits passed archive and per-file digest checks; checked 14 Markdown files with zero broken local links; `git diff --cached --check` passed before commit.
