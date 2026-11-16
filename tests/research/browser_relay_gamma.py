"""Synthetic80/60 rows through the real gamma publisher and public browser."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from playwright.sync_api import sync_playwright

REPO=Path(__file__).resolve().parents[2]
ROOT=REPO/'data/reproductions/lp1054-relay-gamma80-60'


def fixture():
    spec=importlib.util.spec_from_file_location('_lp1054_gamma_campaign',ROOT/'run.py')
    run=importlib.util.module_from_spec(spec);sys.modules[spec.name]=run;spec.loader.exec_module(run)
    report=run.module('_lp1054_gamma_report',ROOT/'report.py');plan=run.design()
    plan.update(study_id='relay-gamma-browser-fixture',label='Synthetic gamma browser fixture')
    (ROOT/'results').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='browser-publisher-',dir=ROOT/'results') as name:
        directory=Path(name);rows=[]
        for p in (.06,.08):
            job={'id':'fixture-'+str(p),'background':'fixture','physical_p':p,
                 'numeric_controls':{'damping':.3,'alpha':.8,'beta':.2}}
            point=directory/str(p);point.mkdir();(point/'summary.json').write_text('{"synthetic":true}\n')
            rows.append({'job':job,'controls':run.relay(job,.35,-.254,.985),'roles':['gamma_selected'],
                'shots':1000,'failures':10,'rate':.01,'ci95_low':.005,'ci95_high':.02,
                'iterations':10000,'directed_edge_updates':74400000,'decode_ns':100000000,
                'gamma_bias_updates':10540000,'disorder_draws':1054000,'memory_clips':0,
                'counts':{'success':990,'type_i':8,'type_ii':2},'stage':'confirmation',
                'stop_reason':'synthetic_fixture','uncertainty_method':'synthetic_fixture',
                'directory':str(point.relative_to(REPO)),
                'latency_quantiles_seconds':{'0.5':1e-4,'0.95':2e-4,'0.99':3e-4}})
        original=report.ROOT;report.ROOT=directory
        try:report.publish(plan,rows);extension=json.loads((directory/'catalog.json').read_text())
        finally:report.ROOT=original
    catalog=json.loads((REPO/'web/research/catalog.json').read_text())
    catalog['result_series']=[s for s in catalog['result_series'] if s['code_id']!='lp1054']
    for key in ('datasets','decoders','result_series','experiments'):catalog[key].extend(extension[key])
    return catalog,extension['decoders'][0]['decoder_id']


def verify(url,output):
    output.mkdir(parents=True,exist_ok=False);catalog,identifier=fixture();checks=[];errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch();page=browser.new_page(accept_downloads=True,viewport={'width':1550,'height':1100})
        page.on('pageerror',lambda e:errors.append(str(e)))
        app=(REPO/'web/research/app.js').read_text().replace('\nload();','\nwindow.testRefreshCatalog=c=>{S.catalog=c;fillSavedChoices();renderCards();availability();};\nload();')
        page.route('**/app.js',lambda route:route.fulfill(body=app,content_type='text/javascript'))
        page.route('**/catalog.json',lambda route:route.fulfill(body=json.dumps(catalog),content_type='application/json'))
        page.goto(url+'#results');page.wait_for_function("document.querySelector('#catalog-status').textContent.includes('measured')")
        card=page.locator('[data-plot]').first;card.locator('[data-select=input]').select_option('lp1054')
        card.locator('[data-select=decoder]').select_option('')
        assert card.locator('.curve-list input').count()==1 and card.locator('tbody tr').count()==2
        label=card.locator('.curve-list').inner_text()
        assert all(s in label for s in ('RelayBP','I₀ = 80','I₊ = 60','U = 1','γ₀ = 0.35','γₗ = -0.254','γₕ = 0.985'))
        checks.append('Actual publisher output preserves80/60 caps and both gamma regimes in a compatible multi-rate curve')
        with page.expect_download() as download:card.get_by_role('button',name='Download run settings').click()
        path=output/'settings.json';download.value.save_as(path);text=path.read_text()
        assert 'first_gamma' in text and 'lp1054-relay-gamma80-60-v1' in text and 'gamma_high' in text
        checks.append('Settings export retains exact coefficients, memory seeds and distinct execution backend')
        page.locator('[data-nav=builder]').click();page.locator('#build-preset').select_option(identifier)
        page.locator('#validate-spec').click();assert page.locator('#download-package').is_disabled()
        assert 'study-specific execution path' in page.locator('#builder-feedback').inner_text()
        checks.append('Saved Relay gamma controller cannot silently become ordinary BP in the experiment builder')
        for s in catalog['result_series']:
            if s['dataset_id']=='relay-gamma-browser-fixture':
                for point in s['points']:point['x']=.06
        page.evaluate('c=>testRefreshCatalog(c)',catalog)
        assert 'lp1054' not in page.locator('#build-code option').evaluate_all('xs=>xs.map(x=>x.value)')
        assert page.locator('#build-preset').input_value()!=identifier
        checks.append('Same-rate cohorts cannot qualify the curve; stale input and saved gamma selections clear')
        assert not errors;browser.close()
    value={'checks':checks,'errors':errors,'fixture':'synthetic publisher data; no scientific measurements','simulations':0}
    (output/'verification.json').write_text(json.dumps(value,indent=2)+'\n');return value
