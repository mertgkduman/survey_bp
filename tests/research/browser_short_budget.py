"""Retained long curves and inferred short curves, synthetic display overlay only."""
import argparse
from copy import deepcopy
import csv
import importlib.util
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('_browser_short',ROOT/'data/reproductions/mackay-0304161-inferred-budget/run.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
NEW={'mackay-inferred-t100-baseline','mackay-damping-t100-confirmation'}


def overlay(base):
    base=deepcopy(base)
    base['result_series']=[s for s in base['result_series'] if s['dataset_id'] not in NEW]
    out=deepcopy(base);plan=m.design()
    dataset=deepcopy(next(d for d in base['datasets'] if d['dataset_id']=='mackay-unicycle-paper-rates'))
    dataset.update(dataset_id='browser-short-only',label='Synthetic inferred-budget fixture',points=[]);out['datasets'].append(dataset)
    for code in plan['codes']:
        for arm in ('binary_sp','qbp','unicycle_sp'):
            j=next(j for j in plan['jobs'] if j['code']==code and j['arm']==arm)
            original=next(s for s in base['result_series'] if s['code_id']==code and s['source_decoder_id']==arm and s['dataset_id']=='mackay-unicycle-paper-rates')
            identifier=f'test-short:{code}:{arm}';row=deepcopy(original)
            row.update(series_id=identifier,dataset_id='browser-short-only',decoder_id=identifier,points=deepcopy(original['points'][:2]))
            for i,p in enumerate(row['points']):p['metadata'].update(cohort_kind='test_fixture',source_evidence_path=f'test-fixture-{identifier}-{i}.json')
            out['result_series'].append(row)
            out['decoders'].append({'decoder_id':identifier,'label':'Synthetic short-budget fixture',
                'configuration':{'effective_configuration':j['decoder']}})
    return base,out


def verify(url,output):
    output.mkdir(parents=True,exist_ok=False);checks=[];errors=[]
    base,future=overlay(json.loads((ROOT/'web/research/catalog.json').read_text()))
    with sync_playwright() as p:
        browser=p.chromium.launch();page=browser.new_page(accept_downloads=True,viewport={'width':1512,'height':1100})
        page.on('pageerror',lambda e:errors.append(str(e)))
        app=(ROOT/'web/research/app.js').read_text().replace('\nload();','''
window.testRefreshCatalog=c=>{S.catalog=c;fillSavedChoices();renderCards();availability();};
window.testSelection=()=>({cards:S.cards.map(c=>({input:c.input,decoder:c.decoder})),spec:S.spec});
load();''')
        page.route('**/app.js',lambda route:route.fulfill(body=app,content_type='text/javascript'))
        page.route('**/catalog.json',lambda route:route.fulfill(body=json.dumps(base),content_type='application/json'))
        page.goto(url+'#results');page.wait_for_function("document.querySelector('#catalog-status').textContent.includes('measured')")
        page.evaluate('c=>testRefreshCatalog(c)',future)
        card=page.locator('[data-plot]').first
        for code in ('unicycle74','unicycle274'):
            card.locator('[data-select=input]').select_option(code);card.locator('[data-select=decoder]').select_option('')
            assert card.locator('.curve-list input').count()==6
            assert card.locator('tbody tr').count()==21
            text=card.locator('.curve-list').inner_text()
            assert 'T = 88200' in text and 'T = 100' in text and 'budget = inferred' in text
            assert 'Tₕ = 100' in text and 'T = 200' in text
        checks.append('Both codes retain all three 88200-budget curves beside three distinct inferred short-budget curves')
        checks.append('BP/Q-BP T=100 and source unicycle T_h=100 / total T=200 are explicit; inferred budget is labeled')
        with page.expect_download() as d:card.get_by_role('button',name='Export visible table').click()
        path=output/'budgets.csv';d.value.save_as(path)
        with path.open(newline='') as f:assert len(list(csv.reader(f)))==22
        with page.expect_download() as d:card.get_by_role('button',name='Download run settings').click()
        path=output/'settings.json';d.value.save_as(path);settings=json.loads(path.read_text())
        assert len(settings['series'])==6
        assert 'curve_inferred_not_source_specified' in json.dumps(settings)
        checks.append('Tables, CSV and settings keep both budgets, work metrics and inferred provenance separate')
        page.locator('[data-nav=builder]').click()
        page.locator('#build-preset').select_option('test-short:unicycle274:unicycle_sp')
        assert 'study-specific execution path' in page.locator('#builder-feedback').inner_text()
        page.locator('#validate-spec').click();assert page.locator('#download-package').is_disabled()
        hidden=deepcopy(future)
        for s in hidden['result_series']:
            if s['dataset_id']=='browser-short-only':s['points']=s['points'][:1]
        page.evaluate('c=>testRefreshCatalog(c)',hidden)
        assert not page.locator('#build-preset option[value="test-short:unicycle274:unicycle_sp"]').count()
        assert 'test-short:' not in json.dumps(page.evaluate('testSelection()'))
        page.locator('[data-nav=results]').click()
        card.locator('[data-select=input]').select_option('unicycle274');card.locator('[data-select=decoder]').select_option('')
        assert card.locator('.curve-list input').count()==3 and card.locator('tbody tr').count()==15
        page.screenshot(path=str(output/'preserved-long-curves.png'))
        checks.append('Singleton short evidence cannot borrow long-budget points; stale saved choices clear and original curves stay')
        browser.close()
    assert not errors,errors
    result={'checks':checks,'errors':errors,'simulations':0};(output/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--url',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();verify(a.url,a.output)
