"""Strict, portable experiment contract for the reusable research interface.

This contract deliberately describes only the small set of kernels that can be
executed without changing the meaning of a frozen public manifest.  Historical
studies are registered adapters, not alternate spellings of this schema.
"""

from __future__ import annotations

from copy import deepcopy
import json
import math
from pathlib import Path
from typing import Any, Mapping

import numpy as np

from bp_registry.resolution import BpFloodingPolicy
from bp_registry.css import CssCode
from .inputs import input_registry
from .evidence import timing_boundaries


SCHEMA = "research-experiment-v1"
_RESOLUTION_FORMATS = ("float16", "float32", "float64", "int8", "int16", "int32")
_RESOLUTION_SCOPES = ("scalar_edges", "all_messages", "all_state")
_CIRCUIT_RULE_PROFILES = {"spa": "binary-spa-flooding-f64-v1", "min_sum": "binary-min-sum-flooding-f64-v1"}
CLOSED_FIELDS = {
    "experiment": {"schema", "id", "problem", "channel", "decoder", "rate_points", "sampling", "budgets", "provenance"},
    # ``sampling`` is the frozen v1 wire shape.  The companion set is an
    # opt-in extension: absent stopping keys stay absent after validation.
    "sampling": {"seed", "shot_start", "shots"},
    "sampling_with_stopping": {"seed", "shot_start", "shots", "stop_failures", "stop_type_i", "stop_type_ii", "stop_mode", "per_point"},
    "per_point_sampling": {"shots", "stop_failures", "stop_type_i", "stop_type_ii"},
    "budgets": {"max_shots", "max_iterations"},
    "provenance": {"relation", "source_spec_id", "notes"},
    "code_problem": {"kind", "code"}, "circuit_problem": {"kind", "circuit", "dem"},
    "registered_input": {"kind", "id"}, "inline_stim": {"kind", "text"},
    "embedded_css": {"kind", "hx", "hz", "lx", "lz"},
    "channel": {"kind"}, "explicit_channel": {"kind", "probabilities"}, "circuit_channel": {"kind", "noise_sweep"},
    "rate_point": {"physical_p", "decoder_p0"}, "explicit_rate_point": {"decoder_p0"}, "circuit_rate_point": {"label"}, "circuit_sweep_rate_point": {"label", "physical_p"},
    "decoder": {"family", "implementation", "variant", "rule", "numerical_profile", "policy", "schedule", "stop_on_convergence"},
    "circuit_decoder": {"family", "implementation", "rule", "numerical_profile", "schedule", "max_iterations", "tie_break"},
    "qbpgd": {"iterations_per_round", "epsilon", "round_limit"},
    "policy": set(BpFloodingPolicy().as_spec()),
    "resolution": set(BpFloodingPolicy().resolution.as_evidence()),
}


def _object(value: object, name: str, *, keys: set[str]) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != keys:
        actual = sorted(value) if isinstance(value, Mapping) else type(value).__name__
        raise ValueError(f"{name} must contain exactly {sorted(keys)} (got {actual})")
    return dict(value)


def _string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a nonempty string")
    return value


