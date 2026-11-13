"""Future Roffe publication workflows, using synthetic display-only overlays."""
import argparse
from copy import deepcopy
import csv
import importlib.util
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('_browser_roffe',ROOT/'data/reproductions/roffe-2005-07016-bp/run.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)


def overlay(base):
    c=deepcopy(base);plan=m.design()
    template=next(x for x in c['result_series'] if x['dataset_id']=='mackay-unicycle-paper-rates')
    dataset=deepcopy(next(x for x in c['datasets'] if x['dataset_id']==template['dataset_id']))
    dataset.update(dataset_id='browser-roffe-only',label='Synthetic Roffe workflow fixture',points=[])
    c['datasets'].append(dataset)
    for code in plan['codes']:
        for arm in ['binary_ms','qbp_ms']:
            jobs=[j for j in plan['jobs'] if j['code']==code and j['arm']==arm][:2]
            identifier=f'test-roffe:{code}:{arm}'
            dec={'decoder_id':identifier,'label':'Synthetic workflow fixture',
                 'configuration':{'effective_configuration':jobs[0]['decoder']}}
            points=deepcopy(template['points'][:2])
            for p,j in zip(points,jobs,strict=True):
                p.update(x=j['physical_p'],y=.1,n=100,failures=10,ci_low=.05,ci_high=.2,mean_iterations=4,mean_directed_edge_updates=8*j['graph_edges'])
            series={**deepcopy(template),'series_id':identifier,'dataset_id':'browser-roffe-only','code_id':code,
                    'decoder_id':identifier,'source_decoder_id':arm,'points':points,
                    'channel_kind':jobs[0]['decoder']['noise_model']}
            c['decoders'].append(dec);c['result_series'].append(series)
    return c


def verify(url,output):
    output.mkdir(parents=True,exist_ok=False);checks=[];errors=[]
    catalog=json.loads((ROOT/'web/research/catalog.json').read_text());future=overlay(catalog)
    with sync_playwright() as p:
        browser=p.chromium.launch();page=browser.new_page(accept_downloads=True,viewport={'width':1512,'height':1100})
        page.on('pageerror',lambda e:errors.append(str(e)))
        app=(ROOT/'web/research/app.js').read_text().replace('\nload();','''
window.testRefreshCatalog=c=>{S.catalog=c;fillSavedChoices();renderCards();availability();};
window.testSelection=()=>({cards:S.cards.map(c=>({input:c.input,decoder:c.decoder})),spec:S.spec});
load();''')
        page.route('**/app.js',lambda route:route.fulfill(body=app,content_type='text/javascript'))
        page.goto(url+'#results');page.wait_for_function("document.querySelector('#catalog-status').textContent.includes('measured')")
        assert not page.locator('[data-select=input] option[value=toric9]').count()
        assert not page.locator('#build-code option[value=toric9]').count()
        checks.append('All four registered toric inputs remain hidden before measured multi-rate evidence')
        page.evaluate('c=>testRefreshCatalog(c)',future)
        card=page.locator('[data-plot]').first
        for code in ['toric9','toric11','toric13','toric15']:
            card.locator('[data-select=input]').select_option(code)
            card.locator('[data-select=decoder]').select_option('')
            assert card.locator('tbody tr').count()==4, (code, card.locator('tbody tr').count(), card.locator('[data-select=decoder]').input_value())
            assert card.locator('.curve-list input').count()==2
            assert 'αₜ = 1 − 2⁻ᵗ' in card.locator('.curve-list').inner_text()
            assert page.locator(f'#build-code option[value={code}]').count()==1
        checks.append('Every toric input: both measured curves, tables, builder choices and changing min-sum scale agree')
        with page.expect_download() as download:card.get_by_role('button',name='Export visible table').click()
        path=output/'toric.csv';download.value.save_as(path)
        with path.open(newline='') as f:assert len(list(csv.reader(f)))==5
        with page.expect_download() as download:card.get_by_role('button',name='Download run settings').click()
        path=output/'settings.json';download.value.save_as(path)
        data=json.loads(path.read_text());assert len(data['series'])==2
        assert all('alpha_schedule' in json.dumps(s) for s in data['series'])
        checks.append('CSV and settings exports retain both work metrics and the original variable-scale configuration')
        page.locator('[data-nav=builder]').click()
        page.locator('#builder-form').wait_for(state='visible')
        page.locator('#build-code').select_option('toric15')
        page.wait_for_function("document.querySelector('#build-matrix').value.includes('450') || document.querySelector('#build-matrix').value.includes('hx')")
        page.locator('#build-preset').select_option('test-roffe:toric15:binary_ms')
        assert 'study-specific execution path' in page.locator('#builder-feedback').inner_text()
        page.locator('#validate-spec').click()
        assert page.locator('#download-package').is_disabled()
        checks.append('Source-specific sweep schedule is preserved; saved study cannot silently become a constant-scale decoder')
        hidden=deepcopy(future)
        for s in hidden['result_series']:
            if s['dataset_id']=='browser-roffe-only':s['points']=s['points'][:1]
        page.evaluate('c=>testRefreshCatalog(c)',hidden)
        assert not page.locator('[data-select=input] option[value=toric15]').count()
        assert not page.locator('#build-code option[value=toric15]').count()
        assert not page.locator('#build-preset option[value="test-roffe:toric15:binary_ms"]').count()
        assert page.locator('#build-code').input_value()!='toric15'
        assert 'toric15' not in json.dumps(page.evaluate('testSelection()'))
        page.screenshot(path=str(output/'after-hiding.png'))
        checks.append('Losing the second measured rate hides toric codes and saved choices and clears stale selections')
        browser.close()
    assert not errors,errors
    result={'checks':checks,'errors':errors,'simulations':0};(output/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--url',required=True);a.add_argument('--output',type=Path,required=True);args=a.parse_args();verify(args.url,args.output)
