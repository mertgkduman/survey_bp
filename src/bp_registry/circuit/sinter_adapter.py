"""Sinter wrapper for the canonical binary parity BP circuit projection."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import sinter
import stim

from bp_registry.canonical.numerics import REFERENCE_CPU_F64
from .compiled import _decode_batch
from .dem import DemBinaryModel


def _validate_settings(max_iterations: int, rule: str, tie_break: str) -> None:
    if type(max_iterations) is not int or not 0 <= max_iterations <= np.iinfo(np.int64).max:
        raise ValueError("max_iterations must be a nonnegative int64-range integer")
    if type(rule) is not str or rule not in {"spa", "min_sum"}:
        raise ValueError("rule must be spa or min_sum")
    if type(tie_break) is not str or tie_break not in {"zero", "one"}:
        raise ValueError("tie_break must be zero or one")


@dataclass(frozen=True, slots=True)
class CanonicalBpSinterDecoder(sinter.Decoder):
    """Plain flooding BP on an exact independent-mechanism DEM projection."""

    max_iterations: int = 30
    rule: str = "spa"
    tie_break: str = "zero"

    def __post_init__(self) -> None:
        _validate_settings(self.max_iterations, self.rule, self.tie_break)

    def compile_decoder_for_dem(self, *, dem: stim.DetectorErrorModel) -> "CompiledCanonicalBpDecoder":
        return CompiledCanonicalBpDecoder(DemBinaryModel.from_dem(dem), self.max_iterations, self.rule, self.tie_break)


@dataclass(frozen=True, slots=True)
class CompiledCanonicalBpDecoder(sinter.CompiledDecoder):
    model: DemBinaryModel
    max_iterations: int
    rule: str
    tie_break: str

    def __post_init__(self) -> None:
        if not isinstance(self.model, DemBinaryModel):
            raise ValueError("compiled circuit decoder requires a validated DEM model")
        _validate_settings(self.max_iterations, self.rule, self.tie_break)

    def decode_shots_bit_packed(self, *, bit_packed_detection_event_data: np.ndarray) -> np.ndarray:
        packed = np.asarray(bit_packed_detection_event_data)
        expected_bytes = (self.model.table.check_count + 7) // 8
        if packed.dtype != np.uint8 or packed.ndim != 2 or packed.shape[1] != expected_bytes:
            raise ValueError("packed detection data must be uint8 with one row per shot")
        syndromes = np.unpackbits(packed, axis=1, bitorder="little", count=self.model.table.check_count)
        syndromes = np.ascontiguousarray(syndromes ^ self.model.syndrome_bias, dtype=np.uint8)
        predictions, _converged, _iterations = _decode_batch(
            self.model.row_ptr, self.model.variables, self.model.prior_llrs,
            self.model.observable_matrix, syndromes, REFERENCE_CPU_F64.saturation,
            self.max_iterations, 0 if self.rule == "spa" else 1, self.tie_break == "one",
        )
        predictions ^= self.model.observable_bias
        return np.packbits(predictions, axis=1, bitorder="little")

    def decode_detailed(self, detection_events: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return predictions, convergence, and sweeps for evidence-aware callers."""
        events = np.asarray(detection_events)
        if events.ndim != 2 or events.shape[1] != self.model.table.check_count or np.any((events != 0) & (events != 1)):
            raise ValueError("detection_events must be a binary shot-by-detector matrix")
        syndromes = np.ascontiguousarray(events.astype(np.uint8) ^ self.model.syndrome_bias)
        predictions, converged, iterations = _decode_batch(
            self.model.row_ptr, self.model.variables, self.model.prior_llrs,
            self.model.observable_matrix, syndromes, REFERENCE_CPU_F64.saturation,
            self.max_iterations, 0 if self.rule == "spa" else 1, self.tie_break == "one",
        )
        return predictions ^ self.model.observable_bias, converged.astype(bool), iterations
