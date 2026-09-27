#!/usr/bin/env python3
"""Read-only, producer-verified Phase 4 notebook campaign adapters.

The notebook calls this module to obtain evidence snapshots.  It neither calls
an experiment command nor writes a campaign artifact: an absent, running, or
unverified producer remains visible as such.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_PATHS = {
    "baseline": "data/results/phase4-memory-relay/baseline/result.json",
    "benchmark": "data/results/phase4-memory-relay/benchmark.json",
    "calibration": "data/results/phase4-memory-relay/calibration/result.json",
    "selected_settings": "data/results/phase4-memory-relay/selected-settings.json",
    "evaluation": "data/results/phase4-memory-relay/evaluation/result.json",
    "factorial": "data/results/phase4-memory-relay/factorial/result.json",
    "native": "data/results/phase4-memory-relay/native/result.json",
    "traces": "data/results/phase4-memory-relay/traces/index.json",
}
TERMINAL = frozenset({"completed", "completed_with_inconclusive", "completed_precision", "cap_reached"})
POST_SELECTION = frozenset({"evaluation", "factorial", "native", "traces"})


def canonical_digest(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                             allow_nan=False).encode("utf-8")).hexdigest()


def byte_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _read(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"campaign artifact must be an object: {path}")
    return value


def _relative(root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError as error:
        raise ValueError("campaign artifact escapes repository root") from error


def _verify_embedded_digest(value: Mapping[str, Any]) -> tuple[bool, str | None]:
    """Verify the producer's canonical object digest, never just copy a flag."""
    fields = [key for key in ("result_digest", "benchmark_digest", "agreement_result_digest", "summary_digest")
              if isinstance(value.get(key), str)]
    if not fields:
        return False, "producer does not retain a canonical result digest"
    for field in fields:
        expected = value[field]
        if expected == canonical_digest({key: item for key, item in value.items() if key != field}):
            return True, None
    return False, "producer canonical digest does not verify"


def _caps_binding(root: Path, value: Mapping[str, Any]) -> tuple[dict[str, str], str | None]:
    caps = root / "data/manifests/phase4-pilot-caps.json"
    cited = value.get("caps_digest")
    if cited is None:
        return {}, None
    if not caps.is_file():
        return {}, "cited frozen caps are unavailable"
    document = _read(caps)
    if cited != document.get("caps_digest") or cited != canonical_digest({k: v for k, v in document.items() if k != "caps_digest"}):
        return {}, "cited frozen caps digest does not match current frozen caps"
    return {_relative(root, caps): byte_sha256(caps)}, None


def _selection_binding(root: Path, value: Mapping[str, Any]) -> tuple[dict[str, str], str | None]:
    cited = value.get("selected_settings_digest")
    if cited is None:
        return {}, None
    path = root / "data/results/phase4-memory-relay/selected-settings.json"
    if not path.is_file():
        return {}, "cited selected-settings artifact is unavailable"
    if cited != canonical_digest(_read(path)):
        return {}, "cited selected-settings digest does not match retained selection"
    return {_relative(root, path): byte_sha256(path)}, None


def _cited_bytes(root: Path, value: Mapping[str, Any], fields: tuple[str, ...], *, subtree: str,
                 label: str) -> tuple[dict[str, str], str | None]:
    cited = next((value[field] for field in fields if isinstance(value.get(field), Mapping)), None)
    if not isinstance(cited, Mapping) or not cited:
        return {}, f"producer does not bind {label} bytes"
    bound: dict[str, str] = {}
    for relative, expected in cited.items():
        if not isinstance(relative, str) or not isinstance(expected, str):
            return {}, f"producer {label} byte binding is malformed"
        path = (root / relative).resolve()
        try:
            path.relative_to((root / subtree).resolve())
        except ValueError:
            return {}, f"producer {label} path escapes {subtree}"
        if not path.is_file() or byte_sha256(path) != expected:
            return {}, f"producer {label} bytes do not verify"
        bound[_relative(root, path)] = expected
    return bound, None


def _sample_bindings(value: Mapping[str, Any]) -> dict[str, object]:
    """Keep producer-declared sample facts; never manufacture replacements."""
    facts: dict[str, object] = {}
    for key in ("sample_identity", "sample_namespace", "sample_identities", "matched_sample_ids",
                "fresh_matched_samples_per_arm_by_code"):
        if key in value:
            facts[key] = value[key]
    return facts


