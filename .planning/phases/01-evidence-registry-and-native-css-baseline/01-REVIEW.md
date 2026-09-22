---
phase: 01-evidence-registry-and-native-css-baseline
reviewed: 2026-09-22T03:18:28Z
depth: standard
files_reviewed: 37
files_reviewed_list:
  - .gitignore
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
  - tests/test_reference_smoke.py
  - tests/test_sampling.py
  - tests/test_source_artifact.py
  - tools/freeze_css_source.py
findings:
  critical: 6
  warning: 2
  info: 0
  total: 8
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-09-22T03:18:28Z
**Depth:** standard
**Files Reviewed:** 37
**Status:** issues_found

## Summary

The CSS algebra, artifact hashes, hidden-truth separation in the native call, and checked-in 32-shot data were reviewed. The declared environment's full suite passed (`58 passed`), as did the published preflight, evidence validation, and run verification commands. Those checks do not cover several bypasses that let the platform create or accept evidence outside its declared provenance and budget contracts.

## Narrative Findings (AI reviewer)

The findings below were established by direct source tracing and targeted temporary-run checks; no submitted implementation files were changed.

## Critical Issues

### CR-01: Fresh legacy manifests can run without immutable preflight

**Classification:** BLOCKER

**File:** `src/bp_registry/manifests.py:257`

**Issue:** `_parse_for_preflight` treats every schema-v1 document lacking the complete-field set as `LegacyManifestV1`, and `preflight` then returns the built-in fixture without artifact, environment, source-artifact, or matrix-hash verification. `run_one` accepts that result and executes it. This contradicts the stated read-only historical replay exception: a new file with arbitrary URI/revision and the minimal shape was accepted and ran as `new-unpinned-legacy` during review.

**Fix:** Restrict legacy support to an immutable allowlist of historical fixture records (including their digest), or make legacy parsing a read-only inspection/replay path that `run_one` refuses. Require `ManifestV1` and successful artifact/environment preflight for every new execution.

### CR-02: The one-shot entry point ignores the manifest shot budget

**Classification:** BLOCKER

**File:** `src/bp_registry/runner.py:71`

**Issue:** `run_one` never checks `shot_id` against `ManifestV1.budget.max_shots`. Although `run_pilot` loops over the budget, the public one-shot CLI path can emit extra final rows under the same pinned run. A review invocation with the 32-shot selected manifest accepted `shot_id=32` and created a final row, outside the declared `0..31` budget.

**Fix:** Before opening the ledger, reject out-of-range complete-manifest IDs:

```python
if isinstance(manifest, ManifestV1) and not 0 <= shot_id < manifest.budget.max_shots:
    raise ValueError("shot_id is outside the manifest budget")
```

Add a regression test through the public `run_one`/CLI path.

### CR-03: `verify-run` accepts tampered or mixed terminal provenance

**Classification:** BLOCKER

**File:** `src/bp_registry/cli.py:31`

**Issue:** `_terminal_rows` returns final events, but `_result_from_final_rows` uses only their IDs, outcomes, termination states, and a nonconvergence flag. `verify_run` reconstructs those counts and compares result JSON without checking any final row's manifest hash, artifact hashes, source identity, decoder configuration, sample identity, or candidate/evaluation linkage. In a copied run, changing a terminal row's `manifest_sha256` to 64 zeroes still made `verify_run` return success for all 32 rows.

**Fix:** Validate every terminal row against the resolved manifest before aggregation: run ID, shot range, manifest/artifact/matrix identities, source and decoder fields, expected status, and deterministic sample identity. Preserve and validate begin-to-terminal lineage as well; a digest or hash chain over canonical events would make post-hoc ledger edits detectable.

### CR-04: Resource provenance always claims one OpenMP thread

**Classification:** BLOCKER

**File:** `src/bp_registry/cli.py:77`

