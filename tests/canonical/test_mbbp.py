"""MBBP-LD algebra and independent-member controller fixtures."""

from __future__ import annotations

from dataclasses import replace
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

from bp_registry.canonical.problems import OriginalProblem


H = np.asarray([[1, 1, 0], [0, 1, 1]], dtype=np.uint8)
S = np.asarray([1, 0], dtype=np.uint8)


def test_mbbp_module_exports_augmented_basis_seam() -> None:
    assert importlib.util.find_spec("bp_registry.canonical.mbbp") is not None


def _original() -> OriginalProblem:
    return OriginalProblem("original-mbbp-fixture", np.zeros((1, 3), dtype=np.uint8), H, S)


def _basis(member_id: str, ordinal: int, transforms: tuple[tuple[int, ...], ...] = ((1, 1),)):
    from bp_registry.canonical.mbbp import MbbpBasis

    return MbbpBasis(
        member_id=member_id,
        local_ordinal=ordinal,
        partition_identity="declared-fixture-partition",
        permutation_identity="declared-fixture-permutation",
        redundant_transforms=transforms,
    )


def test_augmented_basis_derives_ordered_rows_and_matching_syndrome_without_mutation() -> None:
    original = _original()
    matrix_before, syndrome_before = original.hz.copy(), original.syndrome.copy()
    system = _basis("basis-a", 0).augment(original)

    assert system.check_matrix.tolist() == [[1, 1, 0], [0, 1, 1], [1, 0, 1]]
    assert system.syndrome.tolist() == [1, 0, 1]
    assert system.source_status == "canonical_adaptation"
    assert system.content_identity.startswith("basis-")
    np.testing.assert_array_equal(original.hz, matrix_before)
    np.testing.assert_array_equal(original.syndrome, syndrome_before)


def test_augmented_system_satisfies_an_independent_exhaustive_gf2_oracle() -> None:
    original = _original()
    system = _basis("basis-a", 0).augment(original)
    for value in range(1 << original.hz.shape[1]):
        error = np.asarray([(value >> bit) & 1 for bit in range(original.hz.shape[1])], dtype=np.uint8)
        if np.array_equal((original.hz @ error) % 2, original.syndrome):
            np.testing.assert_array_equal((system.check_matrix @ error) % 2, system.syndrome)


@pytest.mark.parametrize("transforms", [((1, 2),), ((1,),), ((0, 0),)])
def test_malformed_basis_transforms_fail_before_member_bp(transforms) -> None:
    with pytest.raises(ValueError):
        _basis("basis-a", 0, transforms).augment(_original())


def test_duplicate_member_identity_and_unordered_descriptor_are_rejected() -> None:
    from bp_registry.canonical.mbbp import MbbpSpec

    with pytest.raises(ValueError, match="unique"):
        MbbpSpec(bases=(_basis("same", 0), _basis("same", 1)), max_iterations=2)
    with pytest.raises(ValueError, match="ordered"):
        MbbpSpec(bases=(_basis("later", 1), _basis("earlier", 0)), max_iterations=2)


def test_mbbp_exports_independent_member_controller() -> None:
    import bp_registry.canonical.mbbp as mbbp

    assert hasattr(mbbp, "MbbpController")


def test_independent_serial_normalized_members_aggregate_admitted_frequency_and_work() -> None:
    from bp_registry.canonical.mbbp import MbbpController, MbbpSpec

    spec = MbbpSpec(bases=(_basis("basis-a", 0), _basis("basis-b", 1, ((1, 0),))), max_iterations=8)
    result = MbbpController(spec).run(_original(), error_rate=0.1)

    assert result.source_status == "canonical_adaptation"
    assert [member.schedule for member in result.members] == ["check_node_serial", "check_node_serial"]
    assert [member.normalized_min_sum_alpha for member in result.members] == [0.875, 0.875]
    assert len({member.initial_state_identity for member in result.members}) == 2
    assert len({leaf_id for leaf_id, _scope, _work in result.work_leaves}) == len(result.work_leaves)
    admitted = [member for member in result.members if member.admitted]
    assert admitted
    assert result.selection is not None
    assert result.selected_candidate is not None
    selected = next(origin for origin in result.selection.origins if origin.lineage_id == result.selected_origin_id)
    assert selected.frequency == 2
    assert selected.score == selected.frequency / (sum(selected.candidate) + 1)
    assert result.work == sum((member.work for member in result.members), start=type(result.work).zero())


