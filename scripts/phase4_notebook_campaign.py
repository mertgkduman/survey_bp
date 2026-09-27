#!/usr/bin/env python3
"""Read-only adapters for retained Phase 4 campaign evidence.

This module deliberately has no runner or subprocess entry point.  A notebook
may display an artifact only with the producer verification that its own stage
schema supports; it may never promote a copied ``status: completed`` flag.
"""
from __future__ import annotations

from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import sys
from typing import Any, Mapping
from bp_registry.phase4_analysis import wilson_interval

ROOT = Path(__file__).resolve().parents[1]
STAGES = ("baseline", "benchmark", "calibration", "selected_settings", "evaluation", "factorial", "native", "traces")
POST_SELECTION = frozenset({"evaluation", "factorial", "native", "traces"})


class _InventoryProofCache:
    """One inventory call's immutable evidence cache; never shared globally."""
    def __init__(self) -> None:
        self.ledgers: dict[tuple[Path, str], list[Mapping[str, Any]]] = {}
        self.contexts: dict[tuple[Path, str, int], Any] = {}

    def events(self, path: Path) -> tuple[tuple[Path, str], list[Mapping[str, Any]]]:
        from bp_registry.ledger import read_canonical_events
        resolved, digest = path.resolve(), _byte_sha(path)
        key = (resolved, digest)
        if key not in self.ledgers:
            events = read_canonical_events(resolved)
            if _byte_sha(resolved) != digest:
                raise ValueError("ledger bytes changed while inventory proof was constructed")
            self.ledgers[key] = events
        return key, self.ledgers[key]

    def context(self, manifest_path: Path, shot_id: int):
        from bp_registry.runner import canonical_public_shot_context
        resolved, digest = manifest_path.resolve(), _byte_sha(manifest_path)
        key = (resolved, digest, shot_id)
        if key not in self.contexts:
            context = canonical_public_shot_context(resolved, shot_id=shot_id)
            if _byte_sha(resolved) != digest:
                raise ValueError("manifest bytes changed while inventory context was constructed")
            self.contexts[key] = context
        return self.contexts[key]


def _json_digest(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                             allow_nan=False).encode()).hexdigest()


def _byte_sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _json_value(value: object) -> object:
    if hasattr(value, "tolist"):
        return _json_value(value.tolist())
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected an object: {path}")
    return value


