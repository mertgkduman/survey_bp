---
phase: 01-evidence-registry-and-native-css-baseline
verified: 2026-09-22T04:33:43Z
status: human_needed
score: 28/31 must-haves verified
covered_files:
  - .planning/REQUIREMENTS.md
  - .planning/ROADMAP.md
  - .planning/phases/01-evidence-registry-and-native-css-baseline/01-01-PLAN.md
  - .planning/phases/01-evidence-registry-and-native-css-baseline/01-01-SUMMARY.md
  - .planning/phases/01-evidence-registry-and-native-css-baseline/01-02-PLAN.md
  - .planning/phases/01-evidence-registry-and-native-css-baseline/01-02-SUMMARY.md
  - .planning/phases/01-evidence-registry-and-native-css-baseline/01-03-PLAN.md
  - .planning/phases/01-evidence-registry-and-native-css-baseline/01-03-SUMMARY.md
  - .planning/phases/01-evidence-registry-and-native-css-baseline/01-04-PLAN.md
  - .planning/phases/01-evidence-registry-and-native-css-baseline/01-04-SUMMARY.md
  - .planning/phases/01-evidence-registry-and-native-css-baseline/01-05-PLAN.md
  - .planning/phases/01-evidence-registry-and-native-css-baseline/01-05-SUMMARY.md
  - .planning/phases/01-evidence-registry-and-native-css-baseline/01-06-PLAN.md
  - .planning/phases/01-evidence-registry-and-native-css-baseline/01-06-SUMMARY.md
  - .planning/phases/01-evidence-registry-and-native-css-baseline/01-07-PLAN.md
  - .planning/phases/01-evidence-registry-and-native-css-baseline/01-07-SUMMARY.md
  - .planning/phases/01-evidence-registry-and-native-css-baseline/01-08-PLAN.md
  - .planning/phases/01-evidence-registry-and-native-css-baseline/01-08-SUMMARY.md
  - .planning/phases/01-evidence-registry-and-native-css-baseline/01-09-PLAN.md
  - .planning/phases/01-evidence-registry-and-native-css-baseline/01-09-SUMMARY.md
  - .planning/phases/01-evidence-registry-and-native-css-baseline/01-CONTEXT.md
  - .planning/phases/01-evidence-registry-and-native-css-baseline/01-DISCUSSION-LOG.md
  - .planning/phases/01-evidence-registry-and-native-css-baseline/01-PATTERNS.md
  - .planning/phases/01-evidence-registry-and-native-css-baseline/01-RESEARCH.md
  - .planning/phases/01-evidence-registry-and-native-css-baseline/01-REVIEW-FIX.md
  - .planning/phases/01-evidence-registry-and-native-css-baseline/01-REVIEW.md
  - .planning/phases/01-evidence-registry-and-native-css-baseline/01-SECURITY.md
  - .planning/phases/01-evidence-registry-and-native-css-baseline/01-SOURCE-AUDIT.md
  - .planning/phases/01-evidence-registry-and-native-css-baseline/01-VALIDATION.md
  - .planning/phases/01-evidence-registry-and-native-css-baseline/SKELETON.md
  - data/artifacts/project-three-qubit-css-fixture.json
  - data/artifacts/selected-css.json
  - data/artifacts/selected-css.provenance.json
  - data/evidence/code-inventory.json
  - data/evidence/events.jsonl
  - data/evidence/protocol.json
  - data/evidence/seed-records.json
  - data/manifests/project-three-qubit-fixture.json
  - data/manifests/schema-v1.json
  - data/manifests/selected-css-pilot_adaptation-not_assessed.json
  - data/results/pilot_adaptation-not_assessed/events.jsonl
  - data/results/pilot_adaptation-not_assessed/result.json
  - docs/environment-freeze.txt
  - docs/environment-pins.md
  - docs/phase1-pilot.md
  - docs/phase1-source-decisions.md
  - pyproject.toml
  - src/bp_registry/__init__.py
  - src/bp_registry/artifacts.py
  - src/bp_registry/cli.py
  - src/bp_registry/css.py
  - src/bp_registry/evaluator.py
  - src/bp_registry/evidence.py
  - src/bp_registry/ledger.py
  - src/bp_registry/manifests.py
  - src/bp_registry/reference.py
  - src/bp_registry/runner.py
  - src/bp_registry/sampling.py
  - tests/conftest.py
  - tests/test_css_small.py
  - tests/test_evidence.py
  - tests/test_ledger.py
  - tests/test_manifest.py
  - tests/test_phase1_cli.py
  - tests/test_reference_smoke.py
  - tests/test_sampling.py
  - tests/test_source_artifact.py
  - tools/freeze_css_source.py
