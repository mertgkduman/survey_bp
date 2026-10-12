"""Closed, source-grounded decoder policy documents.

Only the seven registered policy roles and closed, declared terminal controls
are projected into execution. Paper prose remains immutable request provenance.
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
    "ensemble", "list_selection", "vote",
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
_RABETI_VOTE = {
    "object": "correction_bits",
    "electorate_rule": "admitted_members",
    "aggregation": "coordinate_majority",
    "tie_bit": 1,
}


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
        ensemble = self.executable.get("ensemble")
        return bool(
            isinstance(intervention, Mapping)
            and (intervention.get("round_limit") == _CODE_BLOCK_LENGTH
                 or intervention.get("attempt_cap") == _CODE_BLOCK_LENGTH
                 or intervention.get("coordinate_order") == "index_ascending")
            or isinstance(ensemble, Mapping) and any(
                isinstance(basis, Mapping) and "source_rows" in basis
                for basis in ensemble.get("bases", ())
            )
        )

    def decoder_projection(
        self, *, code_block_length: int | None = None, code_check_count: int | None = None,
    ) -> dict[str, Any]:
        """Return a fresh canonical-decoder object for the study compiler."""
        executable = _resolve_symbolic_controls(
            self.executable, code_block_length=code_block_length, code_check_count=code_check_count,
        )
        return {"schema_version": 1, "engine": "canonical_css", **executable}

    def execution_identity_for(
        self, *, code_block_length: int | None = None, code_check_count: int | None = None,
    ) -> str:
        """Return the numerical identity after any source control is resolved."""
        return _identity(_resolve_symbolic_controls(
            self.executable, code_block_length=code_block_length, code_check_count=code_check_count,
        ))


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


@dataclass(frozen=True)
class RabetiSourceDisposition:
    """Source controls awaiting an explicitly qualified local basis set."""

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
    executable: Mapping[str, Any], *, code_block_length: int | None, code_check_count: int | None,
) -> dict[str, Any]:
    """Resolve source controls from validated artifact dimensions.

    Yao's R=n, Bhatnagar's coordinate range, and Rabeti's one-hot check rows
    enter the persisted decoder projection before cache and manifest identity.
    """
    resolved = _copy_executable(executable)
    intervention = resolved.get("intervention")
    if isinstance(intervention, dict):
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
    ensemble = resolved.get("ensemble")
    if isinstance(ensemble, dict) and ensemble.get("kind") == "mbbp_ld":
        bases = ensemble.get("bases")
        if not isinstance(bases, list):
            raise ValueError("MBBP ensemble must declare basis descriptors")
        resolved_bases = []
        for basis in bases:
            if not isinstance(basis, dict) or "source_rows" not in basis:
                raise ValueError("MBBP basis requires explicit source rows")
            if type(code_check_count) is not int or code_check_count < 1:
                raise ValueError("MBBP check count must come from a validated artifact")
            rows = basis["source_rows"]
            if not isinstance(rows, list) or not rows or any(type(i) is not int or i < 0 or i >= code_check_count for i in rows):
                raise ValueError("MBBP source row is outside the validated check count")
            transforms = [[int(j == i) for j in range(code_check_count)] for i in rows]
            resolved_bases.append({name: value for name, value in basis.items() if name != "source_rows"} | {
                "redundant_transforms": transforms,
            })
        ensemble["bases"] = resolved_bases
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
    for name in ("memory", "relay", "intervention_limits", "ensemble", "list_selection", "vote"):
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
    if (source["revision"] == "arxiv:2605.14170v1" or document["variant_id"] in {"mbbp-ld", "mbbp-ld-vote"}):
        expected = qualify_rabeti_source_record(source_path.parent)
        ensemble = executable.get("ensemble")
        score = executable.get("list_selection")
        is_vote = document["variant_id"] == "mbbp-ld-vote"
        vote = executable.get("vote")
        if (document["variant_id"] not in {expected.variant_id, "mbbp-ld-vote"}
                or source["revision"] != "arxiv:2605.14170v1"
                or document["qualification"] != expected.qualification
                or {role: executable[role] for role in ROLES} != {role: expected.executable[role] for role in ROLES}
                or not isinstance(ensemble, dict)
                or not isinstance(score, dict)
                or score != expected.executable["list_selection"]
                or (vote != _RABETI_VOTE if is_vote else vote is not None)
                or not isinstance(document.get("unresolved"), dict)
                or not set(expected.unresolved) <= set(document["unresolved"])):
            raise ValueError("Rabeti runnable policy must match its closed source controls and qualification")
        expected_ensemble = expected.executable["ensemble"]
        bases = ensemble.get("bases")
        if (set(ensemble) != set(expected_ensemble) | {"max_member_c2v_updates", "max_total_members", "bases"}
                or any(ensemble[name] != value for name, value in expected_ensemble.items())
                or type(ensemble["max_member_c2v_updates"]) is not int
                or ensemble["max_member_c2v_updates"] < 1
                or type(ensemble["max_total_members"]) is not int
                or ensemble["max_total_members"] < 1
                or not isinstance(bases, list) or not bases):
            raise ValueError("Rabeti ensemble requires finite independent members and one-hot bases")
        if len(bases) > ensemble["max_total_members"]:
            raise ValueError("Rabeti basis count exceeds the declared member cap")
        member_ids: set[str] = set()
        for ordinal, basis in enumerate(bases):
            if (not isinstance(basis, dict)
                    or set(basis) != {"member_id", "local_ordinal", "partition_identity", "permutation_identity", "transform_kind", "source_rows"}
                    or any(not isinstance(basis[name], str) or not basis[name]
                           for name in ("member_id", "partition_identity", "permutation_identity"))
                    or basis["member_id"] in member_ids
                    or type(basis["local_ordinal"]) is not int or basis["local_ordinal"] != ordinal
                    or basis["transform_kind"] != "one_hot_original_check_rows"
                    or not isinstance(basis["source_rows"], list) or not basis["source_rows"]
                    or any(type(row) is not int or row < 0 for row in basis["source_rows"])
                    or len(set(basis["source_rows"])) != len(basis["source_rows"])):
                raise ValueError("Rabeti basis must use ordered one-hot original check rows")
            member_ids.add(basis["member_id"])
    elif {"ensemble", "list_selection", "vote"} & set(executable):
        raise ValueError("ensemble controls require a registered source-family compiler")
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


_RABETI_UNRESOLVED = (
    "source_partition_permutation", "augmented_syndrome_notation",
    "candidate_score_ties", "author_implementation_identity",
    "ordered_paper_experiment_artifact_identity",
)


def qualify_rabeti_source_record(directory: str | Path) -> RabetiSourceDisposition:
    """Map the paper's fixed MBBP controls without inventing its basis set.

    The source constructs H_t from selected original check rows.  A local
    runnable policy must still bind exact one-hot row descriptors and disclose
    its partition/permutation choice before claiming a canonical adaptation.
    """
    path = Path(directory) / "mbbp-ld.spec.toml"
    source = _source_record(path)
    expected = {
        "update": {"kind": "normalized_min_sum", "alpha": 0.875},
        "schedule": {"kind": "check_node_serial"},
        "state_memory": {"kind": "stateless"},
        "intervention": {
            "kind": "subtree_redundant_check_ensemble", "member_state": "independent",
            "subtree_rule": "maximal_cycle_free_check_partition",
        },
        "stopping": {"kind": "syndrome_or_budget", "max_iterations": 100},
        "selection": {
            "kind": "frequency_weighted_score",
            "score": "candidate_frequency/(hamming_weight+1)",
        },
        "postprocessing": {"kind": "identity"},
    }
    if (source.get("record_kind") != "literature_policy_spec"
            or source.get("variant_id") != "mbbp-ld"
            or source.get("execution_status") != "not_runnable"
            or not isinstance(source.get("source"), dict)
            or source["source"].get("revision") != "arxiv:2605.14170v1"
            or any(source.get(role) != controls for role, controls in expected.items())):
        raise ValueError("Rabeti source record does not match the named MBBP-LD controls")
    executable = {
        "update": {"kind": "normalized_min_sum", "parameter_assignment": {"shape": "scalar", "value": 0.875}},
        "schedule": {"kind": "check_node_serial"},
        "state_memory": {"kind": "identity"},
        "intervention": {"kind": "identity"},
        "stopping": {"kind": "syndrome_or_budget", "max_iterations": 100},
        "selection": {"kind": "stable_first"},
        "postprocessing": {"kind": "identity"},
        "ensemble": {
            "kind": "mbbp_ld", "source_status": "canonical_adaptation",
            "member_state": "independent", "max_iterations": 100,
            "no_member_terminal": "no_member_converged_zero_return",
        },
        "list_selection": {
            "kind": "frequency_over_weight_plus_one",
            "tie_rule": "local_ordinal_then_lineage",
        },
    }
    return RabetiSourceDisposition(
        variant_id="mbbp-ld", source_path=path.resolve(),
        disposition="requires_local_basis_descriptors",
        executable=MappingProxyType(executable), qualification="canonical_adaptation_not_assessed",
        unresolved=_RABETI_UNRESOLVED,
    )


_PHASE9_SOURCE_SPECS = (
    ("bhatnagar", "first-convergence-0", "literature_policies/bhatnagar-2026-impulse-decoding/first-convergence-0.spec.toml", "c66b32606067b6aaa598b8d3a735a85f3e2d8788b32287af3a4006989cef8099"),
    ("bhatnagar", "first-convergence-1", "literature_policies/bhatnagar-2026-impulse-decoding/first-convergence-1.spec.toml", "3528635ed1ab9de8af997dce055bc170e5357f89362fcdbce8bfe3d6df0e52fe"),
    ("bhatnagar", "minimum-weight-1", "literature_policies/bhatnagar-2026-impulse-decoding/minimum-weight-1.spec.toml", "9352a8936aa3a708989f51a64770ac2c455d1b86c9e74acda6eb0fe0d6657ff4"),
    ("rabeti", "mbbp-ld", "literature_policies/rabeti-2026-multiple-bases-bp-list-decoding/mbbp-ld.spec.toml", "ce330e0212982047165ac1f8aba244dbb16853b1445a411ac8b957450f642f2e"),
    ("yao", "bp-t100", "literature_policies/yao-2024-guided-decimation/bp-t100.spec.toml", "7b0540d334025e654af4c90d78453f2d9908ba58229803bedd489ad201b7405a"),
    ("yao", "bpgd-t001", "literature_policies/yao-2024-guided-decimation/bpgd-t001.spec.toml", "ca3832a5fa3ead750d331028752cbbe7776ee7bcdfba9274be5aacbc8ada2f8a"),
    ("yao", "bpgd-t010", "literature_policies/yao-2024-guided-decimation/bpgd-t010.spec.toml", "f800a9d6dd689ccbb020c2541661c1389adf5a601027bc0562cfd8f46a2eee59"),
    ("yao", "bpgd-t070", "literature_policies/yao-2024-guided-decimation/bpgd-t070.spec.toml", "4ef743753a220310ab87e9114282a63c6de6cab2d766d5380f181d631a07a0a3"),
    ("yao", "bpgd-t100", "literature_policies/yao-2024-guided-decimation/bpgd-t100.spec.toml", "5b1f956643bf6da2a2f507f6853dded7d402e4e9e675f9f945ce9c928104b324"),
    ("yao", "bpgd-t100-r002", "literature_policies/yao-2024-guided-decimation/bpgd-t100-r002.spec.toml", "e66ce9ff55d05ca36f31200febb95ec3ec208f550cbc0f8d299a6109bd2f0fe8"),
    ("yao", "bpgd-t100-r005", "literature_policies/yao-2024-guided-decimation/bpgd-t100-r005.spec.toml", "fc4b60550e34959a5778f07713609a6b9b974ff9aa75b32403a942dc264157d7"),
    ("yao", "bpgd-t100-r010", "literature_policies/yao-2024-guided-decimation/bpgd-t100-r010.spec.toml", "421a1209008bf4f685089e78d7d8afa3b5d9623aaf31bc643254355fe47a3319"),
    ("yao", "bpgd-t100-r050", "literature_policies/yao-2024-guided-decimation/bpgd-t100-r050.spec.toml", "27e1d813fcd7ed37280a909ee43f8700ac4794af68d40fb9a532cb4560671a97"),
    ("yao", "bpgd-t100-r882", "literature_policies/yao-2024-guided-decimation/bpgd-t100-r882.spec.toml", "f41ffa51fc0c6bc46557ddd532124a8ac3c0b3cc6b56cfac5f9c354eb36cff29"),
)
_PHASE9_RUNNABLE_COUNTERPARTS = {
    ("bhatnagar", "first-convergence-0"): "literature_policies/bhatnagar-2026-impulse-decoding/first-convergence-0.toml",
    ("rabeti", "mbbp-ld"): "literature_policies/rabeti-2026-multiple-bases-bp-list-decoding/mbbp-ld.toml",
    ("yao", "bp-t100"): "literature_policies/yao-2024-guided-decimation/bp-t100.toml",
    ("yao", "bpgd-t001"): "literature_policies/yao-2024-guided-decimation/bpgd-t001.toml",
    ("yao", "bpgd-t100-r002"): "literature_policies/yao-2024-guided-decimation/bpgd-t100-r002.toml",
}
_PHASE9_RECEIPTS = {
    "bhatnagar": "literature_policies/bhatnagar-2026-impulse-decoding/paper_reproduction/source-qualification-v1.json",
    "rabeti": "literature_policies/rabeti-2026-multiple-bases-bp-list-decoding/paper_reproduction/source-targets-v1.json",
    "yao": "literature_policies/yao-2024-guided-decimation/paper_reproduction/source-targets-v1.json",
}
PHASE9_QUALIFICATION_INVENTORY_PATH = "literature_policies/qualification-phase9-v1.json"


def _phase9_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Phase 9 qualification receipt is unreadable: {path}") from error
    if not isinstance(value, dict):
        raise ValueError(f"Phase 9 qualification receipt must be a JSON object: {path}")
    return value


def _phase9_receipt_summary(root: Path, family: str) -> tuple[dict[str, Any], tuple[str, ...], dict[str, Any]]:
    """Validate each paper receipt while retaining every observed discrepancy."""
    relative = _PHASE9_RECEIPTS[family]
    path = root / relative
    receipt = _phase9_json(path)
    digest = sha256(path.read_bytes()).hexdigest()
    if family == "bhatnagar":
        paper = receipt.get("paper")
        figure = receipt.get("vector_figure")
        if (not isinstance(paper, dict) or paper.get("revision") != "arXiv:2606.18240v1"
                or paper.get("sha256") != "ad7b63a456b9ec16a20aa7712b8be1f1c8d0cad48f6702583746b05363940208"
                or not isinstance(figure, dict)
                or figure.get("sha256") != "7e49980c87891a7bd21bbeca29563e2026713ef59e447e34e654118f96a454d1"
                or receipt.get("target_extraction", {}).get("status") != "blocked"
                or receipt.get("author_numeric_data", {}).get("status") != "unavailable_to_workspace"
                or receipt.get("author_implementation", {}).get("status") != "identity_unverified"):
            raise ValueError("Bhatnagar receipt does not retain its pinned unavailable evidence state")
        blockers = tuple(receipt.get("source_experiment_blockers", ()))
        target = {"status": "blocked", "reason": "author_data_unavailable_to_workspace_and_digitization_unperformed"}
    else:
        archive = receipt.get("source_archive")
        qualifications = receipt.get("source_experiment_qualifications")
        targets = receipt.get("targets")
        expected = {
            "yao": ("arXiv:2312.10950v2", "8ddade4c50c9b12853e5431c53f4906fd29913bbf3be306422bafd984a05d654"),
            "rabeti": ("arXiv:2605.14170v1", "467622e2f17f01d302d6c790b13078569f17d71cd83910558535019a594e07c1"),
        }[family]
        if (not isinstance(archive, dict) or (archive.get("revision"), archive.get("sha256")) != expected
                or not isinstance(qualifications, list) or not qualifications
                or not isinstance(targets, list) or not targets):
            raise ValueError(f"{family} receipt does not retain its pinned source targets")
        first = qualifications[0]
        if not isinstance(first, dict) or not isinstance(first.get("qualification_blockers"), list):
            raise ValueError(f"{family} receipt lacks source-qualification blockers")
        blockers = tuple(first["qualification_blockers"])
        if family == "rabeti":
            snapshot = first.get("source_experiment", {}).get("paper_snapshot", {})
            if not isinstance(snapshot, dict) or snapshot.get("sha256") != "7b19e17fb1ffe04c3e61aef38d02967715cba84e568667206bce2a525a79928f":
                raise ValueError("Rabeti live-source digest discrepancy is missing from the qualification receipt")
            blockers += ("live_source_digest_discrepancy_unresolved",)
        target = {"status": "authored_targets_available", "count": len(targets)}
    if not all(isinstance(blocker, str) and blocker for blocker in blockers):
        raise ValueError(f"{family} receipt has malformed source-qualification blockers")
    return {"path": relative, "sha256": digest}, tuple(sorted(set(blockers))), target


def qualify_phase9_source_inventory(root: str | Path | None = None) -> bytes:
    """Compile the complete, sorted Phase 9 inventory from pinned inputs.

    The output is stored separately at
    ``literature_policies/qualification-phase9-v1.json``.  It lists source and
    runnable identities separately, and never uses numerical agreement or
    another variant's settings to grant faithfulness.
    """
    workspace = Path(root) if root is not None else Path(__file__).resolve().parents[2]
    workspace = workspace.resolve()
    policies = workspace / "literature_policies"
    if not policies.is_dir():
        raise ValueError("Phase 9 qualification root lacks literature_policies")
    receipt_data = {family: _phase9_receipt_summary(workspace, family) for family in _PHASE9_RECEIPTS}
    identities: set[str] = set()
    records: list[dict[str, Any]] = []
    for family, variant_id, relative, expected_digest in _PHASE9_SOURCE_SPECS:
        identity = f"{family}:{variant_id}"
        if identity in identities:
            raise ValueError(f"duplicate Phase 9 variant identity: {identity}")
        identities.add(identity)
        path = workspace / relative
        raw = path.read_bytes()
        actual_digest = sha256(raw).hexdigest()
        if actual_digest != expected_digest:
            raise ValueError(f"Phase 9 source specification digest mismatch: {relative}")
        document = _source_record(path)
        source = document.get("source")
        if (document.get("record_kind") != "literature_policy_spec"
                or document.get("variant_id") != variant_id
                or document.get("execution_status") != "not_runnable"
                or not isinstance(source, dict)
                or not isinstance(source.get("revision"), str)):
            raise ValueError(f"Phase 9 source specification is malformed: {relative}")
        receipt_ref, receipt_blockers, target = receipt_data[family]
        blockers = set(receipt_blockers)
        raw_blockers = document.get("blocking_features", ())
        if not isinstance(raw_blockers, list) or not all(isinstance(item, str) and item for item in raw_blockers):
            raise ValueError(f"Phase 9 source specification lacks explicit blockers: {relative}")
        blockers.update(raw_blockers)
        blockers.update(("ordered_paper_experiment_artifact_identity", "author_implementation_identity"))
        counterpart_relative = _PHASE9_RUNNABLE_COUNTERPARTS.get((family, variant_id))
        counterpart = None
        if counterpart_relative is not None:
            counterpart_path = workspace / counterpart_relative
            counterpart = {
                "path": counterpart_relative,
                "sha256": sha256(counterpart_path.read_bytes()).hexdigest(),
                "execution_status": "runnable_canonical_adaptation",
                "qualification": "canonical_adaptation_not_assessed",
            }
        records.append({
            "assessment_eligibility": "not_eligible",
            "blockers": sorted(blockers),
            "identity": identity,
            "native_status": "identity_unverified",
            "qualification": "canonical_adaptation_not_assessed",
            "receipt": receipt_ref,
            "runnable_counterpart": counterpart,
            "source_execution_status": "not_runnable",
            "source_faithful": False,
            "source_revision": source["revision"],
            "source_spec": relative,
            "source_spec_sha256": actual_digest,
            "target_status": target,
        })
    if len(records) != 14:
        raise ValueError("Phase 9 inventory must contain exactly fourteen selected variants")
    records.sort(key=lambda record: record["identity"])
    assessment_relative = "data/studies/phase9-yao-b1-t001-p010-v4-assessment.json"
    assessment_path = workspace / assessment_relative
    if assessment_path.exists():
        if assessment_path.is_symlink() or not assessment_path.is_file():
            raise ValueError("Phase 9 Yao adaptation assessment must be a regular file")
        assessment = json.loads(assessment_path.read_bytes())
        report_ref = assessment.get("artifacts", {}).get("report", {})
        report_path = workspace / report_ref.get("path", "")
        if (assessment.get("schema") != "phase9_yao_b1_t001_p010_assessment_v1"
                or assessment.get("source_label") != "canonical_adaptation"
                or assessment.get("source_faithful") is not False
                or assessment.get("assessment_status") != "inconclusive_cap_censored"
                or assessment.get("verified") is not True
                or report_path.is_symlink() or not report_path.is_file()
                or sha256(report_path.read_bytes()).hexdigest() != report_ref.get("sha256")):
            raise ValueError("Phase 9 Yao adaptation assessment differs from verified receipts")
        selected = next(record for record in records if record["identity"] == "yao:bpgd-t001")
        selected["canonical_assessment"] = {
            "status": "inconclusive_cap_censored", "source_label": "canonical_adaptation",
            "path": assessment_relative, "sha256": sha256(assessment_path.read_bytes()).hexdigest(),
            "target_id": "yao-fig3-bpgd-t001-p010", "completed_shots": assessment["completed_shots"],
            "target_failures": assessment["frozen_target_failures"],
        }
    return (json.dumps({
        "evidence_kind": "phase9_css_source_qualification_inventory_v1",
        "format_version": 1,
        "records": records,
    }, indent=2, sort_keys=True) + "\n").encode("utf-8")
