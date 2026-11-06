from __future__ import annotations

import json
from pathlib import Path

from bp_registry.research.catalog import build_catalog, write_catalog


REPOSITORY = Path(__file__).resolve().parents[2]


def test_catalog_uses_retained_summary_evidence_without_raw_ledger_promotion(tmp_path: Path) -> None:
    catalog = build_catalog(REPOSITORY)

    assert catalog["schema_version"] == 1
    assert {paper["paper_id"] for paper in catalog["papers"]} >= {
        "yao-2312-10950-v2", "pfister-presentation-excerpt", "relaybp-2506-01779-v2",
    }
    datasets = {item["dataset_id"]: item for item in catalog["datasets"]}
    assert datasets["pfister-presentation-source-curves"]["evidence_status"] == "source_transcription"
    assert datasets["yao-vanilla-a5-b2"]["evidence_status"] == "canonical_adaptation"
    assert datasets["yao-non-osd-results"]["points"]
    source = datasets["pfister-presentation-source-curves"]["points"]
    assert source[0]["source_value"] == source[0]["y"]
    assert any(point["metadata"]["source_point_type"] == "upper_95_one_sided" and not point["metadata"]["is_rate_estimate"]
               for point in source)
    bb72 = datasets["bb72-fair-beam-relay-v2"]
    assert any(point["n"] == 512 and point["failures"] == 96 for point in bb72["points"])
    raw = next(asset for asset in datasets["yao-vanilla-a5-b2"]["assets"] if asset["kind"] == "jsonl_zstd")
    assert raw["availability"] == "tracked"
    assert raw["url"] == raw["path"]
    assert all({"x", "y", "n", "failures", "ci_low", "ci_high", "status", "mean_work", "work_unit", "mean_seconds", "type_i", "type_ii", "source_value"} <= set(point)
               for dataset in catalog["datasets"] for point in dataset["points"])
    public_inputs = {code["code_id"] for code in catalog["codes"]} | {circuit["circuit_id"] for circuit in catalog["circuits"]}
    assert {series["code_id"] for series in catalog["result_series"]} <= public_inputs
    assert {series["decoder_id"] for series in catalog["result_series"]} <= {decoder["decoder_id"] for decoder in catalog["decoders"]}
    assert len(catalog["decoders"]) == len({decoder["decoder_id"] for decoder in catalog["decoders"]})
    assert {dataset["dataset_id"] for dataset in catalog["datasets"]} <= {experiment.get("dataset_id") for experiment in catalog["experiments"]}
    assert {"a5", "b2", "b1", "c2", "double-gross", "bb72", "gb46"} <= {code["code_id"] for code in catalog["codes"]}
    assert "three-qubit" not in {code["code_id"] for code in catalog["codes"]}
    gross = next(code for code in catalog["codes"] if code["code_id"] == "double-gross")
    assert gross["artifact_path"] == "from_dr_pfister_presentetations/run_reproduction.py"
    assert any(study["study_id"] == "phase11-gb46-bounded-policy-mechanisms" for study in catalog["studies"])
    smoke_circuit = next(circuit for circuit in catalog["circuits"] if circuit["circuit_id"] == "relay-surface-d3")
    assert smoke_circuit["asset"]["path"] == "data/circuits/relay-v0.2.2/rotated_surface_code_memory_X.stim"
    assert smoke_circuit["asset"]["availability"] == "tracked"
    assert smoke_circuit["asset"]["sha256"]
    circuit = [series for series in catalog["result_series"] if series["dataset_id"].startswith("circuit-cpu-profile-")]
    assert {series["code_id"] for series in circuit} == {"relay-surface-d3", "relay-bb144-memory-z", "beamsearch-bb144-memory-z-p005"}
    assert all(series["channel_kind"] == "embedded_circuit" for series in circuit)
    surface = next(series for series in circuit if series["code_id"] == "relay-surface-d3")
    assert surface["points"][0]["n"] == 4096 and surface["points"][0]["failures"] == 96
    assert surface["points"][0]["metadata"]["prior_comparison_report"].endswith("circuit-bp-cpu-profile-v1.json")


def test_series_policies_are_namespaced_and_never_default_to_another_arm() -> None:
    catalog = build_catalog(REPOSITORY)
    decoders = {record["decoder_id"]: record for record in catalog["decoders"]}
    binary_v1 = next(series for series in catalog["result_series"]
                     if series["dataset_id"] == "yao-vanilla-a5-b2" and series["source_decoder_id"] == "binary_v1")
    record = decoders[binary_v1["decoder_id"]]
    assert record["asset"]["path"].endswith("yao-2312-10950-vanilla/decoders/binary_v1.json")
    assert record["configuration"]["settings_status"] == "exact_policy_file"
    assert record["configuration"]["effective_policy"]["id"] == "binary_v1"
    assert record["configuration"]["effective_policy"]["family"] == "binary_css_separate"
    assert binary_v1["decoder_id"].startswith("yao-vanilla-a5-b2:")


