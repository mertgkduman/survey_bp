"""Matched initial BP, followed by Relay memory legs or Beam decimation branches.

This is a controlled CSS adaptation of Relay-BP and BeamSearch, not a circuit
reproduction. Both paths use the same canonical min-sum flooding kernel and
V2C damping rule. No hidden physical error is accepted by this controller.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
import math
from typing import Literal

import numpy as np

from .budgets import WorkVector
from .kernel import BinarySpaKernel
from .memory import V2CDamping
from .numerics import MIN_SUM_CPU_F64, finite_saturate
from .schedules import EdgeTable, FloodingSchedule
from .updates import MinSumUpdate


Mode = Literal["beam", "relay"]


@dataclass(frozen=True, slots=True)
class FairLegConfig:
    """Frozen controlled comparison controls, including a shared work ceiling."""

    initial_iterations: int = 20
    extra_iterations_per_unit: int = 20
    max_extra_units: int = 4
    max_extra_c2v_updates: int = 8640
    v2c_gamma: float = 0.5
    beam_width: int = 2
    beam_rounds: int = 2
    solution_limit: int = 1
    relay_gamma_low: float = -0.24
    relay_gamma_high: float = 0.66
    relay_seed: str = "fair-relay-memory-v1"

    def __post_init__(self) -> None:
        integers = (self.initial_iterations, self.extra_iterations_per_unit, self.max_extra_units,
                    self.max_extra_c2v_updates, self.beam_width, self.beam_rounds, self.solution_limit)
        if any(type(value) is not int or value < 1 for value in integers):
            raise ValueError("fair-leg counts and work limits must be positive integers")
        if (type(self.v2c_gamma) is not float or not math.isfinite(self.v2c_gamma)
                or not 0.0 < self.v2c_gamma <= 1.0):
            raise ValueError("V2C damping uses a finite fresh-message coefficient in (0, 1]")
        if (not math.isfinite(self.relay_gamma_low) or not math.isfinite(self.relay_gamma_high)
                or self.relay_gamma_low >= self.relay_gamma_high or not self.relay_seed):
            raise ValueError("Relay disordered-memory interval and seed must be explicit")

    def as_evidence(self) -> dict[str, object]:
        from dataclasses import asdict
        return asdict(self)


@dataclass(frozen=True, slots=True)
class BPSegment:
    """A decoder-visible BP state; edge messages are keyed in original coordinates."""

    candidate: np.ndarray
    posterior: np.ndarray
    sum_llr: np.ndarray
    edge_messages: tuple[tuple[int, int, float], ...]
    unmasked: tuple[int, ...]
    fixed: tuple[tuple[int, int], ...]
    iterations: int
    converged: bool
    work: WorkVector
    stage_id: str

    @property
    def next_variable(self) -> int | None:
        if not self.unmasked:
            return None
        return self.unmasked[min(range(len(self.unmasked)), key=lambda i: (abs(float(self.sum_llr[i])), self.unmasked[i]))]

    @property
    def reliability_score(self) -> float:
        return float(np.sum(np.abs(self.sum_llr)))

    def as_evidence(self) -> dict[str, object]:
        return {
            "stage_id": self.stage_id, "fixed": [list(pair) for pair in self.fixed],
            "candidate": self.candidate.tolist(), "posterior": self.posterior.tolist(),
            "sum_llr": self.sum_llr.tolist(), "unmasked": list(self.unmasked),
            "edge_messages_sha256": sha256(json.dumps(self.edge_messages, separators=(",", ":")).encode()).hexdigest(),
            "iterations": self.iterations, "converged": self.converged,
            "next_variable": self.next_variable, "reliability_score": self.reliability_score,
            "work": self.work.as_evidence(structural_event_version=4),
        }


@dataclass(frozen=True, slots=True)
class ExtraUnit:
    unit_id: str
    mode: Mode
    index: int
    parent_id: str
    segment: BPSegment | None
    status: Literal["valid", "failed", "pruned", "denied"]
    gamma_sha256: str | None = None
    gamma_min: float | None = None
    gamma_max: float | None = None
    work: WorkVector = WorkVector()

    def as_evidence(self) -> dict[str, object]:
        return {
            "unit_id": self.unit_id, "mode": self.mode, "index": self.index,
            "parent_id": self.parent_id, "status": self.status,
            "gamma_sha256": self.gamma_sha256, "gamma_min": self.gamma_min,
            "gamma_max": self.gamma_max,
            "segment": None if self.segment is None else self.segment.as_evidence(),
            "work": self.work.as_evidence(structural_event_version=4),
        }


@dataclass(frozen=True, slots=True)
class FairLegResult:
    mode: Mode
    initial: BPSegment
    units: tuple[ExtraUnit, ...]
    candidate: np.ndarray | None
    selected_stage_id: str | None
    stopping_reason: str
    initial_work: WorkVector
    extra_work: WorkVector
    source_status: str = "controlled_css_adaptation"

    @property
    def source_profile(self) -> str:
        return ("paper_v2_masked_min_sum_css_adaptation" if self.mode == "beam"
                else "relay_v022_disordered_memory_after_shared_bp_css_adaptation")

    @property
    def total_work(self) -> WorkVector:
        return self.initial_work + self.extra_work

    def as_evidence(self) -> dict[str, object]:
        return {
            "mode": self.mode, "source_status": self.source_status, "source_profile": self.source_profile,
            "initial": self.initial.as_evidence(), "units": [unit.as_evidence() for unit in self.units],
            "candidate": None if self.candidate is None else self.candidate.tolist(),
            "selected_stage_id": self.selected_stage_id, "stopping_reason": self.stopping_reason,
            "initial_work": self.initial_work.as_evidence(structural_event_version=4),
            "extra_work": self.extra_work.as_evidence(structural_event_version=4),
            "total_work": self.total_work.as_evidence(structural_event_version=4),
        }


class FairLegController:
    """Run two source-informed extensions after one identical initial BP stage."""

    def __init__(self, check_matrix: np.ndarray, syndrome: np.ndarray, *, error_rate: float, config: FairLegConfig):
        h = np.asarray(check_matrix)
        s = np.asarray(syndrome)
        if (h.ndim != 2 or h.shape[0] == 0 or h.shape[1] == 0 or not np.issubdtype(h.dtype, np.integer)
                or np.any((h != 0) & (h != 1)) or s.shape != (h.shape[0],)
                or not np.issubdtype(s.dtype, np.integer) or np.any((s != 0) & (s != 1))):
            raise ValueError("fair-leg decoding requires a binary check matrix and matching syndrome")
        if not math.isfinite(error_rate) or not 0.0 < error_rate < 0.5:
            raise ValueError("fair-leg error rate must be in (0, 0.5)")
        self.h = np.array(h, dtype=np.uint8, copy=True)
        self.s = np.array(s, dtype=np.uint8, copy=True)
        self.h.setflags(write=False)
        self.s.setflags(write=False)
        self.error_rate = error_rate
        self.config = config
        self.kernel = BinarySpaKernel(profile=MIN_SUM_CPU_F64, update_rule=MinSumUpdate())
        self.channel_prior = self.kernel.prior(error_rate)
        self._initial: BPSegment | None = None

    def _valid(self, candidate: np.ndarray) -> bool:
        return bool(np.array_equal((self.h.astype(np.int64) @ candidate.astype(np.int64)) % 2, self.s))

    @staticmethod
    def _frozen(value: np.ndarray, *, dtype: object) -> np.ndarray:
        result = np.array(value, dtype=dtype, copy=True)
        result.setflags(write=False)
        return result

    def _bp_segment(
        self, *, fixed: tuple[tuple[int, int], ...], iterations: int, stage_id: str,
        warm_messages: tuple[tuple[int, int, float], ...] | None = None,
        start_posterior: np.ndarray | None = None, relay_gamma: np.ndarray | None = None,
    ) -> BPSegment:
        fixed_map = dict(fixed)
        if (len(fixed_map) != len(fixed) or any(type(index) is not int or type(bit) is not int
                or not 0 <= index < self.h.shape[1] or bit not in (0, 1) for index, bit in fixed)):
            raise ValueError("masked positions must be distinct original variables with binary values")
        unmasked = tuple(index for index in range(self.h.shape[1]) if index not in fixed_map)
        local_h = self.h[:, unmasked]
        target = self.s.astype(np.int64).copy()
        for index, bit in fixed:
            if bit:
                target ^= self.h[:, index].astype(np.int64)
        local_s = target.astype(np.uint8)
        table = EdgeTable.from_check_matrix(local_h)
        start = (np.full(len(unmasked), self.channel_prior, dtype=np.float64)
                 if start_posterior is None else np.asarray(start_posterior, dtype=np.float64)[list(unmasked)])
        if start.shape != (len(unmasked),) or not np.all(np.isfinite(start)):
            raise ValueError("warm-start posterior is incompatible or nonfinite")
        if relay_gamma is not None and (relay_gamma.shape != (self.h.shape[1],) or not np.all(np.isfinite(relay_gamma))):
            raise ValueError("Relay gamma vector must be finite and original-variable aligned")
        local_gamma = None if relay_gamma is None else relay_gamma[list(unmasked)]
        schedule = FloodingSchedule(table, kernel=self.kernel, profile=MIN_SUM_CPU_F64)
        inherited = {} if warm_messages is None else {(check, var): value for check, var, value in warm_messages}
        if len(inherited) != (0 if warm_messages is None else len(warm_messages)):
            raise ValueError("warm-start edge identity is duplicated")
        messages = np.asarray([
            inherited.get((check, unmasked[local]), self.channel_prior)
            for check, local in table.edges
        ], dtype=np.float64)
        if not np.all(np.isfinite(messages)):
            raise ValueError("warm-start V2C messages must be finite")
        posterior = np.array(start, dtype=np.float64, copy=True)
        summed = np.zeros(len(unmasked), dtype=np.float64)
        candidate = np.zeros(self.h.shape[1], dtype=np.uint8)
        for index, bit in fixed:
            candidate[index] = bit
        if unmasked:
            candidate[list(unmasked)] = self.kernel.candidate_from_beliefs(posterior)
        work = WorkVector.zero()
        completed = 0
        converged = False
        damping = V2CDamping("fair-leg-v2c", self.config.v2c_gamma) if table.edge_count else None
        damping_state = None if damping is None else damping.initial_state(messages)
        for iteration in range(iterations):
            if not table.edge_count:
                converged = self._valid(candidate)
                break
            if local_gamma is None:
                prior = np.full(len(unmasked), self.channel_prior, dtype=np.float64)
            else:
                prior = finite_saturate(
                    (1.0 - local_gamma) * self.channel_prior + local_gamma * posterior,
                    boundary="relay_dynamic_affine_prior", profile=MIN_SUM_CPU_F64,
                )
            proposals = []

            def damp(fresh: np.ndarray) -> np.ndarray:
                assert damping is not None and damping_state is not None
                proposal = damping.propose(damping_state.v2c, fresh, boundary="source_iteration")
                proposals.append(proposal)
                return proposal.value

            sweep = schedule.sweep(
                messages, local_s, error_rate=self.error_rate, source_iteration=iteration,
                prior_llrs=prior, transform_v2c=damp,
            )
            assert damping is not None and damping_state is not None and len(proposals) == 1
            damping_state = damping.commit(proposals[0], damping_state)
            messages = sweep.new_v2c
            posterior = sweep.beliefs
            summed += posterior
            candidate = np.zeros(self.h.shape[1], dtype=np.uint8)
            candidate[list(unmasked)] = sweep.candidate
            for index, bit in fixed:
                candidate[index] = bit
            completed += 1
            work += WorkVector.from_flooding_counts(edge_count=table.edge_count, variable_count=len(unmasked))
            work += WorkVector(original_checks=1)
            if self._valid(candidate):
                converged = True
                break
        if completed:
            work += WorkVector(bp_calls=1)
        edge_messages = tuple((check, unmasked[local], float(messages[edge_index]))
                              for edge_index, (check, local) in enumerate(table.edges))
        return BPSegment(
            self._frozen(candidate, dtype=np.uint8), self._frozen(posterior, dtype=np.float64),
            self._frozen(summed if completed else posterior, dtype=np.float64),
            edge_messages, unmasked, tuple(sorted(fixed)), completed, converged, work, stage_id,
        )

    def initial_bp(self) -> BPSegment:
        if self._initial is None:
            self._initial = self._bp_segment(fixed=(), iterations=self.config.initial_iterations, stage_id="initial-bp")
        return self._initial

    def _require_initial(self, initial: BPSegment) -> None:
        if initial is not self.initial_bp():
            raise ValueError("extensions must use this controller’s exact matched initial BP run")

    def _select(self, segments: list[BPSegment]) -> BPSegment | None:
        valid = [segment for segment in segments if segment.converged and self._valid(segment.candidate)]
        return min(enumerate(valid), key=lambda item: (float(np.sum(item[1].candidate)) * self.channel_prior, item[0]))[1] if valid else None

    def _early(self, mode: Mode, initial: BPSegment) -> FairLegResult | None:
        if initial.converged:
            return FairLegResult(mode, initial, (), initial.candidate, initial.stage_id,
                                 "initial_bp_converged", initial.work, WorkVector.zero())
        return None

    def run_relay(self, initial: BPSegment, *, sample_seed_identity: str) -> FairLegResult:
        """Additional units are disordered-memory runs; initial BP is separate."""
        self._require_initial(initial)
        early = self._early("relay", initial)
        if early is not None:
            return early
        if not sample_seed_identity:
            raise ValueError("Relay draws require a public sample seed identity")
        units: list[ExtraUnit] = []
        valid: list[BPSegment] = []
        previous = initial
        extra = WorkVector.zero()
        used_updates = 0
        reason = "unit_limit"
        table = EdgeTable.from_check_matrix(self.h)
        for index in range(1, self.config.max_extra_units + 1):
            remaining = self.config.max_extra_c2v_updates - used_updates
            allowed = min(self.config.extra_iterations_per_unit, remaining // max(1, table.edge_count))
            unit_id = f"relay-leg-{index}"
            if allowed < 1:
                units.append(ExtraUnit(unit_id, "relay", index, previous.stage_id, None, "denied"))
                reason = "shared_work_budget"
                break
            seed = sha256(f"{self.config.relay_seed}:{sample_seed_identity}:leg:{index}".encode()).digest()
            rng = np.random.Generator(np.random.PCG64(int.from_bytes(seed[:16], "big")))
            gamma = rng.uniform(self.config.relay_gamma_low, self.config.relay_gamma_high, self.h.shape[1])
            # Relay transfers only the previous posterior. C2V/V2C and damping
            # histories reset to channel priors in each new disordered leg.
            segment = self._bp_segment(
                fixed=(), iterations=allowed, stage_id=unit_id,
                start_posterior=previous.posterior, relay_gamma=gamma,
            )
            delta = segment.work + WorkVector(relay_transfers=1)
            extra += delta
            used_updates += segment.work.check_to_variable_updates
            status = "valid" if segment.converged else "failed"
            units.append(ExtraUnit(
                unit_id, "relay", index, previous.stage_id, segment, status,
                sha256(np.asarray(gamma, dtype="<f8").tobytes()).hexdigest(),
                float(gamma.min()), float(gamma.max()), delta,
            ))
            previous = segment
            if segment.converged:
                valid.append(segment)
                if len(valid) >= self.config.solution_limit:
                    reason = "solution_limit"
                    break
        selected = self._select(valid)
        return FairLegResult("relay", initial, tuple(units), None if selected is None else selected.candidate,
                             None if selected is None else selected.stage_id, reason, initial.work, extra)

    def run_beam(self, initial: BPSegment) -> FairLegResult:
        """Each additional unit is one source-shaped masked BP branch."""
        self._require_initial(initial)
        early = self._early("beam", initial)
        if early is not None:
            return early
        units: list[ExtraUnit] = []
        valid: list[BPSegment] = []
        frontier = [initial]
        extra = WorkVector.zero()
        used_updates = 0
        reason = "round_limit"
        for _round in range(1, self.config.beam_rounds + 1):
            children: list[BPSegment] = []
            for parent in frontier:
                variable = parent.next_variable
                if variable is None:
                    continue
                for bit in (0, 1):
                    index = len([unit for unit in units if unit.segment is not None]) + 1
                    unit_id = f"beam-branch-{index}"
                    if index > self.config.max_extra_units:
                        reason = "unit_limit"
                        break
                    fixed = tuple(sorted((*parent.fixed, (variable, bit))))
                    unmasked = tuple(v for v in range(self.h.shape[1]) if v not in dict(fixed))
                    edge_count = EdgeTable.from_check_matrix(self.h[:, unmasked]).edge_count
                    remaining = self.config.max_extra_c2v_updates - used_updates
                    allowed = min(self.config.extra_iterations_per_unit,
                                  remaining // edge_count if edge_count else 1)
                    if allowed < 1:
                        units.append(ExtraUnit(unit_id, "beam", index, parent.stage_id, None, "denied"))
                        reason = "shared_work_budget"
                        break
                    segment = self._bp_segment(
                        fixed=fixed, iterations=allowed, stage_id=unit_id,
                        warm_messages=parent.edge_messages, start_posterior=self._lift_posterior(parent),
                    )
                    delta = segment.work + WorkVector(branch_expansions=1, fixation_actions=1, transformations=1)
                    used_updates += segment.work.check_to_variable_updates
                    extra += delta
                    status = "valid" if segment.converged else "failed"
                    units.append(ExtraUnit(unit_id, "beam", index, parent.stage_id, segment, status, work=delta))
                    if segment.converged:
                        valid.append(segment)
                        if len(valid) >= self.config.solution_limit:
                            reason = "solution_limit"
                            selected = self._select(valid)
                            return FairLegResult("beam", initial, tuple(units), selected.candidate,
                                                 selected.stage_id, reason, initial.work, extra)
                    else:
                        children.append(segment)
                if reason in {"unit_limit", "shared_work_budget"}:
                    break
            if reason in {"unit_limit", "shared_work_budget"}:
                break
            children.sort(key=lambda segment: -segment.reliability_score)
            for child in children[self.config.beam_width:]:
                position = next(i for i, unit in enumerate(units) if unit.unit_id == child.stage_id)
                units[position] = replace(units[position], status="pruned",
                                          work=units[position].work + WorkVector(branch_prunes=1))
                extra += WorkVector(branch_prunes=1)
            frontier = children[:self.config.beam_width]
            if not frontier:
                reason = "frontier_exhausted"
                break
        selected = self._select(valid)
        return FairLegResult("beam", initial, tuple(units), None if selected is None else selected.candidate,
                             None if selected is None else selected.stage_id, reason, initial.work, extra)

    def _lift_posterior(self, parent: BPSegment) -> np.ndarray:
        posterior = np.full(self.h.shape[1], self.channel_prior, dtype=np.float64)
        posterior[list(parent.unmasked)] = parent.posterior
        return posterior

    def run_pair(self, *, sample_seed_identity: str) -> tuple[FairLegResult, FairLegResult]:
        initial = self.initial_bp()
        return self.run_beam(initial), self.run_relay(initial, sample_seed_identity=sample_seed_identity)
