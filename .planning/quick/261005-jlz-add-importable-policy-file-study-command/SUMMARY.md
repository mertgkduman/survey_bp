---
status: complete
quick_id: 261005-jlz
date: 2026-10-05
---

# Importable policy-file study command

Added `bp_registry.study.ensure_study` and the `bp-registry` installed command. Both accept a study JSON file plus a declarative decoder file. TOML is the documented hand-written format with comments; JSON is also accepted and has the same semantics. Canonical CSS studies expand seven explicit policy roles and optional schema v4 memory/Relay controls into the existing strict manifest and engine. A registered adapter exposes the published BB72 BeamSearch/RelayBP campaign through the same command.

For a complete result, the command verifies evidence before returning it. Otherwise it runs the study and verifies the new result. Canonical results are keyed by the effective manifest and source identity; a fixed physical sample identity supports matched comparisons. Published BB72 reuse checks the package file hashes and decompressed shot ledgers. The command rejects altered evidence and nonempty incomplete campaign output.

Implementation commit: `1f8b1c3`. Six focused tests passed, including compute/reuse and the existing campaign test; a tiny missing-campaign smoke passed; the previously published package still verified. See `docs/researcher-study-command.md` and `examples/` for commands and files. The command does not interpret arbitrary Python code from a policy file and does not qualify unsupported policy families or circuit-level studies.
