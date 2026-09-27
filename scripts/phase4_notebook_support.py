"""Confined, immutable evidence reuse for the Phase 4 notebook.

Notebook snapshots are distinct from the production campaign artifacts. A
producer must qualify an artifact's originating execution before packaging it;
adding an analysis identity alone never qualifies an old execution.
"""
from __future__ import annotations

from hashlib import sha256
from importlib.metadata import version
import json
from pathlib import Path
from typing import Callable, Mapping

ANALYSIS_VERSIONS = {
    "numpy": "2.2.6", "matplotlib": "3.10.9", "nbformat": "5.10.4",
    "nbclient": "0.10.2", "ipykernel": "6.29.5",
}
SECTIONS = (
    "identity", "equations", "baseline", "benchmark", "calibration",
    "selected_settings", "evaluation", "factorial", "native", "traces",
    "work_runtime_resources", "cross_code", "limitations",
)
IDENTITY_FIELDS = frozenset({
    "manifest", "source_policy", "code", "environment", "sample", "stage",
    "caps", "selection",
})
TERMINAL = frozenset({"completed", "completed_with_inconclusive", "cap_reached",
                      "incomplete_or_inconclusive"})


def digest(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False).encode()).hexdigest()


def confined(root: Path, value: str | Path, subtree: str) -> Path:
    root = root.resolve()
    path = (root / value).resolve()
    try:
        path.relative_to((root / subtree).resolve())
    except ValueError as error:
        raise ValueError(f"path must be confined below {subtree}") from error
    # An approved subtree itself may not be redirected outside the repository.
    try:
        (root / subtree).resolve().relative_to(root)
    except ValueError as error:
        raise ValueError("approved subtree escapes repository") from error
    return path


def identity(stage: str, facts: Mapping[str, object]) -> dict[str, object]:
    if stage not in SECTIONS or set(facts) != IDENTITY_FIELDS or facts["stage"] != stage:
        raise ValueError("complete manifest/source-policy/code/environment/sample/stage identity required")
    if any(value is None or value == "" for value in facts.values()):
        raise ValueError("identity facts must be explicit; use not_applicable where appropriate")
    if facts["environment"] != ANALYSIS_VERSIONS:
        raise ValueError("analysis environment differs from pinned versions")
    return {"identity_version": 1, "facts": dict(facts), "identity_digest": digest(dict(facts))}


def stage_path(root: Path, expected: Mapping[str, object]) -> Path:
    checked = identity(str(expected["facts"]["stage"]), expected["facts"])
    if checked != expected:
        raise ValueError("stage identity digest does not verify")
    return confined(root, f"data/results/phase4-notebook/stages/{checked['identity_digest']}.json",
                    "data/results/phase4-notebook")


def qualify_current_inputs(root: Path, expected: Mapping[str, object]) -> None:
    """Recheck bytes against the current request, including symlink confinement."""
    facts = expected["facts"]
    required_sources = {str(path.relative_to(root)) for path in (root / "src/bp_registry").rglob("*.py")}
    required_sources.update(str(path.relative_to(root)) for path in (root / "scripts").glob("run_phase4*.py"))
    if not isinstance(facts["source_policy"], dict) or not required_sources <= set(facts["source_policy"]):
        raise ValueError("source_policy omits executable source files")
    allowed = {"manifest": "data/manifests", "source_policy": "src/bp_registry",
               "code": "data/artifacts", "caps": "data/manifests",
               "selection": "data/results/phase4-memory-relay"}
    for field, subtree in allowed.items():
        references = facts[field]
        if field == "selection" and references == "not_applicable":
            if facts["stage"] in {"evaluation", "factorial", "native", "traces", "cross_code", "work_runtime_resources"}:
                raise ValueError("post-selection stages require frozen selection bytes")
            continue
        if not isinstance(references, dict) or not references:
            raise ValueError(f"{field} requires explicit path/byte-digest references")
        for relative, expected_sha in references.items():
            if field == "source_policy" and str(relative).startswith("scripts/"):
                path = confined(root, relative, "scripts")
            else:
                path = confined(root, relative, subtree)
            if not path.is_file() or sha256(path.read_bytes()).hexdigest() != expected_sha:
                raise ValueError(f"current {field} input does not match originating execution: {relative}")
    samples = facts["sample"]
    if not isinstance(samples, dict) or set(samples) != set(facts["manifest"]):
        raise ValueError("sample identities must bind each referenced manifest")
    for relative, namespace in samples.items():
        manifest = json.loads(confined(root, relative, "data/manifests").read_text())
        if manifest.get("randomness", {}).get("physical_sample_identity") != namespace:
            raise ValueError("physical sample namespace differs from manifest")


