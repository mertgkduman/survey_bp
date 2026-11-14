"""Display-only overlays verify future confirmed Roffe damping workflows."""
import argparse
from copy import deepcopy
import csv
import importlib.util
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('_browser_roffe_damping_base', Path(__file__).with_name('browser_roffe.py'))
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def overlay(catalog):
    original = deepcopy(catalog)
    original['result_series'] = [s for s in original['result_series'] if s['dataset_id'] not in
                                 {'roffe-2020-figure3-canonical-bp', 'roffe-damping-confirmation'}]
    future = base.overlay(original)
    for series in list(future['result_series']):
        if series['dataset_id'] != 'browser-roffe-only':
            continue
        identifier = series['series_id'].replace('test-roffe:', 'test-roffe-damped:')
        decoder = deepcopy(next(d for d in future['decoders'] if d['decoder_id'] == series['decoder_id']))
        decoder['decoder_id'] = identifier
        decoder['configuration']['effective_configuration']['v2c_damping'] = .5
        future['decoders'].append(decoder)
        damped = deepcopy(series)
        damped.update(series_id=identifier, decoder_id=identifier)
        for point in damped['points']:
            point['metadata'].update(cohort_kind='heldout_damping_validation', seed=2026111413,
                                     source_evidence_path='damped-' + point['metadata']['source_evidence_path'])
        future['result_series'].append(damped)
    return future


def verify(url, output):
    output.mkdir(parents=True, exist_ok=False)
    catalog = json.loads((ROOT / 'web/research/catalog.json').read_text())
    future = overlay(catalog)
    checks, errors = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(accept_downloads=True, viewport={'width': 1512, 'height': 1100})
        page.on('pageerror', lambda error: errors.append(str(error)))
        app = (ROOT / 'web/research/app.js').read_text().replace('\nload();', '''
window.testRefreshCatalog=c=>{S.catalog=c;fillSavedChoices();renderCards();availability();};
load();''')
        page.route('**/app.js', lambda route: route.fulfill(body=app, content_type='text/javascript'))
        page.route('**/catalog.json', lambda route: route.fulfill(body=json.dumps(future), content_type='application/json'))
        page.goto(url + '#results')
        page.wait_for_function("document.querySelector('#catalog-status').textContent.includes('measured')")
        card = page.locator('[data-plot]').first
        for code in ('toric9', 'toric11', 'toric13', 'toric15'):
            card.locator('[data-select=input]').select_option(code)
            card.locator('[data-select=decoder]').select_option('')
            assert card.locator('.curve-list input').count() == 4
            assert card.locator('tbody tr').count() == 8
            labels = card.locator('.curve-list').inner_text()
            assert 'd = 0.5' in labels and 'αₜ = 1 − 2⁻ᵗ' in labels
            assert 'depolarizing' in labels and 'X-only' in labels
        checks.append('All four codes keep binary/Q-BP and zero/selected damping distinct, with source scale schedule')
        with page.expect_download() as download:
            card.get_by_role('button', name='Export visible table').click()
        table = output / 'toric-damping.csv'
        download.value.save_as(table)
        with table.open(newline='') as stream:
            rows = list(csv.reader(stream))
        assert len(rows) == 9
        assert 'iterations' in ','.join(rows[0]).lower() and 'edge' in ','.join(rows[0]).lower()
        with page.expect_download() as download:
            card.get_by_role('button', name='Download run settings').click()
        settings = output / 'settings.json'
        download.value.save_as(settings)
        exported = json.loads(settings.read_text())
        assert len(exported['series']) == 4
        assert all('alpha_schedule' in json.dumps(s) for s in exported['series'])
        checks.append('CSV and settings export every visible curve and preserve both work metrics and min-sum schedule')
        page.locator('[data-nav=builder]').click()
        page.locator('#builder-form').wait_for(state='visible')
        page.locator('#build-code').select_option('toric15')
        page.wait_for_function("document.querySelector('#build-matrix').value.includes('450') || document.querySelector('#build-matrix').value.includes('hx')")
        page.locator('#build-preset').select_option('test-roffe-damped:toric15:binary_ms')
        assert 'study-specific execution path' in page.locator('#builder-feedback').inner_text()
        page.locator('#validate-spec').click()
        assert page.locator('#download-package').is_disabled()
        checks.append('Selected damping saved choice cannot replace the source changing-scale execution with a builder default')
        hidden = deepcopy(future)
        for series in hidden['result_series']:
            if series['dataset_id'] == 'browser-roffe-only':
                series['points'] = series['points'][:1]
        page.evaluate('c=>testRefreshCatalog(c)', hidden)
        assert not page.locator('[data-select=input] option[value=toric15]').count()
        assert not page.locator('#build-code option[value=toric15]').count()
        assert not page.locator('#build-preset option[value="test-roffe-damped:toric15:binary_ms"]').count()
        assert page.locator('#build-code').input_value() != 'toric15'
        assert page.locator('#build-preset').input_value() != 'test-roffe-damped:toric15:binary_ms'
        page.screenshot(path=str(output / 'after-hiding.png'))
        checks.append('Loss of multi-rate confirmation hides empty inputs and clears stale selected damping choices')
        browser.close()
    assert not errors, errors
    result = {'checks': checks, 'errors': errors, 'simulations': 0}
    (output / 'verification.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    verify(args.url, args.output)