def _code_rows(stage: str, value: Mapping[str, Any]) -> list[dict[str, object]]:
    codes = value.get("codes")
    if not isinstance(codes, Mapping):
        return []
    rows: list[dict[str, object]] = []
    for code_id, detail in sorted(codes.items()):
        if isinstance(detail, Mapping) and any(isinstance(item, Mapping) for item in detail.values()):
            for arm, arm_value in sorted(detail.items()):
                if isinstance(arm_value, Mapping):
                    rows.append({"stage": stage, "code_id": code_id, "arm": arm,
                                 "status": arm_value.get("status", value.get("status")),
                                 "sample_identity": arm_value.get("sample_identity"),
                                 "runtime_seconds": arm_value.get("runtime_seconds")})
        else:
            rows.append({"stage": stage, "code_id": code_id, "arm": None,
                         "status": detail.get("status", value.get("status")) if isinstance(detail, Mapping) else value.get("status"),
                         "sample_identity": detail.get("sample_identity") if isinstance(detail, Mapping) else None,
                         "runtime_seconds": None})
    return rows


def artifact_snapshot(root: Path, stage: str, relative_path: str, *, development_fixture: bool = False) -> dict[str, object]:
    """Return one immutable campaign artifact snapshot and qualification state."""
    if stage not in ARTIFACT_PATHS:
        raise ValueError(f"unknown campaign stage: {stage}")
    path = (root / relative_path).resolve()
    _relative(root, path)
    if not path.is_file():
        return {"stage": stage, "status": "missing", "execution_qualified": False,
                "reason": "producer artifact is absent", "producer": {"path": relative_path}}
    value = _read(path)
    status = value.get("status")
    producer = {"path": _relative(root, path), "byte_sha256": byte_sha256(path)}
    if development_fixture or value.get("development_fixture") is True:
        return {"stage": stage, "status": "development_fixture_not_assessed", "execution_qualified": False,
                "reason": "development fixture cannot support campaign performance claims", "producer": producer,
                "assessment": "not_assessed", "payload": value, "sample_bindings": _sample_bindings(value)}
    if status not in TERMINAL:
        return {"stage": stage, "status": "running_or_incomplete", "execution_qualified": False,
                "reason": f"producer status is {status!r}", "producer": producer,
                "assessment": "not_assessed", "payload": value, "sample_bindings": _sample_bindings(value)}
    digest_ok, reason = _verify_embedded_digest(value)
    caps, caps_reason = _caps_binding(root, value)
    selection, selection_reason = _selection_binding(root, value)
    source, source_reason = _cited_bytes(root, value, ("source_policy_bytes", "source_policy"),
                                          subtree="scripts", label="source-policy")
    code, code_reason = _cited_bytes(root, value, ("code_manifest_bytes", "code_artifact_bytes"),
                                      subtree="data", label="code/manifest")
    samples = _sample_bindings(value)
    sample_reason = None if samples else "producer does not bind sample identity"
    if stage not in POST_SELECTION:
        selection_reason = None
    elif not selection:
        selection_reason = "producer does not bind frozen selected-settings bytes"
    if stage != "selected_settings" and not caps:
        caps_reason = caps_reason or "producer does not bind frozen caps"
    reasons = [item for item in (reason, caps_reason, selection_reason, source_reason, code_reason, sample_reason) if item]
    qualified = digest_ok and not reasons
    return {"stage": stage, "status": "execution_qualified" if qualified else "unavailable_or_inconclusive",
            "execution_qualified": qualified, "reason": None if qualified else "; ".join(reasons),
            "producer": producer, "assessment": "not_assessed", "identity": {"caps": caps, "selection": selection,
            "source_policy": source, "code": code, "sample": samples}, "payload": value, "tables": _code_rows(stage, value)}


def build_campaign_snapshots(root: Path = ROOT, *, development_fixture: bool = False) -> dict[str, object]:
    """Build read-only snapshots and normalized tables for the Phase 4 notebook."""
    root = Path(root).resolve()
    artifacts = {stage: artifact_snapshot(root, stage, path, development_fixture=development_fixture)
                 for stage, path in ARTIFACT_PATHS.items()}
    historical = artifact_snapshot(root, "benchmark", "data/results/phase4-memory-relay/author-v022-agreement-v1/runtime-comparison.json",
                                  development_fixture=development_fixture)
    historical["stage"] = "historical_author_agreement"
    historical["status"] = "historical_provenance_only"
    historical["execution_qualified"] = False
    historical["reason"] = "historical agreement cannot substitute fresh selected evaluation or factorial evidence"
    artifacts["historical_author_agreement"] = historical
    tables = [{"stage": stage, "name": f"{stage}_code_status", "title": f"{stage} code status", "columns": ["stage", "code_id", "arm", "status", "sample_identity", "runtime_seconds"],
               "rows": snapshot.get("tables", [])} for stage, snapshot in artifacts.items()]
    return {"schema_version": 1, "mode": "development_fixture" if development_fixture else "read_only_campaign_inventory",
            "assessment": "not_assessed", "artifacts": artifacts, "tables": tables,
            "summary": {"qualified_stages": sorted(stage for stage, item in artifacts.items() if item.get("execution_qualified") is True),
                        "unavailable_stages": sorted(stage for stage, item in artifacts.items() if item.get("execution_qualified") is not True)}}