def _relative(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError as error:
        raise ValueError("artifact path escapes repository root") from error


def _runners():
    """Import analysis-owned readers, never executable code from campaign data."""
    scripts = str(Path(__file__).resolve().parent)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    evaluation = import_module("run_phase4_evaluation")
    factorial = import_module("run_phase4_factorial")
    pilots = import_module("run_phase4_pilots")
    summarize_author_runtime = import_module("summarize_phase4_author_runtime").summarize_author_runtime
    return evaluation, factorial, pilots, summarize_author_runtime


def _missing(stage: str, path: Path, reason: str = "producer artifact is absent") -> dict[str, object]:
    return {"stage": stage, "status": "missing", "execution_qualified": False, "reason": reason,
            "producer": {"path": str(path)}, "assessment": "not_assessed", "tables": []}


def _snapshot(stage: str, path: Path, payload: Mapping[str, Any], *, qualified: bool, reason: str | None,
              tables: list[dict[str, object]]) -> dict[str, object]:
    return {"stage": stage, "status": payload.get("status", "status_missing"), "execution_qualified": qualified,
            "reason": reason, "producer": {"path": str(path), "byte_sha256": _byte_sha(path)},
            "assessment": "not_assessed", "payload": dict(payload), "tables": tables}


def _failure_rows(stage: str, value: Mapping[str, Any]) -> list[dict[str, object]]:
    """Normalize real outcome summaries without filling missing denominators."""
    rows: list[dict[str, object]] = []
    groups = value.get("aggregate", {}).get("by_cell", {}) if isinstance(value.get("aggregate"), Mapping) else {}
    if isinstance(groups, Mapping):
        for key, summary in sorted(groups.items()):
            if not isinstance(summary, Mapping):
                continue
            failure = summary.get("all_shot_failure", {})
            if isinstance(failure, Mapping):
                code, region, arm = str(key).split("/", 2) if str(key).count("/") >= 2 else (str(key), None, None)
                rows.append({"stage": stage, "code_id": code, "arm": arm, "error_rate": region,
                             "failures": failure.get("failures"), "denominator": failure.get("denominator"),
                             "estimate": failure.get("estimate"), "wilson_95": failure.get("wilson_95"),
                             "runtime_tails": summary.get("runtime_seconds"), "runtime_scope": "public cell boundary", "resource_tails": summary.get("resource_maxrss_kib")})
    codes = value.get("codes")
    if isinstance(codes, Mapping):
        for code_id, arms in sorted(codes.items()):
            if not isinstance(arms, Mapping):
                continue
            for arm, item in sorted(arms.items()):
                if not isinstance(item, Mapping):
                    continue
                summary = item.get("summary", item)
                primary = summary.get("all_shot_failure") if isinstance(summary, Mapping) else None
                if not isinstance(primary, Mapping) and isinstance(summary, Mapping):
                    primary = summary.get("primary")
                if isinstance(primary, Mapping):
                    rows.append({"stage": stage, "code_id": code_id, "arm": arm, "error_rate": item.get("error_rate"),
                                 "failures": primary.get("failures"), "denominator": primary.get("denominator"),
                                 "estimate": primary.get("estimate"), "wilson_95": primary.get("wilson_95", primary.get("interval")),
                                 "runtime_tails": summary.get("public_elapsed_seconds", summary.get("runtime_seconds")), "runtime_scope": "producer-declared public boundary",
                                 "resource_tails": summary.get("resource_measurements", {"missing": "not retained by producer"}),
                                 "diagnostic_cells": summary.get("diagnostic_cells"), "selected_valid_syndrome_logical_error": summary.get("selected_valid_syndrome_logical_error"),
                                 "termination_counts": summary.get("termination_counts"), "work_vectors": summary.get("work_vectors")})
    return rows


def _table(stage: str, rows: list[dict[str, object]]) -> dict[str, object]:
    return {"stage": stage, "name": f"{stage}_failure_accounting", "title": f"{stage} failure accounting",
            "columns": ["stage", "code_id", "arm", "error_rate", "failures", "denominator", "estimate", "wilson_95", "runtime_tails", "runtime_scope", "resource_tails", "diagnostic_cells", "selected_valid_syndrome_logical_error", "termination_counts", "work_vectors"], "rows": rows}


def _benchmark_rows(report: Mapping[str, Any]) -> list[dict[str, object]]:
    """Flatten actual active-V4 code/rate/preset/arm records for presentation."""
    rows = []
    for code_id, code in sorted(report.get("codes", {}).items()):
        if not isinstance(code, Mapping): continue
        for rate_key, rate in sorted(code.get("rates", {}).items()):
            if not isinstance(rate, Mapping): continue
            for preset, arms in sorted(rate.get("presets", {}).items()):
                if not isinstance(arms, Mapping): continue
                for arm_name, arm in sorted(arms.items()):
                    if not isinstance(arm, Mapping): continue
                    rows.append({"stage": "benchmark", "code_id": code_id, "arm": arm_name, "preset": preset, "rate_id": rate_key,
                                 "error_rate": rate.get("error_rate"), "failures": None, "denominator": None, "estimate": None, "wilson_95": None,
                                 "runtime_tails": arm.get("public_command_wall_seconds"), "runtime_scope": "active-V4 public command boundary",
                                 "resource_tails": {"missing": "benchmark producer retains no RSS measurement"}, "raw_work": arm.get("raw_work"),
                                 "termination_counts": arm.get("termination_counts"), "selection_status": code.get("selection_status"),
                                 "active_memory_verified": arm.get("active_memory_verified")})
    return rows


def _verify_active_benchmark(root: Path, report: Mapping[str, Any], *, cache: _InventoryProofCache | None = None) -> None:
    """Reconstruct every retained active-V4 public arm from its own journal."""
    active = import_module("run_phase4_active_benchmark")
    cache = _InventoryProofCache() if cache is None else cache
    artifact_root = root / str(report.get("artifact_root", ""))
    _relative(root, artifact_root)
    if not artifact_root.is_dir():
        raise ValueError("active benchmark artifact root is absent")
    if not isinstance(report.get("core_commits"), list) or not all(isinstance(item, str) for item in report["core_commits"]):
        raise ValueError("active benchmark omits typed core provenance")
    if not isinstance(report.get("author_source_pin"), str):
        raise ValueError("active benchmark omits typed source provenance")
    for code_id, code in report["codes"].items():
        if not isinstance(code, Mapping):
            raise ValueError("active benchmark code record is malformed")
        for rate_key, rate in code.get("rates", {}).items():
            if not isinstance(rate, Mapping) or not isinstance(rate.get("error_rate"), (int, float)):
                raise ValueError("active benchmark rate record is malformed")
            for preset, arms in rate.get("presets", {}).items():
                if not isinstance(arms, Mapping):
                    raise ValueError("active benchmark preset record is malformed")
                for arm_name, arm in arms.items():
                    if not isinstance(arm, Mapping) or arm.get("status") != "completed":
                        raise ValueError("active benchmark arm is nonterminal")
                    if arm.get("active_memory_verified") is not True or not isinstance(arm.get("attempts"), list):
                        raise ValueError("active benchmark arm omits public active-memory observations")
                    cell_root = artifact_root / str(code_id) / str(rate_key) / str(preset) / str(arm_name).replace("_", "-")
                    manifest, journal, run = cell_root / "manifest.json", cell_root / "attempts.json", cell_root / "run"
                    if not manifest.is_file() or not journal.is_file() or not (run / "events.jsonl").is_file():
                        raise ValueError("active benchmark terminal provenance files are absent")
                    if arm.get("manifest_sha256") != _json_digest(_read(manifest)):
                        raise ValueError("active benchmark manifest digest differs from retained manifest")
                    retained_manifest = _read(manifest)
                    if retained_manifest.get("error_rate") != rate.get("error_rate"):
                        raise ValueError("active benchmark manifest error rate differs from labeled rate")
                    if arm.get("active_tuning") != retained_manifest.get("relay", {}).get("memory_tuning"):
                        raise ValueError("active benchmark relay tuning differs from retained manifest")
                    attempts = json.loads(journal.read_text(encoding="utf-8"))
                    if attempts != arm["attempts"] or not attempts:
                        raise ValueError("active benchmark report attempts differ from retained journal")
                    shot_ids = [attempt.get("shot_id") for attempt in attempts if isinstance(attempt, Mapping)]
                    if len(attempts) != int(active.SHOTS) or len(shot_ids) != len(set(shot_ids)) or set(shot_ids) != set(range(int(active.SHOTS))):
                        raise ValueError("active benchmark attempts do not cover each planned shot exactly once")
                    for attempt in attempts:
                        if not isinstance(attempt, Mapping) or attempt.get("status") != "completed":
                            raise ValueError("active benchmark completed arm retains incomplete shot")
                        verified = _verify_relay_shot(manifest, run, shot_id=int(attempt["shot_id"]), expected_row=attempt, cache=cache)
                        facts = attempt.get("active_memory_facts")
                        if not isinstance(facts, list) or not facts:
                            raise ValueError("active benchmark shot omits typed active-memory facts")
                        if any(not isinstance(fact, Mapping) or fact.get("evidence_relation") != "canonical_implemented"
                               or fact.get("assessment_status") != "not_assessed" or fact.get("code_id") != code_id
                               for fact in facts):
                            raise ValueError("active benchmark active-memory facts drift from canonical contract")
                        _ledger_key, ledger_events = cache.events(run / "events.jsonl")
                        ledger_facts = active._attempt_from_events(ledger_events, int(attempt["shot_id"]))
                        if facts != ledger_facts["active_memory_facts"] or not active._active_memory_proven(ledger_facts):
                            raise ValueError("active benchmark facts differ from retained terminal ledger")
                        if verified["work"] != attempt.get("work_vector"):
                            raise ValueError("active benchmark reported work differs from terminal ledger")
                    work_total: dict[str, int] = {}
                    for attempt in attempts:
                        for name, amount in attempt["work_vector"].items():
                            work_total[name] = work_total.get(name, 0) + amount
                    reconstructed = {
                        "status": "completed",
                        "active_memory_verified": all(active._active_memory_proven(attempt) for attempt in attempts),
                        "public_command_wall_seconds": active._distribution(
                            [attempt.get("public_boundary", {}).get("elapsed_seconds") for attempt in attempts]),
                        "distinct_leg_count_distribution": active._distribution(
                            [float(len(attempt["distinct_leg_indices"])) for attempt in attempts]),
                        "raw_work": {"availability": "observed", "total": work_total,
                                     "per_shot": [attempt["work_vector"] for attempt in attempts]},
                        "termination_counts": {key: sum(attempt.get("termination") == key for attempt in attempts)
                                               for key in sorted({attempt.get("termination") for attempt in attempts if attempt.get("termination")})},
                    }
                    if any(arm.get(key) != value for key, value in reconstructed.items()):
                        raise ValueError("active benchmark arm aggregates differ from retained journal")


def _calibration_rows(value: Mapping[str, Any]) -> list[dict[str, object]]:
    rows = []
    for code_id, code in sorted(value.get("codes", {}).items()):
        if not isinstance(code, Mapping): continue
        for preset, group in sorted(code.get("presets", {}).items()):
            if not isinstance(group, Mapping): continue
            for configuration in group.get("configurations", []):
                if not isinstance(configuration, Mapping): continue
                logical = configuration.get("logical_failure", {})
                rows.append({"stage": "calibration", "code_id": code_id, "arm": preset,
                             "error_rate": configuration.get("central_error_rate"),
                             "failures": logical.get("failures") if isinstance(logical, Mapping) else None,
                             "denominator": logical.get("denominator") if isinstance(logical, Mapping) else None,
                             "estimate": logical.get("estimate") if isinstance(logical, Mapping) else None,
                             "wilson_95": logical.get("wilson_95") if isinstance(logical, Mapping) else None,
                             "runtime_tails": configuration.get("runtime_seconds"), "runtime_scope": "calibration public boundary",
                             "resource_tails": configuration.get("resource_measurements"),
                             "configuration_id": configuration.get("configuration_id"), "attempts": configuration.get("attempts")})
    return rows


def _caps(root: Path, pilots) -> tuple[Path, dict[str, Any]]:
    path = root / "data/manifests/phase4-pilot-caps.json"
    value = _read(path)
    if value.get("caps_digest") != pilots._digest({k: v for k, v in value.items() if k != "caps_digest"}):
        raise ValueError("frozen caps digest does not verify")
    return path, value


def _verify_relay_shot(manifest_path: Path, run_dir: Path, *, shot_id: int, expected_row: Mapping[str, Any] | None = None,
                       require_semantic: bool = False, cache: _InventoryProofCache | None = None) -> dict[str, object]:
    """Purely reconstruct one retained public V4 Relay terminal and bind it to its manifest."""
    from bp_registry.canonical.verification import reconstruct_phase4_shot, validate_canonical_shot
    cache = _InventoryProofCache() if cache is None else cache
    context = cache.context(manifest_path, shot_id)
    _ledger_key, events = cache.events(run_dir / "events.jsonl")
    stream = [event for event in events if event.get("run_id") == context.run_id and event.get("shot_id") == shot_id]
    if context.compact_manifest.get("schema_version") == 5:
        terminal = validate_canonical_shot(stream, context, trace_root=run_dir)
        verified = {"terminal": terminal, "work": terminal.get("data", {}).get("work_vector"), "traces": []}
    else:
        verified = reconstruct_phase4_shot(events, run_id=context.run_id, shot_id=shot_id, trace_root=run_dir)
        terminal = verified["terminal"]
    begin = stream[0]
    data = terminal["data"]
    if begin.get("sample_seed_identity") != context.sample_seed_identity:
        raise ValueError("ledger sample identity differs from manifest context")
    for key, expected in (("manifest_sha256", context.manifest_sha256), ("execution_identity", context.execution_identity),
                          ("decoder_seed_identity", context.decoder_seed_identity), ("code_id", context.code_id)):
        if data.get(key) != expected:
            raise ValueError(f"ledger terminal {key} differs from manifest context")
    if expected_row is not None and expected_row.get("work_vector") is not None and expected_row.get("work_vector") != verified["work"]:
        raise ValueError("reported row work differs from reconstructed ledger work")
    evaluation, _factorial, _pilots, _runtime = _runners()
    candidate, candidate_origin = evaluation.terminal_candidate_for_diagnosis(
        data, termination=terminal.get("termination"))
    diagnosis = evaluation.classify_candidate(manifest_path, shot_id=shot_id, candidate=candidate, context=context)
    semantic = {**diagnosis, "selected": data.get("selection_status") == "frozen_decoder_visible_candidate",
                "selection_status": data.get("selection_status"), "candidate_origin": candidate_origin,
                "outcome": data.get("outcome")}
    if expected_row is not None:
        for key, value in semantic.items():
            if require_semantic and key not in expected_row:
                raise ValueError(f"reported row omits terminal semantic field {key}")
            if key in expected_row and expected_row.get(key) != value:
                raise ValueError(f"reported row {key} differs from terminal candidate evidence")
    return {"terminal": terminal, "work": verified["work"], "sample_identity": begin.get("sample_seed_identity"),
            "trace_count": len(verified["traces"]), "semantic": semantic}


def _benchmark(root: Path, *, cache: _InventoryProofCache | None = None) -> dict[str, object]:
    _evaluation, _factorial, pilots, _runtime = _runners()
    cache = _InventoryProofCache() if cache is None else cache
    try:
        caps_path, caps = _caps(root, pilots)
        cited = caps["benchmark_evidence"]["active_v4"]
        report_path = root / str(cited["path"])
        if not report_path.is_file() or _byte_sha(report_path) != cited["byte_sha256"]:
            raise ValueError("active benchmark bytes differ from frozen cap citation")
        report = _read(report_path)
        if report.get("report_digest") != cited["report_digest"] or report.get("report_digest") != pilots._digest({k: v for k, v in report.items() if k != "report_digest"}):
            raise ValueError("active benchmark digest differs from frozen cap citation")
        codes = report.get("codes")
        if report.get("status") != "completed" or not isinstance(codes, Mapping) or not codes:
            raise ValueError("active benchmark is nonterminal or omits code records")
        if any(not isinstance(item, Mapping) or not isinstance(item.get("selected_rate"), (int, float)) or not isinstance(item.get("selection_status"), str) for item in codes.values()):
            raise ValueError("active benchmark code record omits selected-rate status")
        _verify_active_benchmark(root, report, cache=cache)
        return _snapshot("benchmark", report_path, report, qualified=True, reason=None,
                         tables=[_table("benchmark", _benchmark_rows(report))])
    except (KeyError, OSError, ValueError) as error:
        if "report" in locals() and "report_path" in locals() and report_path.is_file():
            return _snapshot("benchmark", report_path, report, qualified=False, reason=str(error),
                             tables=[_table("benchmark", _benchmark_rows(report))])
        fallback = root / "data/results/phase4-memory-relay/benchmark.json"
        if not fallback.is_file(): return _missing("benchmark", fallback, str(error))
        payload = _read(fallback)
        return _snapshot("benchmark", fallback, payload, qualified=False,
                         reason=f"historical benchmark metadata only: {error}", tables=[_table("benchmark", _failure_rows("benchmark", payload))])


def _verified_inputs(root: Path):
    evaluation, _factorial, _pilots, _runtime = _runners()
    relay = root / "data/results/phase4-memory-relay"
    return evaluation, evaluation.verified_inputs(
        root=root, caps_path=root / "data/manifests/phase4-pilot-caps.json",
        calibration_path=relay / "calibration/result.json", selection_path=relay / "selected-settings.json",
        freeze_selection=False,
    )


def _calibration_or_selection(root: Path, stage: str) -> dict[str, object]:
    relay = root / "data/results/phase4-memory-relay"; path = relay / ("calibration/result.json" if stage == "calibration" else "selected-settings.json")
    if not path.is_file(): return _missing(stage, path)
    payload = _read(path)
    try:
        if stage == "calibration":
            evaluation, _factorial, _pilots, _runtime = _runners()
            _caps, chosen = evaluation.verified_calibration_inputs(
                root=root, caps_path=root / "data/manifests/phase4-pilot-caps.json", calibration_path=path)
        else:
            _evaluation, (_caps, _calibration, chosen) = _verified_inputs(root)
        if chosen != payload: raise ValueError("verified producer input differs from retained artifact")
        rows = _calibration_rows(payload) if stage == "calibration" else _failure_rows(stage, payload)
        return _snapshot(stage, path, payload, qualified=True, reason=None, tables=[_table(stage, rows)])
    except (FileNotFoundError, OSError, ValueError) as error:
        rows = _calibration_rows(payload) if stage == "calibration" else _failure_rows(stage, payload)
        return _snapshot(stage, path, payload, qualified=False, reason=str(error), tables=[_table(stage, rows)])


def _evaluation(root: Path, *, cache: _InventoryProofCache) -> dict[str, object]:
    path = root / "data/results/phase4-memory-relay/evaluation/result.json"
    if not path.is_file(): return _missing("evaluation", path)
    payload = _read(path)
    try:
        runner, (caps, _calibration, selection) = _verified_inputs(root)
        plan = runner.evaluation_plan(caps, selection)
        arms = tuple(caps["evaluation"]["arms_per_code"])
        if payload.get("plan_digest") != runner._digest(plan) or payload.get("caps_digest") != caps["caps_digest"] or payload.get("selected_settings_digest") != runner._digest(selection):
            raise ValueError("evaluation result does not bind the verified three-arm plan")
        retained_plan = _read(path.parent / "plan.json")
        if retained_plan != plan:
            raise ValueError("retained evaluation plan differs from verified producer plan")
        if payload.get("shared_settings_view") != plan.get("shared_settings_view"):
            raise ValueError("evaluation result shared settings differ from verified plan")
        if set(payload.get("codes", {})) != set(caps["codes"]) or any(set(payload.get("codes", {}).get(code, {})) != set(arms) for code in caps["codes"]):
            raise ValueError("evaluation result omits or adds frozen arms")
        if payload.get("status") != "completed": raise ValueError("evaluation producer is nonterminal")
        relay = path.parent
        for cell in plan["cells"]:
            arm = payload["codes"][cell["code_id"]][cell["arm"]]
            if arm.get("status") != "completed": raise ValueError("evaluation arm is not terminal")
            cell_root = relay / cell["code_id"] / cell["arm"]
            manifest = cell_root / "manifest.json"; attempts = cell_root / "attempts.json"; run = cell_root / "run"
            if not manifest.is_file() or not attempts.is_file() or not (run / "events.jsonl").is_file():
                raise ValueError("evaluation terminal provenance files are absent")
            rows = json.loads(attempts.read_text(encoding="utf-8"))
            if not isinstance(rows, list): raise ValueError("evaluation attempts are not a list")
            expected_manifest = runner.build_manifest(
                base=_read(root / runner.active.CODE_MANIFESTS[cell["code_id"]]), cell=cell, plan=plan)
            if _read(manifest) != expected_manifest:
                raise ValueError("evaluation manifest differs from verified producer plan")
            if {int(row["shot_id"]) for row in rows if isinstance(row, Mapping)} != set(range(int(cell["shots"]))):
                raise ValueError("evaluation attempts do not cover every planned shot")
            for row in rows:
                if not isinstance(row, Mapping) or row.get("status") != "completed":
                    raise ValueError("completed evaluation result retains incomplete shot")
                _verify_relay_shot(manifest, run, shot_id=int(row["shot_id"]), expected_row=row, require_semantic=True, cache=cache)
            if runner.summarize_rows(rows, planned=int(cell["shots"])) != arm.get("summary"):
                raise ValueError("evaluation summary differs from verified attempts")
        if payload.get("evaluation_category_wall_seconds_used") != runner.retained_category_wall(path.parent):
            raise ValueError("evaluation category wall differs from retained terminal records")
        expected_pairs = {code_id: {arm: runner.matched_summary(output=path.parent, code_id=code_id, first="baseline", second=arm)
                         for arm in arms if arm != "baseline"} for code_id in caps["codes"]}
        if payload.get("paired") != expected_pairs:
            raise ValueError("evaluation matched cohorts differ from retained attempts")
        rows = _failure_rows("evaluation", payload)
        rates = {(cell["code_id"], cell["arm"]): cell["error_rate"] for cell in plan["cells"]}
        for row in rows:
            row["error_rate"] = rates.get((row["code_id"], row["arm"]))
        return _snapshot("evaluation", path, payload, qualified=True, reason=None,
                         tables=[_table("evaluation", rows)])
    except (FileNotFoundError, OSError, ValueError) as error:
        return _snapshot("evaluation", path, payload, qualified=False, reason=str(error), tables=[_table("evaluation", _failure_rows("evaluation", payload))])


def _factorial(root: Path, *, cache: _InventoryProofCache) -> dict[str, object]:
    path = root / "data/results/phase4-memory-relay/factorial/result.json"
    if not path.is_file(): return _missing("factorial", path)
    payload = _read(path)
    try:
        predecessor = _evaluation(root, cache=cache)
        if predecessor.get("execution_qualified") is not True:
            raise ValueError("factorial predecessor lacks full evaluation terminal proof")
        _evaluation_runner, factorial, pilots, _runtime = _runners()
        _caps_path, caps = _caps(root, pilots)
        plan = factorial.build_factorial_plan(design=_read(root / "data/evidence/phase4-pilot-design.json"), caps=caps,
                                              supplement=_read(root / "data/evidence/phase4-factorial-execution-supplement-v1.json"))
        factorial.assert_factorial_predecessor(evaluation_path=root / "data/results/phase4-memory-relay/evaluation/result.json", plan=plan, repository_root=root)
        if payload.get("factorial_digest") != plan["factorial_digest"]: raise ValueError("factorial result plan digest differs")
        rows = payload.get("terminals")
        if not isinstance(rows, list) or len(rows) != len(plan["cells"]):
            raise ValueError("factorial result does not retain every planned terminal")
        if {row.get("cell_id") for row in rows if isinstance(row, Mapping)} != {cell["cell_id"] for cell in plan["cells"]}:
            raise ValueError("factorial result terminal identities differ from frozen plan")
        if any(not isinstance(row, Mapping) or row.get("execution_status") != "completed" for row in rows):
            raise ValueError("factorial producer is incomplete or inconclusive")
        if payload.get("status") != factorial._result_status(payload.get("predecessor", {}), rows):
            raise ValueError("factorial result status differs from retained terminals")
        factorial.validate_trace_inventory(rows, plan)
        cells = {cell["cell_id"]: cell for cell in plan["cells"]}
        for row in rows:
            cell = cells.get(row.get("cell_id")); artifact = row.get("artifact")
            if cell is None or not isinstance(artifact, Mapping): raise ValueError("factorial terminal lacks cell artifact provenance")
            manifest = Path(str(artifact.get("manifest_path", ""))).resolve(); run = Path(str(artifact.get("run_dir", ""))).resolve()
            _relative(root, manifest); _relative(root, run)
            if not manifest.is_file() or _byte_sha(manifest) != artifact.get("manifest_sha256") or not (run / "events.jsonl").is_file():
                raise ValueError("factorial manifest or ledger provenance differs")
            if _read(manifest) != factorial.build_public_manifest(repository_root=root, cell=cell, plan=plan):
                raise ValueError("factorial manifest differs from frozen cell plan")
            verified = _verify_relay_shot(manifest, run, shot_id=int(cell["shot_id"]),
                                          expected_row={**row, "work_vector": row.get("raw_work")}, require_semantic=True, cache=cache)
            if verified["sample_identity"] != row.get("sample_identity"):
                raise ValueError("factorial terminal sample identity differs from verified ledger")
        if payload.get("aggregate") != factorial.aggregate_terminals(rows, plan):
            raise ValueError("factorial aggregates differ from retained terminals")
        expected_trace_inventory = [{"cell_id": row["cell_id"], "code_id": row["code_id"], "noise_region": row["noise_region"],
                                     "arm_id": row["arm_id"], "shot_id": row["shot_id"], "execution_status": row["execution_status"],
                                     "trace": row.get("trace", {"status": "missing"})} for row in rows]
        if payload.get("trace_inventory") != expected_trace_inventory:
            raise ValueError("factorial trace inventory differs from retained terminals")
        display_rows = _failure_rows("factorial", payload)
        rates = {(cell["code_id"], cell["noise_region"]): cell["error_rate"] for cell in plan["cells"]}
        for row in display_rows:
            row["error_rate"] = rates.get((row["code_id"], row["error_rate"]))
        return _snapshot("factorial", path, payload, qualified=True, reason=None,
                         tables=[_table("factorial", display_rows)])
    except (FileNotFoundError, OSError, ValueError) as error:
        return _snapshot("factorial", path, payload, qualified=False, reason=str(error), tables=[_table("factorial", _failure_rows("factorial", payload))])


def _historical_native(root: Path) -> dict[str, object]:
    path = root / "data/results/phase4-memory-relay/author-v022-agreement-v1/runtime-comparison.json"
    if not path.is_file(): return _missing("historical_author_agreement", path)
    payload = _read(path)
    try:
        _evaluation, _factorial, _pilots, summarize = _runners()
        summary = summarize(path.parent)
        if summary != payload: raise ValueError("historical runtime summary differs from verified agreement pairs")
        rows = [{"stage": "native", "code_id": code, "arm": "canonical_vs_author_native",
                 "error_rate": None, "failures": item.get("exact_candidate_disagreements"), "denominator": item.get("paired_shots"),
                 "estimate": None, "wilson_95": None, "runtime_tails": {"canonical_public": item.get("canonical_public_seconds"), "native_pipeline": item.get("native_pipeline_seconds")},
                 "runtime_scope": "unequal recorded public-vs-native pipeline boundaries; diagnostic only", "resource_tails": None}
                for code, item in sorted(summary.get("codes", {}).items()) if isinstance(item, Mapping)]
        return _snapshot("historical_author_agreement", path, payload, qualified=False,
                         reason="historical author agreement is not fresh selected evaluation or factorial evidence",
                         tables=[{**_table("native", rows), "name": "historical_author_agreement", "title": "historical author agreement diagnostics", "display_limit": 30}])
    except (OSError, ValueError) as error:
        return _snapshot("historical_author_agreement", path, payload, qualified=False, reason=str(error), tables=[])


def _native(root: Path, *, cache: _InventoryProofCache) -> dict[str, object]:
    path = root / "data/results/phase4-memory-relay/evaluation/native-pairs/result.json"
    if not path.is_file(): return _missing("native", path)
    payload = _read(path)
    try:
        evaluation, (caps, _calibration, selection) = _verified_inputs(root)
        plan = evaluation.evaluation_plan(caps, selection)
        if payload.get("status") != "completed": raise ValueError("native producer is nonterminal")
        if payload.get("selected_settings_digest") != evaluation._digest(selection) or payload.get("author_pin") != evaluation.pilot._ACTIVE_V4_AUTHOR_PIN:
            raise ValueError("native result does not bind selected settings and approved author pin")
        if set(payload.get("codes", {})) != set(caps["codes"]):
            raise ValueError("native result omits or adds a frozen code")
        native_cells = {code_id: evaluation.native_cell(caps, selection, code_id, plan) for code_id in caps["codes"]}
        for code_id, item in payload["codes"].items():
            if not isinstance(item, Mapping): raise ValueError("native code report is malformed")
            cell = native_cells[code_id]
            if cell.get("status") != "ready" or item.get("planned_pairs") != cell.get("shots") or item.get("namespace") != cell.get("native_pair_namespace"):
                raise ValueError("native report differs from the frozen selected cell")
            journal = path.parent / code_id / "native-attempts.json"
            saved = _read(journal).get("attempts")
            if not isinstance(saved, list) or evaluation.summarize_rows(saved, planned=int(item["planned_pairs"])) != item.get("native_summary"):
                raise ValueError("native retained attempts do not reconstruct native summary")
            canonical_root = path.parent / code_id / "canonical"
            manifest = canonical_root / "manifest.json"
            expected_manifest = evaluation.build_manifest(base=_read(root / evaluation.active.CODE_MANIFESTS[code_id]), cell=cell, plan=plan)
            expected_manifest["run_id"] = "phase4-native-matched-" + evaluation._digest({"cell": cell, "selection": plan["selected_settings_digest"]})[:24]
            if _read(manifest) != expected_manifest:
                raise ValueError("native canonical manifest differs from frozen cell")
            canonical_rows = json.loads((canonical_root / "attempts.json").read_text(encoding="utf-8"))
            if len(canonical_rows) != int(cell["shots"]) or len({row.get("shot_id") for row in canonical_rows}) != len(canonical_rows) or {row.get("shot_id") for row in canonical_rows} != set(range(int(cell["shots"]))):
                raise ValueError("native canonical journal does not cover every planned shot")
            for canonical in canonical_rows:
                if canonical.get("status") != "completed":
                    raise ValueError("completed native result retains incomplete canonical pair")
                _verify_relay_shot(manifest, canonical_root / "run", shot_id=int(canonical["shot_id"]), expected_row=canonical, require_semantic=True, cache=cache)
            if len(saved) != int(cell["shots"]) or len({row.get("shot_id") for row in saved}) != len(saved) or {row.get("shot_id") for row in saved} != set(range(int(cell["shots"]))):
                raise ValueError("native journal does not cover every planned shot")
            pairs = []
            canonical_by_id = {row["shot_id"]: row for row in canonical_rows}
            for native in saved:
                canonical = canonical_by_id.get(native.get("shot_id"))
                if native.get("status") != "completed" or canonical is None or native.get("sample_identity") != canonical.get("sample_identity"):
                    raise ValueError("native paired identity or terminal status differs")
                payload_path = Path(str(native.get("native_payload_path", ""))).resolve()
                result_path = Path(str(native.get("native_result_path", ""))).resolve()
                _relative(root, payload_path); _relative(root, result_path)
                if not payload_path.is_file() or _byte_sha(payload_path) != native.get("native_payload_sha256") or not result_path.is_file() or _byte_sha(result_path) != native.get("native_result_sha256"):
                    raise ValueError("native author payload/result transcript is absent or hash-mismatched")
                transcript = _read(result_path); native_payload = _read(payload_path)
                if transcript.get("candidate") != native.get("candidate") or transcript.get("module_origin") != native.get("native_module_origin") or transcript.get("success") != native.get("success_flag"):
                    raise ValueError("native result transcript differs from retained journal")
                later_legs = 2 if code_id == "b1-ghp-882" else 30
                from bp_registry.native.relay_v022 import RelayV022Adapter
                from bp_registry.runner import canonical_public_shot_context
                context = canonical_public_shot_context(manifest, shot_id=int(native["shot_id"]))
                observation = {"check_matrix": context.code.hz.tolist(), "syndrome": list(context.syndrome),
                               "error_priors": [context.error_rate] * int(context.code.hz.shape[1]),
                               "sample_identity": context.sample_seed_identity, "decoder_seed": int(native["shot_id"])}
                _gammas, expected_digests = evaluation.explicit_native_gammas(manifest, observation, later_legs=later_legs)
                tuning = manifest["relay"]["memory_tuning"]
                settings = {"gamma0": float(cell["candidate"]["gamma0"]), "pre_iter": 80, "num_sets": later_legs,
                            "set_max_iter": 60, "gamma_dist_interval": (float(tuning["later_leg_center"]) - float(tuning["later_leg_width"]) / 2, float(tuning["later_leg_center"]) + float(tuning["later_leg_width"]) / 2),
                            "explicit_gammas": _gammas, "stop_nconv": 1, "stopping_criterion": "nconv", "logging": False}
                expected_payload = RelayV022Adapter().translate(check_matrix=observation["check_matrix"], syndrome=observation["syndrome"],
                    error_priors=observation["error_priors"], relay_settings=settings, seed=observation["decoder_seed"], numerical_profile="f64")
                if _json_value(native_payload) != _json_value(expected_payload):
                    raise ValueError("native author payload differs from canonical public observation")
                if native.get("gamma_digests") != expected_digests or native.get("executed_gamma_digests_checked") != later_legs:
                    raise ValueError("native gamma evidence differs from frozen canonical replay")
                diagnosis = evaluation.classify_candidate(manifest, shot_id=int(native["shot_id"]), candidate=native.get("candidate"))
                if any(native.get(key) != value for key, value in diagnosis.items()) or native.get("selected") != bool(native.get("success_flag") and diagnosis["syndrome_valid"]):
                    raise ValueError("native diagnostic evidence differs from retained candidate")
                pairs.append({"shot_id": native["shot_id"], "sample_identity": native["sample_identity"],
                              "arms": {"canonical_source": canonical, "author_native": native}})
            if item.get("complete_pairs") != len(pairs) or item.get("paired") != evaluation.summarize_matched_cohort(pairs, arm_names=("canonical_source", "author_native")):
                raise ValueError("native paired aggregate differs from retained journals")
        if payload.get("native_category_wall_seconds_used") != evaluation.native_category_wall(path.parent):
            raise ValueError("native category wall differs from retained terminal records")
        return _snapshot("native", path, payload, qualified=True, reason=None, tables=[_table("native", _failure_rows("native", payload))])
    except (FileNotFoundError, OSError, ValueError, KeyError) as error:
        return _snapshot("native", path, payload, qualified=False, reason=str(error), tables=[_table("native", _failure_rows("native", payload))])


def _traces(root: Path, factorial_snapshot: Mapping[str, object]) -> dict[str, object]:
    """Trace links are factorial terminals, not an independent producer index."""
    path = root / "data/results/phase4-memory-relay/factorial/result.json"
    if not path.is_file(): return _missing("traces", path, "factorial terminal trace inventory is absent")
    payload = _read(path)
    if factorial_snapshot.get("execution_qualified") is not True:
        return _snapshot("traces", path, payload, qualified=False,
                         reason="factorial terminal/sidecar reconstruction is unavailable", tables=[])
    return _snapshot("traces", path, payload, qualified=True, reason=None, tables=[])


def _synthetic_fixture() -> dict[str, object]:
    rows = [{"stage": stage, "code_id": "development-fixture-code", "arm": "fixture-baseline", "error_rate": 0.03,
             "failures": 1, "denominator": 7, "estimate": 1 / 7, "wilson_95": wilson_interval(1, 7),
             "runtime_tails": {"p95": 0.01}, "runtime_scope": "synthetic development fixture", "resource_tails": {"missing": 1}} for stage in STAGES]
    artifacts = {stage: {"stage": stage, "status": "development_fixture_not_assessed", "execution_qualified": False,
                         "reason": "synthetic development fixture", "assessment": "not_assessed", "tables": [_table(stage, [row])]} for stage, row in zip(STAGES, rows)}
    return {"schema_version": 1, "mode": "development_fixture", "assessment": "not_assessed", "artifacts": artifacts,
            "tables": [table for item in artifacts.values() for table in item["tables"]], "summary": {"qualified_stages": [], "unavailable_stages": list(STAGES)}}


def build_campaign_snapshots(root: Path = ROOT, *, campaign_root: Path | None = None,
                             development_fixture: bool = False) -> dict[str, object]:
    """Return only retained evidence snapshots; never execute a campaign."""
    if development_fixture: return _synthetic_fixture()
    root = Path(root).resolve()
    campaign_root = root if campaign_root is None else Path(campaign_root).resolve()
    # The notebook executor additionally confines this relationship.  The
    # adapter makes it explicit in every snapshot rather than copying evidence.
    if not (campaign_root / "data").is_dir() or not (campaign_root / "scripts").is_dir():
        raise ValueError("campaign root must contain retained repository data and scripts")
    root = campaign_root; relay = root / "data/results/phase4-memory-relay"
    cache = _InventoryProofCache()
    benchmark = _benchmark(root, cache=cache)
    baseline = {**benchmark, "stage": "baseline", "execution_qualified": False,
                "reason": "baseline view is retained active-benchmark diagnostic evidence, not a fresh selected stage"}
    factorial = _factorial(root, cache=cache)
    artifacts = {"baseline": baseline, "benchmark": benchmark,
                 "calibration": _calibration_or_selection(root, "calibration"), "selected_settings": _calibration_or_selection(root, "selected_settings"),
                 "evaluation": _evaluation(root, cache=cache), "factorial": factorial, "native": _native(root, cache=cache),
                 "traces": _traces(root, factorial), "historical_author_agreement": _historical_native(root)}
    return {"schema_version": 1, "mode": "read_only_campaign_inventory", "campaign_root": str(campaign_root), "assessment": "not_assessed", "artifacts": artifacts,
            "tables": [table for item in artifacts.values() for table in item.get("tables", [])],
            "summary": {"qualified_stages": sorted(stage for stage, item in artifacts.items() if item.get("execution_qualified") is True),
                        "unavailable_stages": sorted(stage for stage, item in artifacts.items() if item.get("execution_qualified") is not True)}}
