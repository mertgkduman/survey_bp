# Verification, 2026-10-05

- Five new workflow tests passed. They cover canonical TOML compute/reuse/tamper rejection, JSON/TOML semantic equivalence, unsupported-policy rejection, schema v4 memory/Relay execution, commented TOML damping changes, and published BB72 package reuse.
- The existing fair BeamSearch/RelayBP campaign end-to-end test also passed; six focused tests passed together.
- A one-shot-per-rate BB72 campaign smoke generated all selection and evaluation shards, selection lock, report, compressed package, and then reused the same output on a second call.
- The installed command's wheel entry point and public module were confirmed in a wheel built from an isolated source copy. Direct `python -m bp_registry.study_cli` reuse returned the published BeamSearch counts.
- The previously published BB72 package still passed its own `verify-package` check after the new API was added. `git diff --check` and Python compilation passed.

The new command composes registered canonical CSS policies through schema v2/v3 and ordered memory/Relay through v4. The BB72 fair-leg campaign is a separate registered backend. New Python policy implementations and Phase 5 controls need their own interface qualification. Phase 6 replanning remains open.
