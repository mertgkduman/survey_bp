"""Integrity-checked import of locally produced portable research results.

The import is deliberately metadata-only: it records a pinned description of a
run and its portable input, while leaving potentially large ledgers in their
original result directory.
"""

from __future__ import annotations

from hashlib import sha256, file_digest
import csv
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Any, Mapping, Iterator
from .contracts import resolved_sampling


_BOUND_FILES = frozenset({"run-manifest.json", "status.json", "requested-spec.json",
                          "effective-spec.json", "events.jsonl", "summary.json", "summary.csv"})
_SUCCESS = {"exact", "stabilizer_equivalent", "observable_success"}


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _read_json(path: Path, name: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid {name}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object")
    return value


def _safe_member(root: Path, name: object) -> Path:
    if not isinstance(name, str) or not name or Path(name).is_absolute() or Path(name).name != name:
        raise ValueError("result manifest contains an unsafe member name")
    member = (root / name).resolve()
    if not member.is_relative_to(root) or member.is_symlink() or not member.is_file():
        raise ValueError(f"result manifest member is unavailable: {name}")
    return member


def _events(path: Path, row_count: int) -> Iterator[dict[str, Any]]:
    """Stream records so import does not retain a large event ledger in RAM."""
    try:
        with path.open(encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                row = json.loads(line)
                if (not isinstance(row, dict) or row.get("kind") != "shot"
                        or type(row.get("rate_index")) is not int
                        or not 0 <= row["rate_index"] < row_count
                        or row.get("family") not in {"binary_css", "bp4", "circuit_dem_bp"}
                        or row.get("outcome") not in {"exact", "stabilizer_equivalent", "invalid_syndrome", "logical_failure", "observable_success", "observable_failure"}):
                    raise ValueError(f"invalid events.jsonl record {line_number}")
                yield row
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("invalid events.jsonl") from error


def _work_columns(root: Path, spec: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    binary = spec["decoder"]["family"] == "binary_css"
    result = [{"mean_iterations": row["mean_iterations"], "mean_directed_edge_updates": None,
               "iteration_unit": "component sweeps" if binary else "sweeps"} for row in rows]
    code = spec["problem"].get("code", {})
    if code.get("kind") != "embedded_css":
        return result
    hx, hz = (sum(sum(row) for row in code[key]) for key in ("hx", "hz"))
    if not binary or hx == hz:
        edges = hz if binary else hx + hz
        for metrics in result:
            metrics["mean_directed_edge_updates"] = 2 * edges * metrics["mean_iterations"]
        return result
    # Unequal X/Z graphs require the retained component counters.
    totals = [0] * len(rows)
    for event in _events(root / "events.jsonl", len(rows)):
        counts = event["iterations"]
        totals[event["rate_index"]] += 2 * (hz * counts["x"] + hx * counts["z"])
    for metrics, row, total in zip(result, rows, totals, strict=True):
        metrics["mean_directed_edge_updates"] = total / row["n"]
    return result


def _finite_duration(value: object, name: str, *, allow_none: bool = False) -> None:
    if value is None and allow_none:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f"ledger {name} must be a finite nonnegative duration")


def _validate_event(event: Mapping[str, Any], *, spec: Mapping[str, Any], point: Mapping[str, Any], shot_number: int) -> None:
    decoder, budget, sampling = spec["decoder"], spec["budgets"], spec["sampling"]
    expected_family = decoder["family"]
    if event.get("family") != expected_family:
        raise ValueError("ledger family does not match the requested decoder")
    if event.get("shot_id") != sampling["shot_start"] + shot_number:
        raise ValueError("ledger shot ids must begin at sampling.shot_start and be contiguous")
    if event.get("p") != point.get("physical_p") or event.get("decoder_p0") != point.get("decoder_p0"):
        raise ValueError("ledger rate values disagree with the requested point")
    if expected_family == "circuit_dem_bp" and event.get("setting_label") != point.get("label"):
        raise ValueError("circuit ledger setting label disagrees with the requested point")
    limits = resolved_sampling(sampling, int(event["rate_index"]), len(spec["rate_points"]))
    # The prior portable contract already admitted code-capacity failure
    # thresholds without an extension marker.  New wire features, rather than
    # every non-core sampling key, distinguish a marker that must be present.
    requires_extended_marker = ("stop_mode" in sampling or "per_point" in sampling
                                or sampling.get("shots") is None or budget.get("max_shots") is None
                                or "noise_sweep" in spec["channel"]
                                or expected_family == "circuit_dem_bp" and any(sampling.get(name) is not None for name in ("stop_type_i", "stop_type_ii")))
    if requires_extended_marker and "sampling_stop_mode" not in event:
        raise ValueError("ledger omits the required extended sampling marker")
    if event.get("sampling_mode") != ("adaptive_stopping" if any(limits.get(name) is not None for name in ("stop_failures", "stop_type_i", "stop_type_ii")) else "fixed_shots"):
        raise ValueError("ledger sampling mode disagrees with the requested specification")
    if "sampling_stop_mode" in event and event.get("sampling_stop_mode") != limits["stop_mode"]:
        raise ValueError("ledger stop mode disagrees with the requested specification")
    if type(event.get("converged")) is not bool:
        raise ValueError("ledger converged must be boolean")
    if expected_family == "circuit_dem_bp" and "sampling_stop_mode" in event:
        failure = event.get("outcome") == "observable_failure"
        if (type(event.get("detector_fit")) is not bool or type(event.get("observable_failure")) is not bool
                or type(event.get("type_i")) is not bool or type(event.get("type_ii")) is not bool
                or event["detector_fit"] != event["converged"] or event["observable_failure"] != failure
                or event["type_i"] != (failure and not event["converged"])
                or event["type_ii"] != (failure and event["converged"])):
            raise ValueError("circuit observable outcome flags disagree with the detailed decoder result")
    _finite_duration(event.get("decode_seconds"), "decode_seconds", allow_none=True)
    _finite_duration(event.get("end_to_end_seconds"), "end_to_end_seconds")
    iterations = event.get("iterations")
    work = event.get("work_units")
    if expected_family == "binary_css":
        if not isinstance(iterations, Mapping) or set(iterations) != {"x", "z"} or any(type(iterations[key]) is not int or iterations[key] < 0 or iterations[key] > budget["max_iterations"] for key in iterations):
            raise ValueError("binary ledger iterations must be bounded nonnegative component counts")
        if not isinstance(work, Mapping) or work.get("unit") != "binary_component_sweeps" or work.get("x") != iterations["x"] or work.get("z") != iterations["z"]:
            raise ValueError("binary ledger work units disagree with iterations")
    else:
        limit = decoder["max_iterations"] if expected_family == "circuit_dem_bp" else budget["max_iterations"]
        if decoder.get("variant") == "qbpgd":
            limit = min(limit, decoder["qbpgd"]["iterations_per_round"] * decoder["qbpgd"]["round_limit"])
        if type(iterations) is not int or iterations < 0 or iterations > limit:
            raise ValueError("ledger iterations must be a bounded nonnegative count")
        unit = "circuit_dem_bp_sweeps" if expected_family == "circuit_dem_bp" else "bp4_joint_sweeps"
        if not isinstance(work, Mapping) or work.get("unit") != unit or work.get("value") != iterations:
            raise ValueError("ledger work units disagree with iterations")
        if decoder.get("variant") == "qbpgd":
            rounds, fixations = work.get("rounds"), work.get("fixations")
            if (type(rounds) is not int or not 0 <= rounds <= decoder["qbpgd"]["round_limit"]
                    or type(fixations) is not int or not 0 <= fixations <= rounds):
                raise ValueError("Q-BPGD ledger rounds or fixations are out of range")


def _validate_counts(summary: Mapping[str, Any], events: Iterator[dict[str, Any]], *, spec: Mapping[str, Any]) -> None:
    sampling, points, total_cap = spec["sampling"], spec["rate_points"], spec["budgets"]["max_shots"]
    assert isinstance(sampling, Mapping) and isinstance(points, list)
    rows = summary.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("summary.json must contain nonempty rows")
    if len(rows) != len(points):
        raise ValueError("summary rate rows disagree with the requested specification")
    buckets = [{"n": 0, "failures": 0, "type_i": 0, "type_ii": 0,
                "exact_successes": 0, "stabilizer_equivalent_successes": 0,
                "observable_successes": 0, "circuit": None, "stopped": False,
                "last_shot_id": None} for _ in rows]
    mapping = {"invalid_syndrome": "type_i", "logical_failure": "type_ii",
               "exact": "exact_successes", "stabilizer_equivalent": "stabilizer_equivalent_successes",
               "observable_success": "observable_successes"}
    for event in events:
        bucket = buckets[event["rate_index"]]
        if bucket["stopped"]:
            raise ValueError("ledger contains a shot after a sampling stop")
        point = points[event["rate_index"]]
        assert isinstance(point, Mapping)
        _validate_event(event, spec=spec, point=point, shot_number=bucket["n"])
        bucket["last_shot_id"] = event["shot_id"]
        circuit = event["family"] == "circuit_dem_bp"
        if bucket["circuit"] is not None and bucket["circuit"] != circuit:
            raise ValueError("ledger mixes code-capacity and circuit outcomes")
        bucket["circuit"] = circuit
        if circuit != event["outcome"].startswith("observable_"):
            raise ValueError("ledger outcome does not belong to its decoder family")
        bucket["n"] += 1
        bucket["failures"] += event["outcome"] not in _SUCCESS
        if circuit:
            bucket["type_i"] += bool(event.get("type_i"))
            bucket["type_ii"] += bool(event.get("type_ii"))
        key = mapping.get(event["outcome"])
        if key:
            bucket[key] += 1
        limits = resolved_sampling(sampling, event["rate_index"], len(points))
        if limits["stop_mode"] == "any" and limits["shots"] is not None and bucket["n"] > limits["shots"]:
            raise ValueError("ledger exceeds the requested per-rate shot cap")
        from .runner import _stopping_reason
        expected_stop = _stopping_reason(limits, shots=bucket["n"], failures=bucket["failures"], type_i=bucket["type_i"], type_ii=bucket["type_ii"])
        declared_stop = event.get("sampling_stop_reason")
        if expected_stop is not None and declared_stop != expected_stop:
            raise ValueError("ledger omits, overshoots, or mislabels a requested sampling threshold")
        if expected_stop is None and declared_stop is not None:
            raise ValueError("ledger has an early or unsupported sampling stop")
        if declared_stop is not None:
            bucket["stopped"] = True
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping) or row.get("rate_index") != index:
            raise ValueError("summary rate rows must be ordered and indexed")
        expected = buckets[index]
        if expected["n"] == 0:
            raise ValueError("ledger has no valid shot records for a rate point")
        limits = resolved_sampling(sampling, index, len(points))
        if not expected["stopped"] or (limits["stop_mode"] == "any" and limits["shots"] is not None and expected["n"] > limits["shots"]):
            raise ValueError("ledger did not terminate each rate point at a valid sampling boundary")
        for name in ("n", "failures"):
            if row.get(name) != expected[name]:
                raise ValueError(f"summary {name} disagrees with ledger at rate {index}")
        for name in ("type_i", "type_ii", "exact_successes", "stabilizer_equivalent_successes"):
            if not expected["circuit"] and row.get(name) != expected[name]:
                raise ValueError(f"summary {name} disagrees with ledger at rate {index}")
        if expected["circuit"]:
            if row.get("observable_successes") != expected["observable_successes"]:
                raise ValueError(f"circuit summary semantics disagree with ledger at rate {index}")
            if row.get("type_i") not in {None, expected["type_i"]} or row.get("type_ii") not in {None, expected["type_ii"]}:
                raise ValueError(f"circuit type partition disagrees with ledger at rate {index}")
    consumed = sum(bucket["n"] for bucket in buckets)
    if spec["problem"]["kind"] == "circuit":
        consumed += len(buckets) * int(sampling["shot_start"])
    if total_cap is not None and consumed > total_cap:
        raise ValueError("ledger exceeds the total experiment shot cap")


def _validate_summary_csv(path: Path, rows: list[Mapping[str, Any]]) -> None:
    """Require the CSV view to be an exact value-level view of summary rows."""
    if not rows:
        raise ValueError("summary rows are required before validating CSV")
    try:
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.DictReader(stream)
            fields = reader.fieldnames
            csv_rows = list(reader)
    except OSError as error:
        raise ValueError("summary.csv is unavailable") from error
    if not fields or len(fields) != len(set(fields)) or set(fields) != set(rows[0]) or len(csv_rows) != len(rows):
        raise ValueError("summary.csv fields or row count do not match the canonical summary")
    for index, (actual, expected) in enumerate(zip(csv_rows, rows, strict=True)):
        rendered = {key: json.dumps(value, sort_keys=True) if isinstance(value, dict) else "" if value is None else str(value)
                    for key, value in expected.items()}
        if actual != {key: rendered[key] for key in fields}:
            raise ValueError(f"summary.csv row {index} does not match the canonical summary")


def normalize_result_directory(result_dir: str | Path) -> dict[str, Any]:
    """Validate a completed manifest-bound run and return a catalog extension.

    This function never writes or copies files.  It rejects partial outputs,
    hash mismatches, unsafe paths, and summary/ledger count disagreements.
    """
    root = Path(result_dir).expanduser().resolve()
    if not root.is_dir() or root.is_symlink():
        raise ValueError("result directory must be a real directory")
    result_manifest = _read_json(root / "result-manifest.json", "result-manifest.json")
    if result_manifest.get("schema") != "research-result-manifest-v1":
        raise ValueError("unsupported result manifest schema")
    files = result_manifest.get("files")
    if not isinstance(files, Mapping) or set(files) != _BOUND_FILES:
        raise ValueError("result manifest must bind the complete portable result set")
    for name, digest in files.items():
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError("result manifest has invalid SHA-256")
        member = _safe_member(root, name)
        with member.open("rb") as stream:
            actual_digest = file_digest(stream, "sha256").hexdigest()
        if actual_digest != digest:
            raise ValueError(f"result manifest hash mismatch: {name}")
    run = _read_json(root / "run-manifest.json", "run-manifest.json")
    status = _read_json(root / "status.json", "status.json")
    spec = _read_json(root / "requested-spec.json", "requested-spec.json")
    effective = _read_json(root / "effective-spec.json", "effective-spec.json")
    summary = _read_json(root / "summary.json", "summary.json")
    if run.get("schema") != "research-run-manifest-v1" or summary.get("schema") != "research-run-summary-v1" or effective.get("schema") != "research-effective-spec-v1":
        raise ValueError("result contains an unsupported portable output schema")
    from .contracts import validate_experiment
    try:
        normalized_spec = validate_experiment(spec)
    except ValueError as error:
        raise ValueError("requested specification fails the portable experiment contract") from error
    if normalized_spec != spec:
        raise ValueError("requested specification is not the canonical validated representation")
    experiment_id = result_manifest.get("experiment_id")
    if not isinstance(experiment_id, str) or not experiment_id or any(value.get("experiment_id") != experiment_id for value in (run, status, summary)):
        raise ValueError("result manifest, run status, and summary identities must agree")
    if status.get("status") != "completed" or effective.get("experiment") != spec:
        raise ValueError("result is incomplete or its effective specification disagrees")
    configuration_sha256 = sha256(_canonical(spec)).hexdigest()
    provenance = run.get("provenance")
    if not isinstance(provenance, Mapping) or not isinstance(provenance.get("implementation_sha256"), str):
        raise ValueError("run provenance lacks an implementation identity")
    expected_experiment_id = sha256(_canonical({"configuration_sha256": configuration_sha256, "implementation_sha256": provenance["implementation_sha256"]})).hexdigest()
    if experiment_id != expected_experiment_id:
        raise ValueError("experiment identity is not derived from configuration and implementation")
    source_hashes, packages, python = provenance.get("implementation_sources"), provenance.get("packages"), provenance.get("python")
    is_digest = lambda value: isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)
    if (not isinstance(source_hashes, Mapping) or not source_hashes
            or any(not isinstance(name, str) or not name or not is_digest(digest) for name, digest in source_hashes.items())
            or not isinstance(packages, Mapping) or not packages
            or any(not isinstance(name, str) or not name or version is not None and not isinstance(version, str) for name, version in packages.items())
            or not isinstance(python, str) or not python.strip()):
        raise ValueError("implementation provenance requires source hashes, package versions, and Python version")
    recomputed_implementation = sha256(_canonical({"sources": dict(source_hashes), "packages": dict(packages), "python": python})).hexdigest()
    if provenance["implementation_sha256"] != recomputed_implementation:
        raise ValueError("implementation provenance hash is internally inconsistent")
    from .evidence import timing_boundaries
    if summary.get("timing_boundaries") != timing_boundaries(normalized_spec["problem"]["kind"]):
        raise ValueError("summary timing boundaries disagree with the execution contract")
    if (run.get("configuration_sha256") != configuration_sha256 or summary.get("configuration_sha256") != configuration_sha256
            or run.get("requested_spec_sha256") != configuration_sha256):
        raise ValueError("run configuration identity disagrees with the portable specification")
    if summary.get("user_label") != normalized_spec["id"]:
        raise ValueError("summary experiment label disagrees with the requested specification")
    if summary.get("provenance") != provenance or effective.get("implementation_sha256") != provenance["implementation_sha256"]:
        raise ValueError("summary or effective implementation provenance disagrees with run manifest")
    if summary.get("effective_configuration") != effective.get("numerical_settings") or summary.get("input_identity") != effective.get("input_identity"):
        raise ValueError("summary effective settings or input identity disagrees with effective specification")
    rows = summary.get("rows")
    events = _events(root / "events.jsonl", len(rows) if isinstance(rows, list) else 0)
    _validate_counts(summary, events, spec=normalized_spec)
    from .runner import _summary_rows
    regenerated_rows = _summary_rows(root / "events.jsonl", points=normalized_spec["rate_points"], kind=normalized_spec["problem"]["kind"], sampling=normalized_spec["sampling"], budgets=normalized_spec["budgets"])
    if summary.get("rows") != regenerated_rows:
        raise ValueError("summary rows do not match the canonical ledger aggregation")
    _validate_summary_csv(root / "summary.csv", regenerated_rows)
    for index, row in enumerate(summary["rows"]):
        adaptive = any(resolved_sampling(spec["sampling"], index, len(spec["rate_points"])).get(field) is not None for field in ("stop_failures", "stop_type_i", "stop_type_ii"))
        if adaptive and (row.get("ci_method") != "unavailable_optional_stopping" or row.get("ci_low") is not None or row.get("ci_high") is not None):
            raise ValueError("adaptive result must not claim a fixed-N confidence interval")
        if not adaptive and row.get("ci_method") != "wilson_score_95":
            raise ValueError("fixed-shot result must retain its Wilson interval")
    input_ref = spec["problem"].get("code", spec["problem"].get("circuit"))
    input_hash = sha256(_canonical(input_ref)).hexdigest()
    short = experiment_id[:16]
    paper_id, code_id, decoder_id, dataset_id = (f"local-run-{short}", f"local-input-{input_hash[:16]}", f"local-decoder-{short}", f"local-dataset-{short}")
    kind = spec["problem"]["kind"]
    work_columns = _work_columns(root, spec, summary["rows"])
    x_semantics = "physical_circuit_noise_probability" if kind == "circuit" and any("physical_p" in point for point in spec["rate_points"]) else "circuit_setting_index" if kind == "circuit" else ("decoder_prior_probability" if spec["channel"]["kind"] == "explicit" else "physical_error_probability")
    points = [{"x": row.get("p") if x_semantics == "physical_circuit_noise_probability" else row["rate_index"] if kind == "circuit" else (row.get("decoder_p0") if x_semantics == "decoder_prior_probability" else row.get("p")),
               "y": row.get("ler") if row.get("ler") is not None else row.get("failure_rate"),
               "n": row["n"], "failures": row["failures"], "ci_low": row.get("ci_low"), "ci_high": row.get("ci_high"),
               "mean_work": row.get("mean_iterations"), "mean_seconds": row.get("mean_decode_seconds"),
               **work_columns[row["rate_index"]],
               "work_unit": row.get("work_unit"), "type_i": row.get("type_i"), "type_ii": row.get("type_ii"),
               "status": row.get("ci_status"), "ci_method": row.get("ci_method"), "denominator": row.get("n"),
               "sampling_mode": row.get("sampling_mode"), "sampling_termination_reason": row.get("sampling_termination_reason"),
               "setting_label": row.get("setting_label"), "x_semantics": x_semantics,
               "runtime_scope": summary.get("timing_boundaries", {}).get("decode_seconds"), "summary": dict(row)} for row in summary["rows"]]
    confidence_methods = {str(row.get("ci_method")) for row in summary["rows"]}
    confidence_method = next(iter(confidence_methods)) if len(confidence_methods) == 1 else "mixed_by_point"
    extension_digest = sha256(_canonical({"experiment_id": experiment_id, "files": dict(files)})).hexdigest()
    extension_id = f"local-result-{extension_digest[:24]}"
    extension: dict[str, Any] = {"schema": "research-catalog-extension-v1", "import_schema": "research-import-extension-v1", "extension_id": extension_id,
        "papers": [{"paper_id": paper_id, "title": f"Local portable run {summary.get('user_label', experiment_id)}", "kind": "local_study", "evidence_status": "local_user_run"}],
        "decoders": [{"decoder_id": decoder_id, "label": spec["decoder"]["family"], "configuration": {"decoder": spec["decoder"], "experiment": spec}}],
        "codes": [{"code_id": code_id, "label": "Portable inline circuit" if kind == "circuit" else "Portable inline CSS code", "input_sha256": input_hash}],
        "circuits": ([{"circuit_id": code_id, "label": "Portable inline Stim circuit", "input_sha256": input_hash}] if kind == "circuit" else []),
        "experiments": [{"experiment_id": experiment_id, "paper_ids": [paper_id], "dataset_ids": [dataset_id], "configuration_sha256": run["configuration_sha256"], "provenance": run.get("provenance")}],
        "datasets": [{"dataset_id": dataset_id, "paper_id": paper_id, "label": "Validated local portable result", "evidence_status": "local_user_run", "source_path": f"research/imported/{extension_id}.json", "asset": {"kind": "portable_result_directory", "label": "Original manifest-bound local result directory", "storage_path": str(root), "storage_instructions": "Retain this directory unchanged; validate result-manifest.json before using its ledger.", "sha256": sha256((root / "result-manifest.json").read_bytes()).hexdigest()}}],
        "result_series": [{"series_id": f"{dataset_id}:{code_id}:{decoder_id}", "dataset_id": dataset_id, "code_id": code_id, "decoder_id": decoder_id, "label": "Validated local portable result", "confidence_method": confidence_method, "denominator_definition": "completed decoded shots per rate point", "runtime_scope": summary.get("timing_boundaries", {}).get("decode_seconds"), "points": points}],
        "inputs": {"problem": spec["problem"], "channel": spec["channel"], "sampling": spec["sampling"], "budgets": spec["budgets"], "decoder": spec["decoder"]},
        "result_integrity": {"result_manifest": result_manifest, "bound_file_hashes": dict(files), "provenance": run.get("provenance"), "input_identity": summary.get("input_identity")},
        "import_manifest": {"experiment_id": experiment_id, "configuration_sha256": run["configuration_sha256"], "result_file_hashes": dict(files), "derived_entry": "catalog-entry.json"}}
    return extension