def _number(value: object, name: str, *, lower: float = 0.0, upper: float = 1.0,
            lower_open: bool = False, upper_open: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    result = float(value)
    if not math.isfinite(result) or result < lower or result > upper or (lower_open and result == lower) or (upper_open and result == upper):
        raise ValueError(f"{name} must be in the declared finite range")
    return result


def _positive_int(value: object, name: str, *, allow_zero: bool = False) -> int:
    if type(value) is not int or value < (0 if allow_zero else 1):
        raise ValueError(f"{name} must be a {'nonnegative' if allow_zero else 'positive'} integer")
    return value


def _sampling(value: object) -> dict[str, Any]:
    """Accept frozen v1 sampling or its explicitly opt-in stopping extension."""
    if not isinstance(value, Mapping):
        raise ValueError("sampling must be an object")
    keys = set(value)
    core = CLOSED_FIELDS["sampling"]
    extended = CLOSED_FIELDS["sampling_with_stopping"]
    if keys != core and not (core.issubset(keys) and keys.issubset(extended)):
        raise ValueError(f"sampling must contain frozen v1 fields {sorted(core)}, with optional stopping fields")
    result = dict(value)
    result["seed"] = _positive_int(result["seed"], "sampling.seed", allow_zero=True)
    result["shot_start"] = _positive_int(result["shot_start"], "sampling.shot_start", allow_zero=True)
    if result["shots"] is not None:
        result["shots"] = _positive_int(result["shots"], "sampling.shots")
    for name in ("stop_failures", "stop_type_i", "stop_type_ii"):
        if name in result and result[name] is not None:
            result[name] = _positive_int(result[name], f"sampling.{name}")
    if "stop_mode" in result and result["stop_mode"] not in {"any", "all"}:
        raise ValueError("sampling.stop_mode must be any or all")
    if "per_point" in result:
        if not isinstance(result["per_point"], list) or not result["per_point"]:
            raise ValueError("sampling.per_point must be a nonempty list")
        points = []
        for index, limits in enumerate(result["per_point"]):
            limit = _object(limits, f"sampling.per_point[{index}]", keys=CLOSED_FIELDS["per_point_sampling"])
            for name in CLOSED_FIELDS["per_point_sampling"]:
                if limit[name] is not None:
                    limit[name] = _positive_int(limit[name], f"sampling.per_point[{index}].{name}")
            points.append(limit)
        result["per_point"] = points
    return result


def resolved_sampling(sampling: Mapping[str, object], point_index: int, point_count: int) -> dict[str, Any]:
    """Resolve uniform or complete per-rate limits without silently adding a cap."""
    overrides = sampling.get("per_point")
    if overrides is not None:
        if not isinstance(overrides, list) or len(overrides) != point_count:
            raise ValueError("sampling.per_point must contain one complete limit object per rate point")
        result = dict(overrides[point_index])
    else:
        result = {name: sampling.get(name) for name in CLOSED_FIELDS["per_point_sampling"]}
    result["stop_mode"] = sampling.get("stop_mode", "any")
    if not any(result[name] is not None for name in CLOSED_FIELDS["per_point_sampling"]):
        raise ValueError(f"sampling limits for rate point {point_index} are all empty")
    return result


def sweep_stim_text(text: str, *, source_probability: float, physical_p: float) -> str:
    """Replace an explicitly declared baseline probability in noisy Stim gates.

    Targets, repeat structure, non-noisy instructions, and noisy arguments that
    differ from the declared source value are copied byte-for-semantic-byte by
    Stim.  This avoids a broad text replacement accidentally changing a qubit
    index, repeat count, coordinate, or an intentionally distinct noise term.
    """
    try:
        import stim
    except ImportError as error:
        raise ValueError("circuit probability sweeps require Stim") from error
    circuit = stim.Circuit(text)
    replacements = 0
    def copy_block(block):
        nonlocal replacements
        result = stim.Circuit()
        for instruction in block:
            if isinstance(instruction, stim.CircuitRepeatBlock):
                result.append(stim.CircuitRepeatBlock(instruction.repeat_count, copy_block(instruction.body_copy())))
                continue
            args = instruction.gate_args_copy()
            if stim.gate_data(instruction.name).is_noisy_gate:
                revised = []
                for value in args:
                    if abs(float(value) - source_probability) <= 1e-15:
                        revised.append(physical_p); replacements += 1
                    else:
                        revised.append(value)
                args = revised
            result.append(instruction.name, instruction.targets_copy(), args, tag=instruction.tag)
        return result
    swept = copy_block(circuit)
    if replacements == 0:
        raise ValueError("circuit noise_sweep.source_probability did not match any noisy Stim gate argument")
    return str(swept)


def _policy(value: object, *, rule: str) -> dict[str, Any] | None:
    if value is None:
        return None
    policy = _object(value, "decoder.policy", keys=CLOSED_FIELDS["policy"])
    resolution = _object(policy["resolution"], "decoder.policy.resolution", keys=CLOSED_FIELDS["resolution"])
    if policy["version"] != "bp-flooding-policy-v1" or resolution["version"] != "bp-resolution-v1":
        raise ValueError("decoder.policy uses an unsupported policy or resolution version")
    if policy["check_rule"] != rule:
        raise ValueError("decoder.policy.check_rule must match decoder.rule")
    if resolution["format"] not in _RESOLUTION_FORMATS or resolution["scope"] not in _RESOLUTION_SCOPES:
        raise ValueError("decoder.policy has an unsupported resolution format or scope")
    if resolution["coefficients"] not in {"float64", "same"}:
        raise ValueError("decoder.policy.resolution.coefficients is unsupported")
    integer = resolution["format"].startswith("int")
    if integer:
        _positive_int(resolution["scale"], "decoder.policy.resolution.scale")
    elif resolution["scale"] is not None:
        raise ValueError("floating decoder.policy resolutions must use scale=null")
    policy["damping"] = _number(policy["damping"], "decoder.policy.damping", upper=1.0, upper_open=True)
    policy["alpha"] = _number(policy["alpha"], "decoder.policy.alpha", lower=0.0, lower_open=True, upper=float("inf"))
    policy["beta"] = _number(policy["beta"], "decoder.policy.beta", upper=float("inf"))
    if policy["hard_decision"] not in {"min_llr", "strict_pauli"} or type(policy["zero_syndrome_shortcut"]) is not bool:
        raise ValueError("decoder.policy has an unsupported hard decision or shortcut value")
    # Let the existing closed policy contract reject any subtle incompatible
    # combination.  This is also the source of effective coefficient identity.
    BpFloodingPolicy.from_spec(policy)
    return policy


def _code_reference(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("problem.code must be an object")
    kind = value.get("kind")
    if kind == "registered":
        _string(value.get("id"), "problem.code.id")
        return _object(value, "problem.code", keys=CLOSED_FIELDS["registered_input"])
    if kind == "embedded_css":
        allowed = CLOSED_FIELDS["embedded_css"]
        if not set(value).issubset(allowed) or not {"kind", "hx", "hz"}.issubset(value):
            raise ValueError("embedded CSS code requires kind, hx, hz, and optional paired lx/lz")
        if ("lx" in value) != ("lz" in value):
            raise ValueError("embedded CSS code requires both lx and lz or neither")
        result = deepcopy(dict(value))
        CssCode(
            hx=np.asarray(result["hx"]), hz=np.asarray(result["hz"]),
            lx=None if "lx" not in result else np.asarray(result["lx"]),
            lz=None if "lz" not in result else np.asarray(result["lz"]),
        ).validate()
        return result
    raise ValueError("problem.code.kind must be registered or embedded_css")


def _decoder(value: object, *, problem_kind: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError("decoder must be an object")
    family = value.get("family")
    if problem_kind == "circuit":
        decoder = _object(value, "decoder", keys=CLOSED_FIELDS["circuit_decoder"])
        if (family != "circuit_dem_bp" or decoder["implementation"] != "canonical_sinter"
                or decoder["rule"] not in {"spa", "min_sum"} or decoder["schedule"] != "flooding"
                or decoder["numerical_profile"] != _CIRCUIT_RULE_PROFILES.get(decoder["rule"])
                or decoder["tie_break"] not in {"zero", "one"}):
            raise ValueError("only the pinned v1 plain flooding circuit adapter is supported")
        decoder["max_iterations"] = _positive_int(decoder["max_iterations"], "decoder.max_iterations", allow_zero=True)
        return decoder
    common = CLOSED_FIELDS["decoder"]
    if family == "binary_css":
        decoder = _object(value, "decoder", keys=common)
        if (decoder["implementation"] != "compiled" or decoder["variant"] != "plain" or decoder["schedule"] != "flooding"
                or decoder["rule"] not in {"sum_product", "min_sum"}
                or decoder["numerical_profile"] not in {"binary-spa-flooding-f64-v1", "binary-spa-flooding-f64-v2"}):
            raise ValueError("custom binary execution supports only plain compiled flooding profiles")
    elif family == "bp4":
        keys = common | ({"qbpgd"} if value.get("variant") == "qbpgd" else set())
        decoder = _object(value, "decoder", keys=keys)
        if (decoder["implementation"] != "compiled" or decoder["variant"] not in {"plain", "qbpgd"}
                or decoder["schedule"] != "flooding" or decoder["rule"] not in {"sum_product", "min_sum"}
                or decoder["numerical_profile"] not in {"quaternary-bp4-f64-v1", "quaternary-bp4-f64-v2"}):
            raise ValueError("custom BP4 execution supports only compiled flooding profiles or Q-BPGD")
        if decoder["variant"] == "qbpgd":
            qbpgd = _object(decoder["qbpgd"], "decoder.qbpgd", keys=CLOSED_FIELDS["qbpgd"])
            qbpgd["iterations_per_round"] = _positive_int(qbpgd["iterations_per_round"], "decoder.qbpgd.iterations_per_round")
            qbpgd["epsilon"] = _number(qbpgd["epsilon"], "decoder.qbpgd.epsilon", lower=0.0, lower_open=True, upper=1.0, upper_open=True)
            qbpgd["round_limit"] = _positive_int(qbpgd["round_limit"], "decoder.qbpgd.round_limit")
            decoder["qbpgd"] = qbpgd
    else:
        raise ValueError("unsupported decoder family")
    if type(decoder["stop_on_convergence"]) is not bool:
        raise ValueError("decoder.stop_on_convergence must be boolean")
    decoder["policy"] = _policy(decoder["policy"], rule=decoder["rule"])
    if family == "binary_css" and decoder["rule"] == "min_sum" and decoder["policy"] is None:
        raise ValueError("Custom binary min_sum requires an explicit v2 numerical policy overlay")
    if family == "binary_css" and decoder["stop_on_convergence"] is not True:
        raise ValueError("compiled binary flooding only supports stop_on_convergence=true")
    if family == "binary_css" and decoder["policy"] is not None and decoder["policy"]["hard_decision"] != "min_llr":
        raise ValueError("binary flooding cannot use the BP4-only strict_pauli hard decision")
    if family == "binary_css" and decoder["rule"] == "min_sum" and decoder["policy"] is None:
        raise ValueError("custom binary min-sum requires an explicit flooding policy; no implicit resolution is substituted")
    if decoder["policy"] is not None and not decoder["numerical_profile"].endswith("-v2"):
        raise ValueError("a flooding resolution policy requires the unbounded v2 numerical profile")
    if decoder["rule"] == "min_sum" and decoder["policy"] is None and not decoder["numerical_profile"].endswith("-v2"):
        raise ValueError("plain compiled min-sum needs its explicit v2 policy; frozen v1 support is sum-product only")
    if decoder["variant"] == "qbpgd" and decoder["numerical_profile"] != "quaternary-bp4-f64-v2":
        raise ValueError("Q-BPGD requires the quaternary v2 numerical profile")
    if decoder["variant"] == "qbpgd" and decoder["stop_on_convergence"] is not True:
        raise ValueError("compiled Q-BPGD has fixed first-valid stopping")
    return decoder


def _rate_points(value: object, *, channel_kind: str, circuit: bool = False) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise ValueError("rate_points must be a nonempty list")
    points: list[dict[str, Any]] = []
    for index, row in enumerate(value):
        if circuit:
            if not isinstance(row, Mapping):
                raise ValueError(f"rate_points[{index}] must be an object")
            keys = CLOSED_FIELDS["circuit_sweep_rate_point"] if "physical_p" in row else CLOSED_FIELDS["circuit_rate_point"]
            point = _object(row, f"rate_points[{index}]", keys=keys)
            point["label"] = _string(point["label"], f"rate_points[{index}].label")
            if "physical_p" in point:
                point["physical_p"] = _number(point["physical_p"], f"rate_points[{index}].physical_p")
            points.append(point)
            continue
        keys = CLOSED_FIELDS["explicit_rate_point"] if channel_kind == "explicit" else CLOSED_FIELDS["rate_point"]
        point = _object(row, f"rate_points[{index}]", keys=keys)
        point["decoder_p0"] = _number(point["decoder_p0"], f"rate_points[{index}].decoder_p0", lower=0.0, lower_open=True, upper=1.0, upper_open=True)
        if "physical_p" in point:
            point["physical_p"] = _number(point["physical_p"], f"rate_points[{index}].physical_p")
        points.append(point)
    return points


def interface_contract() -> dict[str, object]:
    """Machine-readable defaults, enums, and cross-field admission rules for UI clients."""
    # Kept in the contract so browser-side sweep previews share the same
    # conservative gate boundary as the executable path.  Stim remains the
    # parser/validator; the static UI never claims a text edit is a run.
    noisy_gates = ["DEPOLARIZE1", "DEPOLARIZE2", "E", "ELSE_CORRELATED_ERROR", "HERALDED_ERASE", "HERALDED_PAULI_CHANNEL_1", "M", "MR", "MX", "MXR", "MY", "MYR", "MZ", "MZZ", "PAULI_CHANNEL_1", "PAULI_CHANNEL_2", "X_ERROR", "Y_ERROR", "Z_ERROR"]
    try:
        import stim
        noisy_gates = sorted({alias for gate in stim.gate_data().values() if gate.is_noisy_gate for alias in gate.aliases})
    except (ImportError, AttributeError):
        pass
    return {
        "timing_boundaries": {kind: timing_boundaries(kind) for kind in ("css_code_capacity", "pauli_code_capacity", "circuit")},
        "schema": SCHEMA,
        "field_sets": {name: sorted(fields) for name, fields in CLOSED_FIELDS.items()},
        "profiles": {"binary_css": ["binary-spa-flooding-f64-v1", "binary-spa-flooding-f64-v2"],
                     "bp4": ["quaternary-bp4-f64-v1", "quaternary-bp4-f64-v2"],
                     "circuit_dem_bp": ["binary-spa-flooding-f64-v1", "binary-min-sum-flooding-f64-v1"]},
        "decoder_families": ["binary_css", "bp4", "circuit_dem_bp"],
        "code_kinds": ["registered", "embedded_css"],
        "registered_code_ids": [row["code_id"] for row in input_registry()["codes"] if row["execution"]["kind"] != "unsupported"],
        "registered_code_aliases": {alias: row["code_id"] for row in input_registry()["codes"] for alias in row.get("aliases", [])},
        "registered_circuit_ids": [row["circuit_id"] for row in input_registry()["circuits"]],
        "unsupported_registered_codes": {row["code_id"]: row["execution"]["reason"] for row in input_registry()["codes"] if row["execution"]["kind"] == "unsupported"},
        "channel_kinds": [row["kind"] for row in input_registry()["channels"]],
        "rules": ["sum_product", "min_sum", "spa"],
        "rules_by_family": {"binary_css": ["sum_product", "min_sum"], "bp4": ["sum_product", "min_sum"], "circuit_dem_bp": list(_CIRCUIT_RULE_PROFILES)},
        "circuit_rule_profiles": dict(_CIRCUIT_RULE_PROFILES),
        "stim_noise_sweep": {"argument_match_tolerance": 1e-15, "noisy_gate_names": noisy_gates, "replacement": "every matching noisy-gate argument, including inside REPEAT blocks; no other arguments or targets"},
        "resolution": {"formats": list(_RESOLUTION_FORMATS), "scopes": list(_RESOLUTION_SCOPES), "coefficients": ["float64", "same"]},
        "defaults": {"sampling": {"seed": 0, "shot_start": 0, "shots": 32}, "budgets": {"max_shots": 32, "max_iterations": 30},
                     "binary": {"rule": "sum_product", "numerical_profile": "binary-spa-flooding-f64-v2", "schedule": "flooding", "stop_on_convergence": True},
                     "bp4": {"rule": "sum_product", "numerical_profile": "quaternary-bp4-f64-v2", "schedule": "flooding", "stop_on_convergence": True},
                     "circuit": {"rule": "spa", "numerical_profile": "binary-spa-flooding-f64-v1", "schedule": "flooding", "max_iterations": 30, "tie_break": "zero"}},
        "ui_fields": {"physical_p": {"type": "number", "minimum": 0, "maximum": 1}, "decoder_p0": {"type": "number", "exclusiveMinimum": 0, "exclusiveMaximum": 1},
                      "shots": {"type": ["integer", "null"], "minimum": 1, "scope": "per_rate_point", "null_means": "no_shot_limit"}, "stop_failures": {"type": ["integer", "null"], "minimum": 1, "default": None, "scope": "per_rate_point", "effect": "adaptive_stop"}, "stop_type_i": {"type": ["integer", "null"], "minimum": 1, "default": None, "scope": "per_rate_point", "effect": "adaptive_stop", "families": ["binary_css", "bp4", "circuit_dem_bp"]}, "stop_type_ii": {"type": ["integer", "null"], "minimum": 1, "default": None, "scope": "per_rate_point", "effect": "adaptive_stop", "families": ["binary_css", "bp4", "circuit_dem_bp"]}, "stop_mode": {"enum": ["any", "all"], "default": "any", "all_semantics": "shots is a target; continue until every configured limit is reached"}, "per_point": {"complete_fields": sorted(CLOSED_FIELDS["per_point_sampling"]), "scope": "one complete object per rate point"}, "max_shots": {"type": ["integer", "null"], "minimum": 1, "scope": "legacy_total_hard_ceiling"}, "max_iterations": {"type": "integer", "minimum": 0, "scope": "per_attempt; Q-BPGD total sweeps cap"},
                      "policy": {"version": "bp-flooding-policy-v1", "resolution_version": "bp-resolution-v1", "damping": {"minimum": 0, "exclusiveMaximum": 1}, "alpha": {"exclusiveMinimum": 0}, "beta": {"minimum": 0}}},
        "cross_rule_objects": [
            {"if": {"decoder.family": "circuit_dem_bp", "decoder.rule": rule}, "then": {"decoder.numerical_profile": profile}} for rule, profile in _CIRCUIT_RULE_PROFILES.items()
        ] + [
            {"if": {"decoder.variant": "qbpgd"}, "then": {"decoder.numerical_profile": "quaternary-bp4-f64-v2"}},
            {"if": {"decoder.policy": "non_null"}, "then": {"decoder.numerical_profile": "*_v2", "decoder.policy.check_rule": "decoder.rule"}},
            {"if": {"problem.kind": "circuit"}, "then": {"channel.kind": "embedded_circuit", "rate_points.item": {"label": "string"}, "problem.dem.decompose_errors": False}},
            {"if": {"sampling.stop_failures|sampling.stop_type_i|sampling.stop_type_ii": "non_null"}, "then": {"sampling_mode": "adaptive_stopping", "ci_method": "unavailable_optional_stopping"}},
        ],
        "cross_rules": [
            "custom binary and BP4 execute flooding only; schedules and interventions outside this contract are rejected",
            "Q-BPGD requires v2 and composes its guided-decimation controller with the selected flooding policy; such policy compositions are canonical adaptations unless separately source-qualified",
            "custom circuit uses the v1 Sinter adapter; noise_sweep replaces only declared matching noisy-gate probabilities",
            "physical_p and decoder_p0 are independent and serialized for every rate point",
            "registered historical studies are adapters and are not custom compiled experiments",
        ],
    }


def validate_experiment(spec: object, *, repository: Mapping[str, object] | str | Path | None = None) -> dict[str, Any]:
    """Validate input algebra and the active kernel contract without sampling."""
    try:
        json.dumps(spec, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise ValueError("Portable experiments require JSON-compatible values; convert NumPy arrays to lists") from error
    root = _object(spec, "experiment", keys=CLOSED_FIELDS["experiment"])
    if root["schema"] != SCHEMA:
        raise ValueError(f"experiment.schema must be {SCHEMA}")
    _string(root["id"], "experiment.id")
    problem_value = root["problem"]
    if not isinstance(problem_value, Mapping):
        raise ValueError("problem must be an object")
    kind = problem_value.get("kind")
    if kind in {"css_code_capacity", "pauli_code_capacity"}:
        problem = _object(problem_value, "problem", keys=CLOSED_FIELDS["code_problem"])
        problem["code"] = _code_reference(problem["code"])
        if problem["code"]["kind"] == "registered" and repository is not None:
            value = _repository_value(repository, problem["code"]["id"])
            if isinstance(value, Mapping): value = value.get("code", value.get("value"))
            if not isinstance(value, CssCode): raise ValueError("registered CSS code must resolve to CssCode")
            value.validate()
    elif kind == "circuit":
        problem = _object(problem_value, "problem", keys=CLOSED_FIELDS["circuit_problem"])
        circuit = problem["circuit"]
        if not isinstance(circuit, Mapping) or circuit.get("kind") not in {"inline_stim", "registered"}:
            raise ValueError("circuit must be inline_stim or registered")
        required = CLOSED_FIELDS["inline_stim"] if circuit["kind"] == "inline_stim" else CLOSED_FIELDS["registered_input"]
        problem["circuit"] = _object(circuit, "problem.circuit", keys=required)
        if circuit["kind"] == "registered":
            _string(circuit.get("id"), "problem.circuit.id")
        if circuit["kind"] == "registered" and repository is not None:
            value = _repository_value(repository, circuit["id"])
            if isinstance(value, Mapping): value = value.get("text", value.get("circuit", value.get("value")))
            if not isinstance(value, str) or not value: raise ValueError("registered circuit must resolve to nonempty Stim text")
        problem["dem"] = _object(problem["dem"], "problem.dem", keys={"decompose_errors"})
        if problem["dem"]["decompose_errors"] is not False:
            raise ValueError("circuit DEM extraction is pinned to decompose_errors=false")
    else:
        raise ValueError("problem.kind is unsupported")
    raw_channel = root["channel"]
    channel = _object(raw_channel, "channel", keys=(CLOSED_FIELDS["explicit_channel"] if isinstance(raw_channel, Mapping) and raw_channel.get("kind") == "explicit" else CLOSED_FIELDS["circuit_channel"] if isinstance(raw_channel, Mapping) and raw_channel.get("kind") == "embedded_circuit" and "noise_sweep" in raw_channel else CLOSED_FIELDS["channel"]))
    if channel["kind"] not in {"depolarizing", "x_only", "explicit", "embedded_circuit"}:
        raise ValueError("channel.kind is unsupported")
    if kind == "circuit" and channel["kind"] != "embedded_circuit":
        raise ValueError("circuit sampling is supplied by its Stim text; use channel.kind=embedded_circuit")
    if kind != "circuit" and channel["kind"] == "embedded_circuit":
        raise ValueError("embedded_circuit is only valid for a circuit problem")
    if "noise_sweep" in channel:
        sweep = _object(channel["noise_sweep"], "channel.noise_sweep", keys={"source_probability"})
        sweep["source_probability"] = _number(sweep["source_probability"], "channel.noise_sweep.source_probability", lower=0.0, lower_open=True, upper=1.0, upper_open=True)
        channel["noise_sweep"] = sweep
    decoder = _decoder(root["decoder"], problem_kind=kind)
    if kind == "css_code_capacity" and decoder["family"] != "binary_css":
        raise ValueError("CSS code-capacity needs decoder.family=binary_css")
    if kind == "pauli_code_capacity" and decoder["family"] != "bp4":
        raise ValueError("Pauli code-capacity needs decoder.family=bp4")
    rates = _rate_points(root["rate_points"], channel_kind=channel["kind"], circuit=kind == "circuit")
    sampling = _sampling(root["sampling"])
    budgets = _object(root["budgets"], "budgets", keys=CLOSED_FIELDS["budgets"])
    if budgets["max_shots"] is not None:
        budgets["max_shots"] = _positive_int(budgets["max_shots"], "budgets.max_shots")
    budgets["max_iterations"] = _positive_int(budgets["max_iterations"], "budgets.max_iterations", allow_zero=True)
    if budgets["max_shots"] is not None and sampling["shots"] is not None and len(rates) * sampling["shots"] > budgets["max_shots"]:
        raise ValueError("budgets.max_shots is a total experiment cap; rate points times shots exceeds it")
    if kind != "circuit" and budgets["max_iterations"] == 0:
        raise ValueError("code-capacity execution requires a positive max_iterations budget")
    if kind == "circuit" and decoder["max_iterations"] > budgets["max_iterations"]:
        raise ValueError("decoder.max_iterations exceeds budgets.max_iterations")
    if kind == "circuit" and budgets["max_shots"] is not None and sampling["shots"] is not None and len(rates) * (sampling["shot_start"] + sampling["shots"]) > budgets["max_shots"]:
        raise ValueError("circuit shot_start requires replay/discard and exceeds the total max_shots cap")
    for index in range(len(rates)):
        resolved_sampling(sampling, index, len(rates))
    if kind == "circuit":
        swept = "noise_sweep" in channel
        has_physical = all("physical_p" in point for point in rates)
        if swept != has_physical:
            raise ValueError("circuit noise_sweep requires physical_p at every point, and physical_p requires noise_sweep")
        if not swept and len(rates) != 1:
            raise ValueError("one legacy embedded circuit has one rate point; declare noise_sweep for a circuit sweep")
        labels = [point["label"] for point in rates]
        if len(labels) != len(set(labels)):
            raise ValueError("circuit rate-point labels must be unique")
    if decoder.get("variant") == "qbpgd":
        qbpgd = decoder["qbpgd"]
        assert isinstance(qbpgd, Mapping)
        if qbpgd["iterations_per_round"] * qbpgd["round_limit"] > budgets["max_iterations"]:
            raise ValueError("Q-BPGD iterations_per_round*round_limit exceeds the total max_iterations cap")
    provenance = _object(root["provenance"], "provenance", keys=CLOSED_FIELDS["provenance"])
    if provenance["relation"] not in {"canonical_adaptation", "development_fixture"}:
        raise ValueError("custom portable runs must state canonical_adaptation or development_fixture")
    if provenance["source_spec_id"] is not None:
        _string(provenance["source_spec_id"], "provenance.source_spec_id")
    if provenance["notes"] is not None and not isinstance(provenance["notes"], str):
        raise ValueError("provenance.notes must be a string or null")
    if kind == "circuit":
        reference = problem["circuit"]
        value = reference.get("text") if reference["kind"] == "inline_stim" else _repository_value(repository, reference["id"])
        if isinstance(value, Mapping):
            value = value.get("text", value.get("circuit", value.get("value")))
        if not isinstance(value, str) or not value.strip():
            raise ValueError("circuit.text must be nonempty Stim text")
        try:
            import stim
            from bp_registry.circuit import CanonicalBpSinterDecoder
        except ImportError as error:
            raise ValueError("Circuit validation requires the repository's circuit extra (Stim/Sinter)") from error
        texts = [value] if "noise_sweep" not in channel else [
            sweep_stim_text(value, source_probability=float(channel["noise_sweep"]["source_probability"]), physical_p=float(point["physical_p"]))
            for point in rates
        ]
        adapter = CanonicalBpSinterDecoder(max_iterations=decoder["max_iterations"], rule=decoder["rule"], tie_break=decoder["tie_break"])
        for rate_index, text in enumerate(texts):
            circuit = stim.Circuit(text)
            if circuit.num_observables < 1:
                raise ValueError(f"circuit rate point {rate_index} has no declared observable")
            dem = circuit.detector_error_model(decompose_errors=False)
            adapter.compile_decoder_for_dem(dem=dem)
        if sampling["seed"] >= 2**64:
            raise ValueError("Stim sampling seed must fit uint64")
    else:
        ref = problem["code"]
        if ref["kind"] == "registered":
            value = _repository_value(repository, ref["id"])
            if isinstance(value, Mapping):
                value = value.get("code", value.get("value"))
            if not isinstance(value, CssCode):
                raise ValueError("Registered code must resolve to CssCode")
            code = value.validate()
        else:
            code = CssCode(np.asarray(ref["hx"]), np.asarray(ref["hz"]),
                           None if "lx" not in ref else np.asarray(ref["lx"]),
                           None if "lz" not in ref else np.asarray(ref["lz"])).validate()
        if code.hx.shape[0] == 0 or code.hz.shape[0] == 0:
            raise ValueError("Portable CSS input requires nonempty X and Z check families")
        if np.any(~np.any(code.hx, axis=1)) or np.any(~np.any(code.hz, axis=1)):
            raise ValueError("code-capacity sampling rejects identity-only check rows")
        if channel["kind"] == "explicit":
            from bp_registry.quaternary.sampling import JointPauliChannel
            JointPauliChannel.explicit(channel["probabilities"], n=code.n)
        policy = None if decoder["policy"] is None else BpFloodingPolicy.from_spec(decoder["policy"])
        if decoder["family"] == "bp4":
            from bp_registry.quaternary.compiled import CompiledBp4Graph
            CompiledBp4Graph.from_css(code, rates[0]["decoder_p0"], rule=decoder["rule"], policy=policy)
        else:
            from bp_registry.canonical.compiled import CompiledBinaryFlooding
            from bp_registry.canonical.numerics import BINARY_SPA_F64_V2, REFERENCE_CPU_F64
            rule = "spa" if decoder["rule"] == "sum_product" else "min_sum"
            profile = REFERENCE_CPU_F64 if decoder["numerical_profile"].endswith("-v1") else BINARY_SPA_F64_V2
            CompiledBinaryFlooding.from_check_matrix(code.hz, rule=rule, profile=profile, policy=policy)
            CompiledBinaryFlooding.from_check_matrix(code.hx, rule=rule, profile=profile, policy=policy)
    return {
        "schema": SCHEMA, "id": root["id"], "problem": problem, "channel": channel,
        "decoder": decoder, "rate_points": rates, "sampling": sampling,
        "budgets": budgets, "provenance": provenance,
    }


def _repository_value(repository: Mapping[str, object] | str | Path | object, identifier: str) -> object:
    if callable(repository):
        return repository(identifier)
    if isinstance(repository, Mapping):
        if identifier not in repository: raise ValueError(f"registered input {identifier!r} is unavailable")
        return repository[identifier]
    if repository is None:
        repository = Path(__file__).resolve().parents[3]
    root = Path(repository).expanduser().resolve()
    registry = input_registry(root)
    for row in registry["circuits"]:
        if identifier == row["circuit_id"]:
            identifier = row["path"]
            break
    for row in registry["codes"]:
        if identifier in [row["code_id"], *row.get("aliases", [])]:
            execution = row["execution"]
            if execution["kind"] == "unsupported": raise ValueError(execution["reason"])
            identifier = execution.get("path", execution.get("id"))
            break
    if identifier in {"b2", "c2"}:
        from bp_registry.code_constructions import build_b2_ghp, build_c2_hp
        return build_b2_ghp() if identifier == "b2" else build_c2_hp()
    if identifier in {"double-gross", "double_gross", "double_Gross", "double_Gross_288_12_18"}:
        import importlib.util
        import sys
        source = root / "from_dr_pfister_presentetations/run_reproduction.py"
        module_spec = importlib.util.spec_from_file_location("_portable_double_gross", source)
        if module_spec is None or module_spec.loader is None: raise ValueError("double_gross construction is unavailable")
        module = importlib.util.module_from_spec(module_spec)
        # The retained constructor imports its sibling policy module by name.
        # Resolve that local dependency only for this isolated load; do not
        # make a global repository import-path mutation part of execution.
        added = str(source.parent) not in sys.path
        if added: sys.path.insert(0, str(source.parent))
        try:
            module_spec.loader.exec_module(module)
        finally:
            if added: sys.path.remove(str(source.parent))
        return module.double_gross()
    if identifier == "gb46":
        raise ValueError("gb46 has a retained parity-check artifact but no portable CSS/logical construction for this runner")
    relative = identifier
    target = (root / relative).resolve()
    if not target.is_relative_to(root) or not target.is_file() or target.is_symlink():
        raise ValueError(f"registered input {identifier!r} is unavailable beneath repository")
    if target.suffix == ".stim": return target.read_text(encoding="utf-8")
    if target.suffix in {".json", ".npz"}:
        from bp_registry.artifacts import load_artifact
        return load_artifact(root, target.relative_to(root)).code
    raise ValueError("registered input must be a confined CSS artifact or Stim circuit")


def materialize_experiment(spec: object, repository: Mapping[str, object] | str | Path | object) -> dict[str, Any]:
    """Replace registered code/circuit handles with portable inline data.

    This is intentionally a one-way export seam: an exported package no longer
    depends on a mutable catalog identifier.  The package layer hashes the
    returned JSON bytes along with its own manifest.
    """
    normalized = validate_experiment(spec, repository=repository)
    result = deepcopy(normalized)
    problem = result["problem"]
    if problem["kind"] in {"css_code_capacity", "pauli_code_capacity"} and problem["code"]["kind"] == "registered":
        value = _repository_value(repository, problem["code"]["id"])
        if isinstance(value, Mapping):
            value = value.get("code", value.get("value"))
        try:
            from bp_registry.css import CssCode
            code = value.validate() if isinstance(value, CssCode) else None
        except AttributeError:
            code = None
        if code is None:
            raise ValueError("registered CSS code must resolve to a CssCode or {'code': CssCode}")
        embedded: dict[str, object] = {"kind": "embedded_css", "hx": code.hx.tolist(), "hz": code.hz.tolist()}
        if code.lx is not None and len(code.lx) > 0:
            embedded["lx"] = code.lx.tolist()
            embedded["lz"] = code.lz.tolist()
        problem["code"] = embedded
    if problem["kind"] == "circuit" and problem["circuit"]["kind"] == "registered":
        value = _repository_value(repository, problem["circuit"]["id"])
        if isinstance(value, Mapping):
            value = value.get("text", value.get("circuit", value.get("value")))
        if not isinstance(value, str) or not value:
            raise ValueError("registered circuit must resolve to a nonempty Stim string or {'text': string}")
        problem["circuit"] = {"kind": "inline_stim", "text": value}
    # Revalidate the portable wire representation. The exporter hashes these
    # exact JSON bytes in its own package manifest.
    return validate_experiment(result)


__all__ = ["SCHEMA", "interface_contract", "materialize_experiment", "validate_experiment"]
