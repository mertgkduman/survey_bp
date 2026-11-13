"""Browser-only isolated-control fixture; no simulation or source evidence."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
DATA='mackay-qbp-isolation-t100'

def verify(url,output):
    output.mkdir(parents=True,exist_ok=False);checks=[];errors=[]
    catalog=json.loads((ROOT/'web/research/catalog.json').read_text())
    catalog['result_series']=[s for s in catalog['result_series'] if s['dataset_id']!=DATA]
    future=deepcopy(catalog);plan=json.loads((ROOT/'data/reproductions/mackay-0304161-isolated-qbp/plan.json').read_text())
    dataset=deepcopy(next(d for d in catalog['datasets'] if d['dataset_id']=='mackay-inferred-t100-baseline'))
    dataset.update(dataset_id='browser-isolated-only',label='Synthetic browser fixture',points=[]);future['datasets'].append(dataset)
    for code in ('unicycle274','unicycle74'):
        for arm in ('binary_separate','qbp_undamped'):
            j=next(j for j in plan['jobs'] if j['code']==code and j['arm']==arm)
            old=next(s for s in catalog['result_series'] if s['code_id']==code and s['dataset_id']=='mackay-inferred-t100-baseline' and s['source_decoder_id']=='qbp')
            row=deepcopy(old);key=f'browser-isolate:{code}:{arm}'
            row.update(series_id=key,decoder_id=key,dataset_id='browser-isolated-only',source_decoder_id=arm,points=row['points'][:2])
            for i,p in enumerate(row['points']):
                p['iteration_unit']='paired X/Z rounds' if arm=='binary_separate' else 'joint sweeps'
                p['metadata'].update(cohort_kind='test_fixture',source_evidence_path=f'test-only-{key}-{i}')
            future['result_series'].append(row)
            future['decoders'].append({'decoder_id':key,'configuration':{'effective_configuration':j['decoder']}})
    with sync_playwright() as p:
        browser=p.chromium.launch();page=browser.new_page(accept_downloads=True,viewport={'width':1512,'height':1100})
        page.on('pageerror',lambda e:errors.append(str(e)))
        app=(ROOT/'web/research/app.js').read_text().replace('\nload();','''
window.testRefreshCatalog=c=>{S.catalog=c;fillSavedChoices();renderCards();availability();};
window.testSelection=()=>({cards:S.cards,spec:S.spec});
load();''')
        page.route('**/app.js',lambda r:r.fulfill(body=app,content_type='text/javascript'))
        page.route('**/catalog.json',lambda r:r.fulfill(body=json.dumps(catalog),content_type='application/json'))
        page.goto(url+'#results');page.wait_for_function("document.querySelector('#catalog-status').textContent.includes('measured')")
        page.evaluate('c=>testRefreshCatalog(c)',future);card=page.locator('[data-plot]').first
        for code in ('unicycle274','unicycle74'):
            card.locator('[data-select=input]').select_option(code);card.locator('[data-select=decoder]').select_option('')
            assert card.locator('.curve-list input').count()==8
            text=card.locator('.curve-list').inner_text()
            assert 'Binary BP (separate X/Z)' in text and 'p₀ = 2p/3' in text and 'noise = depolarizing' in text
            assert 'd = 0' in text and 'd = 0.1' in text and 'T = 88200' in text
            assert card.locator('tbody tr').count()==34
        checks.append('Both codes keep d=0 joint and separate controls distinct from X-only and d=.1/long-budget curves')
        with page.expect_download() as d:card.get_by_role('button',name='Export visible table').click()
        csv=output/'visible.csv';d.value.save_as(csv);assert 'paired X/Z rounds' in csv.read_text() and 'joint sweeps' in csv.read_text()
        with page.expect_download() as d:card.get_by_role('button',name='Download run settings').click()
        settings=output/'settings.json';d.value.save_as(settings);text=settings.read_text()
        assert 'separate_xz' in text and 'paired X/Z rounds' in text
        checks.append('Visible CSV and settings preserve distinct work units, priors and exact decoder scopes')
        page.locator('[data-nav=builder]').click();page.locator('#build-preset').select_option('browser-isolate:unicycle74:binary_separate')
        page.locator('#validate-spec').click();assert page.locator('#download-package').is_disabled()
        hidden=deepcopy(future)
        for s in hidden['result_series']:
            if s['dataset_id']=='browser-isolated-only':s['points']=s['points'][:1]
        page.evaluate('c=>testRefreshCatalog(c)',hidden)
        assert 'browser-isolate:' not in json.dumps(page.evaluate('testSelection()'))
        assert not page.locator('#build-preset option[value="browser-isolate:unicycle74:binary_separate"]').count()
        page.locator('[data-nav=results]').click();assert card.locator('.curve-list input').count()==6
        checks.append('Singleton imported controls clear stale saved selections and preserve all original curves')
        page.screenshot(path=str(output/'isolated-controls.png'));browser.close()
    assert not errors,errors
    result={'checks':checks,'errors':errors,'simulations':0};(output/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--url',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();verify(a.url,a.output)