covered_digest: "v1:sha256:167d0ad7bb56bb3b6d14979cd09c9905dfc6091111cc8e1ae4a756bb8a825b60"
behavior_unverified: 0
overrides_applied: 0
unverified_prohibitions: 3
re_verification:
  previous_status: gaps_found
  previous_score: 27/31
  gaps_closed:
    - "Unsuccessful-row validation now rejects fabricated native, sample, and selection fields."
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Compare BPGD v2 and Bhatnagar impulse v1 CSS seed records with the pinned primary-source pages."
    expected: "Figure/table anchors, settings, extracted claims, and documented unknowns agree with the sources."
    why_human: "Editorial source interpretation cannot be established by internal code and fixtures."
  - test: "Compare frozen Gross matrix/logical rows with the pinned Bravyi checkout and bposd 2.1 provider bytes."
    expected: "Upstream rows, construction order, logical-provider output, and recorded digests agree."
    why_human: "The upstream checkout/source bytes are not shipped with the phase artifact."
  - test: "Confirm the Plan 02 package legitimacy decision against the original human checkpoint record."
    expected: "The exact pydantic and bposd package/version approval preceded installation."
    why_human: "The codebase retains a summary of approval, not independent human provenance."
  - test: "Review the three flagged scientific-claim prohibitions in Plans 06 and 09."
    expected: "The pilot is never presented as source-faithful or statistically reproduced, and unresolved identities are not promoted to facts."
    why_human: "These judgment-tier prohibitions were explicitly left unverified for end-of-phase review."
---

# Phase 1: Evidence Registry and Native CSS Baseline Verification

**Phase goal:** As a researcher, I want to trace a source-linked paper record to a validated native CSS experiment, so that I can inspect its outcomes and provenance.
**Status:** `human_needed` — 28 of 31 PLAN truths verified, none failed, three require human evidence. This is re-verification after commits `0cdf1a7`, `d0b88e9`, and `2022257`. The fixture, unsuccessful-shot counting, and T-01-21 provenance gaps are closed. The five ROADMAP success criteria were checked independently and map to the PLAN truths below.

## User Flow Coverage

| Step | Expected | Code and observed evidence | Status |
| --- | --- | --- | --- |
| Find paper record | Open a revision-linked result and identify its evidence maturity | `seed-records.json` has Bhatnagar v1 Figure 6 and `mapped_only` paper experiment; `evidence.load_seed_records` and `validate-evidence` pass | VERIFIED |
| Resolve experiment | Bind selected code, logicals, native settings and source identities | Manifest, provenance and preflight bind Gross/BB-144 artifact to Bravyi commit and `ldpc==2.4.1`; public preflight passed | VERIFIED for adaptation; source-paper fidelity needs human review |
| Run reference | Invoke documented local native BP command for 32 identified shots | `runner.run_one` calls `reference.decode(Hz, sZ, prior...)`; checked-in journal has 32 begin and 32 terminal events | VERIFIED for checked-in run |
| Inspect outcomes | Reconstruct counts and provenance for the executed experiment | `verify-run` passed on all 32 completed rows; named tests count interruption/exception and reject fabricated unavailable fields | VERIFIED in code; source interpretation needs human review |

The Gross construction is a verified local code artifact for this **pilot adaptation**. It is only a parameter-level lead for the Bhatnagar impulse Figure 6 experiment. The checked-in run is BP-only, uses 32 fixed shots, and is `not_assessed`. The Bhatnagar paper experiment stays `mapped_only`; the distinct Gross pilot event is `reference_executable`. This is not a source-faithful impulse run or a statistical curve reproduction.

## Roadmap Success Criteria

| # | Contract | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Versioned mapping protocol and honest seed corpus | VERIFIED | `protocol.json`, `seed-records.json`, event replay and taxonomy queries; source statements still await editorial comparison. |
| 2 | Complete versioned manifest and immutable preflight | VERIFIED | Strict `ManifestV1`, `artifacts.load_artifact`, environment/hash checks, and invalid-input tests. |
| 3 | CSS algebra, ordered identity, sampling and four outcomes | VERIFIED | `CssCode.validate`, semantic bytes, `sample_shot`, independent evaluator and constructed-case tests. |
| 4 | Documented pinned native BP pilot with inspectable outcomes | VERIFIED | `verify-run` returned 32 final rows and `not_assessed`; named tests cover interruption/exception denominators and tampering rejection. |
| 5 | Distinct evidence maturity states | VERIFIED | Paper is `mapped_only`; linked pilot is `reference_executable`, both `not_assessed`; validator rejects paper promotion. |