def test_importance_rows_do_not_present_raw_counts_as_binomial_estimates() -> None:
    catalog = build_catalog(REPOSITORY)
    points = next(dataset["points"] for dataset in catalog["datasets"] if dataset["dataset_id"] == "yao-non-osd-results")
    importance = next(point for point in points if point.get("metadata", {}).get("estimator") == "mixture_importance")
    assert importance["n"] is None and importance["failures"] is None
    assert importance["metadata"]["raw_samples"] == 4580
    assert importance["metadata"]["raw_failures"] == 33
    assert importance["metadata"]["weighted_estimate"] == importance["y"]


def test_source_upper_bound_retains_known_zero_failure_denominator_without_becoming_a_rate() -> None:
    catalog = build_catalog(REPOSITORY)
    source = next(dataset for dataset in catalog["datasets"] if dataset["dataset_id"] == "pfister-presentation-source-curves")
    bound = next(point for point in source["points"]
                 if point["metadata"]["source_point_type"] == "upper_95_one_sided")

    assert bound["x"] == 0.06
    assert bound["n"] == 100000 and bound["failures"] == 0
    assert bound["metadata"]["is_rate_estimate"] is False
    assert bound["metadata"]["confidence_level"] == 0.95
    assert bound["metadata"]["uncertainty_method"] == "exact_one_sided_95_percent_upper_bound"
    assert bound["ci_low"] is None and bound["ci_high"] is None


def test_fair_bb72_profile_selection_is_part_of_the_effective_decoder_identity() -> None:
    catalog = build_catalog(REPOSITORY)
    records = {record["decoder_id"]: record for record in catalog["decoders"]}
    fair = [series for series in catalog["result_series"] if series["dataset_id"] == "bb72-fair-beam-relay-v2"
            and series["source_decoder_id"].startswith("beam-g1000")]
    assert {series["source_decoder_id"] for series in fair} == {"beam-g1000-i05", "beam-g1000-i10"}
    assert len({series["decoder_id"] for series in fair}) == 2
    assert all(records[series["decoder_id"]]["asset"]["path"].endswith("fair-beam-relay-css-v2/result.json") for series in fair)
    fair_dataset = next(dataset for dataset in catalog["datasets"] if dataset["dataset_id"] == "bb72-fair-beam-relay-v2")
    assert fair_dataset["paper_ids"] == ["relaybp-2506-01779-v2", "beamsearch-2512-07057-v2"]
    ledger = next(asset for asset in fair_dataset["assets"] if asset["kind"] == "jsonl_gz")
    assert ledger["availability"] == "tracked"
    assert ledger["path"].endswith("evaluation/p050/i05/events.jsonl.gz")
    tuning = next(dataset for dataset in catalog["datasets"] if dataset["dataset_id"] == "yao-bp4-tuning-fairness-p006")
    assert all(point["metadata"]["confidence_level"] == 0.90 for point in tuning["points"])


def test_selected_validation_arm_embeds_its_matching_candidate_not_a_selected_default() -> None:
    catalog = build_catalog(REPOSITORY)
    records = {record["decoder_id"]: record for record in catalog["decoders"]}
    series = next(series for series in catalog["result_series"]
                  if series["dataset_id"] == "yao-bp4-tuning-selected-validation"
                  and series["source_decoder_id"] == "sp_f64_v2_d01_p006_t10000")
    record = records[series["decoder_id"]]
    assert record["asset"]["path"].endswith("decoders/joint_final_candidates.json")
    assert record["configuration"]["effective_candidate"]["id"] == "sp_f64_v2_d01_p006_t10000"


def test_bpsf_runtime_scope_remains_machine_readable() -> None:
    catalog = build_catalog(REPOSITORY)
    points = next(dataset["points"] for dataset in catalog["datasets"] if dataset["dataset_id"] == "bb72-bpsf-factorial-v2")
    scopes = {point["metadata"]["runtime_scope"] for point in points}
    assert {"canonical_decode_attempt", "canonical_intervention_controller"} <= scopes
    assert all(point["metadata"]["runtime_comparison_status"] == "not_comparable_across_controller_and_decode_scopes" for point in points)


