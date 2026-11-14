"""Synthetic future OSD curves: distinct methods, separate work and stale state."""
import argparse
from copy import deepcopy
import csv
import importlib.util
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('_browser_roffe_osd_campaign', ROOT / 'data/reproductions/roffe-2005-07016-osd-fast/run.py')
campaign = importlib.util.module_from_spec(spec); spec.loader.exec_module(campaign)


def overlay(catalog):
    result = deepcopy(catalog); plan = campaign.design()
    result['result_series'] = [s for s in result['result_series'] if s['dataset_id'] not in
                               {'roffe-2020-figure3-canonical-bp', 'roffe-damping-confirmation', 'roffe-canonical-bp-osd', 'roffe-canonical-bp-osd-fast'}]
    template = next(s for s in result['result_series'] if len(s['points']) >= 2)
    dataset = deepcopy(next(d for d in result['datasets'] if d['dataset_id'] == template['dataset_id']))
    dataset.update(dataset_id='osd-browser-fixture', label='Synthetic OSD workflow fixture', points=[])
    result['datasets'].append(dataset)
    for code in plan['codes']:
        for arm in ('bp_osd0', 'bp_osd_cs10'):
            jobs = [j for j in plan['jobs'] if j['code'] == code and j['arm'] == arm][:2]
            identifier = f'test-osd:{code}:{arm}'
            result['decoders'].append({'decoder_id': identifier, 'label': 'Synthetic OSD',
                                      'configuration': {'effective_configuration': jobs[0]['decoder']}})
            points = deepcopy(template['points'][:2])
            for point, job in zip(points, jobs, strict=True):
                point.update(x=job['physical_p'], y=.1, n=100, failures=10, ci_low=.05, ci_high=.2,
                             mean_iterations=4, mean_directed_edge_updates=8*job['graph_edges'],
                             iteration_unit='BP sweeps', osd_invocation_fraction=.4,
                             mean_osd_candidate_evaluations=.4 if arm == 'bp_osd0' else 50., mean_osd_seconds=.00002)
                point['metadata'] = {'cohort_kind': 'test_fixture', 'seed': 1,
                                     'source_evidence_path': identifier+'-'+str(job['physical_p'])}
            result['result_series'].append({**deepcopy(template), 'series_id': identifier,
                                            'dataset_id': 'osd-browser-fixture', 'code_id': code,
                                            'decoder_id': identifier, 'source_decoder_id': arm,
                                            'channel_kind': 'x_only', 'points': points})
    return result


def verify(url, output):
    output.mkdir(parents=True, exist_ok=False)
    future = overlay(json.loads((ROOT / 'web/research/catalog.json').read_text()))
    checks, errors = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch(); page = browser.new_page(accept_downloads=True, viewport={'width': 1550, 'height': 1100})
        page.on('pageerror', lambda error: errors.append(str(error)))
        app = (ROOT / 'web/research/app.js').read_text().replace('\nload();', '''
window.testRefreshCatalog=c=>{S.catalog=c;fillSavedChoices();renderCards();availability();};
load();''')
        page.route('**/app.js', lambda route: route.fulfill(body=app, content_type='text/javascript'))
        page.route('**/catalog.json', lambda route: route.fulfill(body=json.dumps(future), content_type='application/json'))
        page.goto(url+'#results'); page.wait_for_function("document.querySelector('#catalog-status').textContent.includes('measured')")
        card = page.locator('[data-plot]').first
        for code in ('toric9', 'toric11', 'toric13', 'toric15'):
            card.locator('[data-select=input]').select_option(code)
            card.locator('[data-select=decoder]').select_option('')
            assert card.locator('.curve-list input').count() == 2 and card.locator('tbody tr').count() == 4
            text = card.locator('.curve-list').inner_text()
            assert 'BP+OSD-0' in text and 'BP+OSD-CS' in text and 'λ = 10' in text
            assert 'αₜ = 1 − 2⁻ᵗ' in text
        checks.append('OSD0 and CS10 stay distinct for all four codes with exact BP budget and scale schedule')
        headers = card.locator('thead').inner_text()
        assert all(s in headers for s in ('OSD calls / shot', 'Mean OSD candidates / shot', 'Mean OSD time / shot'))
        assert 'cover the BP stage' in card.inner_text() and 'BP sweeps' in card.locator('tbody').inner_text()
        with page.expect_download() as download:
            card.get_by_role('button', name='Export visible table').click()
        path = output / 'osd-table.csv'; download.value.save_as(path)
        with path.open(newline='') as stream:
            rows = list(csv.reader(stream))
        assert len(rows) == 5
        column = rows[0].index('Mean OSD candidates / shot')
        assert len({r[column] for r in rows[1:]}) == 2
        checks.append('Table and CSV preserve BP work separately from OSD invocation, candidate and time costs')
        with page.expect_download() as download:
            card.get_by_role('button', name='Download run settings').click()
        path = output / 'settings.json'; download.value.save_as(path)
        data = json.loads(path.read_text()); assert len(data['series']) == 2
        assert 'OSD_CS' in json.dumps(data) and 'OSD_0' in json.dumps(data)
        checks.append('Saved settings preserve processor method/depth and original canonical BP configuration')
        page.locator('[data-nav=builder]').click(); page.locator('#builder-form').wait_for(state='visible')
        page.locator('#build-code').select_option('toric15')
        page.wait_for_function("document.querySelector('#build-matrix').value.includes('450') || document.querySelector('#build-matrix').value.includes('hx')")
        page.locator('#build-preset').select_option('test-osd:toric15:bp_osd_cs10')
        assert 'study-specific execution path' in page.locator('#builder-feedback').inner_text()
        page.locator('#validate-spec').click(); assert page.locator('#download-package').is_disabled()
        checks.append('Builder cannot silently turn a saved compound BP/OSD curve into ordinary BP')
        hidden = deepcopy(future)
        for series in hidden['result_series']:
            if series['dataset_id'] == 'osd-browser-fixture':
                series['points'] = series['points'][:1]
        page.evaluate('c=>testRefreshCatalog(c)', hidden)
        assert not page.locator('#build-code option[value=toric15]').count()
        assert not page.locator('#build-preset option[value="test-osd:toric15:bp_osd_cs10"]').count()
        assert page.locator('#build-code').input_value() != 'toric15'
        page.screenshot(path=str(output / 'after-hiding.png'))
        checks.append('Single-rate filtering hides empty inputs/processor choices and clears stale builder state')
        browser.close()
    assert not errors, errors
    result = {'checks': checks, 'errors': errors, 'simulations': 0}
    (output / 'verification.json').write_text(json.dumps(result, indent=2)+'\n'); print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--url', required=True); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); verify(args.url, args.output)
