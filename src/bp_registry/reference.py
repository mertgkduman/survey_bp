"""External native binary BP reference adapter."""

from __future__ import annotations

from dataclasses import dataclass
import numpy as np
from ldpc import BpDecoder

from .canonical.metrics import MetricFact, unavailable_metric


_EDGE_UPDATES_UNAVAILABLE = "ldpc.BpDecoder does not expose edge-update counts"
_CONTROL_FLOW_UNAVAILABLE = "ldpc.BpDecoder does not expose internal control-flow event counts"


@dataclass(frozen=True)
class NativeResult:
    candidate: np.ndarray
    converged: bool
    iterations: int
    metric_facts: tuple[MetricFact, ...] = ()

    def __post_init__(self) -> None:
        if isinstance(self.iterations, bool) or not isinstance(self.iterations, int) or self.iterations < 0:
            raise ValueError("native iterations must be a nonnegative integer")
        facts = self.metric_facts or (
            MetricFact.observed(
                "native_iterations", self.iterations, method="ldpc.BpDecoder.iter",
                scope="native_decoder_call", unit="native_iterations",
                qualification="public_sdk_counter",
            ),
            unavailable_metric(
                "native_edge_updates", method="ldpc.BpDecoder",
                scope="native_decoder_call", unit="edge_messages",
                qualification="opaque_native_internal", reason=_EDGE_UPDATES_UNAVAILABLE,
            ),
            unavailable_metric(
                "native_control_flow_events", method="ldpc.BpDecoder",
                scope="native_decoder_call", unit="events",
                qualification="opaque_native_internal", reason=_CONTROL_FLOW_UNAVAILABLE,
            ),
        )
        if not all(isinstance(fact, MetricFact) for fact in facts):
            raise ValueError("native metric facts must be MetricFact values")
        by_metric = {fact.metric: fact for fact in facts}
        if len(by_metric) != len(facts) or set(by_metric) != {
            "native_iterations", "native_edge_updates", "native_control_flow_events",
        }:
            raise ValueError("native metric facts must describe iterations and opaque internals exactly once")
        iteration = by_metric["native_iterations"]
        if iteration.value != self.iterations or iteration.missingness.value != "observed":
            raise ValueError("native iterations must remain an observed SDK fact")
        for metric in ("native_edge_updates", "native_control_flow_events"):
            if by_metric[metric].missingness.value != "unavailable":
                raise ValueError(f"native {metric} must remain unavailable without SDK instrumentation")
        object.__setattr__(self, "metric_facts", tuple(facts))

    def metric(self, name: str) -> MetricFact:
        for fact in self.metric_facts:
            if fact.metric == name:
                return fact
        raise KeyError(name)

    @property
    def edge_updates(self) -> None:
        """Compatibility view: opaque native edge work is explicitly unavailable."""
        return None

    @property
    def edge_updates_missing_reason(self) -> str:
        return self.metric("native_edge_updates").unavailable_reason or _EDGE_UPDATES_UNAVAILABLE


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
