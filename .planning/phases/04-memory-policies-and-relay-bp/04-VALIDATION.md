---
phase: "04"
slug: "memory-policies-and-relay-bp"
status: draft
nyquist_compliant: false
wave_0_complete: false
created: "2026-09-24"
---

# Phase 04 — Validation Strategy

> Execution feedback contract derived from `04-RESEARCH.md`. Plan and task IDs will be filled after planning; test targets below are Wave 0 dependencies until created.

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | pytest 9.0.3 |
| Config file | `pyproject.toml` |
| Quick run command | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q -x tests/canonical/test_memory_policies.py tests/canonical/test_relay.py` after Wave 0 |
| Full suite command | `OMP_NUM_THREADS=1 .venv/bin/python -m pytest -q` |
| Estimated runtime | Measure and record during Wave 0; do not assume an HPC node is representative of later allocations. |

## Sampling Rate

- After each task commit, run the focused new test and its nearest existing contract, schedule, or manifest test.
- After every plan wave, run the configured full suite.
- Before `$gsd-verify-work`, require the full suite and bounded native differential fixtures to pass.
- Measure feedback latency in Wave 0 and record it in the execution summary.

## Per-Requirement Verification Map

| Requirement | Planned behavior | Test type | Automated target | File exists | Status |
|---|---|---|---|---|---|
| MEM-01 | Damping equation, endpoints, state reset, local and source boundaries | unit and property | `tests/canonical/test_memory_policies.py` | No — Wave 0 | Pending |
| MEM-02 | Field and delta mixing operands, order, and distinguishing fixture | unit and golden | `tests/canonical/test_memory_policies.py` | No — Wave 0 | Pending |
| MEM-03 | Momentum recurrence, zero initial velocity, original C2V subtraction, reset | unit and differential | `tests/canonical/test_memory_policies.py` | No — Wave 0 | Pending |
| MEM-04 | Affine prior memory lifetime and EWAInit/Relay reparameterization | unit and metamorphic | `tests/canonical/test_memory_policies.py` | No — Wave 0 | Pending |
| MEM-05 | Seeded per-variable draws, refresh, history, RNG separation, repeated binding order | unit and property | `tests/canonical/test_memory_composition.py` | No — Wave 0 | Pending |
| MOD-01 | Leg transfer, reset, stopping, candidate selection, and leaf work | integration | `tests/canonical/test_relay.py` | No — Wave 0 | Pending |
| MOD-01 | Author v0.2.2 translation and instrumentation equivalence | differential | `tests/canonical/test_relay_differential.py` | No — Wave 0 | Pending |
| MOD-01 | Ledger reconstruction, identities, trace bounds, and notebook reuse | evidence | `tests/canonical/test_phase4_evidence.py` | No — Wave 0 | Pending |

## Wave 0 Requirements

- [ ] Create `tests/canonical/test_memory_policies.py` for exact source equations and endpoints.
- [ ] Create `tests/canonical/test_memory_composition.py` for ordered and repeated bindings, seeded draws, schedule compatibility, and atomic rollback.
- [ ] Create `tests/canonical/test_relay.py` for real posterior transfer, leg lifecycle, scoring, lineage, and budgets.
- [ ] Create `tests/canonical/test_relay_differential.py` for the pinned original reference and behavior-neutral observer patch.
- [ ] Create `tests/canonical/test_phase4_evidence.py` for B1 identity gating, ledger reconstruction, trace caps, and notebook stage reuse.
- [ ] Establish the isolated author v0.2.2 reference, reconcile B1's semantic digest, and discover the actual compute allocation before locking pilot caps.
- [ ] Benchmark a bounded 32-shot representative sample and freeze finite calibration/evaluation budgets before collecting assessment results.

## Mandatory Invariants

1. Exact equation fixtures distinguish damping, PDBP, PD′BP, momentum, and affine prior memory; EWAInit and Relay memory agree under the documented reparameterization.
2. Each binding owns its history; reversing ordered repeated bindings changes a distinguishing result or has an explicit commutativity proof for that fixture.
3. Budget rejection leaves message state, history, RNG state, and schedule cursor unchanged.
4. Relay legs inherit only the predecessor's finite real posterior LLR vector; message and leg-local state reset. Candidate selection is invariant to hidden truth.
5. Every leg's leaf work reconstructs from the ledger. Native fields unavailable from the pinned author code remain explicitly unavailable.
6. V2/V3 persisted manifests preserve their semantics; new executable policy admission uses a versioned contract.
7. All BB-144, B1, and HGP pilots pass exact matrix/logical identity checks before use; B1's current digest conflict blocks its pilot until resolved.
8. Notebook stages reuse artifacts only when all declared manifest, source, policy, code, environment, sample, and stage identities match; mismatches preserve old evidence.

## Manual-Only Verifications

| Behavior | Requirement | Why manual | Instructions |
|---|---|---|---|
| Native package legitimacy and pin | MOD-01 | Local and repository provenance require a reviewed source identity | Check author tag and commit, compare the local fork separately, record the isolated build digest and any patch diff. |
| Compute allocation and finite pilot caps | MOD-01 | Entitlement is deployment-specific | Record SLURM allocation and concurrency, inspect bounded benchmark, then freeze configuration, shot, work, and runtime caps before calibration. |

## Validation Sign-Off

- [ ] Every task has an automated verification command or a named Wave 0 dependency.
- [ ] No three consecutive tasks lack automated verification.
- [ ] Wave 0 creates all named test targets.
- [ ] The full suite, native differential fixtures, and bounded notebook mode pass.
- [ ] Set `nyquist_compliant: true` only after the implemented tests cover every requirement.

**Approval:** pending
