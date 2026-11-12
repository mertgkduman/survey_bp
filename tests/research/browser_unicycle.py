"""Construction U browser workflows using explicitly synthetic display overlays.

No performance measurements are generated or written to the shared catalog.
Actual registered matrices, frozen policies and the production UI are used.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import csv
import json
from pathlib import Path
import sys

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
STUDY = ROOT / "data/reproductions/mackay-0304161-unicycle"
sys.path.insert(0, str(STUDY))
from publish import extension
from run import PLAN, jobs, load_plan, sha


def overlay(base):
    plan = load_plan()
    rows = []
    for job in jobs(plan):
        if job["matched_x_rate"] not in (.04, .05):
            continue
        rows.append({"id": job["id"], "code": job["code"], "arm": job["arm"],
                     "physical_p": job["physical_p"], "matched_x_rate": job["matched_x_rate"],
                     "shots": 200, "failures": 20, "rate": .1, "ci95_low": .06, "ci95_high": .15,
                     "counts": {"type_i": 12, "type_ii": 8, "exact_success": 170, "stabilizer_success": 10},
                     "iterations": 400, "directed_edge_updates": 800 * job["graph_edges"],
                     "decode_ns": 200000, "stop_reason": "target_block_failures",
                     "ledger_sha256": "a" * 64, "summary_sha256": "b" * 64})
    extra = extension(plan, {"schema": "mackay-unicycle-verification-v1", "plan_sha256": sha(PLAN), "points": rows})
    result = deepcopy(base)
    keys = {"papers": "paper_id", "datasets": "dataset_id", "experiments": "experiment_id",
            "decoders": "decoder_id", "result_series": "series_id"}
    for kind, field in keys.items():
        ids = {row[field] for row in extra[kind]}
        result[kind] = [row for row in result[kind] if row[field] not in ids
                        and not (kind == "result_series" and row["dataset_id"] == "mackay-unicycle-bp")] + extra[kind]
    return result


def verify(output: Path, url: str):
    output.mkdir(parents=True, exist_ok=False)
    catalog = overlay(json.loads((ROOT / "web/research/catalog.json").read_text()))
    checks, errors = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1512, "height": 1100}, accept_downloads=True)
        page.on("pageerror", lambda e: errors.append(str(e)))
        app = (ROOT / "web/research/app.js").read_text().replace("\nload();", """
window.testRefreshCatalog=c=>{S.catalog=c;fillSavedChoices();renderCards();availability();};
window.testSelection=()=>({cards:S.cards.map(c=>({input:c.input,decoder:c.decoder,hidden:[...c.hidden]})),spec:S.spec});
load();""")
        page.route("**/app.js", lambda route: route.fulfill(body=app, content_type="text/javascript"))
        page.goto(url + "#results")
        page.wait_for_function("document.querySelector('#catalog-status').textContent.includes('measured')")
        single = deepcopy(catalog)
        for series in single["result_series"]:
            if series["dataset_id"] == "mackay-unicycle-bp":
                series["points"] = series["points"][:1]
        page.evaluate("c=>testRefreshCatalog(c)", single)
        for name in ("unicycle74", "unicycle274"):
            assert page.locator(f'#build-code option[value="{name}"]').count() == 0
            assert page.locator(f'[data-select=input] option[value="{name}"]').count() == 0
        assert "MacKay unicycle" not in page.locator("#availability").inner_text()
        checks.append("One-rate Construction U results hide both registered inputs and all their saved decoders")

        page.evaluate("c=>testRefreshCatalog(c)", catalog)
        card = page.locator("[data-plot]").first
        for name in ("unicycle74", "unicycle274"):
            page.wait_for_timeout(1100)
            card.locator("[data-select=input]").select_option(name)
            card.locator("[data-select=decoder]").select_option("")
            assert card.locator("tbody tr").count() == 6
            labels = card.locator(".curve-list").inner_text()
            for label in ("Unicycle BP, SP", "Binary BP, SP", "Q-BP, SP"):
                assert label in labels
            assert "Tₕ = 44100" in labels and "H = 2" in labels
            assert card.locator(".curve-list input").count() == 3
            table = card.locator("table").inner_text()
            assert "Mean iterations / shot" in table and "Mean directed edge updates / shot" in table
            with page.expect_download() as download:
                card.get_by_role("button", name="Export visible table").click()
            target = output / f"{name}.csv"
            download.value.save_as(target)
            with target.open(newline="") as stream:
                assert len(list(csv.DictReader(stream))) == 6
            with page.expect_download() as download:
                card.get_by_role("button", name="Download run settings").click()
            target = output / f"{name}-settings.json"
            download.value.save_as(target)
            settings = json.loads(target.read_text())
            assert len(settings["series"]) == 3
            assert any(d["configuration"]["effective_configuration"].get("controller", {}).get("kind")
                       == "unicycle_extra_bit_hypotheses" for d in settings["decoders"])
        checks.append("Both registered codes show three distinct curves, full branch settings, both work averages and matching exports")

        page.locator('[data-nav="builder"]').click()
        page.locator("#build-code").select_option("unicycle274")
        page.wait_for_function("document.querySelector('#build-matrix').value.includes('110') || JSON.parse(document.querySelector('#build-matrix').value||'{}').lx?.length===110")
        matrix = json.loads(page.locator("#build-matrix").input_value())
        assert len(matrix["hx"]) == 273 and len(matrix["hx"][0]) == 274 and len(matrix["lx"]) == 110
        page.locator("#validate-spec").click()
        assert page.locator("#request-results").is_enabled()
        assert page.locator("#download-package").is_enabled()
        page.evaluate("c=>testRefreshCatalog(c)", single)
        replacement = page.locator("#build-code").input_value()
        assert replacement not in ("unicycle74", "unicycle274")
        assert page.evaluate("testSelection().spec.problem.code.id") == replacement
        current_matrix = page.locator("#build-matrix").input_value()
        assert not current_matrix or len(json.loads(current_matrix)["hx"][0]) != 274
        assert page.locator("#request-results").is_disabled()
        assert not any(c["input"].startswith("unicycle") for c in page.evaluate("testSelection().cards"))
        checks.append("The 110-logical registered matrix validates; removing displayed results clears stale plot/builder inputs and disables requests")

        page.evaluate("c=>testRefreshCatalog(c)", catalog)
        page.locator("#build-preset").select_option("mackay-unicycle-bp:unicycle74:unicycle_sp")
        assert "study-specific execution path" in page.locator("#builder-feedback").inner_text()
        page.locator("#validate-spec").click()
        assert page.locator("#download-package").is_disabled()
        assert page.locator("#request-results").is_disabled()
        page.evaluate("c=>testRefreshCatalog(c)", single)
        assert page.locator("#build-preset").input_value() == ""
        checks.append("Saved unicycle settings preserve their source-command execution path and cannot silently become plain BP")
        page.screenshot(path=str(output / "unicycle.png"))
        browser.close()
    assert not errors, errors
    (output / "verification.json").write_text(json.dumps({"status": "passed", "checks": checks, "page_errors": errors}, indent=2) + "\n")
    print(json.dumps({"status": "passed", "checks": len(checks), "output": str(output)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    verify(args.output, args.url)
