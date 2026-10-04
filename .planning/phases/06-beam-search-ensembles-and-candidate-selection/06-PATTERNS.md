# Phase 6: Beam Search, Ensembles, and Candidate Selection - Pattern Map

**Mapped:** 2026-10-04  
**Scope source:** `ROADMAP.md` Phase 6 and `REQUIREMENTS.md` MOD-04, INT-05, CAN-01, CAN-02. Phase 6 has no `CONTEXT.md` or `RESEARCH.md` yet.  
**Files analyzed:** 16 planned create/modify surfaces  
**Analogs found:** 13 / 16

## File Classification

| New/modified file | Role | Data flow | Closest tracked analog | Match quality |
|---|---|---|---|---|
| `src/bp_registry/canonical/beam_search.py` | controller/model | batch transform | `canonical/impulse.py` | role and flow match |
| `src/bp_registry/canonical/ensembles.py` | controller/model | batch transform | `canonical/relay.py` | role and flow match |
| `src/bp_registry/canonical/candidate_selection.py` | utility/model | transform | `canonical/lineage.py` | partial: frozen selection already exists |
| `src/bp_registry/canonical/intervention_session.py` | service | stateful batch transform | itself and `canonical/impulse.py` | extension match |
| `src/bp_registry/canonical/lineage.py` | model | append-only event graph | itself | extension match |
| `src/bp_registry/canonical/budgets.py` | model/service | event-driven accounting | itself and `canonical/relay.py` | extension match |
| `src/bp_registry/canonical/contracts.py` | config/model | request validation | `CanonicalManifestV6/V7` | extension match |
| `src/bp_registry/manifests.py` | config/model | file-I/O validation | `CanonicalExperimentV5/V6` | extension match |
| `src/bp_registry/canonical/execution.py` | controller | request-response to ledger | `_run_phase5_structural_shot` | exact dispatch/evidence shape |
| `src/bp_registry/canonical/verification.py` | service | batch replay/validation | `_reconstruct_phase5` | exact replay shape |
| `src/bp_registry/canonical/__init__.py` | package export | import API | itself | extension match |
| `tests/canonical/test_beam_search.py` | test | deterministic transform | `test_impulse.py` | role and flow match |
| `tests/canonical/test_ensembles.py` | test | deterministic transform | `test_relay.py` | role and flow match |
| `tests/canonical/test_candidate_selection.py` | test | deterministic transform | `test_restart_execution.py` | partial: candidate selection and work |
| `tests/test_phase6_public_execution.py` | test | public manifest/ledger/replay | `test_phase5_public_execution.py` | exact public-surface match |
| `data/manifests/phase6-*.json`, `docs/evidence/phase6-*.json` | config/evidence | file-I/O | Phase 5 manifests/evidence | extension match |

## Pattern Assignments

### `canonical/beam_search.py` — bounded beam controller and source adaptation

**Analog:** `src/bp_registry/canonical/impulse.py` (tracked), especially its `ImpulseSpec` validation and `ImpulseController.run` attempt loop.

Use one immutable `OriginalProblem`; create only certified working views or independent branch sessions. Reserve the full leaf work before each branch reset/expansion, retain an `ImpulseAttempt`-style row for every admitted, invalid, pruned, denied, and cap-hit child, and lift/validate before candidate selection.

```python
# src/bp_registry/canonical/impulse.py: its controller loop pattern
for attempt_index, target_index in enumerate(order[:self.spec.attempt_cap]):
    # reserve transformation/action work before constructing the child
    # construct child, run bounded fresh BP, lift to original coordinates
    # append a complete attempt row regardless of eligibility
    if row.eligible:
        selected = row
        break
```

`BeamSearch` needs the same deterministic declared order, but it must persist the beam depth, parent branch lineage, mask/branch decision, decoder-visible ranking score, width admission/pruning reason, inherited-state declaration, and child work leaves. Do not use completion order for tie resolution. The Phase 5 impulse controller already demonstrates a source-specific fresh-attempt controller; a beam is an ordered set of such children, not a retry loop.

**Integration seam:** use `BpSession.reset_fresh` in `canonical/intervention_session.py:337-386` for independent children. Its `preserve` contract accepts only the complete compatible BP-state tuple and rejects graph/syndrome/prior/owner mismatches, so Phase 6 must declare independent versus inherited state explicitly and test both paths.

### `canonical/ensembles.py` — generic member execution and work aggregation

**Analog:** `src/bp_registry/canonical/relay.py` (tracked), in particular `RelayMemberSpec`, `RelayCandidateScore`, and `RelayController.select_candidate`.

