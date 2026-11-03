"""Optional real-browser and downloaded-package verification (small fixtures).

Run with a Python environment containing Playwright and a Chromium installation.
This is separate from pytest so ordinary library users need no browser tooling.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import csv
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import zipfile

from playwright.sync_api import sync_playwright


def verify(repository: Path, base: str, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    report = {"schema": "research-interface-browser-verification-v1", "checks": [], "executed": [], "errors": []}
    catalog = json.loads((repository / "web/research/catalog.json").read_text())

    def run_package(zip_path: Path, label: str):
        package = output / label
        with zipfile.ZipFile(zip_path) as archive:
            assert archive.testzip() is None
            archive.extractall(package)
        manifest = json.loads((package / "package-manifest.json").read_text())
        for name, digest in manifest["files"].items():
            assert sha256((package / name).read_bytes()).hexdigest() == digest
        command = [sys.executable, str(package / "run.py"), "--repo", str(repository)]
        validated = subprocess.run(command + ["--validate-only"], cwd=output, text=True, capture_output=True)
        assert validated.returncode == 0, validated.stderr
        result = subprocess.run(command + ["--output", str(package / "result")], cwd=output, text=True, capture_output=True)
        (package / "execution.log").write_text(result.stdout + result.stderr)
        assert result.returncode == 0, result.stderr
        summary = json.loads((package / "result/summary.json").read_text())
        assert all(row["n"] <= 4 for row in summary["rows"])
        assert summary["provenance"]["implementation_sources"]
        assert summary["input_identity"]["raw_sha256"]
        analysis = subprocess.run([sys.executable, str(package / "analyse.py"), str(package / "result")], cwd=output, text=True, capture_output=True)
        (package / "analysis.log").write_text(analysis.stdout + analysis.stderr)
        assert analysis.returncode == 0, analysis.stderr
        preserved = (package / "result/summary.json").read_bytes()
        rerun = subprocess.run(command + ["--output", str(package / "result")], cwd=output, text=True, capture_output=True)
        assert rerun.returncode != 0
        assert (package / "result/summary.json").read_bytes() == preserved
        report["executed"].append({"label": label, "rows": summary["rows"], "experiment_id": summary["experiment_id"], "implementation_sha256": summary["provenance"]["implementation_sha256"], "analysis_png": str(package / "result/failure-rate.png"), "preserved_existing_output": True})

    with sync_playwright() as browser_api:
        browser = browser_api.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1050}, accept_downloads=True)
        page.on("pageerror", lambda error: report["errors"].append(str(error)))
        page.goto(base)
        page.wait_for_function("document.querySelector('#catalog-status').textContent.includes('retained')")
        assert page.locator(".paper-card").count() >= 8
        page.locator('[data-nav="results"]').click()
        assert page.locator("#result-code").input_value() == "a5"
        assert page.locator("#result-experiment").input_value() == "yao-vanilla"
        vanilla = next(s for s in catalog["result_series"] if s["dataset_id"] == "yao-vanilla-a5-b2" and s["code_id"] == "a5" and s["source_decoder_id"] == "bp4_v2")
        page.locator("#result-decoder").select_option(vanilla["decoder_id"])
        assert page.locator("#result-table tbody tr").count() == len(vanilla["points"])
        assert page.locator("#result-plot .plot-point").count() == len(vanilla["points"])
        plot_before = page.locator("#result-plot .plot-line").first.get_attribute("d")
        assert "NaN" not in plot_before
        assert "quaternary-bp4-f64-v2" in page.locator("#frozen-spec").inner_text()
        with page.expect_download() as download_info:
            page.locator("#download-frozen-spec").click()
        frozen_file = output / "frozen-decoder.json"
        download_info.value.save_as(frozen_file)
        definition = next(d for d in catalog["decoders"] if d["decoder_id"] == vanilla["decoder_id"])
        assert frozen_file.read_bytes() == (repository / definition["asset"]["path"]).read_bytes()
        report["checks"].append("paper → experiment → A5 BP4 v2 real results and byte-exact decoder export")
        binary = next(s for s in catalog["result_series"] if s["dataset_id"] == "yao-vanilla-a5-b2" and s["code_id"] == "a5" and s["source_decoder_id"] == "binary_v1")
        page.locator("#result-decoder").select_option(binary["decoder_id"])
        assert page.locator("#result-plot .plot-line").first.get_attribute("d") != plot_before
        assert "binary" in page.locator("#frozen-spec").inner_text()
        page.locator("#result-code").select_option("b2")
        assert page.locator("#result-table tbody tr[data-code='b2']").count() > 0
        page.locator("#result-code").select_option("a5")
        report["checks"].append("code / decoder filters update the plotted series, numerical rows, and exact settings")
        page.locator("#result-paper").select_option("relaybp-2506-01779-v2")
        page.locator("#result-experiment").select_option("fair-beam-relay-css-v2")
        with page.expect_download() as download_info:
            page.locator("#download-registered-workflow").click()
        registered_zip = output / "registered-workflow.zip"
        download_info.value.save_as(registered_zip)
        registered = output / "original registered workflow"
        with zipfile.ZipFile(registered_zip) as archive:
            assert archive.testzip() is None
            archive.extractall(registered)
        validated = subprocess.run([sys.executable, str(registered / "run.py"), "--repo", str(repository), "--validate-only"], cwd=output, text=True, capture_output=True)
        assert validated.returncode == 0, validated.stderr
        assert json.loads(validated.stdout)["experiment_id"] == "fair-beam-relay-css-v2"
        report["checks"].append("original registered study ZIP validates its exact input hashes without launching the campaign")
        page.locator("#result-paper").select_option("yao-2312-10950-v2")
        page.locator("#result-experiment").select_option("yao-vanilla")

        page.screenshot(path=str(output / "desktop-results.png"), full_page=False)
        page.locator('[data-nav="builder"]').click()
        page.locator("#build-preset").select_option(vanilla["decoder_id"])
        imported = json.loads(page.locator("#spec-output").inner_text())
        assert imported["decoder"]["policy"]["damping"] == 0
        assert imported["decoder"]["policy"]["hard_decision"] == "strict_pauli"
        assert imported["decoder"]["policy"]["zero_syndrome_shortcut"] is False
        report["checks"].append("frozen undamped BP4 v2 import preserves damping, hard decisions, and first-sweep stopping")
        page.locator("#reset-visual").click()
        page.locator("#build-shots").fill("4")
        page.locator("#build-iterations").fill("3")
        page.locator("#build-rates").fill("0.1")
        page.locator("#validate-experiment").click()
        assert page.locator("#download-package").is_enabled()
        with page.expect_download() as download_info:
            page.locator("#download-package").click()
        binary_zip = output / "binary.zip"
        download_info.value.save_as(binary_zip)
        run_package(binary_zip, "binary relocated")
        report["checks"].append("visual builder → browser ZIP → isolated binary run, plot, and overwrite refusal")
        base_spec = json.loads(page.locator("#spec-output").inner_text())
        invalid = deepcopy(base_spec)
        invalid["problem"]["code"] = {"kind": "embedded_css", "hx": [[1, 1, 0]], "hz": [[1, 0, 0]]}
        page.locator(".custom-config summary").click()
        page.locator("#custom-json").fill(json.dumps(invalid))
        page.locator("#apply-custom-json").click()
        assert "commute" in page.locator("#custom-json-feedback").inner_text()
        assert page.locator("#download-package").is_disabled()
        custom = deepcopy(base_spec)
        custom["id"] = "custom-bp4"
        custom["problem"] = {"kind": "pauli_code_capacity", "code": {"kind": "embedded_css", "hx": [[1, 1, 0]], "hz": [[0, 0, 1]], "lx": [[1, 0, 0]], "lz": [[1, 1, 0]]}}
        custom["decoder"]["family"] = "bp4"
        custom["decoder"]["numerical_profile"] = "quaternary-bp4-f64-v2"
        page.locator("#custom-json").fill(json.dumps(custom))
        page.locator("#apply-custom-json").click()
        assert page.locator("#download-package").is_enabled()
        with page.expect_download() as download_info:
            page.locator("#download-package").click()
        custom_zip = output / "custom-bp4.zip"
        download_info.value.save_as(custom_zip)
        run_package(custom_zip, "custom bp4")
        report["checks"].append("custom matrix validation rejects noncommutation and exports a real BP4 experiment")
        page.locator('[data-nav="circuits"]').click()
        page.locator("#circuit-select").select_option("relay-surface-d3")
        page.locator("#use-circuit").click()
        page.wait_for_function("document.querySelector('#spec-output').textContent.includes('circuit:relay-surface-d3')")
        page.locator("#build-shots").fill("4")
        page.locator("#build-iterations").fill("3")
        page.locator("#validate-experiment").click()
        with page.expect_download() as download_info:
            page.locator("#download-package").click()
        source_zip = output / "source-circuit.zip"
        download_info.value.save_as(source_zip)
        with zipfile.ZipFile(source_zip) as archive:
            assert "inputs/LICENSE.txt" in archive.namelist()
        run_package(source_zip, "registered source stim")
        report["checks"].append("pinned source circuit selector exports original license and provenance, then runs four observable-evaluated shots")
        page.locator('[data-nav="circuits"]').click()
        stim_file = output / "custom.stim"
        stim_file.write_text("R 0\nX_ERROR(0.1) 0\nM 0\nDETECTOR rec[-1]\nOBSERVABLE_INCLUDE(0) rec[-1]\n")
        page.locator("#circuit-file").set_input_files(stim_file)
        page.locator("#build-shots").fill("4")
        page.locator("#build-iterations").fill("3")
        page.locator("#validate-experiment").click()
        assert page.locator("#download-package").is_enabled()
        circuit_spec = json.loads(page.locator("#spec-output").inner_text())
        assert circuit_spec["decoder"]["family"] == "circuit_dem_bp"
        with page.expect_download() as download_info:
            page.locator("#download-package").click()
        circuit_zip = output / "circuit.zip"
        download_info.value.save_as(circuit_zip)
        run_package(circuit_zip, "stim sinter")
        report["checks"].append("custom .stim → supported adapter package → genuine seeded Stim and Sinter observable evaluation")
        circuit_spec["decoder"]["policy"] = {}
        if page.locator(".custom-config").get_attribute("open") is None:
            page.locator(".custom-config summary").click()
        page.locator("#custom-json").fill(json.dumps(circuit_spec))
        page.locator("#apply-custom-json").click()
        assert any(word in page.locator("#custom-json-feedback").inner_text().lower() for word in ("unsupported", "unknown or missing fields"))
        assert page.locator("#download-package").is_disabled()
        report["checks"].append("unsupported circuit policies are rejected without substitution")
        page.locator('[data-nav="results"]').click()
        assert page.locator("#selection-details a").count() > 0
        assert not page.locator("#selection-details a[href='null']").count()
        for anchor in page.locator("#selection-details a").all():
            assert "/web/research/data/" not in anchor.get_attribute("href")
        report["checks"].append("repository assets resolve at correct routes; missing/local-only assets never become speculative links")
        page.locator("#result-paper").select_option("pfister-presentation-excerpt")
        page.locator("#result-experiment").select_option("catalog-pfister-presentation-full-v2-curves")
        page.locator("#result-code").select_option("b1")
        arm = next(s for s in catalog["result_series"] if s["dataset_id"] == "pfister-presentation-full-v2-curves" and s["code_id"] == "b1" and s["source_decoder_id"] == "bp4_tuned_sp_v2")
        page.locator("#result-decoder").select_option(arm["decoder_id"])
        page.locator("#result-plot .plot-point").first.focus()
        page.keyboard.press("Enter")
        assert "estimate" in page.locator("#plot-caption").inner_text()
        with page.expect_download() as download_info:
            page.locator("#download-configuration-receipt").click()
        receipt_path = output / "effective-decoder-receipt.json"
        download_info.value.save_as(receipt_path)
        effective = json.loads(receipt_path.read_text())["configuration"]["effective_configuration"]
        assert effective["message_resolution"] == "float64" and effective["v2c_damping"] == .1
        report["checks"].append("plot geometry follows selected data, keyboard points expose values, and effective receipt preserves runner overrides")
        local = next(s for s in catalog["result_series"] if s["dataset_id"] == "pfister-presentation-full-v2-curves" and s["code_id"] == "double-gross" and s["source_decoder_id"] == "bp4_tuned_sp_v2")
        page.locator("#result-code").select_option("double-gross")
        page.locator("#result-decoder").select_option(local["decoder_id"])
        assert page.locator('#result-plot [aria-label*="p=0.06;"]').evaluate("node => node.tagName") == "circle"
        page.locator("#result-experiment").select_option("catalog-pfister-presentation-source-curves")
        page.locator("#result-code").select_option("double-gross")
        source = next(s for s in catalog["result_series"] if s["dataset_id"] == "pfister-presentation-source-curves" and s["code_id"] == "double-gross" and s["source_decoder_id"] == "bp4_tuned_sp")
        page.locator("#result-decoder").select_option(source["decoder_id"])
        assert page.locator('#result-plot [aria-label*="p=0.06;"]').evaluate("node => node.tagName") == "path"
        report["checks"].append("A source upper bound uses a triangle; the independently measured local point remains a rate and uses a circle.")
        page.keyboard.press("Tab")
        assert page.evaluate("document.activeElement !== document.body")
        page.set_viewport_size({"width": 390, "height": 844})
        for section in ["papers", "results", "builder", "decoders", "codes", "circuits"]:
            page.locator(f'[data-nav="{section}"]').click()
            if section == "decoders": page.locator("#library-decoder").select_option(vanilla["decoder_id"])
            if section == "codes": page.locator("#library-code").select_option("b1")
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"), section
            page.screenshot(path=str(output / f"mobile-{section}.png"), full_page=False)
        report["checks"].append("desktop/mobile layouts stay inside viewport and keyboard focus is visible")
        browser.close()
    assert not report["errors"], report["errors"]
    (output / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--url", default="http://127.0.0.1:8765/web/research/")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.repo.resolve(), args.url, args.output.resolve()), indent=2))
