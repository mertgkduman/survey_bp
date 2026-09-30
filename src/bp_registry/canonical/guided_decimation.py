"""Source-qualified binary BPGD finite-prior fixation controller."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np

from .budgets import BudgetTree
from .contracts import InterventionSpec
from .intervention_session import BpSession, InterventionProposal, SessionTransition


@dataclass(frozen=True, slots=True)
class GuidedTransition:
    admitted: bool
    termination: str | None
    proposal: InterventionProposal | None
    session_transition: SessionTransition
    eligibility_set: tuple[int, ...]


class GuidedDecimationController:
    """Algorithm 1 v2 interpretation with disclosed zero and final-round rules."""

    def __init__(self, spec: InterventionSpec | Mapping[str, object]) -> None:
        self.spec = spec if isinstance(spec, InterventionSpec) else InterventionSpec.model_validate(spec)

    def fix_one(self, session: BpSession, *, posterior: np.ndarray, budgets: BudgetTree) -> GuidedTransition:
        state = session.state
        values = np.asarray(posterior, dtype=np.float64)
        if values.shape != (session.edge_table.variable_count,) or not np.all(np.isfinite(values)):
            raise ValueError("guided reliability requires finite current posterior for every variable")
        eligible = tuple(index for index in range(len(values)) if index not in state.fixed_indices)
        if not eligible:
            return GuidedTransition(False, "no_eligible_target", None, SessionTransition(False, state, "no_eligible_target", None), ())
        # max uses original index as the secondary key independently of array or worker order.
        target = min(eligible, key=lambda index: (-abs(float(values[index])), index))
        signed = self.spec.finite_bias_magnitude if values[target] >= 0 else -self.spec.finite_bias_magnitude
        proposal = session.propose_finite_prior(
            target, signed, source_variant=self.spec.variant, target_order=eligible,
        )
        transition = session.commit_intervention(
            proposal, budgets=budgets, leaf_id=f"guided-fix:{state.revision}:{target}",
        )
        return GuidedTransition(transition.admitted, transition.termination, proposal, transition, eligible)
