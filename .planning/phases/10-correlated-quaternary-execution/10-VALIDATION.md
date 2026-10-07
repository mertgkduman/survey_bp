---
phase: "10"
slug: "correlated-quaternary-execution"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-10-06"
---

# Phase 10 — Validation Strategy

> Execution feedback contract for the 16 checked plans and 28 tasks. Test files and evidence are created during Phase 10 execution.

## Test Infrastructure

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml` (`testpaths = ["tests"]`, `pythonpath = ["src"]`) |
| Quick run command | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary -x` |
| Full suite command | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` |
| Existing targeted baseline | 24 tests in 1.76 s on 2026-10-06, per `10-RESEARCH.md` |

## Sampling Rate

- **After every task commit:** Run the file-specific test named in that task, plus the closest existing boundary test.
- **After every plan wave:** Run `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary tests/test_sampling.py tests/test_css_small.py tests/test_phase6_public_execution.py`.
- **Before `$gsd-verify-work`:** Run `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` and retain the result.
- **Max feedback latency:** Keep the per-task command under 30 seconds where fixtures permit; split slow native build checks into an explicit bounded integration gate.

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 10-01-01 | 01 | 1 | QBP-01,QBP-02,QBP-03,QBP-04 | — | Task 1: Execute and replay one public non-CSS joint-Pauli shot | planned task check | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_public_execution.py -k 'tracer or installed_cli or non_css or null or empty or one_qubit or encoding or truth_boundary or replay or tamper or assessment' -x` | ❌ W0 | ⬜ pending |
| 10-02-01 | 02 | 2 | QBP-01,QBP-03 | — | Task 1: Freeze Pauli algebra and independent oracle fixtures | planned task check | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_algebra.py -k 'encoding or commutation or symplectic or syndrome or weight or null or empty or one_qubit or invalid' -x` | ❌ W0 | ⬜ pending |
| 10-02-02 | 02 | 2 | QBP-01,QBP-03 | — | Task 2: Compile immutable general and CSS Pauli problems | planned task check | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_algebra.py -k 'problem or css or semantic or immutable or logical or transform or lift or order' -x` | ❌ W0 | ⬜ pending |
| 10-03-01 | 03 | 3 | QBP-03 | — | Task 1: Classify general Pauli candidates independently | planned task check | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_evaluator.py -k 'invalid_syndrome or exact or stabilizer_equivalent or logical_failure or unavailable or exhaustive or css or independent or malformed' -x` | ❌ W0 | ⬜ pending |
| 10-04-01 | 04 | 3 | QBP-02 | — | Task 1: Validate and identify named and explicit joint channels | planned task check | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_sampling.py -k 'channel or depolarizing or endpoint or precision or tolerance or malformed or heterogeneous or physical_rate or smoothing' -x` | ❌ W0 | ⬜ pending |
| 10-04-02 | 04 | 3 | QBP-02 | — | Task 2: Sample one categorical Pauli and prove X/Z correlation | planned task check | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_sampling.py -k 'categorical or all_i or all_x or all_y or all_z or single_y or correlation or covariance or tie or replay or truth_boundary' -x` | ❌ W0 | ⬜ pending |
| 10-05-01 | 05 | 3 | QBP-01 | — | Task 1: Build stable three-LLR numerical primitives and independent oracles | planned task check | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_vector_oracle.py tests/canonical/quaternary/test_kernel.py -k 'numerics or commutation or logsum or boxplus or saturation or nonfinite or tie or exact or vector or normalization' -x` | ❌ W0 | ⬜ pending |
| 10-05-02 | 05 | 3 | QBP-01 | — | Task 2: Execute source-equation scalar LLR-BP4 sessions | planned task check | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_kernel.py tests/canonical/quaternary/test_vector_oracle.py -k 'kernel or check_message or variable_message or posterior or marginal or tree or five_qubit or work or cap or truth_boundary' -x` | ❌ W0 | ⬜ pending |
| 10-06-01 | 06 | 4 | QBP-01,QBP-04 | — | Task 1: Execute flooding and source variable-serial BP4 | planned task check | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_schedules.py -k 'flooding or serial or freshness or snapshot or order or IIIYI or work' -x` | ❌ W0 | ⬜ pending |
| 10-06-02 | 06 | 4 | QBP-01,QBP-04 | — | Task 2: Apply source quaternary normalization and offset | planned task check | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_schedules.py -k 'normalization or offset or transform or parameter or scoped or unsupported' -x` | ❌ W0 | ⬜ pending |
| 10-07-01 | 07 | 5 | QBP-01,QBP-02,QBP-03,QBP-04 | — | Task 1: Resolve closed quaternary compositions before sampling | planned task check | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_public_execution.py -k 'compatibility or composition or source_backed or canonical_adaptation or qbpgd_reserved or component_fidelity or run_fidelity or unsupported or binary or ambp4 or non_css or empty or unknown' -x` | ❌ W0 | ⬜ pending |
| 10-07-02 | 07 | 5 | QBP-01,QBP-02,QBP-03,QBP-04 | — | Task 2: Run full baseline compositions through public evidence and replay | planned task check | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_public_execution.py -k 'full_public or installed_cli or manifest or channel or ledger or work or outcome or replay or tamper or historical or truth_boundary or not_assessed' -x` | ❌ W0 | ⬜ pending |
| 10-08-01 | 08 | 6 | QBP-04 | — | Task 1: Run persistent four-state Q-BPGD rounds | planned task check | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_bpgd.py -k 'reliability or undecimated or fixation or raw or normalized or continuation or run_fidelity or component_identity or tie or early or round_cap or work or replay or truth_boundary' -x` | ❌ W0 | ⬜ pending |
| 10-08-02 | 08 | 6 | QBP-04 | — | Task 2: Expose source components and canonical-adaptation Q-BPGD runs publicly | planned task check | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_bpgd.py tests/canonical/quaternary/test_public_execution.py -k 'qbpgd and (source_component or run_fidelity or depolarizing_adaptation or general_prior_adaptation or installed_cli or ledger or outcome or replay or unverified or unsupported)' -x` | ❌ W0 | ⬜ pending |
| 10-09-01 | 09 | 7 | QBP-01,QBP-04 | — | Task 1: Execute the fixed-alpha MBP4 recurrence | planned task check | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_mbp4.py -k 'fixed_alpha or recurrence or posterior or inhibition or normalized or flooding or serial or invalid or ambp4 or work' -x` | ❌ W0 | ⬜ pending |
| 10-09-02 | 09 | 7 | QBP-01,QBP-04 | — | Task 2: Run and replay fixed-alpha MBP4 publicly | planned task check | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_mbp4.py tests/canonical/quaternary/test_public_execution.py -k 'mbp4 and (public or installed_cli or source or adaptation or replay or tamper or ambp4 or unsupported)' -x` | ❌ W0 | ⬜ pending |
| 10-10-01 | 10 | 3 | QBP-04 | — | Task 1: Construct canonical splitter batches and verify the pinned source fixture | planned task check | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_asced_splitters.py -k 'construct or canonical_adaptation or source_component or source_fixture_verified or h_ext_digest or independent_constructor or independent_source_fixture or exhausted or witness or rank or detectable or partition or css_type or weight or cycle or even_delta or hash or native_fixture or non_css' -x` | ❌ W0 | ⬜ pending |
| 10-10-02 | 10 | 3 | QBP-04 | — | Task 2: Materialize stable batch graphs and transform lineage | planned task check | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_asced_splitters.py -k 'materialize or construction_receipt or source_fixture_receipt or fidelity or reject_raw or reject_exhausted or batch or transform or lineage or stable_order or path_count or cap or tamper' -x` | ❌ W0 | ⬜ pending |
| 10-11-01 | 11 | 4 | QBP-04 | — | Task 1: Qualify and apply generic overcomplete aSCED mappings | planned task check | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_asced_overcomplete.py -k 'source_fixture_binding or exact_h_ext_digest or source_bound_receipt or reject_constructed_batch or matrix_relation or syndrome_mapping or all_virtual_bits or gf2 or rank or row_order or gb46 or toric or immutable or tamper' -x` | ❌ W0 | ⬜ pending |
| 10-12-01 | 12 | 8 | QBP-04 | — | Task 1: Run all CSS aSCED paths and select by the paper rule | planned task check | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_asced_ensemble.py -k 'all_paths or cardinality or lsb or fresh_session or extended_valid or original_valid or minimum_weight or stable_tie or source_component or canonical_adaptation or receipt_pair or pinned_map_mismatch or type_i or work or immutable or exhaustive' -x` | ❌ W0 | ⬜ pending |
| 10-12-02 | 12 | 8 | QBP-04 | — | Task 2: Execute and independently replay aSCED publicly | planned task check | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_asced_ensemble.py tests/canonical/quaternary/test_public_execution.py -k 'asced and (installed_cli or ordinary or overcomplete or preflight or receipt or fidelity or canonical_adaptation or non_css or path_cap or source_component or ledger or replay or tamper)' -x` | ❌ W0 | ⬜ pending |
| 10-13-01 | 13 | 2 | QBP-04 | — | Task 1: Audit the exact native source and preserve discrepancies | planned task check | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_asced_evidence.py -k 'source_identity or exact_commit or digest or discrepancy or pauli_translation or selection or channel or instrumentation or no_install' -x` | ❌ W0 | ⬜ pending |
| 10-13-02 | 13 | 2 | QBP-04 | — | Task 2: Generate a digest-bound isolated build proposal | planned task check | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_asced_evidence.py -k 'proposal or package_lock or registry or hash or overlay or cmake_identity or cmake_artifact or allowed_executable or driver or isolation or algorithm_guard or pending_human or build_refusal' -x` | ❌ W0 | ⬜ pending |
| 10-14-01 | 14 | 3 | QBP-04 | — | Task 1: Approve the exact native aSCED isolated-build proposal | planned task check | `OMP_NUM_THREADS=1 .venv/bin/python scripts/qualify_phase10_native_asced.py verify-proposal --spec data/native/phase10-asced-source-spec.json` | ❌ W0 | ⬜ pending |
| 10-15-01 | 15 | 4 | QBP-04 | — | Task 1: Build the approved exact native source in isolation | planned task check | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_asced_evidence.py -k 'approval or isolation or source_digest or algorithm_guard or package_hash or cmake_identity or allowed_executable or build_receipt or import_probe or api_probe or qualified_failure or primary_environment' -x && OMP_NUM_THREADS=1 .venv/bin/python scripts/qualify_phase10_native_asced.py build --spec data/native/phase10-asced-source-spec.json --approval-summary .planning/phases/10-correlated-quaternary-execution/10-14-SUMMARY.md --receipt data/native/phase10-asced-build-receipt.json && OMP_NUM_THREADS=1 .venv/bin/python scripts/qualify_phase10_native_asced.py verify-receipt --spec data/native/phase10-asced-source-spec.json --receipt data/native/phase10-asced-build-receipt.json --require-terminal build_success` | ❌ W0 | ⬜ pending |
| 10-15-02 | 15 | 4 | QBP-04 | — | Task 2: Invoke the bounded native reference to a required successful terminal | planned task check | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_asced_evidence.py -k 'native_run or exact_terminal or equal_proportion or pauli_translation or aggregate or missingness or unavailable or not_assessed or receipt_chain' -x && OMP_NUM_THREADS=1 .venv/bin/python scripts/qualify_phase10_native_asced.py run --spec data/native/phase10-asced-source-spec.json --build-receipt data/native/phase10-asced-build-receipt.json --output-receipt data/native/phase10-asced-run-receipt.json --code GB46 --physical-error-rate 0.05 --workers 1 --max-trials 10000 --target-errors 10 && OMP_NUM_THREADS=1 .venv/bin/python scripts/qualify_phase10_native_asced.py verify-receipt --spec data/native/phase10-asced-source-spec.json --receipt data/native/phase10-asced-run-receipt.json --require-terminal native_success` | ❌ W0 | ⬜ pending |
| 10-16-01 | 16 | 9 | QBP-01,QBP-02,QBP-03,QBP-04 | — | Task 1: Freeze the 256-shot matched canonical design and required native terminal | planned task check | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q tests/canonical/quaternary/test_asced_evidence.py -k 'design or gb46 or p_005 or seed_10 or shot_ids_0_255 or source_fixture_digest or overcomplete_map_digest or exact_receipt_pair or canonical_adaptation or source_component or shared_sample or arm_identity or four_paths or iteration_cap or native_success_required or native_failure_blocks or not_assessed or phase11_boundary' -x` | ❌ W0 | ⬜ pending |
| 10-16-02 | 16 | 9 | QBP-01,QBP-02,QBP-03,QBP-04 | — | Task 2: Run once and verify every canonical path and native fact | planned task check | `OMP_NUM_THREADS=1 .venv/bin/python scripts/run_phase10_quaternary_gate.py run --study data/studies/phase10-quaternary-b1-gate.json --native-receipt data/native/phase10-asced-run-receipt.json --output data/results/phase10-quaternary-b1-gate && OMP_NUM_THREADS=1 .venv/bin/python scripts/run_phase10_quaternary_gate.py verify --study data/studies/phase10-quaternary-b1-gate.json --native-receipt data/native/phase10-asced-run-receipt.json --output data/results/phase10-quaternary-b1-gate` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky. Task IDs and commands reflect the final checked plans; executable artifacts are created during Phase 10.*

## Wave 0 Requirements

- [ ] Create the `tests/canonical/quaternary/` package and files listed in the verification map, plus `test_schedules.py` and `conftest.py`.
- [ ] Establish hand algebra and exact-enumeration Pauli oracles independent of the production kernel.
- [ ] Pin source fixtures for the five-qubit `IIIYI` case and aSCED `H/H0/M` artifacts before implementation tests rely on them.
- [ ] Include manifest/ledger replay and tamper tests in `test_public_execution.py`; ensure each command selects at least one test once its file exists.
- [ ] Use the installed pytest environment; no framework installation is required.

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Native aSCED source/build license and interface qualification | D-12 | Upstream repository packaging and native build may require human source interpretation | Inspect pinned checkout, build receipt, license evidence, and documented source divergences before labeling native output qualified. |

## Validation Sign-Off

- [ ] Every task has a runnable `<automated>` command or a Wave 0 dependency.
- [ ] No three consecutive tasks lack automated verification.
- [ ] Wave 0 resolves all test-file references.
- [ ] No watch-mode flags are used.
- [ ] Per-task feedback is under the stated budget or an explicit exception is recorded.
- [ ] Set `nyquist_compliant: true` only after validation against the final plans and executed evidence.

**Approval:** pending