def test_worker_completion_order_cannot_change_selection_lineage_or_work() -> None:
    from bp_registry.canonical.mbbp import MbbpController, MbbpSpec

    spec = MbbpSpec(bases=(_basis("basis-a", 0), _basis("basis-b", 1, ((1, 0),))), max_iterations=8)
    forward = MbbpController(spec).run(_original(), error_rate=0.1, completion_order=("basis-a", "basis-b"))
    reversed_order = MbbpController(spec).run(_original(), error_rate=0.1, completion_order=("basis-b", "basis-a"))

    assert forward.as_evidence() == reversed_order.as_evidence()


def test_declared_vote_uses_only_admitted_members_and_validates_the_aggregate() -> None:
    """The public decision closes over member terminals, not hidden truth."""
    from bp_registry.canonical.mbbp import MbbpController, MbbpSpec
    from bp_registry.canonical import phase6

    assert hasattr(phase6, "execute_declared_mbbp_decision")

    result = MbbpController(MbbpSpec(
        bases=(_basis("basis-a", 0), _basis("basis-b", 1, ((1, 0),))), max_iterations=8,
    )).run(_original(), error_rate=0.1)

    decision = phase6.execute_declared_mbbp_decision(_original(), result=result, vote_tie_bit=1)

    assert decision.terminal_status == "vote_selected_original_valid_candidate"
    assert decision.vote is not None and decision.vote.original_valid is True
    assert decision.electorate == tuple(sorted(
        (member.lineage_id for member in result.members if member.admitted), key=lambda identifier: identifier.value,
    ))
    assert len(decision.ballots) == len(decision.electorate)
    assert decision.exclusions == ()
    assert decision.selected_candidate == decision.vote.correction


def _two_solution_vote_result():
    """Freeze two individually valid, coordinate-tied member terminals."""
    from bp_registry.canonical.mbbp import MbbpController, MbbpSpec

    result = MbbpController(MbbpSpec(
        bases=(_basis("basis-a", 0), _basis("basis-b", 1, ((1, 0),))), max_iterations=8,
    )).run(_original(), error_rate=0.1)
    members = (
        replace(result.members[0], status="converged_original_valid", candidate=(1, 0, 0), original_valid=True),
        replace(result.members[1], status="converged_original_valid", candidate=(0, 1, 1), original_valid=True),
    )
    return replace(result, members=members)


def test_declared_vote_retains_invalid_aggregate_without_list_fallback() -> None:
    from bp_registry.canonical.phase6 import execute_declared_mbbp_decision

    decision = execute_declared_mbbp_decision(_original(), result=_two_solution_vote_result(), vote_tie_bit=0)

    assert decision.terminal_status == "vote_aggregate_original_invalid"
    assert decision.selected_candidate is None and decision.selected_origin_id is None
    assert decision.vote is not None
    assert decision.vote.correction == (0, 0, 0)
    assert decision.vote.original_valid is False


def test_declared_vote_records_each_nonadmitted_member_and_empty_electorate() -> None:
    from bp_registry.canonical.phase6 import execute_declared_mbbp_decision

    result = _two_solution_vote_result()
    denied = replace(
        result.members[0], status="budget_denied", candidate=None, original_valid=None, terminal_posterior=None,
    )
    invalid = replace(result.members[1], status="converged_original_invalid", original_valid=False)
    decision = execute_declared_mbbp_decision(
        _original(), result=replace(result, members=(denied, invalid)), vote_tie_bit=1,
    )

    assert decision.terminal_status == "no_eligible_vote_candidate"
    assert decision.electorate == () and decision.ballots == () and decision.vote is None
    assert [(item.member_id, item.disposition) for item in decision.exclusions] == [
        (denied.member_id, "budget_denied"), (invalid.member_id, "original_invalid"),
    ]


