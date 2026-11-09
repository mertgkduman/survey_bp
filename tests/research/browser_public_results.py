"""Display/catalog regression in Chromium; no decoding or new simulation evidence.

Synthetic overlays exercise only the display layer. Import integrity and ledger
validation are independently covered by test_import_evidence.py.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import csv
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]


def verify(output: Path, url: str):
    output.mkdir(parents=True, exist_ok=False)
    catalog = json.loads((ROOT / 'web/research/catalog.json').read_text())
    checks, errors = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(accept_downloads=True, viewport={'width': 1512, 'height': 1100})
        page = context.new_page()
        page.on('pageerror', lambda e: errors.append(str(e)))
        # Test-only access to refresh the catalog while controls have selections.
        # The served production file has no test API.
        app = (ROOT / 'web/research/app.js').read_text().replace('\nload();', '''
window.testRefreshCatalog=c=>{S.catalog=c;fillSavedChoices();renderCards();availability();};
window.testSelection=()=>({cards:S.cards.map(c=>({input:c.input,decoder:c.decoder,chosen:c.chosen?[...c.chosen]:null,hidden:[...c.hidden]})),spec:S.spec});
load();''')
        page.route('**/app.js', lambda route: route.fulfill(body=app, content_type='text/javascript'))
        page.goto(url + '#results')
        page.wait_for_function("document.querySelector('#catalog-status').textContent.startsWith('63 measured')")
        active = page.evaluate('''async()=>{const c=await(await fetch('catalog.json')).json();const v=ResearchCurves.active(c,DecoderDisplay.labels(c));return {...v,decoderIds:[...v.decoderIds]};}''')
        ids = {x['code_id'] for x in active['codes']}
        assert len(active['curves']) == 63 and sum(len(s['points']) for s in active['curves']) == 319
        assert ids == {'a5', 'b2', 'b1', 'c2', 'double-gross', 'bb72'}
        assert not active['circuits']
        card = page.locator('[data-plot]').first
        assert set(card.locator('[data-select=input] option').evaluate_all('xs=>xs.map(x=>x.value)')) == ids
        assert set(page.locator('#build-code option').evaluate_all('xs=>xs.map(x=>x.value)')) == ids | {'custom'}
        assert page.locator('#build-circuit option').evaluate_all('xs=>xs.map(x=>x.value)') == ['']
        saved = set(page.locator('#build-preset option').evaluate_all('xs=>xs.map(x=>x.value)'))
        assert saved - {'', '__baseline-binary', '__baseline-quaternary'} == set(active['decoderIds'])
        availability = page.locator('#availability').inner_text()
        for item in catalog['circuits'] + [next(c for c in catalog['codes'] if c['code_id'] == 'gb46')]:
            assert item['label'] not in availability
        checks.append('63 curves / 319 rows; all public input and saved-decoder lists use the active view; GB46 and all three singleton circuits absent')

        curves_by_input = {id: [s for s in active['curves'] if s['code_id'] == id] for id in ids}
        for id in sorted(ids):
            page.wait_for_timeout(1100)  # Allow Chromium's automatic-download window to expire.
            card.locator('[data-select=input]').select_option(id)
            card.locator('[data-select=decoder]').select_option('')
            expected = curves_by_input[id]
            assert card.locator('tbody tr').count() == sum(len(s['points']) for s in expected)
            assert card.locator('.curve-list input').count() == len(expected)
            card.locator('.curve-picker input').focus()
            assert card.locator('[role=option]').count() == len(expected)
            page.keyboard.press('Escape')
            with page.expect_download() as d:
                card.get_by_role('button', name='Download run settings').click()
            receipt_path = output / f'{id}-settings.json'
            d.value.save_as(receipt_path)
            receipt = json.loads(receipt_path.read_text())
            assert {s['curve_id'] for s in receipt['series']} == {s['curve_id'] for s in expected}
            assert all(s['evidence'] for s in receipt['series'])
            assert all(len({p['x'] for p in s['points']}) >= 2 for s in receipt['series'])
            with page.expect_download() as d:
                card.get_by_role('button', name='Export visible table').click()
            csv_path = output / f'{id}.csv'
            d.value.save_as(csv_path)
            with csv_path.open(newline='') as stream:
                assert len(list(csv.reader(stream))) - 1 == card.locator('tbody tr').count()
        checks.append('Every remaining code: picker, legend, plotted collection, table, settings receipt and CSV agree')
        page.locator('#add-plot').click()
        second = page.locator('[data-plot]').nth(1)
        second_input = second.locator('[data-select=input]').input_value()
        card.locator('[data-select=input]').select_option('a5')
        assert second.locator('[data-select=input]').input_value() == second_input
        page.screenshot(path=str(output / 'results.png'))

        # Leave both curve and saved-decoder selections active before removal.
        card.locator('.curve-picker input').focus()
        page.keyboard.press('ArrowDown')
        page.keyboard.press('Enter')
        card.locator('.curve-list input').first.uncheck()
        with_saved = deepcopy(catalog)
        request = json.loads((ROOT / 'research/examples/code-capacity.json').read_text())
        with_saved['decoders'].append({'decoder_id': 'test-saved-exact', 'configuration': {'experiment': request}})
        saved_series = deepcopy(next(s for s in catalog['result_series'] if s['code_id'] == 'bb72'))
        saved_series.update(series_id='test-saved-series', decoder_id='test-saved-exact')
        saved_series['points'] = [dict(saved_series['points'][0], x=x) for x in (.03, .04)]
        with_saved['result_series'].append(saved_series)
        page.evaluate('c=>testRefreshCatalog(c)', with_saved)
        page.locator('[data-nav=builder]').click()
        page.locator('#build-preset').select_option('test-saved-exact')
        assert page.locator('#build-code').is_disabled()

        # Empty active view with full retained entities still present.
        empty = deepcopy(catalog)
        empty['result_series'] = []
        page.evaluate('c=>testRefreshCatalog(c)', empty)
        assert page.locator('[data-plot] .empty').count() == 2
        assert page.locator('[data-select=input] option').count() == 0
        assert all(c['input'] == '' and c['decoder'] == '' and c['chosen'] is None and not c['hidden']
                   for c in page.evaluate('testSelection().cards'))
        assert page.locator('#build-code').input_value() == 'custom'
        assert page.locator('#build-matrix').input_value() == ''
        assert page.locator('#build-preset').input_value() == ''
        assert page.locator('#build-code').is_enabled()
        assert page.locator('#custom-spec').input_value() == ''
        assert page.locator('#build-circuit option').count() == 1
        assert page.locator('#build-preset option').count() == 3  # custom and two new-experiment baselines
        assert 'No inputs have multi-rate results' in page.locator('#availability').inner_text()
        page.locator('[data-nav=builder]').click()
        page.locator('#reset-spec').evaluate("n=>n.closest('details').open=true")
        page.locator('#reset-spec').click()
        assert page.locator('#build-code').input_value() == 'custom'
        matrices = {'hx': [[1, 1, 1, 1]], 'hz': [[1, 1, 1, 1]]}
        page.locator('#build-matrix').fill(json.dumps(matrices))
        page.locator('#validate-spec').click()
        assert page.locator('#download-json').is_enabled(), page.locator('#builder-feedback').inner_text()
        page.locator('#build-regime').select_option('circuit')
        page.locator('#build-circuit-base').fill('0.005')
        page.locator('#build-stim').fill('R 0\nX_ERROR(0.005) 0\nM 0\nDETECTOR rec[-1]\nOBSERVABLE_INCLUDE(0) rec[-1]\n')
        page.locator('#validate-spec').click()
        assert page.locator('#download-json').is_enabled(), page.locator('#builder-feedback').inner_text()
        checks.append('Empty active view clears plot/decoder/input state and stale matrices; reset, custom matrix and custom Stim still validate')

        # No A5/B2 defaults: controls and actual model select a displayed input.
        bb = deepcopy(catalog)
        bb['result_series'] = [s for s in catalog['result_series'] if s['code_id'] == 'bb72']
        page.evaluate('c=>testRefreshCatalog(c)', bb)
        assert all(c['input'] == 'bb72' for c in page.evaluate('testSelection().cards'))
        page.locator('#reset-spec').evaluate("n=>n.closest('details').open=true")
        page.locator('#reset-spec').click()
        assert page.locator('#build-code').input_value() == 'bb72'
        assert page.evaluate('testSelection().spec.problem.code.id') == 'bb72'
        checks.append('Missing default A5/B2 inputs fall back to a displayed input in both DOM and experiment/plot state')

        # Live import display refresh, using a test double for already-verified
        # imported evidence. First singleton stays hidden, then multi-rate shows.
        circuit = next(s for s in catalog['result_series'] if s['code_id'] == 'relay-surface-d3')
        def overlay(multi):
            s = deepcopy(circuit)
            s['series_id'] = 'test-import-multi' if multi else 'test-import-single'
            s['points'] = [dict(p, x=.01) for p in s['points']]
            if multi:
                s['points'] += [dict(p, x=.02) for p in s['points'][:1]]
            return {'result_series': [s]}
        def upload(entry, identifier):
            page.evaluate('v=>{ResearchImport.read=async()=>({entry:v.entry,summary:{experiment_id:v.id}});}', {'entry': entry, 'id': identifier})
            page.locator('[data-nav=getting-started]').click()
            page.locator('#upload-results').set_input_files({'name': identifier+'.json', 'mimeType': 'application/json', 'buffer': b'{}'})
            page.wait_for_function("document.querySelector('#upload-feedback').className==='success'")
        upload(overlay(False), 'display-single')
        assert page.locator('#build-circuit option').count() == 1
        upload(overlay(True), 'display-multi')
        assert page.locator('#build-circuit option[value=relay-surface-d3]').count() == 1
        assert 'Rotated' in page.locator('#availability').inner_text() or 'surface' in page.locator('#availability').inner_text().lower()
        page.locator('[data-nav=builder]').click()
        page.locator('#build-regime').select_option('circuit')
        page.locator('#build-circuit').select_option('relay-surface-d3')
        page.wait_for_function("document.querySelector('#build-stim').value.includes('QUBIT_COORDS')")
        page.evaluate('c=>testRefreshCatalog(c)', empty)
        assert page.locator('#build-circuit').input_value() == ''
        assert page.locator('#build-stim').input_value() == ''
        assert page.locator('#download-json').is_disabled()
        checks.append('Import refresh hides singleton, admits multi-rate circuit and updates availability; hiding the selected circuit clears its Stim bytes and download validation')

        # Saved overlays are re-evaluated on page reload, and custom input lists
        # do not expose the internal fixture through a normalized import.
        page.reload()
        page.wait_for_function("document.querySelector('#catalog-status').textContent.includes('measured')")
        assert page.locator('#build-circuit option[value=relay-surface-d3]').count() == 1
        page.locator('[data-nav=results]').click()
        card = page.locator('[data-plot]').first
        card.locator('[data-select=input]').select_option('relay-surface-d3')
        assert card.locator('tbody tr').count() == 3
        fixture = deepcopy(catalog)
        fixture['codes'].append({'code_id': 'three-qubit', 'label': 'internal fixture'})
        hidden = deepcopy(circuit)
        hidden.update(series_id='test-internal-fixture', code_id='three-qubit')
        hidden['points'] = [dict(hidden['points'][0], x=x) for x in (.01, .02)]
        fixture['result_series'] = [hidden]
        page.evaluate('c=>testRefreshCatalog(c)', fixture)
        assert page.locator('[data-select=input] option').count() == 0
        assert page.locator('#build-code option').count() == 1
        checks.append('Saved imports reapply eligibility after reload; internal three-qubit fixture remains hidden even with two rates')
        page.set_viewport_size({'width': 390, 'height': 844})
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        page.screenshot(path=str(output / 'empty-mobile.png'))
        page.unroute('**/app.js')
        page.goto(url + 'v1/')
        page.wait_for_function("document.querySelector('#catalog-status').textContent.includes('retained')")
        assert page.locator('.paper-card').count() > 0
        checks.append('Empty mobile layout fits; archived v1 still loads its retained catalog')
        assert not errors, errors
        browser.close()
    report = {'checks': checks, 'errors': errors, 'simulations': 0}
    (output / 'verification.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--url', default='http://127.0.0.1:8876/web/research/')
    args = parser.parse_args()
    print(json.dumps(verify(args.output.resolve(), args.url), indent=2))
