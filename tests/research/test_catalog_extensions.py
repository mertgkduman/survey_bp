"""A new normalized study enters the same catalog without interface edits."""
from __future__ import annotations

from copy import deepcopy
import json

import pytest

from bp_registry.research.catalog_model import extend_catalog, validate_catalog


def test_additive_catalog_extension_resolves_entities_and_assigns_stable_series_id(tmp_path):
    base = {kind: [] for kind in ("papers", "decoders", "codes", "circuits", "experiments", "datasets", "result_series")}
    extension = {
        "schema": "research-catalog-extension-v1",
        "papers": [{"paper_id": "fixture-study", "title": "Test fixture", "kind": "local_study"}],
        "decoders": [{"decoder_id": "fixture-decoder", "label": "Fixture"}],
        "codes": [{"code_id": "fixture-code", "label": "Fixture"}],
        "experiments": [{"experiment_id": "fixture-experiment", "paper_ids": ["fixture-study"], "dataset_ids": ["fixture-data"]}],
        "datasets": [{"dataset_id": "fixture-data", "paper_id": "fixture-study", "label": "Synthetic test only", "evidence_status": "development_fixture", "source_path": "test-source.json"}],
        "result_series": [{"dataset_id": "fixture-data", "code_id": "fixture-code", "decoder_id": "fixture-decoder", "label": "Synthetic test only", "points": [{"x": .1, "y": .1, "n": 10, "failures": 1, "status": "development_fixture"}]}],
    }
    (tmp_path / "extension.json").write_text(json.dumps(extension))
    catalog = extend_catalog(base, {"normalized_catalogs": ["extension.json"]}, tmp_path)
    assert catalog["papers"][0]["paper_id"] == "fixture-study"
    assert catalog["result_series"][0]["series_id"] == "fixture-data:fixture-code:fixture-decoder"
    assert catalog["extension_sources"][0]["sha256"]
    assert not base["papers"]
    duplicate = deepcopy(catalog)
    duplicate["result_series"].append(deepcopy(duplicate["result_series"][0]))
    with pytest.raises(ValueError, match="duplicate result series"):
        validate_catalog(duplicate)
    broken = deepcopy(catalog)
    broken["result_series"][0]["decoder_id"] = "unregistered"
    with pytest.raises(ValueError, match="unresolved decoders"):
        validate_catalog(broken)


def test_catalog_extension_cannot_escape_repository(tmp_path):
    with pytest.raises(ValueError, match="unavailable within repository"):
        extend_catalog({}, {"normalized_catalogs": ["../outside.json"]}, tmp_path)


def test_independent_studies_share_identical_paper_without_merging_datasets(tmp_path):
    base = {kind: [] for kind in ("papers", "decoders", "codes", "circuits", "experiments", "datasets", "result_series")}
    paper = {"paper_id": "same-paper", "title": "The same source", "kind": "paper"}
    for name in ("original", "confirmation"):
        extension = {"schema": "research-catalog-extension-v1", "papers": [paper],
                     "datasets": [{"dataset_id": name, "paper_id": paper["paper_id"]}]}
        (tmp_path / f"{name}.json").write_text(json.dumps(extension))
    registry = {"normalized_catalogs": ["original.json", "confirmation.json"]}
    value = extend_catalog(base, registry, tmp_path)
    assert value["papers"] == [paper]
    assert [r["dataset_id"] for r in value["datasets"]] == ["original", "confirmation"]
    assert len(value["extension_sources"]) == 2
    assert not base["papers"]
    base["papers"] = [deepcopy(paper)]
    assert extend_catalog(base, registry, tmp_path)["papers"] == [paper]


def test_conflicting_paper_and_duplicate_dataset_remain_invalid(tmp_path):
    base = {"papers": [{"paper_id": "same-paper", "title": "Original"}], "datasets": []}
    extension = {"schema": "research-catalog-extension-v1",
                 "papers": [{"paper_id": "same-paper", "title": "Conflicting"}]}
    path = tmp_path / "extension.json"
    path.write_text(json.dumps(extension))
    with pytest.raises(ValueError, match="conflicting paper metadata: same-paper"):
        extend_catalog(base, {"normalized_catalogs": [path.name]}, tmp_path)
    extension["papers"] = deepcopy(base["papers"])
    extension["datasets"] = [{"dataset_id": "duplicate", "paper_id": "same-paper"}] * 2
    path.write_text(json.dumps(extension))
    with pytest.raises(ValueError, match="duplicate dataset_id"):
        extend_catalog(base, {"normalized_catalogs": [path.name]}, tmp_path)


def test_external_large_data_is_a_storage_declaration_not_a_download(tmp_path):
    import subprocess
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    base = {kind: [] for kind in ("papers", "decoders", "codes", "circuits", "experiments", "datasets", "result_series")}
    extension = {"schema": "research-catalog-extension-v1", "papers": [{"paper_id": "fixture", "asset": {"kind": "raw_data", "label": "HPC ledger", "storage_path": "/external/archive/events.jsonl.gz", "storage_instructions": "Ask the storage owner for access; verify the declared checksum.", "sha256": "a" * 64}}]}
    (tmp_path / "extension.json").write_text(json.dumps(extension))
    value = extend_catalog(base, {"normalized_catalogs": ["extension.json"]}, tmp_path)["papers"][0]["asset"]
    assert value["url"] is None
    assert value["availability"] == "external_unverified"
    assert value["checksum_status"] == "declared_unverified"


def test_retired_public_datasets_resolve_to_preserved_evidence():
    base = {kind: [] for kind in ("papers", "decoders", "codes", "circuits", "experiments", "datasets", "result_series")}
    base['papers'] = [{'paper_id': 'p'}]
    base['datasets'] = [{'dataset_id': 'd', 'paper_id': 'p'}]
    valid = {**base, 'public_retired_dataset_ids': ['d']}
    assert validate_catalog(valid)['datasets'] == base['datasets']
    for invalid in (['missing'], ['d', 'd'], [{}], 'd'):
        with pytest.raises(ValueError, match='public retired datasets'):
            validate_catalog({**base, 'public_retired_dataset_ids': invalid})
