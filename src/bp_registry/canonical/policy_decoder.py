"""Shared decoder-visible binary policies for code capacity and DEM fault graphs.

This opt-in contract leaves historical manifest and circuit-policy-v1 meanings
intact. A binary graph and channel LLRs are the only numerical inputs; neither
physical errors nor logical outcomes are available to a policy.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from hashlib import sha256
import json
from typing import Literal

import numpy as np
from scipy.sparse import csr_matrix
from pydantic import BaseModel, ConfigDict, Field, JsonValue, TypeAdapter, field_validator, model_validator

from bp_registry.compiled_contracts import immutable_snapshot
from bp_registry.resolution import BpFloodingPolicy
from .budgets import BudgetTree, WorkVector
from .contracts import MemoryCompositionSpec, MemoryBindingV4, RelayLegSpec, RelayMemoryTuningV4
from .kernel import BinarySpaKernel, _binary
from .memory_execution import MemoryFloodingSchedule, LocalMemoryExecution, validate_single_attempt_memory
from .numerics import BinaryNumericalProfileV3, REFERENCE_CPU_F64, finite_saturate
from .schedules import (EdgeTable, FloodingSchedule, LayeredSchedule,
                        CheckNodeSerialSchedule, VariableNodeSerialSchedule, RandomizedTraversalPlan)
from .updates import MinSumUpdate, NormalizedMinSumUpdate, OffsetMinSumUpdate, ParameterAssignment, ParameterRefreshPlan


def canonical_json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def evidence(value):
    """Serialize existing typed policy receipts without losing their work/lineage."""
    if isinstance(value, WorkVector):
        return value.as_evidence(structural_event_version=4)
    if hasattr(value, "as_evidence"):
        return evidence(value.as_evidence())
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if is_dataclass(value):
        return evidence(asdict(value))
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {k: evidence(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [evidence(v) for v in value]
    return value


class RelayOptions(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
    legs: tuple[RelayLegSpec, ...] = Field(min_length=1)
    memory_bindings: tuple[MemoryBindingV4, ...] = Field(min_length=1)
    memory_tuning: RelayMemoryTuningV4 | None = None
    solution_limit: int = Field(default=1, ge=1)
    transfer: Literal["posterior_only", "disabled"] = "posterior_only"

    @model_validator(mode="after")
    def ordered_memory(self):
        bindings = self.memory_bindings
        if (tuple(b.order for b in bindings) != tuple(range(len(bindings)))
                or len({b.binding_id for b in bindings}) != len(bindings)):
            raise ValueError("Relay requires unique bindings in contiguous explicit order")
        return self


def _source_spec(controller, options):
    from .contracts import InterventionSpec
    from .impulse import ImpulseSpec
    from .interventions import FreezingSpec, SyndromeFlipSpec, SignFlipSpec
    from .restarting import RestartSpec
    from .mbbp import MbbpSpec
    from .fair_legs import FairLegConfig
    kinds = {"guided_decimation": InterventionSpec, "impulse": ImpulseSpec,
             "freezing": FreezingSpec, "syndrome_flip": SyndromeFlipSpec,
             "sign_flip": SignFlipSpec, "restart_belief": RestartSpec,
             "mbbp": MbbpSpec, "beam": FairLegConfig, "relay": RelayOptions}
    cls = kinds[controller]
    allowed = set(cls.model_fields) if issubclass(cls, BaseModel) else {f.name for f in fields(cls)}
    if set(options) - allowed:
        raise ValueError(f"unknown {controller} controls: {sorted(set(options) - allowed)}")
    if controller == "beam":
        defaults = FairLegConfig()
        if any(name in options and options[name] != getattr(defaults, name)
               for name in ("relay_gamma_low", "relay_gamma_high", "relay_seed")):
            raise ValueError("Relay-only controls do not apply to beam execution")
    if controller == "mbbp":
        from .mbbp import MbbpBasis
        basis_fields = {f.name for f in fields(MbbpBasis)}
        for basis in options.get("bases", []):
            if isinstance(basis, dict) and set(basis) - basis_fields:
                raise ValueError("unknown MBBP basis controls")
    # JSON admission restores immutable tuples, while strict validation rejects
    # string/integer coercions in the actual source specifications.
    return TypeAdapter(cls).validate_json(canonical_json(options), strict=True)


class BinaryPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, allow_inf_nan=False)
    version: Literal["binary-policy-v1"] = "binary-policy-v1"
    backend: Literal["auto", "scalar", "compiled"] = "auto"
    rule: Literal["spa", "min_sum", "normalized_min_sum", "offset_min_sum"] = "spa"
    parameter: ParameterAssignment = Field(default_factory=lambda: ParameterAssignment(shape="scalar", value=1.0))
    parameter_refresh: ParameterRefreshPlan | None = None
    flooding_policy: BpFloodingPolicy | None = None
    max_iterations: int = Field(default=30, ge=0, le=100_000)
    schedule: Literal["flooding", "layered", "check_node_serial", "variable_node_serial", "group_shuffled", "residual"] = "flooding"
    partitions: tuple[tuple[int, ...], ...] | None = None
    randomized: Literal["configuration", "attempt", "sweep"] | None = None
    seed: str = "binary-policy-v1"
    memory: MemoryCompositionSpec | None = None
    controller: Literal["single", "guided_decimation", "impulse", "freezing", "syndrome_flip", "sign_flip", "restart_belief", "mbbp", "beam", "relay"] = "single"
    options: dict[str, JsonValue] = Field(default_factory=dict)
    damping_gamma: float | None = Field(default=None, ge=0.0, le=1.0)
    vote_tie_bit: int | None = Field(default=None, ge=0, le=1)

    @field_validator("flooding_policy", mode="before")
    @classmethod
    def closed_precision_spec(cls, value):
        if isinstance(value, dict):
            from bp_registry.resolution import ResolutionPolicy
            if set(value) - {f.name for f in fields(BpFloodingPolicy)}:
                raise ValueError("unknown flooding policy controls")
            resolution = value.get("resolution")
            if isinstance(resolution, dict) and set(resolution) - {f.name for f in fields(ResolutionPolicy)}:
                raise ValueError("unknown resolution controls")
        return value

    @model_validator(mode="after")
    def supported(self):
        if self.flooding_policy is not None:
            if (self.controller != "single" or self.schedule != "flooding" or self.memory is not None
                    or self.rule != "spa" or self.parameter != ParameterAssignment(shape="scalar", value=1.0)
                    or self.parameter_refresh is not None):
                raise ValueError("explicit flooding policy owns check, damping and resolution controls")
            if self.flooding_policy.version not in {"bp-flooding-policy-v2", "bp-flooding-policy-v3"} or self.flooding_policy.hard_decision != "min_llr":
                raise ValueError("binary vector flooding requires a v2/v3 min_llr policy")
            if self.backend == "scalar":
                raise ValueError("explicit precision policies use the compiled CPU flooding backend")
        if not self.seed:
            raise ValueError("seed identity must be nonempty")
        if (self.schedule == "layered") != (self.partitions is not None):
            raise ValueError("explicit partitions are required exactly for layered scheduling")
        if self.randomized is not None and self.schedule not in {"layered", "check_node_serial", "variable_node_serial"}:
            raise ValueError("randomized traversal requires an existing local traversal")
        if self.rule in {"spa", "min_sum"} and self.parameter != ParameterAssignment(shape="scalar", value=1.0):
            raise ValueError("parameter assignments apply only to normalized/offset min-sum")
        if self.parameter_refresh is not None:
            if self.rule not in {"normalized_min_sum", "offset_min_sum"} or self.parameter_refresh.generator is None:
                raise ValueError("generated parameters require NMS/OMS and an explicit generator")
            if self.parameter != ParameterAssignment(shape="scalar", value=1.0):
                raise ValueError("choose an explicit assignment or a generated assignment")
        if self.parameter.shape == "source_iteration" and len(self.parameter.values) < self.max_iterations:
            raise ValueError("parameter assignment must cover every source iteration")
        if self.schedule in {"group_shuffled", "residual"} and self.rule != "spa":
            raise ValueError("source group/residual scheduling requires SPA")
        if self.memory is not None:
            validate_single_attempt_memory(self.memory, schedule=self.schedule)
        if self.controller != "single":
            spec = _source_spec(self.controller, self.options)
            if (self.schedule != "flooding" or self.randomized is not None or self.memory is not None
                    or self.rule != "spa" or self.max_iterations != 30):
                raise ValueError("source controllers own their update, schedule, memory and iteration controls")
            if (self.controller == "impulse" and self.damping_gamma is not None
                    and (spec.realization != "exact_shortening" or spec.v2c_clip is not None)):
                raise ValueError("source impulse supports damping only with unclipped exact shortening")
        elif self.options:
            raise ValueError("single execution has no controller options")
        if self.damping_gamma is not None and self.controller not in {
            "guided_decimation", "impulse", "freezing", "syndrome_flip", "sign_flip", "restart_belief",
        }:
            raise ValueError("damping_gamma is a continuing intervention-session control; use ordinary memory otherwise")
        if self.vote_tie_bit is not None and self.controller != "mbbp":
            raise ValueError("coordinate voting requires an MBBP member ensemble")
        if self.backend == "compiled" and not self.compilable:
            raise ValueError("compiled execution supports scalar-parameter ordinary flooding; this policy uses scalar CPU")
        return self

    @property
    def compilable(self):
        return (self.controller == "single" and self.schedule == "flooding"
                and self.memory is None and self.parameter.shape == "scalar" and self.parameter_refresh is None)

    def kernel(self, table):
        p = self.parameter
        if self.parameter_refresh is not None and self.parameter_refresh.generator.graph_sha256 != table.graph_sha256:
            raise ValueError("parameter generator graph_sha256 does not match the immutable graph")
        kwargs = dict(graph_sha256=table.graph_sha256, check_count=table.check_count,
                      edge_count=table.edge_count, edge_checks=tuple(c for c, _ in table.edges))
        resolved = tuple(p.resolve(source_iteration=0, **kwargs)) if p.shape in {"check", "edge"} else None
        update = (None if self.rule == "spa" else MinSumUpdate() if self.rule == "min_sum" else
                  NormalizedMinSumUpdate(p, resolved_alpha=resolved) if self.rule == "normalized_min_sum" else
                  OffsetMinSumUpdate(p, resolved_beta=resolved))
        # Residual selection requires undamped SPA. Hsu's existing source
        # implementation uses the finite reference profile at group boundaries.
        profile = (REFERENCE_CPU_F64 if self.schedule == "group_shuffled" else
                   BinaryNumericalProfileV3(v2c_damping=0.0) if self.schedule == "residual" else None)
        return BinarySpaKernel(update_rule=update, profile=profile)


@dataclass(frozen=True)
class BinaryPolicyResult:
    candidate: np.ndarray
    converged: bool
    iterations: int
    ledger_json: str

    def __post_init__(self):
        bits = _binary(self.candidate, "candidate", ndim=1)
        record = json.loads(self.ledger_json)
        if (type(self.converged) is not bool or type(self.iterations) is not int or self.iterations < 0
                or record["candidate"] != bits.tolist() or record["converged"] != self.converged
                or record["iterations"] != self.iterations):
            raise ValueError("binary result disagrees with its execution receipt")
        object.__setattr__(self, "candidate", immutable_snapshot(bits))

    @property
    def ledger(self):
        return json.loads(self.ledger_json)


class BinaryPolicyDecoder:
    """A reusable graph; all attempt, controller and memory state is shot-local."""
    def __init__(self, check_matrix, policy: BinaryPolicy = BinaryPolicy()):
        if isinstance(check_matrix, EdgeTable):
            self.table = EdgeTable.from_edges(check_matrix.check_count, check_matrix.variable_count, check_matrix.edges)
            if self.table != check_matrix:
                raise ValueError("graph edges must be in canonical order")
        else:
            self.table = EdgeTable.from_check_matrix(_binary(check_matrix, "check_matrix", ndim=2))
        table = self.table
        rows = np.zeros(table.check_count + 1, dtype=np.int64)
        for check, _ in table.edges:
            rows[check + 1] += 1
        np.cumsum(rows, out=rows)
        self.row_ptr = immutable_snapshot(rows)
        self.variables = immutable_snapshot(np.array([v for _, v in table.edges], dtype=np.int64))
        self._h = csr_matrix((np.ones(table.edge_count, dtype=np.uint8), self.variables, self.row_ptr),
                            shape=(table.check_count, table.variable_count))
        self._graph_sha256 = table.graph_sha256
        self._graph_record = dict(check_count=table.check_count, variable_count=table.variable_count,
                                  edges=[list(e) for e in table.edges])
        self._policy_json = policy.model_dump_json()
        self._policy = BinaryPolicy.model_validate_json(self._policy_json)
        self._kernel = self._policy.kernel(self.table)
        self._controller_spec = (None if self._policy.controller == "single" else
                                 _source_spec(self._policy.controller, self._policy.options))
        self._controller_h = (None if self._policy.controller == "single" else immutable_snapshot(self._h.toarray()))
        if self._policy.controller != "single" and (not table.variable_count or not table.check_count):
            raise ValueError("source controllers require nonempty variable and check operands")
        # Construct once for graph-specific admission, never retain local state.
        if self._policy.controller == "single" and self._policy.schedule != "flooding":
            local = self._local_schedule("admission")
            if getattr(local, "unit_count", 1) == 0:
                raise ValueError("local scheduling requires a nonempty traversal")

    @property
    def h(self):
        return self._h.copy()

    @property
    def policy(self):
        return BinaryPolicy.model_validate_json(self._policy_json)

    def _local_schedule(self, identity, kernel=None):
        p, table = self._policy, self.table
        kernel = self._kernel if kernel is None else kernel
        if p.schedule == "layered":
            return LayeredSchedule(table, kernel=kernel, partitions=p.partitions, provenance="explicit")
        if p.schedule == "check_node_serial":
            return CheckNodeSerialSchedule(table, kernel=kernel)
        if p.schedule == "variable_node_serial":
            return VariableNodeSerialSchedule(table, kernel=kernel)
        if p.schedule == "group_shuffled":
            from .group_shuffled import HsuGroupSchedule
            return HsuGroupSchedule(table, kernel=kernel, root_identity=sha256(p.seed.encode()).hexdigest(), attempt_identity=identity)
        from .residual import SyndromeResidualSchedule
        return SyndromeResidualSchedule(table, kernel=kernel)

    def decode(self, syndrome, *, prior_llrs=None, error_rate=None, shot_identity="shot-0"):
        bits = _binary(syndrome, "syndrome", ndim=1)
        if bits.shape != (self.table.check_count,):
            raise ValueError("syndrome must match the original check rows")
        if (prior_llrs is None) == (error_rate is None):
            raise ValueError("provide exactly one of prior_llrs or error_rate")
        from .intervention_session import _frozen_f64
        prior = (_frozen_f64(prior_llrs, self.table.variable_count, "prior_llrs") if prior_llrs is not None else
                 np.full(self.table.variable_count, self._kernel.prior(error_rate)))
        if not isinstance(shot_identity, str) or not shot_identity:
            raise ValueError("shot identity must be nonempty")
        header = dict(schema="binary-policy-shot-v1", policy=json.loads(self._policy_json),
                      graph_sha256=self._graph_sha256, graph=self._graph_record,
                      prior_llrs=prior.tolist(), syndrome=bits.tolist(), shot_identity=shot_identity)
        identity = sha256(canonical_json(header).encode()).hexdigest()
        if self._policy.controller == "single":
            candidate, iterations, detail = self._ordinary(bits, prior, identity)
        else:
            candidate, iterations, detail = self._controller(bits, prior, identity)
        valid = bool(np.array_equal((self._h @ candidate) % 2, bits))
        record = dict(header, execution_identity=identity, candidate=candidate.tolist(),
                      converged=valid, iterations=iterations, execution=detail,
                      output_validation_work=evidence(WorkVector(original_checks=1)))
        return BinaryPolicyResult(candidate, valid, iterations, canonical_json(record))

    def verify_ledger(self, ledger_json):
        record = json.loads(ledger_json)
        replay = self.decode(record["syndrome"], prior_llrs=record["prior_llrs"], shot_identity=record["shot_identity"])
        if replay.ledger_json != ledger_json:
            raise ValueError("binary policy ledger does not replay")
        return True

    def _ordinary(self, syndrome, prior, identity):
        p, table = self._policy, self.table
        # Only generated coefficients mutate a kernel; those kernels are
        # attempt-local. Static graph-resolved rules and validated controls
        # are reused without revalidation in the per-shot hot path.
        kernel = self._kernel if p.parameter_refresh is None else p.kernel(table)
        initial_work = WorkVector(bp_calls=1, candidate_constructions=1, candidate_checks=table.variable_count,
                                  original_checks=1)
        if p.flooding_policy is not None:
            from .vector_flooding import decode_vector_policy
            fp = p.flooding_policy
            initial_work = WorkVector(bp_calls=1, candidate_constructions=1, candidate_checks=table.variable_count,
                                      original_checks=int(fp.zero_syndrome_shortcut))
            result = decode_vector_policy(self.row_ptr, self.variables, prior, syndrome, p.max_iterations,
                fp.resolution.format_code, fp.resolution.fixed_scale, fp.resolution.scope == "all_state",
                int(fp.check_rule == "min_sum"), *fp.coefficients,
                fp.zero_syndrome_shortcut, *fp.stabilization_args)
            candidate, posterior, count, _ = result
            work = _times(WorkVector.from_flooding_counts(edge_count=table.edge_count, variable_count=table.variable_count), int(count))
            return candidate, int(count), dict(backend="compiled", posterior=posterior.tolist(),
                work=evidence(work + initial_work), initial_work=evidence(initial_work), numerical_profile=fp.as_evidence(),
                stopping="declared_initial_shortcut_then_complete_sweep")
        prior = finite_saturate(prior, boundary="shared_initial_prior", profile=kernel.profile)
        valid = lambda c: bool(np.array_equal((self._h @ c) % 2, syndrome))
        candidate = kernel.candidate_from_beliefs(prior)
        if p.compilable and p.backend != "scalar":
            from bp_registry.circuit.policy_compiled import decode_attempt
            result = decode_attempt(self.row_ptr, self.variables, prior, syndrome, p.max_iterations,
                                    ("spa", "min_sum", "normalized_min_sum", "offset_min_sum").index(p.rule), p.parameter.value)
            candidate, posterior, count, _ = result
            work = WorkVector.from_flooding_counts(edge_count=table.edge_count, variable_count=table.variable_count)
            return candidate, int(count), dict(backend="compiled", posterior=posterior.tolist(),
                work=evidence(_times(work, int(count)) + initial_work), initial_work=evidence(initial_work),
                numerical_profile=kernel.profile.as_evidence(), stopping="prior_then_complete_sweep")
        tree = BudgetTree(limits=(), parents={})
        initial = tree.reserve("attempt", initial_work, leaf_id="attempt:initial-candidate")
        initial.commit_once()
        context = dict(configuration_identity=identity, decoder_identity=identity, attempt_identity=identity)
        parameter_evidence = []
        refresh_parameter = self._parameter_refresh(kernel, identity, tree, parameter_evidence)
        if p.schedule == "flooding":
            schedule = (FloodingSchedule(table, kernel=kernel) if p.memory is None else
                        MemoryFloodingSchedule(table, kernel=kernel, memory=p.memory, execution_context=context))
            messages = schedule.initialize(0.1, prior_llrs=prior)
            count = 0
            posterior = prior
            converged = valid(candidate)
            while count < p.max_iterations and not converged:
                refresh_parameter(count)
                reservation = tree.reserve("attempt", WorkVector.from_flooding_counts(
                    edge_count=table.edge_count, variable_count=table.variable_count), leaf_id=f"sweep:{count}")
                try:
                    sweep = schedule.sweep(messages, syndrome, error_rate=0.1, source_iteration=count,
                                           **({"prior_llrs": prior} if p.memory is None else {}))
                    if p.memory is not None:
                        schedule.commit(sweep)
                    messages, posterior, candidate = sweep.new_v2c, sweep.beliefs, sweep.candidate
                except BaseException:
                    reservation.rollback()
                    raise
                reservation.commit_once()
                count += 1
                converged = valid(candidate)
            detail = dict(backend="scalar", posterior=posterior.tolist(), work=evidence(tree.summary("attempt")),
                          leaves=evidence(tree.leaf_events()), numerical_profile=kernel.profile.as_evidence(),
                          stopping="prior_then_complete_sweep")
            detail["parameter_refreshes"] = parameter_evidence
            if p.memory is not None:
                detail["memory"] = schedule.evidence()
            return candidate, count, detail
        return self._local(syndrome, prior, identity, tree, context, kernel, refresh_parameter, parameter_evidence)

    def _parameter_refresh(self, kernel, identity, tree, receipts):
        plan = self._policy.parameter_refresh
        if plan is None:
            return lambda iteration: None
        state = plan.initial_state(configuration_identity=sha256(self._policy_json.encode()).hexdigest(), attempt_identity=identity)

        def refresh(iteration):
            nonlocal state
            if iteration and plan.scope != "source_iteration":
                return
            result = plan.refresh(state, boundary=plan.scope, source_iteration=iteration,
                graph_sha256=self._graph_sha256, check_count=self.table.check_count,
                edge_count=self.table.edge_count, budgets=tree, budget_scope="attempt")
            state = result.state
            assignment = result.assignment
            resolved = tuple(assignment.resolve(graph_sha256=self._graph_sha256,
                check_count=self.table.check_count, edge_count=self.table.edge_count, source_iteration=iteration,
                edge_checks=tuple(c for c, _ in self.table.edges)))
            kernel.update_rule = (NormalizedMinSumUpdate(assignment, resolved_alpha=resolved)
                                  if self._policy.rule == "normalized_min_sum" else
                                  OffsetMinSumUpdate(assignment, resolved_beta=resolved))
            receipts.append(result.evidence)
        return refresh

    def _local(self, syndrome, prior, identity, tree, context, kernel, refresh_parameter, parameter_evidence):
        from .execution import CanonicalLocalStepExecutor, ScheduleProgress
        p, table = self._policy, self.table
        schedule = self._local_schedule(identity, kernel)
        messages = FloodingSchedule(table, kernel=kernel).initialize(0.1, prior_llrs=prior)
        progress = ScheduleProgress(0, 0, (0,))
        executor = CanonicalLocalStepExecutor(tree, scope="attempt")
        candidate = kernel.candidate_from_beliefs(prior)
        converged = bool(np.array_equal((self._h @ candidate) % 2, syndrome))

        def valid(candidate):
            nonlocal converged
            converged = bool(np.array_equal((self._h @ candidate) % 2, syndrome))
            return converged
        local_memory = None
        if p.memory is not None:
            local_memory = LocalMemoryExecution(table, memory=p.memory, profile=kernel.profile, execution_context=context)
            local_memory.initialize(error_rate=0.1, initial_v2c=messages, initial_beliefs=prior)
        random_plan = random_state = order = None
        orders = []
        if p.randomized is not None:
            random_plan = RandomizedTraversalPlan(schedule, refresh_scope=p.randomized, root_identity=sha256(p.seed.encode()).hexdigest())
            random_state = random_plan.initial_state(configuration_identity=sha256(self._policy_json.encode()).hexdigest(), attempt_identity=identity)
        if p.schedule == "residual":
            c2v = np.zeros(table.edge_count)
            cache = schedule.initialize(messages, c2v, syndrome, error_rate=0.1, budgets=tree)
            while progress.iteration < p.max_iterations and not converged:
                proposal = schedule.propose_local_step(messages, c2v, cache, syndrome, error_rate=0.1, prior_llrs=prior)
                step = schedule.execute_local_step(executor, proposal, v2c=messages, c2v=c2v, cache=cache,
                                                   progress=progress, is_converged=valid)
                progress, candidate, c2v, cache = step.progress, step.candidate, step.c2v, step.cache
            orders = [dict(selected_edge=leaf[0]) for leaf in tree.leaf_events()]
        else:
            active_prior = prior
            while progress.iteration < p.max_iterations and not converged:
                if progress.cursor == (0,):
                    refresh_parameter(progress.iteration)
                    if local_memory is not None:
                        staged = local_memory.begin_source_iteration()
                        active_prior = prior if staged is None else staged
                    if p.schedule == "group_shuffled":
                        schedule.refresh_order(progress, budgets=tree)
                    if random_plan is not None and (p.randomized == "sweep" or progress.iteration == 0):
                        refresh = random_plan.refresh(random_state, boundary=p.randomized, budgets=tree, budget_scope="attempt")
                        random_state, order = refresh.state, refresh.order
                        orders.append(dict(iteration=progress.iteration, order=list(order)))
                selected_progress = (progress if order is None else
                                     ScheduleProgress(progress.iteration, progress.local_steps, (order[progress.cursor[0]],)))
                if local_memory is not None:
                    local_memory.begin_step()
                try:
                    step = schedule.execute_local_step(executor, messages, syndrome, error_rate=0.1,
                        progress=selected_progress, is_converged=valid, prior_llrs=active_prior,
                        **({"transform_beliefs": local_memory.transform_beliefs,
                            "transform_v2c": local_memory.transform_v2c} if local_memory is not None else {}))
                    if local_memory is not None:
                        local_memory.commit(local_memory.proposal())
                except BaseException:
                    if local_memory is not None:
                        local_memory.discard()
                        local_memory.abort_source_iteration()
                    raise
                candidate = step.candidate
                cursor = progress.cursor[0] + 1
                completed = cursor == schedule.unit_count
                progress = ScheduleProgress(progress.iteration + int(completed), step.progress.local_steps,
                                            (0 if completed else cursor,))
                if local_memory is not None and completed:
                    local_memory.complete_source_iteration()
            if local_memory is not None:
                local_memory.abort_source_iteration()
        detail = dict(backend="scalar", numerical_profile=kernel.profile.as_evidence(),
                      stopping="prior_then_local_unit", iteration_unit="committed_local_unit",
                      completed_source_iterations=progress.iteration, work=evidence(tree.summary("attempt")),
                      leaves=evidence(tree.leaf_events()), orders=orders)
        detail["parameter_refreshes"] = parameter_evidence
        if random_plan is not None:
            detail["randomized_traversal"] = random_plan.evidence(random_state)
        if local_memory is not None:
            detail["memory"] = local_memory.evidence()
        if p.schedule == "group_shuffled":
            detail["schedule"] = schedule.evidence()
        return candidate, progress.local_steps, detail

    def _controller(self, syndrome, prior, identity):
        from .problems import OriginalProblem
        from .intervention_session import BpSession
        from .guided_decimation import GuidedDecimationController
        from .impulse import ImpulseController
        from .interventions import FreezingController, SyndromeFlipController, SignFlipController
        from .restarting import RestartController
        from .mbbp import MbbpController
        from .fair_legs import FairLegController
        from .relay import RelayController
        kind = self._policy.controller
        spec = self._controller_spec
        original = OriginalProblem("original-" + identity, np.zeros((0, self.table.variable_count), dtype=np.uint8), self._controller_h, syndrome)
        tree = BudgetTree(limits=(), parents={})
        diagnostic = self._kernel.candidate_from_beliefs(prior)
        decision = None
        if kind == "guided_decimation":
            session = BpSession(self.table, syndrome, error_rate=0.1, prior_llrs=prior, owner_identity=identity,
                                damping_gamma=self._policy.damping_gamma)
            run = GuidedDecimationController(spec).run(session, check_matrix=self._controller_h, budgets=tree)
            selected, diagnostic = run.candidate, session.state.candidate
        elif kind == "mbbp":
            run = MbbpController(spec).run(original, error_rate=0.1, prior_llrs=prior)
            selected = run.selected_candidate
            if self._policy.vote_tie_bit is not None:
                from .phase6 import execute_declared_mbbp_decision
                decision = execute_declared_mbbp_decision(original, result=run, vote_tie_bit=self._policy.vote_tie_bit)
                selected = decision.selected_candidate
            if run.source_zero_return is not None:
                diagnostic = np.asarray(run.source_zero_return, dtype=np.uint8)
        elif kind == "beam":
            control = FairLegController(self._controller_h, syndrome, error_rate=0.1, config=spec, prior_llrs=prior)
            run = control.run_beam(control.initial_bp())
            selected, diagnostic = run.candidate, run.initial.candidate
        elif kind == "relay":
            kernel = BinarySpaKernel(update_rule=MinSumUpdate()) if spec.memory_tuning is not None else self._kernel
            run = RelayController(memory_bindings=spec.memory_bindings, numerical_profile=kernel.profile.profile_id,
                                  memory_tuning=spec.memory_tuning).run(
                edge_table=self.table, check_matrix=self._h, syndrome=syndrome, kernel=kernel,
                error_rate=0.1, prior_llrs=prior, legs=spec.legs, budgets=tree, scope="attempt",
                lineage_prefix=identity, solution_limit=spec.solution_limit, transfer=spec.transfer,
                sample_seed_identity=identity)
            selected, diagnostic = run.candidate, run.legs[-1].candidate
        else:
            classes = {"impulse": ImpulseController, "freezing": FreezingController,
                       "syndrome_flip": SyndromeFlipController, "sign_flip": SignFlipController,
                       "restart_belief": RestartController}
            run = classes[kind](spec).run(original, error_rate=0.1, prior_llrs=prior, budgets=tree,
                                          damping_gamma=self._policy.damping_gamma)
            selected = run.selected_candidate
            for attr in ("baseline_diagnostic_candidate", "baseline_candidate", "root_candidate"):
                if hasattr(run, attr):
                    diagnostic = np.asarray(getattr(run, attr), dtype=np.uint8)
                    break
        detail = dict(backend="scalar", controller=kind, receipt=evidence(run),
                      selection_succeeded=selected is not None,
                      failure_output="controller_diagnostic_else_prior_decision",
                      iteration_unit="committed_bp_sweep_or_local_unit")
        if decision is not None:
            detail["vote_decision"] = decision.as_evidence()
            detail["vote_work"] = evidence(WorkVector.zero() if decision.vote is None else WorkVector(
                candidate_constructions=1, original_checks=1, candidate_checks=self.table.variable_count,
                ranking_scans=self.table.variable_count * len(decision.ballots)))
        if kind == "relay":
            count = sum(leg.iterations for leg in run.legs)
        elif kind == "beam":
            count = run.initial.iterations + sum(unit.segment.iterations for unit in run.units if unit.segment is not None)
        elif kind == "mbbp":
            count = run.work.candidate_constructions
        else:
            count = sum(work.convergence_checks for _, _, work in run.leaves)
        return np.asarray(diagnostic if selected is None else selected, dtype=np.uint8), int(count), detail


def _times(work, count):
    return WorkVector(**{f.name: getattr(work, f.name) * count for f in fields(work)})
