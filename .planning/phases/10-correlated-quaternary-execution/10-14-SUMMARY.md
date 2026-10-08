---
phase: 10-correlated-quaternary-execution
plan: "14"
subsystem: native-aSCED-qualification
tags: [asced, native-reference, human-approval, provenance]
requires:
  - phase: 10-13
    provides: Digest-bound inert native source and build proposal
provides:
  - User approval of the exact isolated native build and execution proposal
affects: [phase-10-plan-15, phase-10-plan-16]
actuals:
  tokens: 1100
  tasks: 1
  commits: 1
tech-stack:
  added: []
  patterns: [digest-bound-human-decision]
key-files:
  created: [.planning/phases/10-correlated-quaternary-execution/10-14-SUMMARY.md]
  modified: [.planning/phases/10-correlated-quaternary-execution/10-EXECUTION-DECISIONS.md]
key-decisions:
  - "Accept the user's attestation of permission from the collaborator-author for this bounded isolated build and run."
  - "Record verbal permission accurately; do not infer or claim a repository license or written grant."
requirements-completed: [QBP-04]
coverage:
  - id: D1
    description: Human decision tied to the exact native proposal digest and bounded scope.
    requirement: QBP-04
    verification:
      - kind: manual_procedural
        ref: "User approval and permission attestation on 2026-10-07"
        status: pass
    human_judgment: true
    rationale: "This is the user's explicit human decision on the reviewed proposal and author permission."
metrics:
  duration: 0m
  completed: 2026-10-07
status: complete
---

# Phase 10 Plan 14: Native aSCED Human Decision

**Decision: approved for the exact isolated executable-reference build and bounded run.**

`source_spec_sha256`: `55359962431c055cf971171f81d75997282beb29e8928a8d82e023fbb6c1f24e`

The user's exact digest approval signal was `approved phase10 native spec 55359962431c055cf971171f81d75997282beb29e8928a8d82e023fbb6c1f24e`. On 2026-10-07, the user clarified: “Permission is given, author is a collaborator, we are in verbal communication, on top of all these, the repo is an open-source research project, this scrutiny is overblown.” This is a user-attested grant of **verbal permission from the collaborator-author** for this isolated build and execution. No written permission text or license file was supplied or located. The user's decision accepts verbal author permission for this bounded research execution; this summary does not assign a formal license or assert redistribution rights. This is a documented deviation from Plan 10-14's request for written permission.

## Exact approved inputs

- Source: `kit-cel/quantum_asced`, commit `816772071486615dfc7d71d1e15df597edc58a26`, tree `a87af78b8f014e25f9659d0926ef5f9f5452882e`; algorithm-file hashes are those in the digest-bound source spec.
- Official PyPI wheel identities and SHA-256 digests:

| Project | Version | Wheel SHA-256 |
| --- | --- | --- |
| numpy | 2.5.3 | `b7e18c623bb5c95acb3b3328861272816ba199fb531921c5d6d0b675f1fde9e3` |
| galois | 0.4.11 | `d2e12a2b7fd44b108cc15d7de27dabcb8a98a556ea2c69c94fe695139629d9aa` |
| matplotlib | 3.11.2 | `df4f7784aca81a94f254c0a2767d592ee25f407e488f5fa7203e51093fb6ca27` |
| scikit-build-core | 1.1.1 | `6f6d6cf600e2e9639fd258ecd11cfc19bd189354b968916a519c6793e7e26237` |
| pybind11 | 3.1.0 | `b8488090f8acffbcb6b5d6a85571a6827a0a2981ffb75e5a0b27b87c4a6b7dd0` |

- Build-only pybind11 overlay: official `pybind/pybind11` tag `v3.1.0`, commit `97bf890db679505a14dfe547a5e77bb2bd05dc90`, archive SHA-256 `ef712655692a2e9bf7bb7874c022564a45f91d847ddee987e720cd9e28849665`, mounted at `/tmp/phase10-asced-native/source/quantum_asced/pybind11`.
- CMake: official Kitware `4.2.0` `linux-x86_64` archive `https://cmake.org/files/v4.2/cmake-4.2.0-linux-x86_64.tar.gz`, SHA-256 `bbcebd4c433eab3af03a8c80bb5d84e8dfc3ff8a4ab9d01547b21240c23f7c2c`. Acquire only to `/tmp/phase10-asced-native/downloads`, unpack under `/tmp/phase10-asced-native/tools`, and execute only `/tmp/phase10-asced-native/tools/cmake-4.2.0-linux-x86_64/bin/cmake`, whose expected SHA-256 is `1b8bffb9e82925587e70a6211d5e539e06133cae978610917e1ed90e111bd208`. No ambient `PATH` fallback.
- Disposable root: `/tmp/phase10-asced-native`; source checkout, out-of-tree driver, build directory, install prefix and receipts have the exact paths in the approved spec. The driver may correct demo/artifact paths and expose an aggregate entry point only. Algorithm source, Pauli semantics, candidate selection and channel code may not change. Source algorithm digests must match before and after build.
- Native run bounds: one worker, at most 10,000 trials, target 10 errors, equal-proportion depolarizing channel only. Native results remain a distinct executable reference with unavailable shot matching and counters stated explicitly. This approval does not confer source-fidelity status on the deterministic canonical splitter adaptation or allow native code to replace the canonical engine.

## Verification and handoff

The source spec file's SHA-256 matched `source_spec_sha256`; its `verify-proposal` check returned `verified_pending_human` before this decision. The spec bytes remain unchanged. Plan 10-15 may consume this summary as the approval record and must enforce exact input identities and isolation at build time.