## PLAN Must-Haves: Observable Truths

| ID | Truth condensed from PLAN frontmatter | Status | Evidence or limit |
| --- | --- | --- | --- |
| 01-01.1 | Wave 0 test collection precedes later tests | VERIFIED | Git history places `183ee7c`/`f745d27` Wave 0 tests before later phase implementation commits. |
| 01-01.2 | Actual node package identities recorded and rechecked | VERIFIED | `environment-pins.md`; manifest preflight compares live Python, NumPy, SciPy, ldpc and OpenMP values. |
| 01-02.1 | Human examined suspicious package identities before installation | UNCERTAIN | `01-02-SUMMARY.md` and `environment-pins.md` record a user confirmation, but neither independently proves the human review. Preserve the checkpoint record for human sign-off. |
| 01-03.1 | Three-qubit fixture runs full local tracer path | VERIFIED | Complete fixture manifest and frozen project artifact preflight; documented `bp_registry.runner` command exited 0 and wrote begin/terminal rows. |
| 01-03.2 | Fixture is labelled smoke/adaptation, never a paper result | VERIFIED | Fixture manifest and docs disclose project-owned code, `pilot_adaptation`, and `not_assessed`. |
| 01-03.3 | Begin precedes sampling and terminal links native/evaluation fields | VERIFIED | `runner.run_one` ordering and 64 checked-in events; `test_runner_consumes_the_verified_resolved_experiment` passed. |
| 01-04.1 | Validate CSS dimensions, GF(2) commutation, rank, logical independence/pairing | VERIFIED | `css.py:CssCode.validate`; small-code and selected-artifact tests passed. |
| 01-04.2 | Role/order/bit-sensitive raw and semantic hashes | VERIFIED | `css.semantic_bytes`, `manifests.matrix_hashes`, mutation/golden-byte tests passed. |
| 01-04.3 | X-only and separate X/Z samples with boundaries/rate rejection | VERIFIED | `sampling.sample_shot` and `tests/test_sampling.py` passed. |
| 01-04.4 | Four exclusive outcomes from original constraints and hidden truth | VERIFIED | `evaluator.evaluate_candidate`; constructed exact, degenerate, logical and invalid tests passed. |
| 01-04.5 | Version 1 artifact loader remains explicit | VERIFIED | `artifacts.load_artifact` dispatches v1 and rejects unknown versions without rewriting bytes. |
| 01-05.1 | One durable terminal per begun shot, including failure/interruption | VERIFIED at ledger layer | `LedgerWriter` and `test_active_owner_stays_pending_then_dead_owner_is_repaired_once` passed. Public pilot consumption is a separate failed truth. |
| 01-05.2 | Empty/adjacent/duplicate journal behavior | VERIFIED | `reconcile`, `_states`, and named ledger tests passed. |
| 01-05.3 | Concurrent shot ownership and final-row-only counts | VERIFIED | Owner locks, `summarize`, and active-owner test passed. |
| 01-05.4 | Reconcile only abandoned owners | VERIFIED | Live owner produces no final row; released owner produces one interrupted row in named test. |
| 01-06.1 | BPGD/impulse CSS extraction matches source revisions | UNCERTAIN | Records enumerate anchored figures and tables with unavailable curve data disclosed; independent comparison to pinned paper pages is the declared manual source-fidelity check. |
| 01-06.2 | B1, C2 and Gross remain distinct code leads | VERIFIED | `code-inventory.json` records lifted-product B1, HGP C2 and BB Gross with different identity maturity. |
| 01-06.3 | Search/screen/revision history retains order and empty/adjacent cases | VERIFIED | `EvidenceRegistry` and `test_search_import_preserves_adjacent_raw_hits_and_empty_search` passed. |
| 01-06.4 | Repeated/concurrent events and claim maturity are handled | VERIFIED | Content-addressed append, lock, conflict and taxonomy tests passed. |
| 01-07.1 | Complete versioned manifest fields | VERIFIED | Selected manifest and strict Pydantic models include decoder, hashes, noise, seed, budget, environment, expected-output state and discrepancies. |
| 01-07.2 | Invalid/missing/escaped/changed inputs fail before native call | VERIFIED | `preflight` orders validation before runner sampling; spy and path/hash mutation tests passed. |
| 01-07.3 | Unassessed pilot has reason | VERIFIED | Manifest, CLI and result carry `not_assessed` and reason. |
| 01-07.4 | Saved v1 records remain parseable via version dispatch | VERIFIED | Complete v1 parses; legacy v1 can be inspected through `_parse_for_preflight`, though it cannot execute. |
| 01-08.1 | Inventory distinguishes three candidate families and unresolved identities | VERIFIED | Candidate records and `test_inventory_distinguishes_b1_c2_and_gross_and_records_d04_gate` passed. |
| 01-08.2 | Selection uses source/artifact/logical/algebra evidence | VERIFIED | Freeze recipe checks pinned commit/source construction; artifact rows and GF(2) checks are tested independently. |
| 01-08.3 | Exact upstream Gross source and logical rows are independently confirmed | UNCERTAIN | Provenance has commit, source-file and provider digests, but no pinned checkout/source bytes are shipped to rerun the source probe here; manual source comparison remains required. |
| 01-08.4 | Frozen raw and semantic hashes reflect actual files | VERIFIED | `load_artifact` recomputes both hashes; checked-in artifact and provenance agree. |
| 01-09.1 | Selected BP-only pilot command and honest labels | VERIFIED | `docs/phase1-pilot.md`, `preflight` and `verify-run` commands passed; manifest/result label adaptation and no assessment. |
| 01-09.2 | One manifest resolves 32 linked samples and result | VERIFIED | 32 distinct shot IDs, 64 events, complete result, pinned versions and hashes; `verify-run` passed. |
| 01-09.3 | Every selected outcome, including unsuccessful/interrupted, reaches trustworthy denominators | VERIFIED | Named tests prove interrupted/exception counts; hardened `_validate_pilot_ledger` rejects fabricated candidate, sample, native work and selection fields (T-01-21 closed). |
| 01-09.4 | Pilot maturity does not promote paper experiment | VERIFIED | `load_seed_records` keeps Bhatnagar Figure 6 `mapped_only`, pilot `reference_executable`; promotion test passed. |

