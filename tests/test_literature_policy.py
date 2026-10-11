"""Literature policy documents are closed executable inputs with separate provenance."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tomllib

import pytest

from bp_registry.literature import (
    parse_literature_policy, qualify_yao_source_records,
    qualify_bhatnagar_source_records, qualify_rabeti_source_record,
)
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


def test_bhatnagar_source_variants_have_distinct_closed_controls() -> None:
    folder = ROOT / "literature_policies/bhatnagar-2026-impulse-decoding"
    unresolved = qualify_bhatnagar_source_records(folder)
    assert [row.variant_id for row in unresolved] == [
        "minimum-weight-1", "first-convergence-0", "first-convergence-1",
    ]
    assert all(row.disposition == "requires_artifact_block_length" for row in unresolved)
    rows = {row.variant_id: row for row in qualify_bhatnagar_source_records(folder, code_block_length=3)}
    assert all(row.disposition == "runnable" for row in rows.values())
    for name, forced, selection in (
        ("minimum-weight-1", 1, "minimum_original_weight"),
        ("first-convergence-0", 0, "first_convergence"),
        ("first-convergence-1", 1, "first_convergence"),
    ):
        row = rows[name]
        control = row.executable["intervention"]
        assert control["forced_value"] == forced
        assert control["realization"] == ("semantic_forced_zero" if forced == 0 else "semantic_forced_one")
        assert control["selection"] == selection
        assert control["baseline_sweeps"] == control["attempt_sweeps"] == 100
        assert control["attempt_cap"] == 3
        assert control["coordinate_order"] == [0, 1, 2]
        assert control["v2c_clip"] == 25.0
        assert control["reset_rule"] == "fresh_per_coordinate"
        assert "source_schedule_unspecified" in row.unresolved
        assert row.qualification != "source_faithful"


def test_bhatnagar_variant_suffix_and_source_controls_fail_closed(tmp_path: Path) -> None:
    folder = ROOT / "literature_policies/bhatnagar-2026-impulse-decoding"
    for source in folder.glob("*.spec.toml"):
        (tmp_path / source.name).write_bytes(source.read_bytes())
    zero = tmp_path / "first-convergence-0.spec.toml"
    zero.write_text(zero.read_text().replace("shorten_value = 0", "shorten_value = 1"))
    with pytest.raises(ValueError, match="named variant"):
        qualify_bhatnagar_source_records(tmp_path, code_block_length=3)
    zero.write_bytes((folder / zero.name).read_bytes())
    runnable = tmp_path / "first-convergence-0.toml"
    runnable.write_text((folder / runnable.name).read_text().replace("forced_value = 0", "forced_value = 1"))
    with pytest.raises(ValueError, match="closed source variant"):
        parse_literature_policy(runnable)


def test_bhatnagar_first_convergence_0_runnable_public_reuse(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OMP_NUM_THREADS", "1")
    # Another execution wave may edit independent kernel files while this test
    # runs; pin the source receipt so this checks the requested policy path.
    monkeypatch.setattr("bp_registry.study._source_identity", lambda: "test-source-snapshot")
    folder = ROOT / "literature_policies/bhatnagar-2026-impulse-decoding"
    policy = folder / "first-convergence-0.toml"
    parsed = parse_literature_policy(policy)
    assert parsed.decoder_projection(code_block_length=3)["intervention"]["forced_value"] == 0
    assert parsed.decoder_projection(code_block_length=3)["intervention"]["coordinate_order"] == [0, 1, 2]
    study = _phase5_study(tmp_path)
    document = json.loads(study.read_text())
    document["run_id"] = "bhatnagar-impulse-three-qubit"
    document["budgets"]["max_shots"] = 1
    for scope in ("shot", "search", "attempt"):
        document["budgets"][scope]["max_iterations"] = 100
    study.write_text(json.dumps(document))
    first = ensure_study(study, policy, results_root=tmp_path / "results")
    assert first["status"] == "computed"
    manifest = json.loads((Path(first["output"]) / "manifest.json").read_text())
    assert manifest["intervention"]["forced_value"] == 0
    assert manifest["intervention"]["attempt_cap"] == 3
    assert manifest["intervention"]["coordinate_order"] == [0, 1, 2]
    assert manifest["intervention"]["v2c_clip"] == 25.0
    assert manifest["intervention"]["reset_rule"] == "fresh_per_coordinate"
    assert first["result"]["assessment_status"] == "not_assessed"
    second = ensure_study(study, policy, results_root=tmp_path / "results")
    assert second["status"] == "reused"
    assert first["cache_key"] == second["cache_key"]


def test_bhatnagar_first_convergence_0_installed_common_command(tmp_path: Path) -> None:
    policy = ROOT / "literature_policies/bhatnagar-2026-impulse-decoding/first-convergence-0.toml"
    study = _phase5_study(tmp_path)
    document = json.loads(study.read_text())
    document["run_id"] = "bhatnagar-cli-three-qubit"
    document["budgets"]["max_shots"] = 1
    for scope in ("shot", "search", "attempt"):
        document["budgets"][scope]["max_iterations"] = 100
    study.write_text(json.dumps(document))
    command = Path(sys.executable).with_name("bp-registry")
    completed = subprocess.run(
        [command, study, "--decoder", policy, "--results-root", tmp_path / "cli-results"],
        check=True, capture_output=True, text=True,
        env={**os.environ, "OMP_NUM_THREADS": "1"},
    )
    result = json.loads(completed.stdout)
    assert result["status"] == "computed"
    assert result["verification"]["final_row_count"] == 1
    assert result["verification"]["intervention"]["specification"]["forced_value"] == 0


def test_rabeti_mbbp_source_controls_require_explicit_local_bases() -> None:
    root = ROOT / "literature_policies/rabeti-2026-multiple-bases-bp-list-decoding"
    row = qualify_rabeti_source_record(root)
    assert row.variant_id == "mbbp-ld"
    assert row.disposition == "requires_local_basis_descriptors"
    assert row.qualification == "canonical_adaptation_not_assessed"
    assert row.executable["update"]["parameter_assignment"] == {"shape": "scalar", "value": 0.875}
    assert row.executable["schedule"] == {"kind": "check_node_serial"}
    assert row.executable["ensemble"]["kind"] == "mbbp_ld"
    assert row.executable["ensemble"]["member_state"] == "independent"
    assert row.executable["ensemble"]["max_iterations"] == 100
    assert row.executable["list_selection"]["kind"] == "frequency_over_weight_plus_one"
    assert row.executable["ensemble"]["no_member_terminal"] == "no_member_converged_zero_return"
    assert "source_partition_permutation" in row.unresolved


def test_rabeti_source_record_rejects_misnamed_score_and_shared_state(tmp_path: Path) -> None:
    root = ROOT / "literature_policies/rabeti-2026-multiple-bases-bp-list-decoding"
    source = (root / "mbbp-ld.spec.toml").read_text()
    path = tmp_path / "mbbp-ld.spec.toml"
    path.write_text(source.replace("member_state = \"independent\"", "member_state = \"shared\""))
    with pytest.raises(ValueError, match="Rabeti source record"):
        qualify_rabeti_source_record(tmp_path)
    path.write_text(source.replace("candidate_frequency/(hamming_weight+1)", "candidate_frequency/hamming_weight"))
    with pytest.raises(ValueError, match="Rabeti source record"):
        qualify_rabeti_source_record(tmp_path)


def test_mbbp_ld_runnable_policy_resolves_one_hot_bases_from_artifact() -> None:
    root = ROOT / "literature_policies/rabeti-2026-multiple-bases-bp-list-decoding"
    policy = parse_literature_policy(root / "mbbp-ld.toml")
    assert policy.disposition == "runnable"
    assert policy.requires_artifact_block_length()
    with pytest.raises(ValueError, match="check count"):
        policy.decoder_projection(code_block_length=3)
    decoder = policy.decoder_projection(code_block_length=3, code_check_count=2)
    assert decoder["ensemble"]["kind"] == "mbbp_ld"
    assert decoder["ensemble"]["no_member_terminal"] == "no_member_converged_zero_return"
    assert decoder["ensemble"]["member_state"] == "independent"
    assert decoder["ensemble"]["bases"][0]["redundant_transforms"] == [[1, 0]]
    assert decoder["ensemble"]["bases"][1]["redundant_transforms"] == [[0, 1]]
    assert all(basis["transform_kind"] == "one_hot_original_check_rows" for basis in decoder["ensemble"]["bases"])
    assert decoder["list_selection"]["kind"] == "frequency_over_weight_plus_one"
    assert "source_rows" not in decoder["ensemble"]["bases"][0]
    assert policy.execution_identity_for(code_block_length=3, code_check_count=2) != policy.execution_identity_for(
        code_block_length=72, code_check_count=36,
    )


def test_mbbp_ld_source_policy_rejects_non_one_hot_and_changed_score(tmp_path: Path) -> None:
    root = ROOT / "literature_policies/rabeti-2026-multiple-bases-bp-list-decoding"
    for source in root.glob("*.spec.toml"):
        (tmp_path / source.name).write_bytes(source.read_bytes())
    policy = (root / "mbbp-ld.toml").read_text()
    path = tmp_path / "mbbp-ld.toml"
    path.write_text(policy.replace('transform_kind = "one_hot_original_check_rows"', 'transform_kind = "gf2_general"'))
    with pytest.raises(ValueError, match="one-hot|one_hot|Rabeti"):
        parse_literature_policy(path)
    path.write_text(policy.replace('kind = "frequency_over_weight_plus_one"', 'kind = "minimum_weight"'))
    with pytest.raises(ValueError, match="Rabeti|list selection"):
        parse_literature_policy(path)


def _mbbp_bb72_study(tmp_path: Path) -> Path:
    study = json.loads(_phase5_study(tmp_path).read_text())
    paper = json.loads((ROOT / "data/manifests/phase3-pilot-bb72.json").read_text())
    study["schema_version"] = 7
    study["run_id"] = "rabeti-mbbp-bb72-bounded"
    study["numerical_profile"] = "cpu-float64-min-sum-v1"
    study["error_rate"] = 0.001
    study["artifact"] = {**paper["artifact"], "root": str(ROOT / "data/artifacts")}
    study["budgets"]["max_shots"] = 1
    study["randomness"]["physical_sample_identity"] = "rabeti-mbbp-bb72-bounded-v1"
    for scope in ("shot", "search", "attempt"):
        study["budgets"][scope]["max_iterations"] = 100
    path = tmp_path / "mbbp-study.json"
    path.write_text(json.dumps(study))
    return path


def test_mbbp_ld_runnable_public_compute_reuse_and_receipt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OMP_NUM_THREADS", "1")
    # Keep the numerical source snapshot fixed while another execution wave
    # may update separate kernel files in this shared checkout.
    monkeypatch.setattr("bp_registry.study._source_identity", lambda: "mbbp-test-source-snapshot")
    policy = ROOT / "literature_policies/rabeti-2026-multiple-bases-bp-list-decoding/mbbp-ld.toml"
    study = _mbbp_bb72_study(tmp_path)
    first = ensure_study(study, policy, results_root=tmp_path / "results")
    second = ensure_study(study, policy, results_root=tmp_path / "results")
    assert first["status"] == "computed" and second["status"] == "reused"
    assert first["cache_key"] == second["cache_key"]
    assert first["request_receipt"] == second["request_receipt"]
    manifest = json.loads((Path(first["output"]) / "manifest.json").read_text())
    assert manifest["schema_version"] == 7
    assert manifest["ensemble"]["bases"][0]["redundant_transforms"][0] == [1, *([0] * 35)]
    assert manifest["ensemble"]["bases"][1]["redundant_transforms"][0] == [0, 1, *([0] * 34)]
    assert first["result"]["assessment_status"] == "not_assessed"
    assert first["result"]["terminations"] == {"selected_original_valid_candidate": 1}
    receipt = json.loads((Path(first["output"]) / "request-receipts" /
                          f'{first["request_receipt"]}.json').read_text())
    assert receipt["source_path"] == "literature_policies/rabeti-2026-multiple-bases-bp-list-decoding/mbbp-ld.toml"
    events = [json.loads(line) for line in (Path(first["output"]) / "events.jsonl").read_text().splitlines()]
    assert any(event["kind"] == "original_check" for event in events)
    assert any(event["kind"] == "evaluation" for event in events)


def test_mbbp_vote_policy_compiles_runs_and_replays_as_a_canonical_adaptation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A declared vote must use the same public study and replay boundary."""
    monkeypatch.setenv("OMP_NUM_THREADS", "1")
    monkeypatch.setattr("bp_registry.study._source_identity", lambda: "mbbp-vote-test-source-snapshot")
    root = ROOT / "literature_policies/rabeti-2026-multiple-bases-bp-list-decoding"
    policy_path = root / "mbbp-ld-vote.toml"
    policy = parse_literature_policy(policy_path)
    projection = policy.decoder_projection(code_block_length=72, code_check_count=36)
    assert projection["vote"] == {
        "object": "correction_bits", "electorate_rule": "admitted_members",
        "aggregation": "coordinate_majority", "tie_bit": 1,
    }
    assert policy.execution_identity != parse_literature_policy(root / "mbbp-ld.toml").execution_identity

    first = ensure_study(_mbbp_bb72_study(tmp_path), policy_path, results_root=tmp_path / "results")
    second = ensure_study(_mbbp_bb72_study(tmp_path), policy_path, results_root=tmp_path / "results")
    assert first["status"] == "computed" and second["status"] == "reused"
    assert first["result"]["assessment_status"] == "not_assessed"
    events = [json.loads(line) for line in (Path(first["output"]) / "events.jsonl").read_text().splitlines()]
    assert events[0]["data"]["identity"]["source_status"] == "canonical_adaptation"
    assert any(event["kind"] == "vote_electorate" for event in events)
    assert events[-1]["termination"] in {
        "vote_selected_original_valid_candidate", "vote_aggregate_original_invalid", "no_eligible_vote_candidate",
    }


