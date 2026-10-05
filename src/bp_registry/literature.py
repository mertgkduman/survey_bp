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
    "root_sweeps", "residual_sweeps", "exact_distance", "variant", "source_revision", "qualification",
    "native_availability", "trigger", "operator", "selection", "lift_rule", "reset_rule", "preserved_fields",
    "unresolved", "stream_status", "source_code_commit",
}
_TOP_LEVEL = {
    "schema_version", "record_kind", "variant_id", "execution_status", "qualification", "source", "equations",
    "explanations", "unresolved", "blocking_features", *ROLES, "memory", "relay", "intervention_limits",
}
_SOURCE_KEYS = {"paper", "revision", "url", "anchors", "note"}


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

    def decoder_projection(self) -> dict[str, Any]:
        """Return a fresh canonical-decoder object for the study compiler."""
        return {"schema_version": 1, "engine": "canonical_css", **self.executable}


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
    provenance = {name: document[name] for name in ("record_kind", "variant_id", "qualification", "source", "equations", "explanations", "unresolved") if name in document}
    return LiteraturePolicy(
        source_path=source_path, disposition="runnable", blocking_features=(),
        executable=MappingProxyType(executable), provenance=MappingProxyType(provenance),
        execution_identity=_identity(executable), provenance_identity=_identity(provenance),
        raw_document_identity=raw_identity,
    )
