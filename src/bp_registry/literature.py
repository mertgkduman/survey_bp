"""Closed, source-grounded decoder policy documents.

Only the seven registered policy roles and their declared numerical controls are
projected into execution.  Paper prose remains immutable request provenance.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import math
from pathlib import Path
from types import MappingProxyType
import tomllib
from typing import Any, Mapping


ROLES = (
    "update", "schedule", "state_memory", "intervention", "stopping", "selection", "postprocessing",
)

_ROLE_KINDS = {
    "update": {"binary_spa", "min_sum", "normalized_min_sum", "offset_min_sum"},
    "schedule": {"flooding", "layered", "check_node_serial", "variable_node_serial", "residual", "randomized", "group_shuffled"},
    "state_memory": {"stateless", "identity"},
    "intervention": {"identity", "guided_decimation", "impulse", "freezing", "syndrome_flip", "sign_flip", "restart_belief"},
    "stopping": {"syndrome_or_budget"},
    "selection": {"stable_first"},
    "postprocessing": {"identity"},
}
_CONTROL_KEYS = {
    "max_iterations", "parameter_assignment", "finite_bias_magnitude", "zero_rule", "final_round_rule",
    "round_limit", "sweeps_per_round", "realization", "baseline_sweeps", "attempt_sweeps", "attempt_cap",
    "coordinate_order", "period_sweeps", "lifetime_sweeps", "retry_cap", "root_seed", "top_k", "max_weight",
    "test_cap", "alpha", "trunk_sweeps", "continuation_sweeps", "preset", "code_id", "eta", "t_cap",
    "forced_value", "v2c_clip",
    "root_sweeps", "residual_sweeps", "exact_distance", "variant", "source_revision", "qualification",
    "native_availability", "trigger", "operator", "selection", "lift_rule", "reset_rule", "preserved_fields",
    "unresolved", "stream_status", "source_code_commit",
}
_TOP_LEVEL = {
    "schema_version", "record_kind", "variant_id", "execution_status", "qualification", "source", "equations",
    "explanations", "unresolved", "blocking_features", *ROLES, "memory", "relay", "intervention_limits",
}
_SOURCE_KEYS = {"paper", "revision", "url", "anchors", "note"}
_CODE_BLOCK_LENGTH = "code_block_length"
_YAO_VARIANT_ORDER = (
    "bp-t100", "bpgd-t001", "bpgd-t010", "bpgd-t070", "bpgd-t100",
    "bpgd-t100-r002", "bpgd-t100-r005", "bpgd-t100-r010", "bpgd-t100-r050", "bpgd-t100-r882",
)
_YAO_UNRESOLVED = (
    "author_implementation_identity",
    "ordered_paper_experiment_artifact_identity",
)
_BHATNAGAR_VARIANTS = (
    ("minimum-weight-1", 1, "minimum_original_weight"),
    ("first-convergence-0", 0, "first_convergence"),
    ("first-convergence-1", 1, "first_convergence"),
)
_BHATNAGAR_UNRESOLVED = (
    "source_schedule_unspecified", "infinite_prior_finite_runtime_surrogate",
    "source_experiment_identity_unverified",
)


def _canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n").encode("utf-8")


def _identity(value: Any) -> str:
    return sha256(_canonical_bytes(value)).hexdigest()


def _validate_finite(value: Any, *, field: str) -> None:
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError(f"{field} must be finite")
    if isinstance(value, dict):
        for name, child in value.items():
            _validate_finite(child, field=f"{field}.{name}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _validate_finite(child, field=f"{field}[{index}]")


@dataclass(frozen=True)
class LiteraturePolicy:
    """Immutable projections and identities for one researcher-owned TOML file."""

    source_path: Path
    disposition: str
    blocking_features: tuple[str, ...]
    executable: Mapping[str, Any]
    provenance: Mapping[str, Any]
    execution_identity: str
    provenance_identity: str
    raw_document_identity: str

    def requires_artifact_block_length(self) -> bool:
        """Whether a bounded source control needs the admitted code length."""
        intervention = self.executable.get("intervention")
        return bool(isinstance(intervention, Mapping)
                    and (intervention.get("round_limit") == _CODE_BLOCK_LENGTH
                         or intervention.get("attempt_cap") == _CODE_BLOCK_LENGTH
                         or intervention.get("coordinate_order") == "index_ascending"))

    def decoder_projection(self, *, code_block_length: int | None = None) -> dict[str, Any]:
        """Return a fresh canonical-decoder object for the study compiler."""
        executable = _resolve_symbolic_controls(self.executable, code_block_length=code_block_length)
        return {"schema_version": 1, "engine": "canonical_css", **executable}

    def execution_identity_for(self, *, code_block_length: int | None = None) -> str:
        """Return the numerical identity after any source control is resolved."""
        return _identity(_resolve_symbolic_controls(self.executable, code_block_length=code_block_length))


@dataclass(frozen=True)
class YaoSourceDisposition:
    """Typed source-to-kernel translation, independent of paper-curve claims."""

    variant_id: str
    source_path: Path
    disposition: str
    executable: Mapping[str, Any]
    qualification: str
    unresolved: tuple[str, ...]


@dataclass(frozen=True)
class BhatnagarSourceDisposition:
    """One exact source name and its qualified canonical impulse controls."""

    variant_id: str
    source_path: Path
    disposition: str
    executable: Mapping[str, Any]
    qualification: str
    unresolved: tuple[str, ...]


def _copy_executable(value: Mapping[str, Any]) -> dict[str, Any]:
    """Copy closed policy tables without preserving caller-owned mappings."""
    copied: dict[str, Any] = {}
    for name, control in value.items():
        copied[name] = dict(control) if isinstance(control, Mapping) else control
    return copied


def _resolve_symbolic_controls(
    executable: Mapping[str, Any], *, code_block_length: int | None,
) -> dict[str, Any]:
    """Resolve the only admitted artifact-dependent literature control.

    ``R = n`` in Yao's Algorithm 1 is intentionally not a default.  The
    persisted decoder projection receives the validated integer so cache and
    manifest identities cannot contain a symbolic token.
    """
    resolved = _copy_executable(executable)
    intervention = resolved.get("intervention")
    if not isinstance(intervention, dict):
        return resolved
    for field, kind in (("round_limit", "guided_decimation"), ("attempt_cap", "impulse")):
        value = intervention.get(field)
        if not isinstance(value, str):
            continue
        if value != _CODE_BLOCK_LENGTH or intervention.get("kind") != kind:
            raise ValueError("unsupported symbolic literature control")
        if type(code_block_length) is not int or code_block_length < 1:
            raise ValueError("literature code block length must be a validated positive integer")
        intervention[field] = code_block_length
    coordinate_order = intervention.get("coordinate_order")
    if isinstance(coordinate_order, str):
        if coordinate_order != "index_ascending" or intervention.get("kind") != "impulse":
            raise ValueError("unsupported symbolic literature coordinate order")
        if type(code_block_length) is not int or code_block_length < 1:
            raise ValueError("literature code block length must be a validated positive integer")
        intervention["coordinate_order"] = list(range(code_block_length))
    return resolved


def _source_specification(path: Path, document: Mapping[str, Any], raw_identity: str) -> LiteraturePolicy:
    blocking = document.get("blocking_features", ())
    if not isinstance(blocking, list) or any(not isinstance(item, str) or not item for item in blocking):
        raise ValueError("non-runnable literature records require a string blocking_features list")
    return LiteraturePolicy(
        source_path=path, disposition="non_runnable", blocking_features=tuple(blocking),
        executable=MappingProxyType({}), provenance=MappingProxyType(dict(document)),
        execution_identity=_identity({}), provenance_identity=_identity(dict(document)),
        raw_document_identity=raw_identity,
    )


def _validate_symbolic_runnable_controls(executable: Mapping[str, Any]) -> None:
    """Reject stringly controls before they can reach a public manifest."""
    intervention = executable.get("intervention")
    if not isinstance(intervention, Mapping):
        return
    for field, kind in (("round_limit", "guided_decimation"), ("attempt_cap", "impulse")):
        value = intervention.get(field)
        if isinstance(value, str) and (value != _CODE_BLOCK_LENGTH or intervention.get("kind") != kind):
            raise ValueError("unsupported symbolic literature control")
    order = intervention.get("coordinate_order")
    if isinstance(order, str) and (order != "index_ascending" or intervention.get("kind") != "impulse"):
        raise ValueError("unsupported symbolic literature coordinate order")


def parse_literature_policy(path: str | Path) -> LiteraturePolicy:
    """Parse one TOML policy without interpreting source prose as executable code."""
    source_path = Path(path).resolve()
    if source_path.suffix != ".toml":
        raise ValueError("literature policy files must use the .toml extension")
    raw = source_path.read_bytes()
    try:
        document = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as error:
        raise ValueError("literature policy is not valid UTF-8 TOML") from error
    if not isinstance(document, dict):
        raise ValueError("literature policy must be a TOML table")
    raw_identity = sha256(raw).hexdigest()
    if source_path.name.endswith(".spec.toml") or document.get("execution_status") == "not_runnable":
        return _source_specification(source_path, document, raw_identity)
    if set(document) - _TOP_LEVEL:
        raise ValueError("literature policy has unknown top-level executable fields")
    required = {"schema_version", "record_kind", "variant_id", "execution_status", "qualification", "source", *ROLES}
    if set(document) & required != required:
        raise ValueError("runnable literature policy must declare source, qualification, and all seven roles")
    if (document["schema_version"] != 1 or document["record_kind"] != "literature_policy"
            or document["execution_status"] != "runnable"
            or not isinstance(document["variant_id"], str) or not document["variant_id"]
            or not isinstance(document["qualification"], str) or not document["qualification"]):
        raise ValueError("unsupported runnable literature policy header")
    source = document["source"]
    if not isinstance(source, dict) or set(source) - _SOURCE_KEYS or not {"paper", "revision", "url"} <= set(source):
        raise ValueError("runnable literature policy source must declare paper, revision, and URL")
    if any(not isinstance(source[name], str) or not source[name] for name in ("paper", "revision", "url")):
        raise ValueError("literature source fields must be nonempty strings")
    executable: dict[str, Any] = {}
    for role in ROLES:
        control = document[role]
        if not isinstance(control, dict) or set(control) - ({"kind"} | _CONTROL_KEYS):
            raise ValueError(f"{role} has unknown executable controls")
        kind = control.get("kind")
        if not isinstance(kind, str) or kind not in _ROLE_KINDS[role]:
            raise ValueError(f"{role} requires a registered policy kind")
        _validate_finite(control, field=role)
        executable[role] = dict(control)
    for name in ("memory", "relay", "intervention_limits"):
        if name in document:
            if not isinstance(document[name], dict):
                raise ValueError(f"{name} must be a table")
            _validate_finite(document[name], field=name)
            executable[name] = dict(document[name])
    _validate_symbolic_runnable_controls(executable)
    if (source["revision"] == "arxiv:2606.18240v1"
            or document["variant_id"] in {name for name, _, _ in _BHATNAGAR_VARIANTS}):
        expected_rows = qualify_bhatnagar_source_records(source_path.parent)
        expected = next((row for row in expected_rows if row.variant_id == document["variant_id"]), None)
        if (expected is None or source["revision"] != "arxiv:2606.18240v1"
                or {role: executable[role] for role in ROLES} != dict(expected.executable)
                or document["qualification"] != expected.qualification
                or not isinstance(document.get("unresolved"), dict)
                or not set(expected.unresolved) <= set(document["unresolved"])):
            raise ValueError("Bhatnagar runnable policy must match its closed source variant and qualification")
    provenance = {name: document[name] for name in ("record_kind", "variant_id", "qualification", "source", "equations", "explanations", "unresolved") if name in document}
    return LiteraturePolicy(
        source_path=source_path, disposition="runnable", blocking_features=(),
        executable=MappingProxyType(executable), provenance=MappingProxyType(provenance),
        execution_identity=_identity(executable), provenance_identity=_identity(provenance),
        raw_document_identity=raw_identity,
    )


def _source_record(path: Path) -> dict[str, Any]:
    try:
        value = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise ValueError(f"literature source record is invalid TOML: {path.name}") from error
    if not isinstance(value, dict):
        raise ValueError(f"literature source record must be a table: {path.name}")
    return value


def _yao_bpgd_executable(*, sweeps_per_round: int, round_limit: int | str) -> dict[str, Any]:
    """The closed Algorithm 1 v2 interpretation used by the existing kernel."""
    return {
        "update": {"kind": "binary_spa"},
        "schedule": {"kind": "flooding"},
        "state_memory": {"kind": "stateless"},
        "intervention": {
            "kind": "guided_decimation", "variant": "algorithm1_v2_interpretation",
            "source_revision": "arxiv:2312.10950v2", "qualification": "algorithm_interpretation",
            "native_availability": "unverified", "trigger": "failed_bp_round",
            "operator": "finite_prior_bias", "selection": "max_abs_reliability",
            "lift_rule": "identity", "reset_rule": "continue_messages",
            "preserved_fields": ["graph", "syndrome", "messages"],
            "unresolved": ["zero_bias_boundary", "final_round_source_interpretation", *_YAO_UNRESOLVED],
            "stream_status": "not_applicable", "finite_bias_magnitude": 25.0,
            "zero_rule": "positive_prior_for_zero_posterior",
            "final_round_rule": "return_after_last_fixation",
            "round_limit": round_limit, "sweeps_per_round": sweeps_per_round,
        },
        "stopping": {"kind": "syndrome_or_budget", "max_iterations": sweeps_per_round},
        "selection": {"kind": "stable_first"},
        "postprocessing": {"kind": "identity"},
    }


def qualify_yao_source_records(
    directory: str | Path, *, code_block_length: int | None = None,
) -> tuple[YaoSourceDisposition, ...]:
    """Translate all requested Yao Figure 3/6 records into closed controls.

    The result describes only the algorithmic mapping.  Source author-code and
    ordered-artifact identity remain unresolved, so no result is source-faithful.
    """
    root = Path(directory)
    records: list[YaoSourceDisposition] = []
    for variant_id in _YAO_VARIANT_ORDER:
        path = root / f"{variant_id}.spec.toml"
        document = _source_record(path)
        if (document.get("record_kind") != "literature_policy_spec"
                or document.get("variant_id") != variant_id
                or document.get("execution_status") != "not_runnable"):
            raise ValueError(f"Yao source record has an invalid header: {path.name}")
        roles = {name: document.get(name) for name in ROLES}
        if (not all(isinstance(control, dict) for control in roles.values())
                or roles["update"].get("kind") != "binary_spa"
                or roles["schedule"].get("kind") != "flooding"
                or roles["state_memory"].get("kind") != "stateless"
                or roles["stopping"].get("kind") != "syndrome_or_budget"
                or roles["selection"].get("kind") != "stable_first"
                or roles["postprocessing"].get("kind") != "identity"):
            raise ValueError(f"Yao source record has an unsupported policy composition: {path.name}")
        if variant_id == "bp-t100":
            if (roles["intervention"].get("kind") != "identity"
                    or roles["stopping"].get("max_iterations") != 100):
                raise ValueError("Yao BP comparator controls are not Figure 3/6 T=100")
            executable = {
                "update": {"kind": "binary_spa"}, "schedule": {"kind": "flooding"},
                "state_memory": {"kind": "stateless"}, "intervention": {"kind": "identity"},
                "stopping": {"kind": "syndrome_or_budget", "max_iterations": 100},
                "selection": {"kind": "stable_first"}, "postprocessing": {"kind": "identity"},
            }
            disposition = "runnable"
        else:
            intervention = roles["intervention"]
            if intervention.get("kind") != "guided_decimation":
                raise ValueError(f"Yao BPGD record is not guided decimation: {path.name}")
            sweeps = intervention.get("sweeps_per_round")
            raw_round_limit = intervention.get("round_limit")
            if type(sweeps) is not int or sweeps < 1:
                raise ValueError(f"Yao T must be a positive integer: {path.name}")
            if raw_round_limit == _CODE_BLOCK_LENGTH:
                if code_block_length is None:
                    executable = _yao_bpgd_executable(sweeps_per_round=sweeps, round_limit=_CODE_BLOCK_LENGTH)
                    disposition = "requires_artifact_block_length"
                elif type(code_block_length) is int and code_block_length > 0:
                    executable = _yao_bpgd_executable(sweeps_per_round=sweeps, round_limit=code_block_length)
                    disposition = "runnable"
                else:
                    raise ValueError("Yao code block length must be a validated positive integer")
            elif type(raw_round_limit) is int and raw_round_limit > 0:
                executable = _yao_bpgd_executable(sweeps_per_round=sweeps, round_limit=raw_round_limit)
                disposition = "runnable"
            else:
                raise ValueError(f"Yao R must be a positive integer or code_block_length: {path.name}")
        records.append(YaoSourceDisposition(
            variant_id=variant_id, source_path=path.resolve(), disposition=disposition,
            executable=MappingProxyType(executable), qualification="canonical_adaptation_not_assessed",
            unresolved=_YAO_UNRESOLVED,
        ))
    return tuple(records)


def _bhatnagar_executable(*, forced_value: int, selection: str, attempt_cap: int | str) -> dict[str, Any]:
    realization = "semantic_forced_zero" if forced_value == 0 else "semantic_forced_one"
    return {
        "update": {"kind": "binary_spa"},
        "schedule": {"kind": "flooding"},
        # The impulse controller owns fresh BP sessions.  It does not preserve
        # messages between coordinates; the public memory role is identity.
        "state_memory": {"kind": "identity"},
        "intervention": {
            "kind": "impulse",
            "variant": "impulse_positive_infinite_semantic_v1" if forced_value == 0 else "impulse_negative_infinite_semantic_v1",
            "source_revision": "arxiv:2606.18240v1",
            "qualification": "source_operator_semantic_adaptation",
            "native_availability": "unverified",
            "trigger": "baseline_invalid",
            "operator": realization,
            "selection": selection,
            "lift_rule": "identity",
            "reset_rule": "fresh_per_coordinate",
            "preserved_fields": ["original_graph", "original_syndrome"],
            "unresolved": list(_BHATNAGAR_UNRESOLVED),
            "stream_status": "not_applicable",
            "realization": realization,
            "forced_value": forced_value,
            "v2c_clip": 25.0,
            "baseline_sweeps": 100,
            "attempt_sweeps": 100,
            "attempt_cap": attempt_cap,
            "coordinate_order": "index_ascending" if isinstance(attempt_cap, str) else list(range(attempt_cap)),
        },
        "stopping": {"kind": "syndrome_or_budget", "max_iterations": 100},
        # The source selector is internal to the intervention controller.
        "selection": {"kind": "stable_first"},
        "postprocessing": {"kind": "identity"},
    }


def qualify_bhatnagar_source_records(
    directory: str | Path, *, code_block_length: int | None = None,
) -> tuple[BhatnagarSourceDisposition, ...]:
    """Translate the three named impulse variants without source-name aliases.

    Flooding schedule, finite forced prior and V2C clip are qualified
    interpretations.  A runnable disposition says only that the canonical
    controls are executable, never that a published curve was reproduced.
    """
    if code_block_length is not None and (type(code_block_length) is not int or code_block_length < 1):
        raise ValueError("literature code block length must be a validated positive integer")
    root = Path(directory)
    rows: list[BhatnagarSourceDisposition] = []
    for variant_id, forced_value, selection in _BHATNAGAR_VARIANTS:
        path = root / f"{variant_id}.spec.toml"
        source = _source_record(path)
        intervention = source.get("intervention")
        if (source.get("record_kind") != "literature_policy_spec"
                or source.get("variant_id") != variant_id
                or source.get("execution_status") != "not_runnable"
                or not isinstance(intervention, dict)
                or source.get("source", {}).get("revision") != "arxiv:2606.18240v1"
                or source.get("update") != {"kind": "binary_spa", "v2c_message_clip": 25.0}
                or source.get("schedule") != {"kind": "flooding", "source_schedule_status": "paper_algorithm_does_not_fix_message_order"}
                or source.get("state_memory") != {"kind": "stateless"}
                or source.get("stopping") != {"kind": "syndrome_or_budget"}
                or source.get("selection") != {"kind": "minimum_weight" if selection == "minimum_original_weight" else "first_convergence"}
                or source.get("postprocessing") != {"kind": "identity"}
                or intervention != {
                    "kind": "impulse", "trigger": "initial_bp_nonconvergence",
                    "shorten_value": forced_value, "attempt_cap": _CODE_BLOCK_LENGTH,
                    "coordinate_order": "index_ascending", "baseline_sweeps": 100,
                    "attempt_sweeps": 100,
                }):
            raise ValueError(f"Bhatnagar source record does not match the named variant: {path.name}")
        cap = _CODE_BLOCK_LENGTH if code_block_length is None else code_block_length
        rows.append(BhatnagarSourceDisposition(
            variant_id=variant_id, source_path=path.resolve(),
            disposition="requires_artifact_block_length" if code_block_length is None else "runnable",
            executable=MappingProxyType(_bhatnagar_executable(
                forced_value=forced_value, selection=selection, attempt_cap=cap,
            )), qualification="canonical_adaptation_not_assessed", unresolved=_BHATNAGAR_UNRESOLVED,
        ))
    return tuple(rows)
