#!/usr/bin/env python3
"""Read-only adapters for retained Phase 4 campaign evidence.

This module deliberately has no runner or subprocess entry point.  A notebook
may display an artifact only with the producer verification that its own stage
schema supports; it may never promote a copied ``status: completed`` flag.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
STAGES = ("baseline", "benchmark", "calibration", "selected_settings", "evaluation", "factorial", "native", "traces")
POST_SELECTION = frozenset({"evaluation", "factorial", "native", "traces"})


def _json_digest(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                             allow_nan=False).encode()).hexdigest()


def _byte_sha(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


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


def _runners(root: Path):
    scripts = str((root / "scripts").resolve())
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    import run_phase4_evaluation as evaluation
    import run_phase4_factorial as factorial
    import run_phase4_pilots as pilots
    from summarize_phase4_author_runtime import summarize_author_runtime
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
                primary = summary.get("primary") if isinstance(summary, Mapping) else None
                if isinstance(primary, Mapping):
                    rows.append({"stage": stage, "code_id": code_id, "arm": arm, "error_rate": item.get("error_rate"),
                                 "failures": primary.get("failures"), "denominator": primary.get("denominator"),
                                 "estimate": primary.get("estimate"), "wilson_95": primary.get("wilson_95", primary.get("interval")),
                                 "runtime_tails": summary.get("runtime_seconds"), "runtime_scope": "producer-declared; do not mix boundaries", "resource_tails": summary.get("resource_measurements")})
    return rows


def _table(stage: str, rows: list[dict[str, object]]) -> dict[str, object]:
    return {"stage": stage, "name": f"{stage}_failure_accounting", "title": f"{stage} failure accounting",
            "columns": ["stage", "code_id", "arm", "error_rate", "failures", "denominator", "estimate", "wilson_95", "runtime_tails", "runtime_scope", "resource_tails"], "rows": rows}


def _caps(root: Path, pilots) -> tuple[Path, dict[str, Any]]:
    path = root / "data/manifests/phase4-pilot-caps.json"
    value = _read(path)
    if value.get("caps_digest") != pilots._digest({k: v for k, v in value.items() if k != "caps_digest"}):
        raise ValueError("frozen caps digest does not verify")
    return path, value


def _benchmark(root: Path) -> dict[str, object]:
    evaluation, _factorial, pilots, _runtime = _runners(root)
    try:
        caps_path, caps = _caps(root, pilots)
        cited = caps["benchmark_evidence"]["active_v4"]
        report_path = root / str(cited["path"])
        if not report_path.is_file() or _byte_sha(report_path) != cited["byte_sha256"]:
            raise ValueError("active benchmark bytes differ from frozen cap citation")
        report = _read(report_path)
        if report.get("benchmark_digest") != cited["report_digest"]:
            raise ValueError("active benchmark digest differs from frozen cap citation")
        # Typed attempts are producer evidence, but fixture-labelled historical
        # runs stay diagnostics even when their report digest is valid.
        attempts = [attempt for code in report.get("codes", {}).values() if isinstance(code, Mapping)
                    for arm in code.get("arms", {}).values() if isinstance(arm, Mapping)
                    for attempt in arm.get("attempts", []) if isinstance(attempt, Mapping)]
        if not attempts or any("status" not in attempt for attempt in attempts):
            raise ValueError("active benchmark omits typed attempts")
        fixture = any(isinstance(attempt.get("terminal"), Mapping) and attempt["terminal"].get("fixture") == "development_fixture" for attempt in attempts)
        return _snapshot("benchmark", report_path, report, qualified=False,
                         reason="development fixture benchmark is diagnostic only" if fixture else "benchmark has no current execution qualification adapter",
                         tables=[_table("benchmark", _failure_rows("benchmark", report))])
    except (KeyError, OSError, ValueError) as error:
        fallback = root / "data/results/phase4-memory-relay/benchmark.json"
        if not fallback.is_file(): return _missing("benchmark", fallback, str(error))
        payload = _read(fallback)
        return _snapshot("benchmark", fallback, payload, qualified=False,
                         reason=f"historical benchmark metadata only: {error}", tables=[_table("benchmark", _failure_rows("benchmark", payload))])


def _verified_inputs(root: Path):
    evaluation, _factorial, _pilots, _runtime = _runners(root)
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
            evaluation, _factorial, _pilots, _runtime = _runners(root)
            _caps, chosen = evaluation.verified_calibration_inputs(
                root=root, caps_path=root / "data/manifests/phase4-pilot-caps.json", calibration_path=path)
        else:
            _evaluation, (_caps, _calibration, chosen) = _verified_inputs(root)
        if chosen != payload: raise ValueError("verified producer input differs from retained artifact")
        return _snapshot(stage, path, payload, qualified=True, reason=None, tables=[_table(stage, _failure_rows(stage, payload))])
    except (FileNotFoundError, OSError, ValueError) as error:
        return _snapshot(stage, path, payload, qualified=False, reason=str(error), tables=[_table(stage, _failure_rows(stage, payload))])


def _evaluation(root: Path) -> dict[str, object]:
    path = root / "data/results/phase4-memory-relay/evaluation/result.json"
    if not path.is_file(): return _missing("evaluation", path)
    payload = _read(path)
    try:
        runner, (caps, _calibration, selection) = _verified_inputs(root)
        plan = runner.evaluation_plan(caps, selection)
        arms = tuple(caps["evaluation"]["arms_per_code"])
        if payload.get("plan_digest") != runner._digest(plan) or payload.get("caps_digest") != caps["caps_digest"] or payload.get("selected_settings_digest") != runner._digest(selection):
            raise ValueError("evaluation result does not bind the verified three-arm plan")
        if any(set(payload.get("codes", {}).get(code, {})) != set(arms) for code in caps["codes"]):
            raise ValueError("evaluation result omits or adds frozen arms")
        if payload.get("status") != "completed": raise ValueError("evaluation producer is nonterminal")
        # The public CLI verifier must be replayed from the retained ledgers by
        # the executor; this reader refuses to call a simulation/subprocess.
        return _snapshot("evaluation", path, payload, qualified=False,
                         reason="ledger terminal verification has not been replayed by this read-only adapter",
                         tables=[_table("evaluation", _failure_rows("evaluation", payload))])
    except (FileNotFoundError, OSError, ValueError) as error:
        return _snapshot("evaluation", path, payload, qualified=False, reason=str(error), tables=[_table("evaluation", _failure_rows("evaluation", payload))])


def _factorial(root: Path) -> dict[str, object]:
    path = root / "data/results/phase4-memory-relay/factorial/result.json"
    if not path.is_file(): return _missing("factorial", path)
    payload = _read(path)
    try:
        _evaluation, factorial, pilots, _runtime = _runners(root)
        _caps_path, caps = _caps(root, pilots)
        plan = factorial.build_factorial_plan(design=_read(root / "data/evidence/phase4-pilot-design.json"), caps=caps,
                                              supplement=_read(root / "data/evidence/phase4-factorial-execution-supplement-v1.json"))
        factorial.assert_factorial_predecessor(evaluation_path=root / "data/results/phase4-memory-relay/evaluation/result.json", plan=plan, repository_root=root)
        if payload.get("factorial_digest") != plan["factorial_digest"]: raise ValueError("factorial result plan digest differs")
        if payload.get("status") != "completed_not_assessed": raise ValueError("factorial producer is nonterminal or inconclusive")
        factorial.validate_trace_inventory(payload.get("terminals", []), plan)
        return _snapshot("factorial", path, payload, qualified=False,
                         reason="factorial terminal ledgers have not been replayed by this read-only adapter",
                         tables=[_table("factorial", _failure_rows("factorial", payload))])
    except (FileNotFoundError, OSError, ValueError) as error:
        return _snapshot("factorial", path, payload, qualified=False, reason=str(error), tables=[_table("factorial", _failure_rows("factorial", payload))])


def _historical_native(root: Path) -> dict[str, object]:
    path = root / "data/results/phase4-memory-relay/author-v022-agreement-v1/runtime-comparison.json"
    if not path.is_file(): return _missing("historical_author_agreement", path)
    payload = _read(path)
    try:
        _evaluation, _factorial, _pilots, summarize = _runners(root)
        summary = summarize(path.parent)
        if summary != payload: raise ValueError("historical runtime summary differs from verified agreement pairs")
        rows = [{"stage": "historical_author_agreement", "code_id": code, "arm": "canonical_vs_author_native",
                 "error_rate": None, "failures": item.get("exact_candidate_disagreements"), "denominator": item.get("paired_shots"),
                 "estimate": None, "wilson_95": None, "runtime_tails": {"canonical_public": item.get("canonical_public_seconds"), "native_pipeline": item.get("native_pipeline_seconds")},
                 "runtime_scope": "unequal recorded public-vs-native pipeline boundaries; diagnostic only", "resource_tails": None}
                for code, item in sorted(summary.get("codes", {}).items()) if isinstance(item, Mapping)]
        return _snapshot("historical_author_agreement", path, payload, qualified=False,
                         reason="historical author agreement is not fresh selected evaluation or factorial evidence",
                         tables=[{**_table("historical_author_agreement", rows), "display_limit": 30}])
    except (OSError, ValueError) as error:
        return _snapshot("historical_author_agreement", path, payload, qualified=False, reason=str(error), tables=[])


def _synthetic_fixture() -> dict[str, object]:
    rows = [{"stage": stage, "code_id": "development-fixture-code", "arm": "fixture-baseline", "error_rate": 0.03,
             "failures": 1, "denominator": 7, "estimate": 1 / 7, "wilson_95": [0.025, 0.513],
             "runtime_tails": {"p95": 0.01}, "resource_tails": {"missing": 1}} for stage in STAGES]
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
    artifacts = {"baseline": _missing("baseline", relay / "baseline/result.json"), "benchmark": _benchmark(root),
                 "calibration": _calibration_or_selection(root, "calibration"), "selected_settings": _calibration_or_selection(root, "selected_settings"),
                 "evaluation": _evaluation(root), "factorial": _factorial(root), "native": _missing("native", relay / "native/result.json"),
                 "traces": _missing("traces", relay / "traces/index.json"), "historical_author_agreement": _historical_native(root)}
    return {"schema_version": 1, "mode": "read_only_campaign_inventory", "campaign_root": str(campaign_root), "assessment": "not_assessed", "artifacts": artifacts,
            "tables": [table for item in artifacts.values() for table in item.get("tables", [])],
            "summary": {"qualified_stages": sorted(stage for stage, item in artifacts.items() if item.get("execution_qualified") is True),
                        "unavailable_stages": sorted(stage for stage, item in artifacts.items() if item.get("execution_qualified") is not True)}}