def test_bb72_effective_controls_and_grouped_curves_are_preserved() -> None:
    catalog = build_catalog(REPOSITORY)
    decoders = {record["decoder_id"]: record for record in catalog["decoders"]}
    bpsf_series = [series for series in catalog["result_series"] if series["dataset_id"] == "bb72-bpsf-factorial-v2"]
    assert len(bpsf_series) == 12
    assert all([point["x"] for point in series["points"]] == [0.05, 0.08] for series in bpsf_series)
    bpsf = next(series for series in bpsf_series if series["source_decoder_id"] == "ms-g0500-bpsf20plus4x5")
    bpsf_config = decoders[bpsf["decoder_id"]]["configuration"]["effective_configuration"]
    assert bpsf_config["update"] == "min_sum" and bpsf_config["damping_gamma"] == 0.5
    assert bpsf_config["bpsf_controls"]["test_cap"] == 4
    assert all(point["metadata"]["raw_asset"]["availability"] == "tracked" for point in bpsf["points"])
    fair = next(series for series in catalog["result_series"] if series["dataset_id"] == "bb72-fair-beam-relay-v2"
                and series["source_decoder_id"] == "beam-g1000-i10")
    fair_config = decoders[fair["decoder_id"]]["configuration"]["effective_configuration"]
    assert fair_config["selected_profile"] == "i10"
    assert fair_config["profile_controls"]["extra_iterations_per_unit"] == 10
    keys = [(series["dataset_id"], series["code_id"], series["decoder_id"]) for series in catalog["result_series"]]
    assert len(keys) == len(set(keys))
    assert len({series["series_id"] for series in catalog["result_series"]}) == len(catalog["result_series"])


def test_catalog_keeps_qbpgd_cohorts_and_exact_per_arm_configuration_separate() -> None:
    catalog = build_catalog(REPOSITORY)
    datasets = {dataset["dataset_id"]: dataset for dataset in catalog["datasets"]}
    records = {record["decoder_id"]: record for record in catalog["decoders"]}
    confirmation = datasets["yao-tuned-qbpgd-p006"]
    pilot = datasets["yao-tuned-qbpgd-p006-pilot-n1000"]

    assert confirmation["cohort"]["kind"] == "confirmation"
    assert confirmation["cohort"]["shots_per_arm"] == 10000
    assert all(point["n"] == 10000 and point["metadata"]["seed"] == 20261030 for point in confirmation["points"])
    assert pilot["cohort"]["kind"] == "pilot"
    assert pilot["cohort"]["shots_per_arm"] == 1000
    assert all(point["n"] == 1000 and point["metadata"]["seed"] == 20261029 for point in pilot["points"])
    assert all("summary.json" in point["metadata"]["summary_path"] for point in confirmation["points"] + pilot["points"])

    confirmation_series = [series for series in catalog["result_series"] if series["dataset_id"] == confirmation["dataset_id"]]
    pilot_series = [series for series in catalog["result_series"] if series["dataset_id"] == pilot["dataset_id"]]
    assert len(confirmation_series) == len(pilot_series) == 4
    assert all(len(series["points"]) == 1 for series in confirmation_series + pilot_series)
    a5_control = next(series for series in confirmation_series
                      if series["source_code_label"] == "a5" and series["source_decoder_id"] == "control")
    a5_tuned = next(series for series in confirmation_series
                    if series["source_code_label"] == "a5" and series["source_decoder_id"] == "tuned")
    assert records[a5_control["decoder_id"]]["configuration"]["effective_configuration"]["arm_policy"] == {
        "check_cap": None, "decoder_p0": 0.06, "kernel": "bp4-f64-v2",
        "product_epsilon": 1e-10, "v2c_damping": 0.0,
    }
    assert records[a5_tuned["decoder_id"]]["configuration"]["effective_configuration"]["arm_policy"] == {
        "check_cap": None, "decoder_p0": 0.005, "kernel": "bp4-f64-v2",
        "product_epsilon": 1e-10, "v2c_damping": 0.2,
    }


def test_cross_code_records_bind_shared_policy_to_selected_arm_channel_and_source_figure() -> None:
    catalog = build_catalog(REPOSITORY)
    records = {record["decoder_id"]: record for record in catalog["decoders"]}
    cross = next(series for series in catalog["result_series"]
                 if series["dataset_id"] == "yao-cross-code-plain-baselines"
                 and series["source_code_label"] == "a5" and series["source_decoder_id"] == "binary_v2")
    configuration = records[cross["decoder_id"]]["configuration"]["effective_configuration"]
    assert configuration["selected_arm"] == "binary_v2"
    assert configuration["channel_binding"] == "depolarizing"
    assert configuration["shared_policy"]["schema"] == "cross-code-plain-bp-policies-v1"

    scoped = [series for series in catalog["result_series"]
              if series["dataset_id"] == "yao-non-osd-results"
              and series["source_code_label"] == "b1" and series["source_decoder_id"] == "bp"]
    assert {series["series_scope"]["figure"] for series in scoped} == {"2", "3", "4", "6"}
    assert all(len({point["x"] for point in series["points"]}) == len(series["points"]) for series in scoped)
    referenced = {series["decoder_id"] for series in catalog["result_series"]}
    assert {record["decoder_id"] for record in catalog["decoders"]} == referenced