**Issue:** Result generation writes `"omp_num_threads": 1` unconditionally. The pilot path neither sets nor checks `OMP_NUM_THREADS`, and `verify_run` deliberately excludes all `resource_context` fields from comparison at `src/bp_registry/cli.py:129`. Running the command with `OMP_NUM_THREADS=7` produced a result declaring one thread. This makes the documented one-thread execution claim in `docs/phase1-pilot.md:6` unverifiable and can misstate resource-dependent behavior.

**Fix:** Make the thread requirement a manifest/preflight field and reject the pilot unless the effective value is exactly one, or record the actual effective thread value without claiming a pinned one. Validate immutable resource fields in `verify_run`; only invocation-specific values such as elapsed time may be excluded.

### CR-05: Evidence validation permits arbitrary maturity promotion

**Classification:** BLOCKER

**File:** `src/bp_registry/evidence.py:276`

**Issue:** `load_seed_records` only verifies that an execution event references an existing paper-experiment key and that a non-completed event is `mapped_only`. It does not validate the record schema, allowed status transitions, paper-result/revision linkage, result and manifest identities, assessment criteria, or the reciprocal `pilot_run_ids` link. A modified seed record that labelled both the paper experiment and its pilot `statistically_assessed` with an `assessed` status was accepted; `validate-evidence` would report it valid. The registry therefore cannot prevent the source-status overclaim it is intended to guard against.

**Fix:** Define strict models for records and cross-record validation. Require paper experiment work/revision/result anchors to exist, verify all pilot paths and hashes through `verify_run`, allow `reference_executable` only for a completed verified run, and require prespecified values/tolerance/verdict plus an assessment artifact before `statistically_assessed`. Reject promotion of a linked paper experiment by a pilot adaptation.

### CR-06: Ledger source URI and source revision identify different sources

**Classification:** BLOCKER

**File:** `data/manifests/selected-css-pilot_adaptation-not_assessed.json:5`

**Issue:** The manifest's `paper.uri` identifies the Bhatnagar paper, whose source record is revision `v1` (`data/evidence/seed-records.json:22`), while its `paper.revision` is the Bravyi Git commit and its `source_artifact_sha256` is the Bravyi `decoder_setup.py` file hash. `preflight_pilot` treats that revision/hash as the selected implementation provenance (`src/bp_registry/runner.py:37`), then `run_one` writes the paper URI and Git commit together as one `source_uri`/`source_revision` pair (`src/bp_registry/runner.py:77`). The resulting ledger cannot truthfully identify either the paper revision or the source-code revision.

**Fix:** Model paper evidence and implementation provenance as separate required records. Store the Bhatnagar work/revision/anchor independently from the Bravyi repository URI, commit, source path, and source-file hash; preflight and ledger rows must retain and validate both identities separately.

## Warnings

### WR-01: Native adapter silently coerces nonbinary floating inputs

**Classification:** WARNING

**File:** `src/bp_registry/reference.py:30`

**Issue:** `decode` casts matrices and syndromes to `uint8` before checking whether they are binary. Inputs such as `1.5` and `0.5` are silently converted to `1` and `0`, respectively, then decoded. Direct adapter users can therefore obtain a result for invalid observations while the function says it requires binary inputs.

**Fix:** Validate the original arrays' shape, integer/bool dtype, and values before conversion to `uint8`, then validate the native candidate is binary before returning it.

### WR-02: Source evidence appends are not durable after reporting success

**Classification:** WARNING

**File:** `src/bp_registry/evidence.py:199`

**Issue:** `EvidenceRegistry.append_event` flushes the JSONL stream but never calls `os.fsync`. A power loss or process failure after the method returns can lose the screening/search event that callers believe was persisted, despite the class describing append behavior as atomic.

**Fix:** Call `os.fsync(event_file.fileno())` after `flush()` (and consider syncing the containing directory when creating a new journal). Add a fault-injection or mocked-fsync test for the durable write contract.

---

_Reviewed: 2026-09-22T03:18:28Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