def test_public_v7_manifest_admits_a_complete_coordinate_vote_declaration() -> None:
    from bp_registry.manifests import CanonicalExperimentV7, parse_manifest

    value = json.loads(Path("data/manifests/canonical-three-qubit-development.json").read_text())
    value["schema_version"] = 7
    value["numerical_profile"] = "cpu-float64-min-sum-v1"
    policies = value["policies"]
    assert isinstance(policies, dict)
    policies["update"].update({"kind": "normalized_min_sum", "parameter_assignment": {"shape": "scalar", "value": 0.875}})
    policies["schedule"].update({"kind": "check_node_serial"})
    policies["state_memory"].update({"kind": "identity"})
    value["ensemble"] = {
        "kind": "mbbp_ld", "source_status": "canonical_adaptation", "member_state": "independent",
        "max_iterations": 8, "max_member_c2v_updates": 100, "max_total_members": 1,
        "no_member_terminal": "no_member_converged_zero_return",
        "bases": [{"member_id": "member-0", "local_ordinal": 0, "partition_identity": "p0",
                    "permutation_identity": "q0", "transform_kind": "one_hot_original_check_rows",
                    "redundant_transforms": [[1]]}],
    }
    value["list_selection"] = {"kind": "frequency_over_weight_plus_one", "tie_rule": "local_ordinal_then_lineage"}
    value["vote"] = {"object": "correction_bits", "electorate_rule": "admitted_members",
                     "aggregation": "coordinate_majority", "tie_bit": 1}

    parsed = parse_manifest(value)

    assert isinstance(parsed, CanonicalExperimentV7)
    assert parsed.vote is not None and parsed.vote.tie_bit == 1


def test_vote_projection_classifies_nonconvergence_and_is_order_invariant() -> None:
    from bp_registry.canonical.phase6 import phase6_events

    result = _two_solution_vote_result()
    nonconverged = replace(
        result.members[0], status="iteration_cap", candidate=None, original_valid=None, terminal_posterior=None,
    )
    mixed = replace(result, members=(nonconverged, result.members[1]))
    bases = (_basis("basis-a", 0), _basis("basis-b", 1, ((1, 0),)))
    projection = phase6_events(_original(), bases=bases, result=mixed, vote_tie_bit=1)

    exclusion = next(payload for kind, payload in projection.events if kind == "vote_exclusion")
    assert exclusion["disposition"] == "nonconvergence"
    electorate = next(payload for kind, payload in projection.events if kind == "vote_electorate")
    ballots = [payload for kind, payload in projection.events if kind == "vote_ballot"]
    assert electorate["tie_bit"] == 1
    assert electorate["electorate"] == [ballots[0]["member_id"]]
    assert "selection" not in [kind for kind, _ in projection.events]


def test_vote_projection_retains_ties_invalid_aggregate_and_stable_lineage() -> None:
    from bp_registry.canonical.phase6 import phase6_events

    result = _two_solution_vote_result()
    bases = (_basis("basis-a", 0), _basis("basis-b", 1, ((1, 0),)))
    tied = phase6_events(_original(), bases=bases, result=result, vote_tie_bit=1)
    reversed_members = phase6_events(_original(), bases=bases, result=replace(result, members=tuple(reversed(result.members))), vote_tie_bit=1)
    invalid = phase6_events(_original(), bases=bases, result=result, vote_tie_bit=0)

    assert tied.events == reversed_members.events
    aggregate = next(payload for kind, payload in tied.events if kind == "vote_aggregate")
    assert aggregate["correction"] == [1, 1, 1]
    assert aggregate["tie_coordinates"] == [0, 1, 2]
    assert aggregate["candidate_lineage_id"] and aggregate["vote_lineage_id"]
    validation = next(payload for kind, payload in invalid.events if kind == "vote_validation")
    assert invalid.terminal == "vote_aggregate_original_invalid"
    assert validation["original_valid"] is False and invalid.candidate is None


def test_no_member_converged_returns_typed_zero_sentinel_without_candidate_admission() -> None:
    from bp_registry.canonical.mbbp import MbbpController, MbbpSpec

    impossible = OriginalProblem(
        "nonzero-no-member", np.zeros((1, 3), dtype=np.uint8),
        np.zeros((1, 3), dtype=np.uint8), np.asarray([1], dtype=np.uint8),
    )
    result = MbbpController(MbbpSpec(bases=(_basis("basis-a", 0, ((1,),)), _basis("basis-b", 1, ((1,),))), max_iterations=2)).run(
        impossible, error_rate=0.1,
    )

    assert result.terminal_status == "no_member_converged_zero_return"
    assert result.source_zero_return == (0, 0, 0)
    assert result.selected_candidate is None
    assert result.selected_origin_id is None
    assert result.selection is not None and result.selection.selected_origin_id is None
    assert all(
        member.status == "iteration_cap" and member.candidate == (0, 0, 0)
        and member.terminal_posterior is not None and np.all(np.isfinite(member.terminal_posterior))
        for member in result.members
    )
    assert np.any((impossible.hz @ np.asarray(result.source_zero_return, dtype=np.uint8)) % 2 != impossible.syndrome)


