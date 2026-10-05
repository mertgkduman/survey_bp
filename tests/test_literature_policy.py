"""Literature policy documents are closed executable inputs with separate provenance."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib

import pytest

from bp_registry.literature import parse_literature_policy, qualify_yao_source_records
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


def _phase5_study(tmp_path: Path) -> Path:
    """A tiny public study whose decoder owns the BPGD controls."""
    study = json.loads((ROOT / "data/manifests/canonical-three-qubit-development.json").read_text())
    study["schema_version"] = 5
    study["run_id"] = "literature-bpgd-three-qubit"
    study["randomness"]["physical_sample_identity"] = "literature-bpgd-three-qubit-v1"
    study["artifact"]["root"] = str(ROOT / "data/artifacts")
    study.pop("policies")
    legacy_caps = {
        "check_to_variable_updates": 100000000, "variable_to_check_updates": 100000000,
        "belief_assemblies": 100000000, "residual_priority_evaluations": 100000000,
        "bp_calls": 1000000, "candidate_checks": 100000000,
        "intervention_actions": 2000, "branch_expansions": 0, "branch_prunes": 0,
        "relay_transfers": 0, "fallback_calls": 0,
    }
    for scope in ("shot", "search", "attempt"):
        study["budgets"][scope]["max_iterations"] = 1
        study["budgets"][scope]["work_limits"] = legacy_caps
    path = tmp_path / "phase5-study.json"
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


def test_shared_compute_keeps_append_only_request_receipts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OMP_NUM_THREADS", "1")
    study = _study(tmp_path)
    first_policy = tmp_path / "first.toml"
    second_policy = tmp_path / "second.toml"
    first_policy.write_text(_runnable_policy(source_note="same source") + "# raw-a\n")
    second_policy.write_text(_runnable_policy(source_note="same source") + "# raw-b\n")
    first = ensure_study(study, first_policy, results_root=tmp_path / "results")
    second = ensure_study(study, second_policy, results_root=tmp_path / "results")
    assert first["status"] == "computed" and second["status"] == "reused"
    assert first["cache_key"] == second["cache_key"]
    assert first["request_receipt"] != second["request_receipt"]
    receipts = Path(first["output"]) / "request-receipts"
    first_receipt = json.loads((receipts / f'{first["request_receipt"]}.json').read_text())
    second_receipt = json.loads((receipts / f'{second["request_receipt"]}.json').read_text())
    assert first_receipt["computation_key"] == second_receipt["computation_key"]
    assert first_receipt["raw_document_sha256"] != second_receipt["raw_document_sha256"]
    receipt_path = receipts / f'{first["request_receipt"]}.json'
    receipt_path.write_text('{"tampered": true}')
    with pytest.raises(ValueError, match="frozen study file differs"):
        ensure_study(study, first_policy, results_root=tmp_path / "results")


def test_yao_source_table_preserves_t_r_and_source_identity_gaps() -> None:
    records = qualify_yao_source_records(
        ROOT / "literature_policies/yao-2024-guided-decimation", code_block_length=882,
    )
    assert [record.variant_id for record in records] == [
        "bp-t100", "bpgd-t001", "bpgd-t010", "bpgd-t070", "bpgd-t100",
        "bpgd-t100-r002", "bpgd-t100-r005", "bpgd-t100-r010", "bpgd-t100-r050", "bpgd-t100-r882",
    ]
    assert all(record.disposition == "runnable" for record in records)
    bpgd = {record.variant_id: record for record in records if record.variant_id.startswith("bpgd")}
    assert bpgd["bpgd-t001"].executable["intervention"]["sweeps_per_round"] == 1
    assert bpgd["bpgd-t070"].executable["intervention"]["sweeps_per_round"] == 70
    assert bpgd["bpgd-t100-r050"].executable["intervention"]["round_limit"] == 50
    assert bpgd["bpgd-t100"].executable["intervention"]["round_limit"] == 882
    assert bpgd["bpgd-t100"].executable == bpgd["bpgd-t100-r882"].executable
    assert all(record.qualification != "source_faithful" for record in records)
    assert all("author_implementation_identity" in record.unresolved for record in records)
    assert all("ordered_paper_experiment_artifact_identity" in record.unresolved for record in records)


def test_yao_symbolic_round_limit_requires_validated_code_length() -> None:
    folder = ROOT / "literature_policies/yao-2024-guided-decimation"
    unresolved = qualify_yao_source_records(folder)
    dispositions = {record.variant_id: record.disposition for record in unresolved}
    assert {dispositions[name] for name in ("bpgd-t001", "bpgd-t010", "bpgd-t070", "bpgd-t100")} == {
        "requires_artifact_block_length",
    }
    assert {dispositions[name] for name in ("bpgd-t100-r002", "bpgd-t100-r005", "bpgd-t100-r010", "bpgd-t100-r050", "bpgd-t100-r882")} == {
        "runnable",
    }
    policy = parse_literature_policy(folder / "bpgd-t001.toml")
    with pytest.raises(ValueError, match="code block length"):
        policy.decoder_projection()
    resolved_three = policy.decoder_projection(code_block_length=3)
    resolved_b1 = policy.decoder_projection(code_block_length=882)
    assert resolved_three["intervention"]["round_limit"] == 3
    assert resolved_b1["intervention"]["round_limit"] == 882
    assert policy.execution_identity_for(code_block_length=3) != policy.execution_identity_for(code_block_length=882)


def test_bpgd_t001_runnable_policy_resolves_after_artifact_and_reuses(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OMP_NUM_THREADS", "1")
    policy = ROOT / "literature_policies/yao-2024-guided-decimation/bpgd-t001.toml"
    source_spec = tomllib.loads(policy.with_suffix(".spec.toml").read_text())
    parsed_policy = parse_literature_policy(policy)
    executable = parsed_policy.decoder_projection(code_block_length=3)
    assert source_spec["execution_status"] == "not_runnable"
    assert executable["update"] == source_spec["update"]
    assert executable["schedule"] == source_spec["schedule"]
    assert executable["state_memory"] == source_spec["state_memory"]
    assert executable["intervention"]["sweeps_per_round"] == source_spec["intervention"]["sweeps_per_round"]
    assert executable["intervention"]["finite_bias_magnitude"] == source_spec["intervention"]["finite_bias_magnitude"]
    assert executable["intervention"]["round_limit"] == 3
    first = ensure_study(_phase5_study(tmp_path), policy, results_root=tmp_path / "results")
    assert first["status"] == "computed"
    manifest = json.loads((Path(first["output"]) / "manifest.json").read_text())
    assert manifest["intervention"]["round_limit"] == 3
    assert manifest["intervention"]["sweeps_per_round"] == 1
    assert manifest["intervention"]["finite_bias_magnitude"] == 25.0
    assert manifest["intervention"]["zero_rule"] == "positive_prior_for_zero_posterior"
    assert manifest["intervention"]["final_round_rule"] == "return_after_last_fixation"
    assert first["result"]["assessment_status"] == "not_assessed"
    assert ensure_study(_phase5_study(tmp_path), policy, results_root=tmp_path / "results")["status"] == "reused"


def test_bpgd_t001_runnable_policy_uses_installed_common_command(tmp_path: Path) -> None:
    policy = ROOT / "literature_policies/yao-2024-guided-decimation/bpgd-t001.toml"
    command = Path(sys.executable).with_name("bp-registry")
    result = subprocess.run(
        [command, _phase5_study(tmp_path), "--decoder", policy,
         "--results-root", tmp_path / "cli-results"],
        check=True, capture_output=True, text=True,
        env={**os.environ, "OMP_NUM_THREADS": "1"},
    )
    assert json.loads(result.stdout)["status"] == "computed"