```python
# src/bp_registry/canonical/relay.py:377-380
@staticmethod
def select_candidate(scores: Iterable[RelayCandidateScore]) -> RelayCandidateScore | None:
    candidates = tuple(scores)
    return None if not candidates else min(candidates, key=lambda score: score.selection_key)
```

Copy this explicit score object and stable tuple key approach. Phase 6 should name the member identity, parent identity, state mode (`independent` or a precisely allowed inherited state), member result, eligibility, score fields, and tie key. Preserve rejected members and do not select from an unrecorded list.

For work, follow `RelayWorkAccounting` in `canonical/budgets.py:137-193`: idempotent leaves have semantic conflict detection and total work is the sum of unique leaves. Generalize the leaf kind only when its meaning changes; otherwise retain the existing `branch_expansions`, `branch_prunes`, BP, candidate, and validation counters in `WorkVector` rather than creating a universal-cost number.

### `canonical/candidate_selection.py` — list scoring, eligibility, and voting

**Analog:** `src/bp_registry/canonical/lineage.py:183-274` (tracked).

```python
# src/bp_registry/canonical/lineage.py:263-274
if not candidates or selected_id not in {item.lineage_id for item in candidates}:
    raise ValueError("frozen selection must name one known candidate")
if tuple(sorted(candidates, key=lambda item: (item.local_ordinal, item.lineage_id.value))) != candidates:
    raise ValueError("candidate selection must use declared stable order")
...
node = graph.append_node("selection", {...}, parent=selected_id, relation="select")
```

Build Phase 6 selection records on this representation. A candidate must retain its parent/origin, payload digest, finite score or explicit absent score, eligibility/validation facts, rejection reason, stable ordinal, and selected/unselected status. The selector receives no hidden truth. It freezes exactly one decoder-visible choice before `execution.py` calls the evaluator.

For voting, define a separate typed vote record: voting object (original-space correction, logical class, or other declared object), electorate eligibility, per-member ballot, aggregation, tie rule, and post-vote candidate. The voted correction still requires original-syndrome validation; a vote count is never validity evidence. There is no exact existing voting implementation, so use `CandidateRecord` + `SelectionRecord` rather than inventing an unlinked result type.

### `canonical/intervention_session.py` and `canonical/lineage.py` — branch state and ancestry

**Analogs:** `intervention_session.py:337-386`; `lineage.py:19-40,100-146` (both tracked).

```python
# src/bp_registry/canonical/intervention_session.py:347-355
preserve_set = frozenset(preserve)
complete = frozenset({"v2c", "c2v", "posterior", "candidate"})
if preserve_set and (... incompatible graph/syndrome/rate/owner ...):
    raise ValueError("incompatible graph, coordinate, prior, dtype, or owner for preserved BP state")
```

```python
# src/bp_registry/canonical/lineage.py:28-39
"member": frozenset({"working", "attempt"}),
"branch": frozenset({"member", "leg", "branch", "attempt"}),
"candidate": frozenset({"working", "attempt", "branch", "leg"}),
```

The typed graph already admits member and branch nodes. Phase 6 should append a content-addressed branch node before child work and use it as the candidate parent. Include declared depth, parent/child ordinal, decision/mask digest, state mode, and finite decoder-visible rank facts in node content. Never encode worker, timing, or truth outcome in IDs.

### `canonical/contracts.py` and `manifests.py` — strict versioned public admission

**Analogs:** `src/bp_registry/canonical/contracts.py:996-1063` and `src/bp_registry/manifests.py:441-546` (tracked).

```python
# contracts.py:1008-1019
if (self.policies.schedule.kind != "flooding"
        or self.policies.intervention.kind != self.intervention.kind
        or self.policies.state_memory.kind != "identity"):
    raise ValueError("...")
```

```python
# manifests.py:431-438
names = set(WorkVector.zero().as_evidence(structural_event_version=4))
if set(self.work_caps) != names ...:
    raise ValueError("Phase 5 work caps must name every bounded WorkVector resource")
```

Add a new strict schema version instead of loosening V6/V7. The Phase 6 contract should close the BeamSearch and ensemble registries, require finite width/depth/member/action caps and full work-cap coverage, bind source revision/reference status, specify mask/branch and ranking/pruning semantics, and make voting optional and exactly typed. Preflight must reject unsupported kernel/schedule/state-sharing/operator combinations before artifact loading or sampling. Preserve V2–V7 parsing exactly.

### `canonical/execution.py` and `canonical/verification.py` — public structural evidence and replay

**Analogs:** `_run_phase5_structural_shot` in `execution.py:915-1036`, `phase5_attempt_events` in `phase5.py:244-300`, and Phase 5 reconstruction in `verification.py:1069-1119` (all tracked).

