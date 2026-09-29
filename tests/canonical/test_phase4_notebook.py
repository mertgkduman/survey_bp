"""Adversarial identity/confinement and actual cleared-output execution checks."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile

import nbformat
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import phase4_notebook_support as support
import execute_phase4_notebook as executor
from preview_phase4_notebook import preview_notebook


def _identity(root, stage="evaluation", **changes):
    facts = {field: f"frozen-{field}" for field in support.IDENTITY_FIELDS}
    facts.update(stage=stage, environment=support.ANALYSIS_VERSIONS)
    files = {"manifest": "data/manifests/test.json", "source_policy": "src/bp_registry/test.py",
             "code": "data/artifacts/test.json", "caps": "data/manifests/caps.json",
             "selection": "data/results/phase4-memory-relay/selected-settings.json"}
    for field, relative in files.items():
        path = root / relative
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"randomness": {"physical_sample_identity": "fixture-samples"}}))
        facts[field] = {relative: support.sha256(path.read_bytes()).hexdigest()}
    facts["sample"] = {files["manifest"]: "fixture-samples"}
    facts.update(changes)
    return support.identity(stage, facts)


def _record(expected):
    return {"identity": expected, "execution_qualified": True, "status": "completed",
            "fixture": "development_fixture", "assessment_status": "not_assessed"}


def test_stage_reuse_requires_all_identity_dimensions_and_preserves_mismatch(tmp_path):
    first = _identity(tmp_path)
    record = support.ensure_stage(tmp_path, first, producer=lambda: _record(first), predecessor_verified=True)
    assert record["reused"] is True
    for field in support.IDENTITY_FIELDS - {"stage", "environment"}:
        assert _identity(tmp_path, **{field: "changed"})["identity_digest"] != first["identity_digest"]
    path = support.stage_path(tmp_path, first)
    altered = json.loads(path.read_text())
    altered["identity"] = _identity(tmp_path, sample="other")
    path.write_text(json.dumps(altered))
    before = path.read_bytes()
    assert support.ensure_stage(tmp_path, first, producer=lambda: pytest.fail("producer called"),
                                predecessor_verified=True)["status"] == "identity_mismatch_preserved"
    assert path.read_bytes() == before


def test_generation_gate_precedes_producer_and_rejects_unqualified_evidence(tmp_path):
    expected = _identity(tmp_path)
    with pytest.raises(ValueError, match="predecessor"):
        support.ensure_stage(tmp_path, expected, producer=lambda: pytest.fail("producer called"))
    with pytest.raises(ValueError, match="not been qualified"):
        support.ensure_stage(tmp_path, expected, producer=lambda: {**_record(expected), "execution_qualified": False},
                             predecessor_verified=True)
    assert not support.stage_path(tmp_path, expected).exists()


def test_rehashed_snapshot_identity_and_payload_tampering_rejected(tmp_path):
    expected = _identity(tmp_path)
    support.ensure_stage(tmp_path, expected, producer=lambda: _record(expected), predecessor_verified=True)
    path = support.stage_path(tmp_path, expected)
    altered = json.loads(path.read_text())
    altered["assessment_status"] = "reproduced"
    path.write_text(json.dumps(altered))
    with pytest.raises(ValueError, match="snapshot digest"):
        support.load_stage(tmp_path, expected)
    bad_identity = {**expected, "identity_digest": "0" * 64}
    with pytest.raises(ValueError, match="identity digest"):
        support.stage_path(tmp_path, bad_identity)


def test_stale_originating_source_bytes_reject_even_with_self_consistent_index(tmp_path):
    expected = _identity(tmp_path)
    support.ensure_stage(tmp_path, expected, producer=lambda: _record(expected), predecessor_verified=True)
    (tmp_path / "src/bp_registry/test.py").write_text("changed execution source")
    with pytest.raises(ValueError, match="current source_policy input"):
        support.load_stage(tmp_path, expected)


def test_missing_executable_source_and_selection_cannot_qualify_snapshot(tmp_path):
    expected = _identity(tmp_path)
    (tmp_path / "src/bp_registry/new.py").write_text("new executable source")
    with pytest.raises(ValueError, match="omits executable source"):
        support.load_stage(tmp_path, expected)
    (tmp_path / "src/bp_registry/new.py").unlink()
    expected = _identity(tmp_path, selection="not_applicable")
    with pytest.raises(ValueError, match="require frozen selection"):
        support.load_stage(tmp_path, expected)


def test_notebook_confinement_rejects_traversal_and_symlink_roots(tmp_path):
    outside = tmp_path.parent / f"{tmp_path.name}-outside"
    outside.mkdir()
    with pytest.raises(ValueError, match="confined"):
        support.confined(tmp_path, "../escape", "notebooks")
    (tmp_path / "notebooks").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="escapes repository"):
        support.confined(tmp_path, "notebooks/input.ipynb", "notebooks")


def test_campaign_input_can_use_primary_repo_but_rejects_unrelated_and_nested_roots(tmp_path):
    assert executor.campaign_input_root(ROOT) == ROOT.resolve()
    import subprocess
    common = subprocess.run(["git", "rev-parse", "--git-common-dir"], cwd=ROOT,
                            check=True, capture_output=True, text=True).stdout.strip()
    primary = (ROOT / common).resolve().parent
    assert executor.campaign_input_root(ROOT, primary) == primary
    with pytest.raises(ValueError, match="same Git repository"):
        executor.campaign_input_root(ROOT, tmp_path)
    with pytest.raises(ValueError, match="repository root"):
        executor.campaign_input_root(ROOT, ROOT / "scripts")


def test_missing_evidence_is_not_synthesized_as_performance(tmp_path):
    inventory = support.notebook_inventory(tmp_path)
    assert set(inventory) == set(support.SECTIONS)
    assert {record["status"] for record in inventory.values()} == {"missing_qualified_snapshot"}
    assert not (tmp_path / "data").exists()
    assert all(record["assessment_status"] == "not_assessed" for record in support.fixture_stages().values())


def test_self_consistent_index_cannot_substitute_baseline_for_evaluation(tmp_path):
    baseline = _identity(tmp_path, stage="baseline")
    support.ensure_stage(tmp_path, baseline, producer=lambda: _record(baseline), predecessor_verified=True)
    stages = {stage: _identity(tmp_path, stage=stage) for stage in support.SECTIONS}
    stages["evaluation"] = baseline
    index = {"stages": stages}
    index["index_digest"] = support.digest(index)
    path = tmp_path / "data/results/phase4-notebook/index.json"
    path.write_text(json.dumps(index))
    with pytest.raises(ValueError, match="wrong stage section"):
        support.notebook_inventory(tmp_path)


def test_source_notebook_complete_sections_and_actual_fixture_execution():
    source = ROOT / "notebooks/phase4-memory-relay-analysis.ipynb"
    notebook = nbformat.read(source, as_version=4)
    tagged = {cell.metadata.get("phase4_section") for cell in notebook.cells}
    assert set(support.SECTIONS) <= tagged
    # NFS can briefly retain directory metadata after the kernel closes files.
    with tempfile.TemporaryDirectory(dir=ROOT / "data/results/phase4-notebook", prefix=".test-kernel-",
                                     ignore_cleanup_errors=True) as temporary:
        destination = executor.execute_notebook(repository_root=ROOT, input_path=str(source),
                                                output_path=str(Path(temporary) / "executed.ipynb"),
                                                fixture=True)
        executed = nbformat.read(destination, as_version=4)
        assert list((Path(temporary) / "figures").glob("*.png"))
        preview = preview_notebook(ROOT, str(destination), str(Path(temporary) / "preview.html"))
        html = preview.read_text()
        assert "data:image/png;base64," in html
        assert "<table" in html
        assert "development_fixture" in html and "not_assessed" in html
    assert all(cell.execution_count is not None for cell in executed.cells if cell.cell_type == "code")
    assert all("execution" not in cell.metadata for cell in executed.cells)
    assert executed.metadata["phase4_validation"]["mode"] == "development_fixture"
    text = "".join(str(output) for cell in executed.cells if cell.cell_type == "code" for output in cell.outputs)
    assert "development_fixture" in text
    assert "not_assessed" in text
    outputs = [output for cell in executed.cells if cell.cell_type == "code" for output in cell.outputs]
    assert any("image/png" in output.get("data", {}) for output in outputs)
    assert any("<table" in output.get("data", {}).get("text/html", "") for output in outputs)
    assert "95% Wilson" in text