**Score:** 28/31 verified; 0 failed; 3 uncertain. The prior fixture, counting, and T-01-21 gaps are now closed. No accepted overrides exist.

### Advisory (New Scope, Unevidenced)

None. The previously blocking T-01-21 finding has a passing tampered-row rejection test and direct rejection spot-check.

## Required Artifacts and Key Links

| Artifacts or link | Existence and substance | Wiring and data flow | Status |
| --- | --- | --- | --- |
| Protocol, seed records, event journal, inventory | Present and populated with source IDs/anchors, status, candidate gaps | `EvidenceRegistry` loads events and claims; `validate-evidence` resolves pilot result | VERIFIED; source accuracy needs human review |
| CSS artifact and source provenance | Present with 72×144 checks and 12 ordered logical pairs | Manifest hashes feed `artifacts.load_artifact` then `CssCode.validate` | VERIFIED locally; external source fidelity uncertain |
| Manifest schema and preflight | Complete v1 model plus exported schema | CLI/pilot call preflight before sampling/native decoder | VERIFIED |
| Native adapter and evaluator | Real `ldpc.BpDecoder` call; four-way independent evaluator | `runner.run_one` passes only `Hz`, syndrome and prior to decoder; hidden truth reaches evaluator | VERIFIED |
| Durable ledger and result | 32 begin/32 completed terminal events; result has 32 shot IDs | CLI reconstructs counts from final rows; named tests count interruption/exception and reject fabricated unsuccessful-row fields | VERIFIED |
| Three-qubit fixture manifest → one-shot runner | Complete manifest and project-owned artifact exist | Documented command preflights, decodes and writes begin/terminal events | VERIFIED |
| Registry paper record → pilot result | Distinct paper/pilot IDs and statuses | `load_seed_records` invokes `verify_run` and checks reciprocal run ID | VERIFIED |

No rendered UI values exist in this CLI phase. The data-flow trace is: pinned seed record → manifest and selected artifact → preflight → deterministic sampler → native candidate → independent evaluator → terminal JSONL → result reconstruction → registry pilot event. Interrupted and exception rows reach the result with explicit unavailable fields that the validator now checks.

