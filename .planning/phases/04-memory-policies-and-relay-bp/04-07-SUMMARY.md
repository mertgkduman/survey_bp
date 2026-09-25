---
phase: 04-memory-policies-and-relay-bp
plan: "07"
subsystem: source-provenance
tags: [relay-bp, source-pin, provenance, supply-chain]
requires: [04-04]
provides: [approved-relay-v0.2.2-reference]
affects: [04-08-native-reference-build, relay-source-evidence]
tech_stack:
  added: []
  patterns: [immutable-author-git-pin, separate-local-fork-identity, human-source-legitimacy-gate]
key_files:
  created:
    - .planning/phases/04-memory-policies-and-relay-bp/04-07-SUMMARY.md
  modified: []
decisions:
  - "Use only trmue/relay tag v0.2.2 at immutable commit 14cb31a18f9b9d7d099791b793e35b8a2951f8f3 as the original Relay reference."
  - "Keep the PyPI relay-bp package and editable mg551-duke/relay fork outside the approved original-reference identity."
metrics:
  duration: "continuation under 1m"
  completed: 2026-09-25
status: complete
plan_head_before: 00afdfbaf4cc01654c1a4b32e466455e7b7945eb
commits: 0
actuals:
  tokens: 2052
  tasks: 1
  commits: 0
---

# Phase 04 Plan 07: Relay Source Legitimacy Summary

The original Relay reference is approved only as `trmue/relay` tag `v0.2.2` at immutable commit `14cb31a18f9b9d7d099791b793e35b8a2951f8f3`, with the PyPI package and local fork retained as separate identities.

## Delivered

- Re-ran the planned read-only tag check: `git ls-remote https://github.com/trmue/relay.git 'refs/tags/v0.2.2*'` resolved `refs/tags/v0.2.2` directly to `14cb31a18f9b9d7d099791b793e35b8a2951f8f3`.
- Re-ran the registry review: `pip index versions relay-bp` reported `0.2.2` as the latest PyPI release and `0.2.1` as installed. The reviewed PyPI metadata does not establish the author-repository identity; its previously recorded source-distribution SHA-256 is `be47a267b87f20bf2545cf744646c5f6abbbac5425f4221586449f9f3355d892`.
- Preserved the installed editable package as `mg551-duke/relay@8216aca3153642044e2cdccbaa41547d15551bb0`. It remains 41 commits beyond merge-base `b68115d062941fb0f11d8e04e2007dec73266be8` and cannot satisfy the original-reference gate.
- Recorded the explicit human response, normalized as `approved author v0.2.2 pin`. It approves the author repository/tag/commit only; it does not approve the PyPI package or the installed `mg551-duke` fork.
- Performed no package installation, native build, source checkout, or source mutation. Plan 04-08 remains responsible for isolated native-reference setup and build verification.

## Provenance

- Paper: [Müller et al., Relay-BP, arXiv:2506.01779v2](https://arxiv.org/abs/2506.01779).
- Author release: [trmue/relay v0.2.2](https://github.com/trmue/relay/releases/tag/v0.2.2).
- Source audit and local-fork distinction: `.planning/phases/04-memory-policies-and-relay-bp/04-RESEARCH.md` and `docs/environment-freeze.txt`.

## Verification

- `git ls-remote https://github.com/trmue/relay.git 'refs/tags/v0.2.2*' | grep -F 14cb31a18f9b9d7d099791b793e35b8a2951f8f3` — passed.
- `.venv/bin/python -m pip index versions relay-bp` — passed; registry metadata was available for review.
- `.venv/bin/python -m pip freeze | rg '^relay'` — confirmed the installed editable `mg551-duke/relay` fork remains separately identified.
- Human approval — passed: `approved author v0.2.2 pin`.

## Decisions Made

- Treat the exact immutable author git pin as the only approved original reference for Relay work in this milestone.
- Require a separate explicit approval before treating either PyPI `relay-bp` or any divergent fork as source evidence.

## Deviations from Plan

None - plan executed exactly as written after the blocking-human checkpoint received the required approval.

## Known Stubs

None.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: external-source-provenance | `.planning/phases/04-memory-policies-and-relay-bp/04-07-SUMMARY.md` | The native build trust boundary remains constrained to the approved immutable author git pin; installation and build are deferred to Plan 04-08. |

## Self-Check: PASSED

The summary exists, the planned source checks passed, and the author pin, excluded package scope, and excluded editable-fork identity are recorded before any native build.