def _atomic_json(path: Path, value: object, *, exclusive: bool = False) -> None:
    if exclusive and path.exists():
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(_canonical(value)); stream.write(b"\n")
        if exclusive and path.exists():
            raise FileExistsError(path)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def persistent_import(root: str | Path, result_dir: str | Path) -> Path:
    """Persist a normalized extension and register it without copying raw data."""
    extension = normalize_result_directory(result_dir)
    from .catalog_model import validate_catalog
    # Validate the extension's complete relation graph before any persistent
    # write; cross-import identifiers are checked below.
    validate_catalog({kind: list(extension.get(kind, [])) for kind in
                      ("papers", "decoders", "codes", "circuits", "channels", "experiments", "datasets", "result_series")})
    repository = Path(root).expanduser().resolve()
    sources_path = repository / "research" / "catalog" / "sources.json"
    sources = _read_json(sources_path, "research/catalog/sources.json")
    target = repository / "research" / "imported" / f"{extension['extension_id']}.json"
    relative = target.relative_to(repository).as_posix()
    registered = sources.get("normalized_catalogs", [])
    if not isinstance(registered, list) or any(not isinstance(item, str) for item in registered):
        raise ValueError("sources.normalized_catalogs must be an array of paths")
    if target.exists() or relative in registered:
        raise FileExistsError(f"import collision: {extension['extension_id']}")
    # Avoid a latent catalog-build failure when a different local import has
    # already claimed one of this run's normalized identifiers.
    id_fields = {"papers": "paper_id", "decoders": "decoder_id", "codes": "code_id",
                 "circuits": "circuit_id", "experiments": "experiment_id", "datasets": "dataset_id"}
    claimed: dict[str, dict[str, Mapping[str, Any]]] = {kind: {} for kind in id_fields}
    for source in registered:
        path = (repository / source).resolve()
        if not path.is_relative_to(repository) or not path.is_file():
            raise ValueError(f"registered normalized catalog is unavailable: {source}")
        existing = _read_json(path, f"normalized catalog {source}")
        for kind, field in id_fields.items():
            for row in existing.get(kind, []):
                if isinstance(row, Mapping) and isinstance(row.get(field), str):
                    claimed[kind][row[field]] = row
    for kind, field in id_fields.items():
        kept = []
        for row in extension.get(kind, []):
            existing = claimed[kind].get(row[field])
            if existing is None:
                kept.append(row)
            elif kind in {"codes", "circuits"} and _canonical(existing) == _canonical(row):
                # Input artifacts are content-addressed and safely shared by
                # multiple local runs; omit the duplicate entity, retaining
                # the result-series reference to the first import's code.
                continue
            else:
                raise FileExistsError(f"import entity collision: {kind}.{row[field]}")
        extension[kind] = kept
    updated = dict(sources)
    updated["normalized_catalogs"] = [*registered, relative]
    _atomic_json(target, extension, exclusive=True)
    try:
        _atomic_json(sources_path, updated)
    except BaseException:
        target.unlink(missing_ok=True)
        raise
    return target


__all__ = ["normalize_result_directory", "persistent_import"]
