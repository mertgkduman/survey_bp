"""Real exported packages and the static preview share portable contracts."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from threading import Thread
from urllib.error import HTTPError
from urllib.request import urlopen
import zipfile

import pytest

from bp_registry.research.cli import preview_server
from bp_registry.research.export import export_package, package_files, registered_package_files


ROOT = Path(__file__).resolve().parents[2]


def specimen():
    return {
        "schema": "research-experiment-v1", "id": "portable-test-fixture",
        "problem": {"kind": "css_code_capacity", "code": {
            "kind": "embedded_css", "hx": [[1, 1, 0]], "hz": [[0, 0, 1]],
            "lx": [[1, 0, 0]], "lz": [[1, 1, 0]],
        }},
        "channel": {"kind": "depolarizing"},
        "decoder": {"family": "binary_css", "implementation": "compiled", "variant": "plain",
                    "rule": "sum_product", "numerical_profile": "binary-spa-flooding-f64-v2",
                    "policy": None, "schedule": "flooding", "stop_on_convergence": True},
        "rate_points": [{"physical_p": .1, "decoder_p0": .1}],
        "sampling": {"seed": 123, "shot_start": 0, "shots": 4},
        "budgets": {"max_shots": 4, "max_iterations": 3},
        "provenance": {"relation": "development_fixture", "source_spec_id": None, "notes": None},
    }


def test_exported_zip_is_self_contained_and_validates_after_relocation(tmp_path):
    target = export_package(specimen(), tmp_path / "package.zip", repository=ROOT)
    relocated = tmp_path / "moved directory"
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        archive.extractall(relocated)
    manifest = json.loads((relocated / "package-manifest.json").read_text())
    for name, digest in manifest["files"].items():
        assert sha256((relocated / name).read_bytes()).hexdigest() == digest
    assert (relocated / "inputs/code.json").exists()
    checked = subprocess.run(
        [sys.executable, str(relocated / "run.py"), "--repo", str(ROOT), "--validate-only"],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert checked.returncode == 0, checked.stderr
    assert json.loads(checked.stdout)["schema"] == "research-experiment-v1"
    assert not (relocated / "results").exists()


def test_package_manifest_rejects_changed_requested_settings(tmp_path):
    files = package_files(specimen(), repository=ROOT)
    for name, content in files.items():
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    (tmp_path / "decoder.json").write_text("{}")
    checked = subprocess.run([sys.executable, str(tmp_path / "run.py"), "--repo", str(ROOT), "--validate-only"],
                             capture_output=True, text=True)
    assert checked.returncode != 0
    assert "Package file changed" in checked.stderr


def test_export_preserves_existing_file_and_rejects_unsupported_schedule(tmp_path):
    target = tmp_path / "existing.zip"
    target.write_bytes(b"preserve this result")
    with pytest.raises(FileExistsError):
        export_package(specimen(), target, repository=ROOT)
    assert target.read_bytes() == b"preserve this result"
    invalid = specimen()
    invalid["decoder"]["schedule"] = "layered"
    with pytest.raises(ValueError):
        export_package(invalid, tmp_path / "unsupported.zip", repository=ROOT)
    assert not (tmp_path / "unsupported.zip").exists()


def test_original_registered_workflow_exports_real_inputs_without_starting_campaign(tmp_path):
    files = registered_package_files("fair-beam-relay-css-v2", repository=ROOT)
    for name, data in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    checked = subprocess.run([sys.executable, str(tmp_path / "run.py"), "--repo", str(ROOT), "--validate-only"],
                             capture_output=True, text=True, cwd=tmp_path)
    assert checked.returncode == 0, checked.stderr
    request = json.loads(checked.stdout)
    assert request["experiment_id"] == "fair-beam-relay-css-v2"
    assert request["repository_inputs"]
    assert not (tmp_path / "results").exists()


def test_preview_serves_interface_and_tracked_assets_without_private_files():
    server = preview_server(ROOT, port=0)
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with urlopen(base + "/") as response:
            assert response.status == 200
            assert b"BP-based QLDPC decoding workbench" in response.read()
        with urlopen(base + "/web/research/v1/") as response:
            assert response.status == 200 and b"Research Registry" in response.read()
        with urlopen(base + "/data/artifacts/project-three-qubit-css-fixture.json") as response:
            assert response.status == 200
        for url in ("/.git/config", "/.venv/pyvenv.cfg", "/%2e%2e/secret", "/src/"):
            with pytest.raises(HTTPError) as failure:
                urlopen(base + url)
            assert failure.value.code in {403, 404}
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


def test_registered_source_circuit_materializes_with_original_license_and_runs(tmp_path):
    pytest.importorskip("stim")
    pytest.importorskip("sinter")
    from bp_registry.research.runner import run_experiment
    value = json.loads((ROOT / "research/examples/circuit.json").read_text())
    value["problem"]["circuit"] = {"kind": "registered", "id": "relay-surface-d3"}
    value["sampling"].update(shots=2, shot_start=0)
    value["budgets"].update(max_shots=2, max_iterations=2)
    value["decoder"]["max_iterations"] = 2
    files = package_files(value, repository=ROOT)
    assert files["inputs/LICENSE.txt"] == (ROOT / "data/circuits/relay-v0.2.2/LICENSE.txt").read_bytes()
    assert json.loads(files["inputs/circuit-source.json"])["upstream_commit"]
    result = run_experiment(json.loads(files["experiment.json"]), output=tmp_path / "source-circuit", repository=ROOT)
    assert result["rows"][0]["n"] == 2
    assert result["rows"][0]["exact_successes"] is None