def test_member_budget_denial_keeps_terminal_and_unique_work_evidence() -> None:
    from bp_registry.canonical.mbbp import MbbpController, MbbpSpec

    result = MbbpController(MbbpSpec(bases=(_basis("basis-a", 0),), max_iterations=2, max_member_c2v_updates=0)).run(
        _original(), error_rate=0.1,
    )

    assert result.members[0].status == "budget_denied"
    assert result.members[0].candidate is None
    assert result.work_leaves == ()


def test_member_postprocessing_snapshot_posterior_preserves_all_failed_terminals_in_declared_order() -> None:
    from bp_registry.canonical import postprocessing

    assert hasattr(postprocessing, "adapt_mbbp_result"), "the MBBP handoff adapter must be public"
    from bp_registry.canonical.lineage import LineageEdge, LineageId
    from bp_registry.canonical.mbbp import MbbpController, MbbpSpec
    from bp_registry.canonical.problems import OriginalProblem, WorkingProblem

    impossible = OriginalProblem(
        "original-mbbp-postprocessing", np.zeros((1, 3), dtype=np.uint8),
        np.zeros((1, 3), dtype=np.uint8), np.asarray([1], dtype=np.uint8),
    )
    working = WorkingProblem(
        "working-mbbp-postprocessing", impossible,
        LineageEdge("identity", LineageId("original", impossible.lineage_id),
                    LineageId("working", "working-mbbp-postprocessing")),
    )
    controller = MbbpController(MbbpSpec(
        bases=(_basis("basis-a", 0, ((1,),)), _basis("basis-b", 1, ((1,),))), max_iterations=2,
    ))
    forward = controller.run(impossible, error_rate=0.1, completion_order=("basis-a", "basis-b"))
    reversed_order = controller.run(impossible, error_rate=0.1, completion_order=("basis-b", "basis-a"))

    result = postprocessing.adapt_mbbp_result(forward, working=working, error_rate=0.1)
    reordered = postprocessing.adapt_mbbp_result(reversed_order, working=working, error_rate=0.1)

    assert result.disposition == "compatible"
    assert [snapshot.declared_attempt_ordinal for snapshot in result.snapshots] == [0, 1]
    assert all(snapshot.posterior_llr.flags.writeable is False for snapshot in result.snapshots)
    assert tuple(snapshot.rank for snapshot in result.snapshots) == tuple(snapshot.rank for snapshot in reordered.snapshots)
    assert all(member.candidate is not None and member.terminal_posterior is not None for member in forward.members)


def test_member_postprocessing_later_success_suppresses_fallback_after_any_original_valid_member() -> None:
    from bp_registry.canonical import postprocessing
    from bp_registry.canonical.lineage import LineageEdge, LineageId
    from bp_registry.canonical.mbbp import MbbpController, MbbpSpec
    from bp_registry.canonical.problems import WorkingProblem

    original = _original()
    working = WorkingProblem(
        "working-mbbp-success", original,
        LineageEdge("identity", LineageId("original", original.lineage_id), LineageId("working", "working-mbbp-success")),
    )
    result = MbbpController(MbbpSpec(
        bases=(_basis("basis-a", 0), _basis("basis-b", 1, ((1, 0),))), max_iterations=8,
    )).run(original, error_rate=0.1)

    handoff = postprocessing.adapt_mbbp_result(result, working=working, error_rate=0.1)

    assert any(member.original_valid for member in result.members)
    assert handoff.disposition == "composition_success"
    assert handoff.snapshots == ()


def test_member_unsupported_postprocessing_compositions_fail_closed_with_stable_reason() -> None:
    from bp_registry.canonical.postprocessing import unsupported_composition

    result = unsupported_composition("relay")

    assert result.disposition == "unsupported_composition"
    assert result.reason == "unsupported_relay_missing_complete_terminal_snapshot_contract"