## Behavioral Spot-Checks and Test Quality

| Check | Observed result | Status |
| --- | --- | --- |
| `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` | 71 passed in 25.13 s | PASS |
| Documented `bp_registry.runner` fixture command | Exit 0; one begin and one terminal, `outcome=exact`, `pilot_adaptation`, `not_assessed` | PASS; prior gap closed |
| Documented pilot `preflight`, `pilot`, and `verify-run` commands | Each exited 0; 32 final rows, `pilot_adaptation`, `not_assessed` | PASS |
| `test_public_pilot_counts_reconciled_interruption` | 1 passed; 32 denominator, one interrupted and unavailable outcome | PASS; prior count gap closed |
| `test_public_pilot_counts_recorded_native_exception` | 1 passed; 32 denominator, one exception and unavailable outcome | PASS; prior count gap closed |
| In-memory interrupted terminal with fabricated `candidate`, `native_iterations`, `native_edge_updates`, `selection_status` passed to `_validate_pilot_ledger` | Rejected: `pilot unsuccessful terminal lacks explicit unavailable fields` | PASS; T-01-21 closed |

There are no declared `probe-*.sh` scripts. Requirement-linked tests contain no disabled or skipped cases. Small-code algebra and native syndrome tests use value assertions; fixture-source regeneration checks rows and hashes, but paper/source agreement remains a manual editorial check. The interruption test now mutates unavailable native/sample fields and asserts public `verify-run` rejects them. No unreferenced `TBD`, `FIXME`, or `XXX` debt markers were found in phase implementation files. `01-REVIEW.md` listed eight findings; their fixes remain present. The updated `01-SECURITY.md` records T-01-21 closure and 24/24 threats closed; the direct code/test checks above support that finding.

## Requirements Coverage

| IDs | Status | Evidence and limit |
| --- | --- | --- |
| MAP-01, MAP-02, MAP-03 | SATISFIED in code; source-fidelity human review pending | Protocol, event history, pinned seed claims and queryable taxonomy. |
| REG-01, REG-02 | SATISFIED | Strict manifest and preflight reject invalid schema, paths and identities. |
| REG-03 | SATISFIED | Native `ldpc` reference executes from both the complete selected manifest and the restored fixture manifest. |
| REG-04 | SATISFIED | Paper `mapped_only`, pilot `reference_executable`, both `not_assessed`. |
| CSS-01, CSS-02, CSS-03, CSS-04 | SATISFIED locally | GF(2) and hash tests, identified sampling and four-outcome evaluator. |
| LED-01 | SATISFIED in code | Public result counts failures and interruptions and rejects fabricated unavailable native fields on those terminal rows. |

All 12 ROADMAP Phase 1 requirement IDs appear in PLAN frontmatter; none is orphaned. Statistical curve assessment and broader campaigns are explicitly later-phase work. The current 32-shot pilot remains `not_assessed`.

### Decision Coverage

`gsd-tools check decision-coverage-verify` reported 5 of 5 CONTEXT decisions honored, with no unhonored entries. This is advisory and does not resolve the source-fidelity human checks.

## Human Verification Required After Gap Closure

1. Compare BPGD v2 and Bhatnagar impulse v1 seed claims, figure/table anchors, settings and unresolved fields to the pinned primary sources. Record any editorial correction. This resolves 01-06.1 and the mapping-source limitation.
2. Compare the frozen Gross rows and ordered logical-provider output with the pinned Bravyi commit and `bposd==2.1` implementation bytes. The local tests confirm internal algebra, not upstream source identity. This resolves 01-08.3.
3. Confirm the Plan 02 exact-version package legitimacy decision from the original human checkpoint record. The summary reports approval; independent human provenance is not in the codebase.
4. Review the three flagged judgment-tier prohibitions in Plans 06 and 09: do not promote a pilot to paper reproduction, do not call unresolved identities proven absent/source-faithful, and do not infer source fidelity from matching code parameters. Current labels are conservative, but the plan flags require explicit human resolution.

## Gaps Summary

The selected Gross/BB-144 BP-only pilot is a traceable 32-shot **pilot adaptation**, with all checked-in shots completed and its published source experiment still `mapped_only`. All automated gaps are closed. Source-fidelity, the historical package checkpoint, and the three flagged scientific-claim judgments remain for the end-of-phase human checkpoint. No statistical curve reproduction is claimed.

---

_Verified: 2026-09-22T04:33:43Z_
_Verifier: gsd-verifier_
