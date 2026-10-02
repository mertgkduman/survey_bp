# Phase 6 candidate-list selection foundation

`bp_registry.canonical.list_selection.select_candidate_list` takes an immutable original CSS problem, a list of candidate records, and an explicit selection specification. Candidate records name their origin, generation order, declared eligibility rule, original-coordinate bits, and optional controller score. The selection specification names the score basis, direction, and tie rule.

The selector checks each available candidate against the **original syndrome** before it can become eligible. This check establishes syndrome validity, not exact or logical recovery; the independent evaluator retains those outcome judgments. Every input candidate remains in the returned evidence with its origin, score, validity, and rejection reason. Input arrival order does not affect the decision.

The generic primitive supports original-coordinate Hamming weight or a finite score supplied by a source-specific controller. It does not assign a BeamSearch ranking equation or define an ensemble voting object. Those source-specific contracts must be pinned before the corresponding controllers use this module.

```python
from bp_registry.canonical.list_selection import ListCandidate, ListSelectionSpec, select_candidate_list

policy = ListSelectionSpec("hamming_weight", "original_hamming_weight", "minimize", "generation_order")
items = [ListCandidate("candidate-0", "member-0", 0, (1, 0, 0), True, "controller:converged")]
result = select_candidate_list(original_problem, items, spec=policy)
evidence = result.as_evidence()
```

A `declared_score` policy must provide its own nonempty `score_basis`. Missing scores leave otherwise valid candidates in the record as ineligible. Rejected candidates keep their bits in this initial small-list contract; a future large beam implementation can define a separately verified storage policy without changing selection semantics.