def load_stage(root: Path, expected: Mapping[str, object]) -> dict[str, object]:
    """Return mismatches as unavailable without deleting or rewriting them."""
    path = stage_path(root, expected)
    qualify_current_inputs(root, expected)
    if not path.is_file():
        return {"status": "missing", "path": str(path), "reused": False}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("stage snapshot must be an object")
    if value.get("identity") != expected:
        return {"status": "identity_mismatch_preserved", "path": str(path), "reused": False}
    if value.get("snapshot_digest") != digest({k: v for k, v in value.items() if k != "snapshot_digest"}):
        raise ValueError("stage snapshot digest does not verify")
    if value.get("execution_qualified") is not True:
        raise ValueError("originating execution has not been qualified")
    if value.get("status") not in TERMINAL:
        return {"status": "nonterminal_preserved", "path": str(path), "reused": False}
    return {**value, "path": str(path), "reused": True}


def ensure_stage(root: Path, expected: Mapping[str, object], *,
                 producer: Callable[[], Mapping[str, object]] | None = None,
                 predecessor_verified: bool = False) -> dict[str, object]:
    """Generation is explicit and gated; never overwrite a retained snapshot."""
    existing = load_stage(root, expected)
    if existing["status"] != "missing" or producer is None:
        return existing
    if not predecessor_verified:
        raise ValueError("production stage generation requires verified predecessor evidence")
    value = dict(producer())
    if value.get("identity") != expected or value.get("status") not in TERMINAL:
        raise ValueError("producer returned unqualified identity or nonterminal evidence")
    if value.get("execution_qualified") is not True:
        raise ValueError("originating execution has not been qualified")
    value["snapshot_digest"] = digest({k: v for k, v in value.items() if k != "snapshot_digest"})
    path = stage_path(root, expected)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents a concurrent notebook from replacing evidence.
    with path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return load_stage(root, expected)


def fixture_stages() -> dict[str, dict[str, object]]:
    """Small execution-test records, never estimates of decoder performance."""
    return {stage: {"status": "development_fixture", "stage": stage,
                    "fixture": "development_fixture", "assessment_status": "not_assessed",
                    "claim_scope": "notebook execution plumbing only; no sampled decoder evidence"}
            for stage in SECTIONS}


def notebook_inventory(root: Path, *, fixture: bool = False) -> dict[str, dict[str, object]]:
    if fixture:
        return fixture_stages()
    # This index is a producer-qualified handoff, not a trust-by-filename cache.
    path = confined(root, "data/results/phase4-notebook/index.json", "data/results/phase4-notebook")
    if not path.is_file():
        return {stage: {"status": "missing_qualified_snapshot", "stage": stage} for stage in SECTIONS}
    index = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(index, dict):
        raise ValueError("notebook index must be an object")
    if index.get("index_digest") != digest({k: v for k, v in index.items() if k != "index_digest"}):
        raise ValueError("notebook index digest does not verify")
    if set(index.get("stages", {})) != set(SECTIONS):
        raise ValueError("notebook index omits required sections")
    for stage, expected in index["stages"].items():
        if not isinstance(expected, dict) or not isinstance(expected.get("facts"), dict) or expected["facts"].get("stage") != stage:
            raise ValueError("notebook index assigns an identity to the wrong stage section")
    return {stage: load_stage(root, index["stages"][stage]) for stage in SECTIONS}


def validate_environment() -> None:
    observed = {package: version(package) for package in ANALYSIS_VERSIONS}
    if observed != ANALYSIS_VERSIONS:
        raise RuntimeError(f"analysis dependency versions drifted: {observed}")
