"""External native binary BP reference adapter."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from ldpc import BpDecoder


@dataclass(frozen=True)
class NativeResult:
    candidate: np.ndarray
    converged: bool
    iterations: int
    edge_updates: None = None
    edge_updates_missing_reason: str = "ldpc.BpDecoder does not expose edge-update counts"


def _binary_uint8(value: np.ndarray, *, name: str) -> np.ndarray:
    array = np.asarray(value)
    if array.dtype.kind not in {"b", "i", "u"}:
        raise ValueError(f"{name} must have a binary integer or bool dtype")
    if np.any((array != 0) & (array != 1)):
        raise ValueError(f"{name} must contain only binary values")
    return array.astype(np.uint8, copy=False)


def decode(
    check_matrix: np.ndarray,
    syndrome: np.ndarray,
    *,
    error_rate: float,
    max_iter: int,
    bp_method: str = "product_sum",
    schedule: str = "parallel",
    input_vector_type: str = "syndrome",
) -> NativeResult:
    """Decode only visible checks/syndrome/prior; hidden truth is excluded."""
    raw_h, raw_s = np.asarray(check_matrix), np.asarray(syndrome)
    if raw_h.ndim != 2 or raw_s.shape != (raw_h.shape[0],):
        raise ValueError("check matrix and syndrome dimensions disagree")
    h = _binary_uint8(raw_h, name="check matrix")
    s = _binary_uint8(raw_s, name="syndrome")
    if bp_method != "product_sum" or schedule != "parallel" or input_vector_type != "syndrome":
        raise ValueError("unsupported pinned native BP settings")
    if max_iter < 1 or not 0 <= error_rate <= 1:
        raise ValueError("invalid native BP budget or prior")
    decoder = BpDecoder(
        h, bp_method=bp_method, schedule=schedule,
        input_vector_type=input_vector_type, max_iter=max_iter,
        error_rate=error_rate,
    )
    raw_candidate = np.asarray(decoder.decode(s))
    if raw_candidate.shape != (h.shape[1],):
        raise RuntimeError("native reference returned wrong candidate shape")
    candidate = _binary_uint8(raw_candidate, name="native candidate")
    return NativeResult(candidate, bool(decoder.converge), int(decoder.iter))


class NativeBpReference:
    decode = staticmethod(decode)
