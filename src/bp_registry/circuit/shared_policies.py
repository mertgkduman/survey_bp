"""Stim/Sinter transport for the shared canonical binary policy decoder."""
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

import numpy as np
import sinter

from bp_registry.canonical.policy_decoder import BinaryPolicy, BinaryPolicyDecoder, canonical_json
from bp_registry.batch_records import encode_records, read_records
from .dem import DemBinaryModel
from .policies import CircuitBatchResult


class SharedCircuitBatchResult(CircuitBatchResult):
    ledger_schema = "circuit-shared-policy-ledger-v1"


@dataclass(frozen=True)
class SharedPolicySinterDecoder(sinter.Decoder):
    """Opt-in shared policies; existing circuit-policy-v1 remains available."""
    policy: BinaryPolicy = field(default_factory=BinaryPolicy)
    ledger_directory: str | None = None

    def __post_init__(self):
        object.__setattr__(self, "policy", BinaryPolicy.model_validate_json(self.policy.model_dump_json()))

    def compile_decoder_for_dem(self, *, dem):
        return SharedCompiledPolicyDecoder(DemBinaryModel.from_dem(dem), self.policy, self.ledger_directory)


class SharedCompiledPolicyDecoder(sinter.CompiledDecoder):
    def __init__(self, model: DemBinaryModel, policy: BinaryPolicy, ledger_directory=None):
        if not isinstance(model, DemBinaryModel):
            raise ValueError("shared circuit execution requires a validated DEM model")
        self._model = model
        self.decoder = BinaryPolicyDecoder(model.table, policy)
        self._ledger_directory = ledger_directory
        if ledger_directory is not None:
            Path(ledger_directory).mkdir(parents=True, exist_ok=True)

    @property
    def model(self):
        return self._model

    def decode_detailed(self, detectors):
        events = np.asarray(detectors)
        m, n = self.model.table.check_count, self.model.table.variable_count
        if (events.ndim != 2 or events.shape[1] != m or events.dtype.kind not in "biu"
                or np.any((events != 0) & (events != 1))):
            raise ValueError("detectors must be a binary shot-by-detector matrix")
        events = np.array(events, dtype=np.uint8, copy=True)
        faults = np.zeros((len(events), n), dtype=np.uint8)
        predictions = np.zeros((len(events), self.model.observable_matrix.shape[0]), dtype=np.uint8)
        valid = np.zeros(len(events), dtype=bool)
        iterations = np.zeros(len(events), dtype=np.int64)
        records = [dict(schema=SharedCircuitBatchResult.ledger_schema,
                        model_sha256=self.model.execution_sha256,
                        policy=self.decoder.policy.model_dump(mode="json"), input_shape=list(events.shape))]
        for index, event in enumerate(events):
            result = self.decoder.decode(event ^ self.model.syndrome_bias, prior_llrs=self.model.prior_llrs,
                                         shot_identity=f"circuit:{index}")
            faults[index], valid[index], iterations[index] = result.candidate, result.converged, result.iterations
            predictions[index] = (self.model.observable_matrix @ result.candidate) % 2 ^ self.model.observable_bias
            records.append(dict(shot=index, detectors=event.tolist(), faults=result.candidate.tolist(),
                                prediction=predictions[index].tolist(), converged=result.converged,
                                iterations=result.iterations, binary_execution=result.ledger))
        return SharedCircuitBatchResult(predictions, faults, valid, iterations, encode_records(records))

    def decode_shots_bit_packed(self, *, bit_packed_detection_event_data):
        packed = np.asarray(bit_packed_detection_event_data)
        m = self.model.table.check_count
        if packed.dtype != np.uint8 or packed.ndim != 2 or packed.shape[1] != (m + 7) // 8:
            raise ValueError("packed detection data must be uint8 with one row per shot")
        result = self.decode_detailed(np.unpackbits(packed, axis=1, bitorder="little", count=m))
        if self._ledger_directory is not None:
            result.write_ledger(Path(self._ledger_directory) / f"{self.model.execution_sha256}-{uuid4().hex}.jsonl")
        return np.packbits(result.predictions, axis=1, bitorder="little")

    def verify_ledger(self, path):
        records = read_records(path, SharedCircuitBatchResult.ledger_schema)
        shape = [len(records) - 1, self.model.table.check_count]
        if records[0].get("input_shape") != shape:
            raise ValueError("invalid circuit ledger dimensions")
        events = np.asarray([row["detectors"] for row in records[1:]]).reshape(shape)
        if not len(events):
            events = events.astype(np.uint8)
        if canonical_json(records) != self.decode_detailed(events).ledger_json:
            raise ValueError("circuit policy ledger does not replay")
        return {"verified": True, "shots": len(events)}