def test_catalog_export_is_json_and_keeps_specialized_recipe_boundaries(tmp_path: Path) -> None:
    destination = tmp_path / "catalog.json"
    catalog = write_catalog(REPOSITORY, destination)

    exported = json.loads(destination.read_text(encoding="utf-8"))
    assert exported["catalog_kind"] == "retained_research_evidence"
    recipes = {item["experiment_id"]: item["reproduction_recipe"] for item in catalog["experiments"]}
    assert recipes["fair-beam-relay-css-v2"]["kind"] == "registered_study"
    assert recipes["yao-vanilla"]["kind"] == "source_command"
    assert recipes["yao-vanilla"]["commands"] == [
        "PYTHONPATH=src python data/reproductions/yao-2312-10950-vanilla/analyze.py"
    ]


def test_fallback_recipes_keep_retained_cohorts_and_extensions_separate() -> None:
    catalog = build_catalog(REPOSITORY)
    recipes = {item["dataset_id"]: item["reproduction_recipe"] for item in catalog["experiments"]
               if item.get("dataset_id")}

    source = recipes["pfister-presentation-source-curves"]
    assert source["kind"] == "retained_source_only"
    assert source["commands"] == []
    assert source["original_instruction_path"] == "from_dr_pfister_presentetations/README.md"

    local_pilot = recipes["pfister-presentation-local-pilots"]
    assert local_pilot["commands"][0].endswith("from_dr_pfister_presentetations/verify_spike.py")
    assert "--shots 100 --seed 20261110" in local_pilot["bounded_extension_commands"][0]
    assert "not a regeneration" in local_pilot["budget_note"]

    full_v2 = recipes["pfister-presentation-full-v2-curves"]
    assert full_v2["commands"] == [
        "PYTHONPATH=src:from_dr_pfister_presentetations .venv/bin/python "
        "from_dr_pfister_presentetations/analyze_full_v2_curves.py"
    ]
    assert "--max-shots 20000" in full_v2["bounded_extension_commands"][0]

    fairness = recipes["yao-bp4-tuning-fairness-p006"]
    assert fairness["commands"][-1].endswith("fairness_t100/plot.py")
    assert fairness["bounded_extension_commands"] == [
        "PYTHONPATH=src python data/reproductions/yao-2312-10950-bp4-tuning-p006/"
        "fairness_t100/run_task.py --stage pilot --index 0"
    ]

    selected = recipes["yao-bp4-tuning-selected-validation"]
    assert selected["commands"][0].endswith("analyze_fixed.py joint_final")
    assert selected["bounded_extension_commands"][0].endswith("run_joint_final_task.py --index 0")

    cross_code = recipes["yao-cross-code-plain-baselines"]
    assert cross_code["bounded_extension_commands"][0].endswith("run.py --index 0 --smoke")
    depolarizing = recipes["yao-cross-code-depolarizing"]
    assert depolarizing["compute_bearing_extension_commands"][0].endswith("depolarizing/campaign.py pilot")

    bpsf = recipes["bb72-bpsf-factorial-v2"]
    assert bpsf["commands"][0].endswith("run_bb72_bpsf_factorial_v2.py preflight")
    assert bpsf["compute_bearing_extension_commands"][0].endswith("run --workers 24")

    qbpgd_pilot = recipes["yao-tuned-qbpgd-p006-pilot-n1000"]
    assert qbpgd_pilot["kind"] == "retained_result_only"
    assert qbpgd_pilot["commands"] == []
    assert "Do not pool" in qbpgd_pilot["budget_note"]
    assert "--seed 20261110" in qbpgd_pilot["bounded_extension_commands"][0]


def test_presentation_float64_curves_do_not_inherit_q8_or_wrong_damping():
    catalog = build_catalog(REPOSITORY)
    records = {item["decoder_id"]: item for item in catalog["decoders"]}
    for series in catalog["result_series"]:
        if series["dataset_id"] != "pfister-presentation-full-v2-curves" or series["source_decoder_id"] not in {"bp4_tuned_sp_v2", "bp4_vanilla_sp_v2"}:
            continue
        decoder = records[series["decoder_id"]]
        assert decoder["asset"]["path"].endswith("canonical_bp4_f64_v2.json")
        assert decoder["configuration"]["settings_status"] == "numerical_profile_with_runner_overrides"
        effective = decoder["configuration"]["effective_configuration"]
        assert effective["message_resolution"] == "float64"
        assert effective["v2c_damping"] == (0 if series["source_decoder_id"] == "bp4_vanilla_sp_v2" else .1)
        assert effective["runner_sha256"]
