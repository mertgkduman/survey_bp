"""Source-construction and replay checks for Hsu's overlapping groups."""

import pytest

from bp_registry.canonical.group_shuffled import HsuGroupPlan, groups_from_order


def test_hsu_construction_matches_paper_worked_example():
    assert groups_from_order((0, 1, 2, 3), check_count=4) == ((0, 1), (1, 2), (2, 3))


def test_hsu_construction_replay_covers_and_counts_repeated_checks():
    plan = HsuGroupPlan(6, "a" * 64)
    first = plan.traversal(attempt_identity="run:shot:0", iteration=0)
    assert first == plan.traversal(attempt_identity="run:shot:0", iteration=0)
    assert first != plan.traversal(attempt_identity="run:shot:0", iteration=1)
    assert len(first.groups) == 5
    assert first.groups == tuple(zip(first.order[:-1], first.order[1:]))
    assert sorted(first.order) == list(range(6))
    assert dict(first.evidence()["membership_multiplicity"]) == {
        check: (1 if check in (first.order[0], first.order[-1]) else 2)
        for check in first.order
    }


@pytest.mark.parametrize("order,count", [((0,), 1), ((0, 0), 2), ((0, 2), 2), ((True, 1), 2), ((0, "1"), 2)])
def test_hsu_construction_rejects_invalid_order(order, count):
    with pytest.raises(ValueError):
        groups_from_order(order, check_count=count)


def test_hsu_replay_rejects_invalid_identity_and_iteration():
    with pytest.raises(ValueError):
        HsuGroupPlan(3, "not-a-digest")
    with pytest.raises(ValueError):
        HsuGroupPlan(3, "a" * 64).traversal(attempt_identity="x", iteration=-1)
