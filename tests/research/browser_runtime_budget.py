"""Future control/cap evidence labels, exports, singleton filtering and builder."""
import argparse
from copy import deepcopy
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[2]


def fixture():
    c = json.loads((REPO / 'web/research/catalog.json').read_text())
    c['result_series'] = [r for r in c['result_series'] if r['code_id'] != 'toric9']
    template = next(r for r in c['result_series'] if len(r['points']) >= 2)
    dataset = deepcopy(next(d for d in c['datasets'] if d['dataset_id'] == template['dataset_id']))
    dataset.update(dataset_id='runtime-browser-fixture', label='Synthetic runtime-control evidence', points=[])
    c['datasets'].append(dataset)
    for family in ('binary_css', 'bp4'):
        for schedule in ('constant', '1-2**(-iteration)'):
            name = family+('-constant' if schedule == 'constant' else '-paper')
            config = {'family': family, 'check_rule': 'min_sum', 'message_resolution': 'float64',
                      'v2c_damping': .5, 'max_iterations': 324, 'alpha_schedule': schedule,
                      'alpha': .75 if schedule == 'constant' else .9, 'beta': .25,
                      'noise_model': 'x_only' if family == 'binary_css' else 'depolarizing',
                      'execution_backend': 'roffe-joint-controls-loop-v1'}
            c['decoders'].append({'decoder_id': name, 'label': name, 'configuration': {'effective_configuration': config}})
            points = deepcopy(template['points'][:2])
            for point, rate in zip(points, (.04, .05), strict=True):
                point.update(x=rate if family == 'binary_css' else 1.5*rate, y=.1, n=100, failures=10, ci_low=.05, ci_high=.2,
                             mean_iterations=50, iteration_unit='BP sweeps', mean_directed_edge_updates=32400)
                point['metadata'] = {'cohort_kind': 'browser_fixture', 'seed': 1, 'source_evidence_path': name+str(rate),
                                     'runtime_ratio_to_bp_osd0': .97 if schedule == 'constant' else 1.03}
            c['result_series'].append({**deepcopy(template), 'series_id': name, 'dataset_id': 'runtime-browser-fixture',
                                       'code_id': 'toric9', 'decoder_id': name, 'source_decoder_id': name,
                                       'channel_kind': config['noise_model'], 'points': points})
    return c


def verify(url, output):
    output.mkdir(parents=True, exist_ok=False); checks, errors = [], []
    catalog = fixture()
    with sync_playwright() as p:
        browser = p.chromium.launch(); page = browser.new_page(accept_downloads=True, viewport={'width': 1550, 'height': 1100})
        page.on('pageerror', lambda e: errors.append(str(e)))
        app = (REPO / 'web/research/app.js').read_text().replace('\nload();', '\nwindow.testRefreshCatalog=c=>{S.catalog=c;fillSavedChoices();renderCards();availability();};\nload();')
        page.route('**/app.js', lambda route: route.fulfill(body=app, content_type='text/javascript'))
        page.route('**/catalog.json', lambda route: route.fulfill(body=json.dumps(catalog), content_type='application/json'))
        page.goto(url+'#results'); page.wait_for_function("document.querySelector('#catalog-status').textContent.includes('measured')")
        card = page.locator('[data-plot]').first
        card.locator('[data-select=input]').select_option('toric9'); card.locator('[data-select=decoder]').select_option('')
        assert card.locator('.curve-list input').count() == 4 and card.locator('tbody tr').count() == 8
        text = card.locator('.curve-list').inner_text()
        assert all(s in text for s in ('α = 0.75', 'αₜ = 0.9 × (1 − 2⁻ᵗ)', 'β = 0.25', 'd = 0.5', 'T = 324', 'X-only', 'depolarizing'))
        checks.append('Both families display exact constant/ramped scaling, damping, offset, cap and distinct channels')
        assert 'Time / BP+OSD-0' in card.locator('thead').inner_text()
        assert '0.97×' in card.locator('tbody').inner_text() and '1.03×' in card.locator('tbody').inner_text()
        with page.expect_download() as download:
            card.get_by_role('button', name='Export visible table').click()
        path = output / 'runtime-table.csv'; download.value.save_as(path)
        assert 'Time / BP+OSD-0' in path.read_text() and '1.03×' in path.read_text()
        page.screenshot(path=str(output / 'runtime-table.png'))
        checks.append('Results table and CSV expose the measured time/reference ratio and tolerance')
        with page.expect_download() as download:
            card.get_by_role('button', name='Download run settings').click()
        path = output / 'settings.json'; download.value.save_as(path); settings = json.loads(path.read_text())
        encoded = json.dumps(settings)
        assert '0.75' in encoded and '0.9' in encoded and '0.25' in encoded and 'execution_backend' in encoded
        checks.append('Run settings preserve numerical controls and compiled execution identity')
        page.locator('[data-nav=builder]').click(); page.locator('#build-code').select_option('toric9')
        page.locator('#build-preset').select_option('binary_css-paper'); page.locator('#validate-spec').click()
        assert page.locator('#download-package').is_disabled()
        assert 'study-specific execution path' in page.locator('#builder-feedback').inner_text()
        checks.append('Builder cannot replace the tuned scheduled decoder with a plain decoder')
        hidden = deepcopy(catalog)
        for series in hidden['result_series']:
            if series['dataset_id'] == 'runtime-browser-fixture': series['points'] = series['points'][:1]
        page.evaluate('c=>testRefreshCatalog(c)', hidden)
        assert not page.locator('#build-code option[value=toric9]').count()
        assert not page.locator('#build-preset option[value="binary_css-paper"]').count()
        assert page.locator('#build-code').input_value() != 'toric9'
        checks.append('Singleton filtering hides ineligible tuned curves and clears stale input/preset selections')
        page.screenshot(path=str(output / 'runtime-controls.png')); browser.close()
    assert not errors, errors
    result = {'checks': checks, 'errors': errors, 'simulations': 0}
    (output / 'verification.json').write_text(json.dumps(result, indent=2)+'\n'); print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--url', required=True); parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(); verify(args.url, args.output)
