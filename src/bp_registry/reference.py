"""External native binary BP reference adapter."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import version
from typing import Any, Callable
import numpy as np
from ldpc import BpDecoder, BpLsdDecoder, BpOsdDecoder

from .canonical.metrics import MetricFact, unavailable_metric


_EDGE_UPDATES_UNAVAILABLE = "ldpc.BpDecoder does not expose edge-update counts"
_CONTROL_FLOW_UNAVAILABLE = "ldpc.BpDecoder does not expose internal control-flow event counts"
_PINNED_LDPC_VERSION = "2.4.1"
_COMPOSITE_IDENTITY_KIND = "native_composite_reference"
_COMPOSITE_INTERNAL_BP_UNAVAILABLE = (
    "ldpc native composite does not expose its internal BP message or fallback work counters"
)


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


@dataclass(frozen=True)
class NativeCompositeResult:
    """Evidence from one opaque BP-plus-reprocessing reference composite."""

    candidate: np.ndarray | None
    bp_candidate: np.ndarray | None
    converged: bool | None
    iterations: int | None
    terminal_status: str
    original_syndrome_valid: bool | None
    observation_identity: str
    identity: dict[str, str]
    constructor_controls: dict[str, Any]
    metric_facts: tuple[MetricFact, ...]
    error_type: str | None = None
    error_message: str | None = None

    def __post_init__(self) -> None:
        if self.terminal_status not in {
            "completed", "invalid_original_syndrome", "malformed_output", "native_error",
        }:
            raise ValueError("unsupported native composite terminal status")
        if not isinstance(self.observation_identity, str) or not self.observation_identity:
            raise ValueError("native composite observation identity must be nonempty")
        if self.identity.get("kind") != _COMPOSITE_IDENTITY_KIND:
            raise ValueError("native composite identity must remain distinct from canonical execution")
        if self.identity.get("package") != "ldpc" or self.identity.get("version") != _PINNED_LDPC_VERSION:
            raise ValueError("native composite identity must retain the exact ldpc pin")
        if self.candidate is not None and self.candidate.dtype != np.uint8:
            raise ValueError("native composite candidate must be binary uint8 evidence")
        if self.bp_candidate is not None and self.bp_candidate.dtype != np.uint8:
            raise ValueError("native composite BP candidate must be binary uint8 evidence")
        if self.terminal_status == "completed" and self.original_syndrome_valid is not True:
            raise ValueError("completed native composite output requires original-syndrome validation")
        if self.terminal_status == "native_error" and not self.error_type:
            raise ValueError("native composite errors require a typed error")
        names = {fact.metric for fact in self.metric_facts}
        if names != {
            "native_iterations", "native_edge_updates", "native_control_flow_events",
            "native_internal_bp_work", "native_fallback_work",
        }:
            raise ValueError("native composite metric facts must retain observed and opaque fields")
        observed = self.metric("native_iterations")
        if self.iterations is None:
            if observed.missingness.value != "unavailable":
                raise ValueError("missing native iterations must remain explicitly unavailable")
        elif observed.value != self.iterations or observed.missingness.value != "observed":
            raise ValueError("native composite iterations must remain an observed SDK fact")
        for name in names - {"native_iterations"}:
            if self.metric(name).missingness.value != "unavailable":
                raise ValueError(f"native composite {name} must remain unavailable without SDK instrumentation")

    def metric(self, name: str) -> MetricFact:
        for fact in self.metric_facts:
            if fact.metric == name:
                return fact
        raise KeyError(name)


def _pinned_ldpc_identity(composite: str) -> dict[str, str]:
    installed = version("ldpc")
    if installed != _PINNED_LDPC_VERSION:
        raise RuntimeError(f"native composite requires ldpc=={_PINNED_LDPC_VERSION}, found {installed}")
    return {
        "kind": _COMPOSITE_IDENTITY_KIND,
        "provider": "quantumgizmos",
        "package": "ldpc",
        "version": installed,
        "composite": composite,
        "includes_internal_bp": "true",
    }


def _validate_composite_controls(
    *, error_rate: float, max_iter: int, bp_method: str, schedule: str,
    input_vector_type: str, controls: dict[str, Any], composite: str,
) -> None:
    if not isinstance(error_rate, (int, float)) or not np.isfinite(error_rate) or not 0 <= error_rate <= 1:
        raise ValueError("native composite error rate must be finite and in [0, 1]")
    if isinstance(max_iter, bool) or not isinstance(max_iter, int) or max_iter < 1:
        raise ValueError("native composite max_iter must be a positive integer")
    if bp_method not in {"product_sum", "minimum_sum"}:
        raise ValueError("unsupported pinned native composite BP method")
    if schedule not in {"parallel", "serial"} or input_vector_type != "syndrome":
        raise ValueError("unsupported pinned native composite schedule or input type")
    method_key = "osd_method" if composite == "BpOsdDecoder" else "lsd_method"
    order_key = "osd_order" if composite == "BpOsdDecoder" else "lsd_order"
    allowed = {"OSD_0", "OSD_E", "OSD_CS"} if composite == "BpOsdDecoder" else {"LSD_0", "LSD_E", "LSD_CS"}
    if controls.get(method_key) not in allowed:
        raise ValueError(f"unsupported pinned native composite {method_key}")
    order = controls.get(order_key)
    if isinstance(order, bool) or not isinstance(order, int) or order < 0:
        raise ValueError(f"native composite {order_key} must be a nonnegative integer")
    if composite == "BpLsdDecoder":
        if isinstance(controls.get("bits_per_step"), bool) or not isinstance(controls.get("bits_per_step"), int) or controls["bits_per_step"] < 1:
            raise ValueError("native composite bits_per_step must be a positive integer")
        if not isinstance(controls.get("always_run_lsd"), bool):
            raise ValueError("native composite always_run_lsd must be boolean")


def _composite_metric_facts(composite: str, iterations: int | None) -> tuple[MetricFact, ...]:
    scope = "native_composite_call"
    if iterations is None:
        iteration = unavailable_metric(
            "native_iterations", method=f"ldpc.{composite}.iter", scope=scope,
            unit="native_iterations", qualification="terminal_not_observed",
            reason="native composite raised before exposing its iteration counter",
        )
    else:
        iteration = MetricFact.observed(
            "native_iterations", iterations, method=f"ldpc.{composite}.iter", scope=scope,
            unit="native_iterations", qualification="public_sdk_counter",
        )
    return (
        iteration,
        unavailable_metric("native_edge_updates", method=f"ldpc.{composite}", scope=scope,
                           unit="edge_messages", qualification="opaque_native_internal",
                           reason=_COMPOSITE_INTERNAL_BP_UNAVAILABLE),
        unavailable_metric("native_control_flow_events", method=f"ldpc.{composite}", scope=scope,
                           unit="events", qualification="opaque_native_internal",
                           reason=_COMPOSITE_INTERNAL_BP_UNAVAILABLE),
        unavailable_metric("native_internal_bp_work", method=f"ldpc.{composite}", scope=scope,
                           unit="work", qualification="opaque_native_internal",
                           reason=_COMPOSITE_INTERNAL_BP_UNAVAILABLE),
        unavailable_metric("native_fallback_work", method=f"ldpc.{composite}", scope=scope,
                           unit="work", qualification="opaque_native_internal",
                           reason=_COMPOSITE_INTERNAL_BP_UNAVAILABLE),
    )


def _native_binary_output(value: object, *, name: str, width: int) -> np.ndarray:
    output = np.asarray(value)
    if output.shape != (width,):
        raise ValueError(f"{name} has wrong candidate shape")
    return _binary_uint8(output, name=name)


def _decode_native_composite(
    decoder_type: Callable[..., Any], *, composite: str, check_matrix: np.ndarray,
    syndrome: np.ndarray, error_rate: float, max_iter: int, bp_method: str,
    schedule: str, input_vector_type: str, observation_identity: str,
    controls: dict[str, Any],
) -> NativeCompositeResult:
    raw_h, raw_s = np.asarray(check_matrix), np.asarray(syndrome)
    if raw_h.ndim != 2 or raw_s.shape != (raw_h.shape[0],):
        raise ValueError("check matrix and syndrome dimensions disagree")
    h = _binary_uint8(raw_h, name="check matrix")
    s = _binary_uint8(raw_s, name="syndrome")
    _validate_composite_controls(
        error_rate=error_rate, max_iter=max_iter, bp_method=bp_method, schedule=schedule,
        input_vector_type=input_vector_type, controls=controls, composite=composite,
    )
    identity = _pinned_ldpc_identity(composite)
    constructor_controls = {
        "error_rate": float(error_rate), "max_iter": max_iter, "bp_method": bp_method,
        "schedule": schedule, "input_vector_type": input_vector_type, **controls,
    }
    try:
        decoder = decoder_type(h, **constructor_controls)
        raw_candidate = decoder.decode(s)
        iterations = int(decoder.iter)
        candidate = _native_binary_output(raw_candidate, name="native composite candidate", width=h.shape[1])
        try:
            bp_candidate = _native_binary_output(
                decoder.bp_decoding, name="native composite BP candidate", width=h.shape[1],
            )
        except (AttributeError, TypeError, ValueError):
            bp_candidate = None
        original_valid = bool(np.array_equal((h @ candidate) % 2, s))
        return NativeCompositeResult(
            candidate=candidate, bp_candidate=bp_candidate, converged=bool(decoder.converge),
            iterations=iterations,
            terminal_status="completed" if original_valid else "invalid_original_syndrome",
            original_syndrome_valid=original_valid, observation_identity=observation_identity,
            identity=identity, constructor_controls=constructor_controls,
            metric_facts=_composite_metric_facts(composite, iterations),
        )
    except (TypeError, ValueError) as exc:
        return NativeCompositeResult(
            candidate=None, bp_candidate=None, converged=None, iterations=None,
            terminal_status="malformed_output", original_syndrome_valid=None,
            observation_identity=observation_identity, identity=identity,
            constructor_controls=constructor_controls,
            metric_facts=_composite_metric_facts(composite, None),
            error_type=type(exc).__name__, error_message=str(exc),
        )
    except Exception as exc:
        return NativeCompositeResult(
            candidate=None, bp_candidate=None, converged=None, iterations=None,
            terminal_status="native_error", original_syndrome_valid=None,
            observation_identity=observation_identity, identity=identity,
            constructor_controls=constructor_controls,
            metric_facts=_composite_metric_facts(composite, None),
            error_type=type(exc).__name__, error_message=str(exc),
        )


def decode_bp_osd(
    check_matrix: np.ndarray, syndrome: np.ndarray, *, error_rate: float, max_iter: int,
    osd_method: str, osd_order: int, observation_identity: str,
    bp_method: str = "product_sum", schedule: str = "parallel",
    input_vector_type: str = "syndrome",
) -> NativeCompositeResult:
    """Run the pinned BP-OSD composite as its own native reference identity."""
    return _decode_native_composite(
        BpOsdDecoder, composite="BpOsdDecoder", check_matrix=check_matrix, syndrome=syndrome,
        error_rate=error_rate, max_iter=max_iter, bp_method=bp_method, schedule=schedule,
        input_vector_type=input_vector_type, observation_identity=observation_identity,
        controls={"osd_method": osd_method, "osd_order": osd_order},
    )


def decode_bp_lsd(
    check_matrix: np.ndarray, syndrome: np.ndarray, *, error_rate: float, max_iter: int,
    lsd_method: str, lsd_order: int, bits_per_step: int, always_run_lsd: bool,
    observation_identity: str, bp_method: str = "product_sum", schedule: str = "parallel",
    input_vector_type: str = "syndrome",
) -> NativeCompositeResult:
    """Run the pinned BP-LSD composite as its own native reference identity."""
    return _decode_native_composite(
        BpLsdDecoder, composite="BpLsdDecoder", check_matrix=check_matrix, syndrome=syndrome,
        error_rate=error_rate, max_iter=max_iter, bp_method=bp_method, schedule=schedule,
        input_vector_type=input_vector_type, observation_identity=observation_identity,
        controls={
            "lsd_method": lsd_method, "lsd_order": lsd_order,
            "bits_per_step": bits_per_step, "always_run_lsd": always_run_lsd,
        },
    )


class NativeBpOsdReference:
    """Pinned ldpc 2.4.1 BP-OSD composite; it is not canonical execution."""

    decode = staticmethod(decode_bp_osd)


class NativeBpLsdReference:
    """Pinned ldpc 2.4.1 BP-LSD composite; it is not canonical execution."""

    decode = staticmethod(decode_bp_lsd)
