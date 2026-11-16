"""Prospective beam/relay labels, exact exports, builder and empty-result state."""
import argparse
from copy import deepcopy
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

REPO=Path(__file__).resolve().parents[2]


def fixture():
    c=json.loads((REPO/'web/research/catalog.json').read_text())
    c['result_series']=[r for r in c['result_series'] if r['code_id']!='toric9']
    template=next(r for r in c['result_series'] if len(r['points'])>=2)
    dataset=deepcopy(next(d for d in c['datasets'] if d['dataset_id']==template['dataset_id']))
    dataset.update(dataset_id='search-browser-fixture',label='Synthetic search workflow fixture',points=[])
    c['datasets'].append(dataset)
    for method in ('beam','relay'):
        controls={'method':method,'initial':20,'per_unit':10,'units':16,'damping':.3,'alpha':.75,
                  'paper_scale':False,'beta':.25,'width':4,'rounds':12,'solutions':4,
                  'first_gamma':.125,'gamma_low':-.24,'gamma_high':.66}
        config={'family':'binary_css','check_rule':'min_sum','message_resolution':'float64','v2c_damping':.3,
                'alpha':.75,'beta':.25,'alpha_schedule':'constant','noise_model':'x_only','prior':'p',
                'max_iterations':180,'search':controls,'execution_backend':'canonical-css-search-traversal-v1'}
        c['decoders'].append({'decoder_id':method,'label':method,'configuration':{'effective_configuration':config}})
        points=deepcopy(template['points'][:2])
        for point,rate in zip(points,(.04,.05),strict=True):
            point.update(x=rate,y=.01,n=1000,failures=10,ci_low=.005,ci_high=.02,mean_iterations=8,
                         mean_directed_edge_updates=5000,mean_seconds=.00002)
            point['metadata']={'cohort_kind':'browser_fixture','seed':1,'source_evidence_path':method+str(rate),
                               'runtime_ratio_to_bp_osd0':.97,'budget_targets':[1.],
                               'latency_quantiles_seconds':{'0.5':1e-5,'0.95':5e-5,'0.99':8e-5}}
        c['result_series'].append({**deepcopy(template),'series_id':method,'dataset_id':'search-browser-fixture',
                                   'code_id':'toric9','decoder_id':method,'source_decoder_id':method,
                                   'channel_kind':'x_only','points':points})
    return c


def verify(url,output):
    output.mkdir(parents=True,exist_ok=False);checks=[];errors=[];catalog=fixture()
    with sync_playwright() as p:
        browser=p.chromium.launch();page=browser.new_page(accept_downloads=True,viewport={'width':1550,'height':1100})
        page.on('pageerror',lambda e:errors.append(str(e)))
        app=(REPO/'web/research/app.js').read_text().replace('\nload();','\nwindow.testRefreshCatalog=c=>{S.catalog=c;fillSavedChoices();renderCards();availability();};\nload();')
        page.route('**/app.js',lambda route:route.fulfill(body=app,content_type='text/javascript'))
        page.route('**/catalog.json',lambda route:route.fulfill(body=json.dumps(catalog),content_type='application/json'))
        page.goto(url+'#results');page.wait_for_function("document.querySelector('#catalog-status').textContent.includes('measured')")
        card=page.locator('[data-plot]').first;card.locator('[data-select=input]').select_option('toric9')
        card.locator('[data-select=decoder]').select_option('')
        assert card.locator('.curve-list input').count()==2 and card.locator('tbody tr').count()==4
        text=card.locator('.curve-list').inner_text()
        assert all(s in text for s in ('BeamSearch','RelayBP','I₀ = 20','I₊ = 10','U = 16','S = 4','w = 4','R = 12','γ₀ = 0.125','γₗ = -0.24','γₕ = 0.66','α = 0.75','β = 0.25','noise = X-only'))
        checks.append('Both search methods expose exact numerical, topology, solution and memory controls')
        with page.expect_download() as download:card.get_by_role('button',name='Export visible table').click()
        path=output/'results.csv';download.value.save_as(path)
        assert 'BeamSearch' in path.read_text() and 'RelayBP' in path.read_text() and '0.97×' in path.read_text()
        checks.append('Table/CSV retain both search methods, measured runtime ratios and all-path work')
        with page.expect_download() as download:card.get_by_role('button',name='Download run settings').click()
        path=output/'settings.json';download.value.save_as(path);encoded=path.read_text()
        assert 'canonical-css-search-traversal-v1' in encoded and 'gamma_low' in encoded and 'solutions' in encoded
        checks.append('Downloaded settings preserve full search configuration and traversal version')
        page.locator('[data-nav=builder]').click();page.locator('#build-code').select_option('toric9')
        page.locator('#build-preset').select_option('beam');page.locator('#validate-spec').click()
        assert page.locator('#download-package').is_disabled() and 'study-specific execution path' in page.locator('#builder-feedback').inner_text()
        checks.append('Saved search decoder cannot silently turn into ordinary BP in experiment builder')
        hidden=deepcopy(catalog)
        for series in hidden['result_series']:
            if series['dataset_id']=='search-browser-fixture':series['points']=series['points'][:1]
        page.evaluate('c=>testRefreshCatalog(c)',hidden)
        assert not page.locator('#build-code option[value=toric9]').count()
        assert not page.locator('#build-preset option[value=beam]').count()
        assert page.locator('#build-code').input_value()!='toric9'
        checks.append('Singleton/empty handling clears stale code and search-decoder selections')
        page.screenshot(path=str(output/'search-controls.png'));browser.close()
    assert not errors,errors
    result={'checks':checks,'errors':errors,'simulations':0}
    (output/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--url',required=True);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();verify(args.url,args.output)