def test_mbbp_vote_policy_rejects_incomplete_or_unknown_vote_controls(tmp_path: Path) -> None:
    root = ROOT / "literature_policies/rabeti-2026-multiple-bases-bp-list-decoding"
    (tmp_path / "mbbp-ld.spec.toml").write_bytes((root / "mbbp-ld.spec.toml").read_bytes())
    policy = (root / "mbbp-ld-vote.toml").read_text()
    incomplete = tmp_path / "mbbp-ld-vote.toml"
    incomplete.write_text(policy.replace("tie_bit = 1\n", ""))
    with pytest.raises(ValueError, match="closed source controls"):
        parse_literature_policy(incomplete)
    incomplete.write_text(policy.replace("tie_bit = 1\n", "tie_bit = 1\nunknown_vote_control = 7\n"))
    with pytest.raises(ValueError, match="closed source controls"):
        parse_literature_policy(incomplete)


def test_mbbp_ld_installed_command_computes_then_reuses(tmp_path: Path) -> None:
    policy = ROOT / "literature_policies/rabeti-2026-multiple-bases-bp-list-decoding/mbbp-ld.toml"
    study = _mbbp_bb72_study(tmp_path)
    command = Path(sys.executable).with_name("bp-registry")
    argv = [command, study, "--decoder", policy, "--results-root", tmp_path / "cli-results"]
    env = {**os.environ, "OMP_NUM_THREADS": "1"}
    first = json.loads(subprocess.run(argv, check=True, capture_output=True, text=True, env=env).stdout)
    second = json.loads(subprocess.run(argv, check=True, capture_output=True, text=True, env=env).stdout)
    assert first["status"] == "computed" and second["status"] == "reused"
    assert first["cache_key"] == second["cache_key"]
    assert first["output"] == second["output"]
    assert second["verification"]["final_row_count"] == 1


