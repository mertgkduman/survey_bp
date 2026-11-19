"""Verify policy controls and exported specifications against the Python contract."""

import argparse
import json
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

from bp_registry.research.contracts import validate_experiment


ROOT = Path(__file__).resolve().parents[2]


def verify(url):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(url + "#builder")
        expect(page.locator("#catalog-status")).to_contain_text("measured")
        spec_preview = page.locator("#spec-preview")

        def validate():
            page.locator("#validate-spec").click()
            expect(page.locator("#builder-feedback")).to_contain_text("Configuration checked")
            return validate_experiment(json.loads(spec_preview.text_content()), repository=ROOT)

        def reset():
            page.locator("#reset-spec").evaluate("button => button.click()")

        expect(page.locator("#build-shortcut, #build-version")).to_have_count(0)
        expect(page.locator("#matrix-note")).to_contain_text("90 × 180")
        page.locator("#build-code").select_option("toric9")
        expect(page.locator("#builder-code-sources a").first).to_have_attribute("href", "https://arxiv.org/abs/2005.07016v2")
        expect(page.locator("#matrix-note")).to_contain_text("162")
        page.locator("#numerical-controls > summary").click()
        expect(page.locator("#build-alpha")).to_be_hidden()
        page.locator("#build-rule").select_option("min_sum")
        expect(page.locator("#build-alpha")).to_be_visible()
        assert validate()["decoder"]["policy"]["zero_syndrome_shortcut"] is True

        reset()
        page.locator("#build-variant").select_option("guided_decimation")
        expect(page.locator("#build-variant option:checked")).to_have_text("On")
        assert validate()["decoder"]["shared_policy"]["controller"] == "guided_decimation"
        page.locator("#build-family").select_option("bp4")
        assert validate()["decoder"]["variant"] == "qbpgd"
        reset()
        page.locator("#build-family").select_option("bp4")
        page.locator("#build-controller-mbp4").select_option("on")
        page.locator("#build-mbp4-schedule").select_option("qbp_variable_serial")
        assert validate()["decoder"]["mbp4"]["schedule"] == "qbp_variable_serial"

        reset()
        page.locator("#build-family").select_option("bp4")
        page.locator("#build-schedule").select_option("variable_node_serial")
        assert validate()["decoder"]["implementation"] == "qbp_variable_serial"

        reset()
        page.locator("#build-memory-affine_prior").select_option("on")
        page.locator("#build-memory-posterior_momentum").select_option("on")
        expect(page.locator("#policy-order")).to_contain_text(
            "Uniform posterior memory → Sum-product check update → Posterior momentum → V2C damping"
        )
        bindings = validate()["decoder"]["shared_policy"]["memory"]["bindings"]
        assert [binding["kind"] for binding in bindings] == ["affine_prior", "posterior_momentum", "v2c_damping"]
        page.locator("#kernel-guide summary").click()
        expect(page.locator("#kernel-guide")).to_contain_text("Posterior momentum")
        expect(page.locator("#kernel-guide")).to_contain_text("zero syndrome")
        expect(page.locator("#kernel-guide .policy-literature")).to_have_count(0)

        reset()
        page.locator("#build-controller-mbbp").select_option("on")
        page.locator("#build-controller-options").fill(json.dumps({
            "bases": [{"member_id": "original", "local_ordinal": 0,
                       "partition_identity": "original", "permutation_identity": "identity",
                       "redundant_transforms": []}],
            "max_iterations": 10,
        }))
        assert validate()["decoder"]["shared_policy"]["controller"] == "mbbp"

        reset()
        page.locator("#build-regime").select_option("circuit")
        page.locator("#build-circuit").select_option("priortilt-bb144-memory-z")
        expect(page.locator("#circuit-feedback")).to_have_text("Stim circuit loaded.")
        assert validate()["decoder"]["shared_policy"]["controller"] == "single"
        page.locator("#build-variant").select_option("guided_decimation")
        assert validate()["decoder"]["shared_policy"]["controller"] == "guided_decimation"

        reset()
        prior = next(option for option in page.locator("#build-preset option").all()
                     if "PriorTilt" in option.text_content())
        page.locator("#build-preset").select_option(prior.get_attribute("value"))
        expect(page.locator("#circuit-feedback")).to_have_text("Stim circuit loaded.")
        assert validate()["decoder"]["implementation"] == "prior_tilt"

        page.locator("[data-nav=policies]").click()
        expect(page.locator("#policy-glossary .katex").first).to_be_visible()
        for name in ("prior_tilt", "relay_disordered_memory", "beam_search"):
            literature = page.locator(f"#policy-{name} .policy-literature")
            assert not literature.evaluate("details => details.open")
            literature.locator("summary").click()
            expect(literature.locator(".katex").first).to_be_visible()
            assert literature.locator("a").get_attribute("href").startswith("https://arxiv.org/")
        assert not errors, errors
        browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8765/web/research/")
    verify(parser.parse_args().url)
