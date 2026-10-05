"""Literature policy documents are closed executable inputs with separate provenance."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bp_registry.literature import parse_literature_policy
from bp_registry.study import ensure_study


ROOT = Path(__file__).resolve().parents[1]


def _runnable_policy(*, source_note: str = "first request", max_iterations: int = 8) -> str:
    return f'''schema_version = 1
record_kind = "literature_policy"
variant_id = "tracer-bp"
execution_status = "runnable"
qualification = "canonical_adaptation"

[source]
paper = "Tracer paper"
revision = "v1"
url = "https://example.invalid/paper"
note = "{source_note}"

[equations]
update = "This prose is inert."

[update]
kind = "binary_spa"
[schedule]
kind = "flooding"
[state_memory]
kind = "stateless"
[intervention]
kind = "identity"
[stopping]
kind = "syndrome_or_budget"
max_iterations = {max_iterations}
[selection]
kind = "stable_first"
[postprocessing]
kind = "identity"
'''


def _study(tmp_path: Path) -> Path:
    study = json.loads((ROOT / "examples/three-qubit-study.json").read_text())
    study["artifact"]["root"] = str(ROOT / "data/artifacts")
    path = tmp_path / "study.json"
    path.write_text(json.dumps(study))
    return path


def test_strict_parser_separates_execution_provenance_and_raw_document(tmp_path: Path) -> None:
    first = tmp_path / "first.toml"
    second = tmp_path / "second.toml"
    first.write_text(_runnable_policy(source_note="one") + "# first raw receipt\n")
    second.write_text(_runnable_policy(source_note="two") + "# second raw receipt\n")
    parsed_first = parse_literature_policy(first)
    parsed_second = parse_literature_policy(second)
    assert parsed_first.disposition == "runnable"
    assert parsed_first.execution_identity == parsed_second.execution_identity
    assert parsed_first.provenance_identity != parsed_second.provenance_identity
    assert parsed_first.raw_document_identity != parsed_second.raw_document_identity
    changed = tmp_path / "changed.toml"
    changed.write_text(_runnable_policy(max_iterations=7))
    assert parse_literature_policy(changed).execution_identity != parsed_first.execution_identity


@pytest.mark.parametrize("replacement", [
    'kind = "binary_spa"\nunknown = 1',
    'kind = "not_registered"',
    'max_iterations = 8\nexpression = "__import__(\\\'os\\\')"',
])
def test_strict_parser_fails_closed_on_unknown_executable_controls(tmp_path: Path, replacement: str) -> None:
    path = tmp_path / "unsafe.toml"
    path.write_text(_runnable_policy().replace('kind = "binary_spa"', replacement, 1))
    with pytest.raises(ValueError):
        parse_literature_policy(path)


def test_non_runnable_source_record_returns_before_artifact_loading(tmp_path: Path) -> None:
    study = tmp_path / "missing-artifact-study.json"
    study.write_text('{"schema_version": 2, "artifact": {"root": "/does/not/exist"}}')
    source = ROOT / "literature_policies/yao-2024-guided-decimation/bp-t100.spec.toml"
    result = ensure_study(study, source, results_root=tmp_path / "results")
    assert result == {
        "status": "non_runnable",
        "disposition": "non_runnable",
        "source_path": str(source.resolve()),
        "blocking_features": ["source_experiment_identity_check", "source_metadata_policy_file_schema"],
    }


def test_tracer_bp_t100_common_command_computes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OMP_NUM_THREADS", "1")
    study = _study(tmp_path)
    first_policy = tmp_path / "first.toml"
    second_policy = tmp_path / "second.toml"
    first_policy.write_text(_runnable_policy(source_note="first") + "# raw-a\n")
    second_policy.write_text(_runnable_policy(source_note="second") + "# raw-b\n")
    first = ensure_study(study, first_policy, results_root=tmp_path / "results")
    second = ensure_study(study, second_policy, results_root=tmp_path / "results")
    assert first["status"] == "computed"
    assert second["status"] == "reused"
    assert first["cache_key"] == second["cache_key"]