```python
# execution.py:968-1017, abbreviated
outcome = execute_phase5_controller(...)
for kind, payload in phase5_attempt_events(spec, outcome):
    ledger.event(..., kind=kind, data={"identity": identity_data, "payload": payload})
ledger.event(..., kind="work", data={..., "payload": phase5_work_evidence(outcome)})
```

```python
# verification.py:1081-1117, abbreviated
candidate = ... outcome.candidate
if candidate is not None and not original_syndrome_valid(candidate):
    raise CanonicalStructuralVerificationError(...)
expected.extend(("branch", row) for row in outcome.branches)
expected.extend(phase5_attempt_events(spec, outcome))
... # selection, work, then truth-aware evaluation
```

Create a Phase 6 projection/event helper analogous to `Phase5Outcome`, preserving header, branch/member rows, candidate rows, selection/vote records, unique leaves, and terminal state. Route only the new manifest through a new structural runner. The verifier must regenerate the full deterministic branch tree from public observation and decoder-only seeds, compare exact events/lineage/leaf work, validate the selected original-space correction, then evaluate hidden truth after selection. Retain runtime as a measurement excluded from deterministic timing equality, following the existing Phase 5 terminal exception.

### Tests and fixtures

**Beam tests analog:** `tests/canonical/test_impulse.py`; **ensemble tests analog:** `tests/canonical/test_relay.py`; **state/rejection/replay analog:** `tests/canonical/test_restart_execution.py`; **public evidence analog:** `tests/test_phase5_public_execution.py`. All are tracked.

Follow the small, hand-checkable binary fixtures in `test_impulse.py`: assert original input immutability, deterministic declared order, fresh versus explicitly preserved state, lift/original validity, cap denial before mutation, and replay rejection after one semantic field is changed.

Follow `test_relay.py` for stable scoring and selection ties. Add explicit tests that changing worker completion order cannot change branch survival, list selection, or voting. Test unique leaf accounting for pruned as well as accepted branches, and assert parent totals equal unique child leaves without double count. Public tests should preflight valid/invalid manifests, run a single matched fixture through CLI/public structural execution, replay it, and reject tampered ranking, origin, eligibility, vote, branch, selected candidate, or work evidence.

## Shared Patterns

### Hidden-truth boundary

**Sources:** `canonical/execution.py:571-633`, `canonical/verification.py:1081-1087`.

Controllers, branch ranks, pruning, list selection, and votes operate only on decoder-visible data. The first logical-outcome evaluation follows frozen selection, and Phase 6 must continue to validate the selected correction against the original syndrome before that evaluation.

### Atomic state and work transactions

**Sources:** `canonical/budgets.py:60-120`, `canonical/intervention_session.py:251-315`, `canonical/budgets.py:137-193`.

Reserve a full `WorkVector` with a stable leaf ID, compute private state, roll back on exception, then commit once. Every branch expansion, prune/rank action, BP child attempt, candidate construction, and original validation needs visible leaf attribution. A denied reservation must leave parent and child state unchanged.

### Deterministic identity and ordering

**Sources:** `canonical/lineage.py:95-146`, `canonical/problems.py:101-103`, `canonical/lineage.py:263-274`.

Content-address identities use semantic ancestry and canonical JSON. Stable candidate order is the declared local ordinal plus lineage ID; ordering cannot depend on process count, timing, or arrival order. Derive ensemble member and beam branch IDs the same way.

### Versioned evidence and replay

**Sources:** `canonical/contracts.py:1045-1063`, `manifests.py:639-664`, `canonical/verification.py:1118-1144`.

Add a closed new schema/ledger path. Keep historical schema versions and event semantics unchanged. Reconstruct every deterministic Phase 6 evidence claim, while checking timing metadata for well-formedness rather than exact elapsed values.

## No Analog Found

| File/concern | Role | Data flow | Reason |
|---|---|---|---|
| Beam-specific masked BP and source-reference adapter | controller/adapter | batch transform | No BeamSearch implementation exists in the tracked codebase; `impulse.py` supplies only bounded independent shortening branches. |
| General ensemble voting rule | utility/model | transform | Relay selects one candidate by score; it has no ballot/object/electorate abstraction. |
| Pinned BeamSearch reference integration | adapter | request-response/file-I/O | No tracked native adapter exists; source/repository identity and license must be qualified before implementation. |

## Metadata

**Analog search scope:** `src/bp_registry/canonical`, `src/bp_registry/manifests.py`, `tests/canonical`, `tests/test_phase5_public_execution.py`, Phase 5 planning artifacts, requirements, and roadmap.  
**Tracked-source gate:** All named code/test analogs were verified with `git ls-files`.  
**Files scanned:** 24 tracked implementation/test files plus Phase 5 planning artifacts.  
**Pattern extraction date:** 2026-10-04