def test_mbbp_ld_runnable_no_member_zero_return_is_not_selected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OMP_NUM_THREADS", "1")
    monkeypatch.setattr("bp_registry.study._source_identity", lambda: "mbbp-test-source-snapshot")
    root = ROOT / "literature_policies/rabeti-2026-multiple-bases-bp-list-decoding"
    (tmp_path / "mbbp-ld.spec.toml").write_bytes((root / "mbbp-ld.spec.toml").read_bytes())
    capped = tmp_path / "mbbp-ld.toml"
    capped.write_text((root / "mbbp-ld.toml").read_text().replace(
        "max_member_c2v_updates = 1000000", "max_member_c2v_updates = 1",
    ))
    first = ensure_study(_mbbp_bb72_study(tmp_path), capped, results_root=tmp_path / "results")
    second = ensure_study(_mbbp_bb72_study(tmp_path), capped, results_root=tmp_path / "results")
    assert first["status"] == "computed" and second["status"] == "reused"
    assert first["result"]["terminations"] == {"no_member_converged_zero_return": 1}
    events = [json.loads(line) for line in (Path(first["output"]) / "events.jsonl").read_text().splitlines()]
    kinds = [event["kind"] for event in events]
    assert kinds.count("member") == 2
    assert "selection" not in kinds and "evaluation" not in kinds
    assert events[-1]["data"]["payload"]["source_zero_return"] == [0] * 72
