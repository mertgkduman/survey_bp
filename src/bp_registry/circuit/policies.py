"""Versioned fault-space policies using the canonical binary execution machinery.

These are circuit adaptations, not claims to reproduce a paper's circuit curves.
The controller never receives sampled faults or logical truth.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Literal
from uuid import uuid4

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator
import sinter
import stim
from scipy.sparse import csr_matrix

from bp_registry.canonical.budgets import BudgetTree
from bp_registry.canonical.contracts import MemoryCompositionSpec, MemoryBindingV4, RelayLegSpec
from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.memory_execution import MemoryFloodingSchedule, validate_single_attempt_memory
from bp_registry.canonical.relay import RelayController
from bp_registry.canonical.schedules import FloodingSchedule
from bp_registry.canonical.updates import MinSumUpdate, NormalizedMinSumUpdate, OffsetMinSumUpdate, ParameterAssignment
from bp_registry.compiled_contracts import immutable_array
from bp_registry.batch_records import encode_records, validate_records, write_records, read_records
from .dem import DemBinaryModel


def _json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


class CircuitPolicy(BaseModel):
    """Closed opt-in contract; finite interventions reset all attempt histories."""
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, allow_inf_nan=False)
    version: Literal["circuit-policy-v1"] = "circuit-policy-v1"
    backend: Literal["auto", "scalar", "compiled"] = "auto"
    rule: Literal["spa", "min_sum", "normalized_min_sum", "offset_min_sum"] = "spa"
    max_iterations: int = Field(default=30, ge=0, le=100_000)
    parameter: float = Field(default=1.0, ge=0.0)
    memory: MemoryCompositionSpec | None = None
    controller: Literal["single", "relay", "guided", "beam"] = "single"
    max_attempts: int = Field(default=1, ge=1, le=10_000)
    beam_width: int = Field(default=1, ge=1, le=1_000)
    bias: float = Field(default=20.0, gt=0.0)
    relay_alpha: float = Field(default=0.5, ge=0.0, le=1.0)
    solution_limit: int = Field(default=1, ge=1, le=10_000)

    @model_validator(mode="after")
    def supported(self):
        if self.memory is not None:
            validate_single_attempt_memory(self.memory, schedule="flooding")
        if self.controller == "relay" and (self.memory is not None or self.max_iterations == 0):
            raise ValueError("Relay requires positive sweeps and its own leg memory; ordinary memory is unsupported")
        if self.backend == "compiled" and (self.memory is not None or self.controller == "relay"):
            raise ValueError("compiled circuit execution supports ordinary attempts without memory or Relay")
        if self.controller == "single" and self.max_attempts != 1:
            raise ValueError("single controller requires max_attempts=1")
        if self.controller != "beam" and self.beam_width != 1:
            raise ValueError("beam_width applies only to beam search")
        if self.controller != "relay" and self.solution_limit != 1:
            raise ValueError("solution_limit applies only to Relay")
        if self.controller != "relay" and self.relay_alpha != 0.5:
            raise ValueError("relay_alpha applies only to Relay")
        if self.controller not in {"guided", "beam"} and self.bias != 20.0:
            raise ValueError("bias applies only to guided or beam search")
        if self.rule in {"spa", "min_sum"} and self.parameter != 1.0:
            raise ValueError("parameter applies only to normalized or offset min-sum")
        return self

    def kernel(self):
        assignment = ParameterAssignment(shape="scalar", value=self.parameter)
        update = {"spa": lambda: None, "min_sum": MinSumUpdate,
                  "normalized_min_sum": lambda: NormalizedMinSumUpdate(assignment),
                  "offset_min_sum": lambda: OffsetMinSumUpdate(assignment)}[self.rule]()
        return BinarySpaKernel(update_rule=update)


@dataclass(frozen=True)
class CircuitBatchResult:
    predictions: np.ndarray
    faults: np.ndarray
    converged: np.ndarray
    iterations: np.ndarray
    ledger_json: str

    def __post_init__(self):
        records = validate_records(self.ledger_json, "circuit-policy-ledger-v1")
        normalized = {}
        for name, key, dtype, rank in (("predictions", "prediction", np.uint8, 2),
                                      ("faults", "faults", np.uint8, 2),
                                      ("converged", "converged", np.bool_, 1),
                                      ("iterations", "iterations", np.int64, 1)):
            value = np.asarray(getattr(self, name))
            if value.ndim != rank or value.shape[0] != len(records) - 1:
                raise ValueError(f"circuit result {name} has invalid dimensions")
            if name in {"predictions", "faults"}:
                valid = (value.dtype.kind in "biu" and not np.any((value != 0) & (value != 1)))
            elif name == "converged":
                valid = value.dtype == np.bool_
            else:
                valid = (value.dtype.kind in "iu" and not np.any(value < 0)
                         and not np.any(value > np.iinfo(np.int64).max))
            if not valid:
                raise ValueError(f"circuit result {name} has invalid execution values")
            # Conversion is now lossless. Bind the owned execution state, not
            # caller values that could wrap or truncate when stored.
            normalized[name] = immutable_array(value, dtype)
            if normalized[name].tolist() != [row[key] for row in records[1:]]:
                raise ValueError("circuit result arrays disagree with bound ledger")
        for name, value in normalized.items():
            object.__setattr__(self, name, value)

    @property
    def ledger(self):
        return json.loads(self.ledger_json)

    def write_ledger(self, path: str | Path):
        write_records(path, self.ledger_json, "circuit-policy-ledger-v1")


@dataclass(frozen=True)
class PolicyBpSinterDecoder(sinter.Decoder):
    policy: CircuitPolicy = field(default_factory=CircuitPolicy)
    ledger_directory: str | None = None

    def __post_init__(self):
        if not isinstance(self.policy, CircuitPolicy):
            raise ValueError("policy must be a CircuitPolicy")
        if self.ledger_directory is not None and (type(self.ledger_directory) is not str or not self.ledger_directory):
            raise ValueError("ledger_directory must be a nonempty path string")
        # Nested parameter dictionaries must not alias caller-owned state.
        object.__setattr__(self, "policy", CircuitPolicy.model_validate_json(self.policy.model_dump_json()))

    def compile_decoder_for_dem(self, *, dem: stim.DetectorErrorModel):
        return CompiledPolicyBpDecoder(DemBinaryModel.from_dem(dem), self.policy, self.ledger_directory)


class CompiledPolicyBpDecoder(sinter.CompiledDecoder):
    def __init__(self, model: DemBinaryModel, policy: CircuitPolicy, ledger_directory: str | None = None):
        if not isinstance(model, DemBinaryModel) or not isinstance(policy, CircuitPolicy):
            raise ValueError("validated DEM and CircuitPolicy required")
        self._model = model
        self._policy_json = policy.model_dump_json()
        self._ledger_directory = ledger_directory
        if ledger_directory is not None:
            Path(ledger_directory).mkdir(parents=True, exist_ok=True)
        self._h = csr_matrix((np.ones(model.table.edge_count, np.uint8), model.variables, model.row_ptr),
                             shape=(model.table.check_count, model.table.variable_count))

    @property
    def model(self):
        return self._model

    @property
    def policy(self):
        return CircuitPolicy.model_validate_json(self._policy_json)

    def _attempt(self, syndrome, prior, kernel, policy):
        if policy.backend != "scalar" and policy.memory is None:
            from .policy_compiled import decode_attempt
            rule = {"spa": 0, "min_sum": 1, "normalized_min_sum": 2, "offset_min_sum": 3}[policy.rule]
            candidate, posterior, iterations, valid = decode_attempt(
                self.model.row_ptr, self.model.variables, prior, syndrome, policy.max_iterations, rule, policy.parameter)
            return candidate, posterior, iterations, valid, None
        schedule = (FloodingSchedule(self.model.table, kernel=kernel) if policy.memory is None else
                    MemoryFloodingSchedule(self.model.table, kernel=kernel, memory=policy.memory))
        messages = schedule.initialize(0.5, prior_llrs=prior)
        posterior = np.array(prior, copy=True)
        candidate = kernel.candidate_from_beliefs(posterior)
        iterations = 0
        # Explicit initial-MAP shortcut applies to every new fault-space attempt.
        valid = bool(np.array_equal((self._h @ candidate) % 2, syndrome))
        while not valid and iterations < policy.max_iterations:
            kwargs = {} if policy.memory is not None else {"prior_llrs": prior}
            sweep = schedule.sweep(messages, syndrome, error_rate=0.5, source_iteration=iterations, **kwargs)
            if policy.memory is not None:
                schedule.commit(sweep)
            messages, posterior, candidate = sweep.new_v2c, sweep.beliefs, sweep.candidate
            iterations += 1
            valid = bool(np.array_equal((self._h @ candidate) % 2, syndrome))
        memory = schedule.evidence() if policy.memory is not None else None
        return candidate, posterior, iterations, valid, memory

    def _shot(self, syndrome, index, policy, kernel):
        base = self.model.prior_llrs
        records = []
        if policy.controller == "relay" and len(base):
            binding = MemoryBindingV4(binding_id="circuit-relay", kind="affine_prior", target="prior",
                                      order=0, alpha=policy.relay_alpha, state_lifetime="leg")
            run = RelayController(memory_bindings=(binding,), numerical_profile=kernel.profile.profile_id).run(
                edge_table=self.model.table, check_matrix=self._h, syndrome=syndrome, kernel=kernel,
                error_rate=0.5, prior_llrs=base,
                legs=tuple(RelayLegSpec(max_iterations=policy.max_iterations) for _ in range(policy.max_attempts)),
                budgets=BudgetTree(limits=()), scope="shot", lineage_prefix=f"circuit:{index}",
                solution_limit=policy.solution_limit)
            for leg in run.legs:
                records.append({"attempt": leg.leg_index, "parent": leg.leg_index - 1 if leg.leg_index else None,
                                "candidate": leg.candidate.tolist(), "posterior": leg.posterior.tolist(),
                                "iterations": leg.iterations, "converged": leg.converged})
            # Existing Relay selects only valid candidates; explicitly expose a
            # deterministic last-leg failure output if it finds no solution.
            selected = run.candidate
            if selected is None:
                selected = run.legs[-1].candidate
            return selected, records, {"work_leaves": run.work_leaves, "termination": run.stopping_reason}
        pending = [(base.copy(), (), None)]
        outputs = []
        while pending and len(records) < policy.max_attempts:
            layer = []
            for prior, fixed, parent in pending:
                if len(records) >= policy.max_attempts:
                    break
                candidate, posterior, iterations, valid, memory = self._attempt(syndrome, prior, kernel, policy)
                attempt = len(records)
                score = (int(np.count_nonzero((self._h @ candidate) % 2 != syndrome)),
                         float(np.dot(candidate.astype(float), base)), attempt)
                records.append({"attempt": attempt, "parent": parent, "fixed": list(fixed),
                                "prior": prior.tolist(), "candidate": candidate.tolist(),
                                "posterior": posterior.tolist(), "iterations": iterations,
                                "converged": valid, "memory": memory,
                                "work": {"c2v": iterations * self.model.table.edge_count,
                                         "v2c": iterations * self.model.table.edge_count,
                                         "candidate_checks": iterations + 1}})
                outputs.append((score, candidate))
                layer.append((score, posterior, prior, fixed, attempt))
            if any(score[0] == 0 for score, _ in outputs) or policy.controller == "single":
                break
            pending = []
            if policy.controller not in {"guided", "beam"}:
                break
            for _, posterior, prior, fixed, parent in sorted(layer, key=lambda item: item[0])[:policy.beam_width]:
                eligible = [v for v in range(len(base)) if v not in fixed]
                if not eligible:
                    continue
                # Guided commits the most reliable remaining marginal; beam
                # branches both signs of the least reliable. Stable ID ties.
                target = min(eligible, key=lambda v: ((-1 if policy.controller == "guided" else 1) * abs(posterior[v]), v))
                signs = (1 if posterior[target] >= 0 else -1,) if policy.controller == "guided" else (1, -1)
                for sign in signs:
                    changed = prior.copy()
                    changed[target] = sign * policy.bias
                    pending.append((changed, (*fixed, target), parent))
        return min(outputs, key=lambda item: item[0])[1], records, {"termination": "bounded_search"}

    def decode_detailed(self, detection_events):
        events = np.asarray(detection_events)
        if (events.ndim != 2 or events.shape[1] != self.model.table.check_count or
                not (events.dtype == np.bool_ or np.issubdtype(events.dtype, np.integer)) or
                np.any((events != 0) & (events != 1))):
            raise ValueError("detection_events must be a binary shot-by-detector matrix")
        events = np.array(events, dtype=np.uint8, order="C", copy=True)
        policy, kernel = self.policy, self.policy.kernel()
        faults = np.empty((len(events), self.model.table.variable_count), dtype=np.uint8)
        predictions = np.empty((len(events), len(self.model.observable_bias)), dtype=np.uint8)
        valid, iterations = np.empty(len(events), bool), np.empty(len(events), np.int64)
        ledger = [{"schema": "circuit-policy-ledger-v1", "model_sha256": self.model.execution_sha256,
                   "policy": policy.model_dump(mode="json"), "numerical_profile": kernel.profile.profile_id,
                   "input_sha256": sha256(events.tobytes()).hexdigest(), "input_shape": list(events.shape),
                   "source_status": "canonical_circuit_adaptation",
                   "execution_backend": "numba-cpu" if policy.backend != "scalar" and policy.memory is None
                   and policy.controller != "relay" else "canonical-python"}]
        for index, event in enumerate(events):
            syndrome = event ^ self.model.syndrome_bias
            candidate, attempts, control = self._shot(syndrome, index, policy, kernel)
            faults[index] = candidate
            predictions[index] = (self.model.observable_matrix @ candidate) % 2 ^ self.model.observable_bias
            valid[index] = np.array_equal((self._h @ candidate) % 2, syndrome)
            iterations[index] = sum(record["iterations"] for record in attempts)
            ledger.append({"shot": index, "detectors": event.tolist(), "faults": candidate.tolist(),
                           "prediction": predictions[index].tolist(), "converged": bool(valid[index]),
                           "iterations": int(iterations[index]), "attempts": attempts, "control": control})
        return CircuitBatchResult(predictions, faults, valid, iterations, encode_records(ledger))

    def decode_shots_bit_packed(self, *, bit_packed_detection_event_data):
        packed = np.asarray(bit_packed_detection_event_data)
        m = self.model.table.check_count
        if packed.dtype != np.uint8 or packed.ndim != 2 or packed.shape[1] != (m + 7) // 8:
            raise ValueError("packed detection data must be uint8 with one row per shot")
        result = self.decode_detailed(np.unpackbits(packed, axis=1, bitorder="little", count=m))
        if self._ledger_directory is not None:
            result.write_ledger(Path(self._ledger_directory) / f"{self.model.execution_sha256}-{uuid4().hex}.jsonl")
        return np.packbits(result.predictions, axis=1, bitorder="little")

    def verify_ledger(self, path: str | Path):
        records = read_records(path, "circuit-policy-ledger-v1")
        if not records or records[0].get("input_shape") != [len(records) - 1, self.model.table.check_count]:
            raise ValueError("invalid circuit ledger dimensions")
        events = np.asarray([row["detectors"] for row in records[1:]], dtype=np.uint8).reshape(records[0]["input_shape"])
        if _json(records) != self.decode_detailed(events).ledger_json:
            raise ValueError("circuit ledger does not match independent replay")
        return {"verified": True, "shots": len(events), "model_sha256": self.model.execution_sha256}
