from __future__ import annotations

import json
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[2]
POLICY_PATH = REPOSITORY / "research/catalog/policies.json"
INPUT_PATH = REPOSITORY / "research/catalog/inputs.json"


def _policy_catalog() -> dict[str, object]:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def test_policy_catalog_has_renderable_equations_and_explicit_routes() -> None:
    catalog = _policy_catalog()
    policies = catalog["policies"]

    assert catalog["schema_version"] == 1
    assert isinstance(policies, list)
    assert len({policy["id"] for policy in policies}) == len(policies)
    expected = {
        "flooding_schedule",
        "v2c_damping",
        "normalized_offset_min_sum",
        "message_resolution",
        "uniform_posterior_memory",
        "modified_bp4",
        "relay_disordered_memory",
        "binary_guided_decimation",
        "quaternary_guided_decimation",
        "bpsf_degeneracy_cutting",
        "beam_search",
    }
    assert expected <= {policy["id"] for policy in policies}

    for policy in policies:
        assert isinstance(policy["label"], str) and policy["label"]
        assert isinstance(policy["notation"], str) and policy["notation"]
        assert policy["equations"] and all(isinstance(equation, str) and equation for equation in policy["equations"])
        assert all(parameter["symbol"] and parameter["meaning"] for parameter in policy["parameters"])
        assert policy["execution_status"]
        assert set(policy["execution"]) == {"custom_builder", "registered_study", "circuit"}
        assert all(route["status"] and route["scope"] for route in policy["execution"].values())
        if policy["source_url"] is not None:
            assert policy["source_url"].startswith("https://arxiv.org/")
            assert policy["source_label"]


def test_policy_catalog_keeps_builder_capability_distinct_from_study_and_circuit_claims() -> None:
    policies = {policy["id"]: policy for policy in _policy_catalog()["policies"]}

    assert policies["quaternary_guided_decimation"]["execution_status"] == "builder_supported"
    assert policies["quaternary_guided_decimation"]["execution"]["custom_builder"] == {
        "status": "supported_with_restrictions",
        "scope": "Compiled BP4 only, quaternary f64 v2, sum_product, flooding, policy=null, and first-valid stopping.",
    }
    assert policies["relay_disordered_memory"]["execution"]["custom_builder"]["status"] == "unavailable"
    assert policies["relay_disordered_memory"]["execution"]["circuit"]["status"] == "unavailable"
    assert policies["beam_search"]["execution"]["registered_study"]["status"] == "controlled_css_adaptation"
    assert policies["bpsf_degeneracy_cutting"]["execution"]["registered_study"]["status"] == "controlled_css_adaptation"
    assert policies["modified_bp4"]["execution_status"] == "mapped_mechanism_only"
    assert policies["binary_guided_decimation"]["execution"]["custom_builder"]["status"] == "unavailable"


def test_code_families_cover_every_registered_input_without_false_bb144_code_membership() -> None:
    catalog = _policy_catalog()
    inputs = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    families = catalog["code_families"]
    known_codes = {record["code_id"] for record in inputs["codes"]}
    known_circuits = {record["circuit_id"] for record in inputs["circuits"]}

    assert len({family["id"] for family in families}) == len(families)
    family_codes = [code_id for family in families for code_id in family["code_ids"]]
    listed_circuits = [circuit["id"] for family in families for circuit in family["circuits"]]
    assert set(family_codes) == known_codes
    assert len(family_codes) == len(set(family_codes))
    assert set(listed_circuits) == known_circuits
    assert len(listed_circuits) == len(set(listed_circuits))

    bivariate = next(family for family in families if family["id"] == "bivariate_bicycle")
    assert bivariate["code_ids"] == ["bb72", "double-gross"]
    assert bivariate["circuit_code_ids"] == []
    assert {item["id"] for item in bivariate["circuits"]} == {
        "relay-bb144-memory-z", "beamsearch-bb144-memory-z-p005"
    }
    assert next(family for family in families if family["id"] == "color_code")["code_ids"] == []
