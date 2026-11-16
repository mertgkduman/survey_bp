"""Synthetic UI fixture: LP1054 results, distinct BP/Q-BP OSD and stale inputs."""
from copy import deepcopy
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parents[2]


def verify(url,output):
    output.mkdir(parents=True,exist_ok=False);errors = [];checks = []
    catalog = json.loads((REPO/'web/research/catalog.json').read_text())
    catalog['result_series'] = [s for s in catalog['result_series'] if s['code_id']!='lp1054']
    template = deepcopy(next(s for s in catalog['result_series'] if len(s['points'])>=2))
    dataset = 'lp1054-browser-fixture'
    catalog['datasets'].append({'dataset_id':dataset,'label':'Synthetic LP1054 browser fixture',
                               'evidence_status':'canonical_adaptation','points':[]})
    for family in ('bp','bp4'):
        identifier = dataset+':'+family
        config = {'family':family,'check_rule':'min_sum','precision':'float64','v2c_damping':0.,
            'alpha':.625,'beta':0.,'max_iterations':32,'noise_model':'depolarizing',
            'execution_backend':'lp1054-canonical-stack-v1','postprocessing':{'method':'OSD_CS','order':10}}
        catalog['decoders'].append({'decoder_id':identifier,'configuration':{'effective_configuration':config}})
        points = deepcopy(template['points'][:2])
        for p,x in zip(points,(.06,.08)):
            p.update(x=x,y=.01,n=1000,failures=10,ci_low=.005,ci_high=.02,
                     mean_iterations=15.,mean_directed_edge_updates=1000.,mean_seconds=.0001)
            p['metadata'] = {'cohort_kind':'synthetic_browser_fixture','seed':1,'source_evidence_path':identifier+str(x)}
        catalog['result_series'].append({**template,'series_id':identifier,'dataset_id':dataset,
            'code_id':'lp1054','decoder_id':identifier,'source_decoder_id':identifier,
            'channel_kind':'depolarizing','points':points})
    with sync_playwright() as p:
        browser = p.chromium.launch();page = browser.new_page(accept_downloads=True,viewport={'width':1550,'height':1100})
        page.on('pageerror',lambda error:errors.append(str(error)))
        app = (REPO/'web/research/app.js').read_text().replace('\nload();','\nwindow.testRefreshCatalog=c=>{S.catalog=c;fillSavedChoices();renderCards();availability();};\nload();')
        page.route('**/app.js',lambda route:route.fulfill(body=app,content_type='text/javascript'))
        page.route('**/catalog.json',lambda route:route.fulfill(body=json.dumps(catalog),content_type='application/json'))
        page.goto(url+'#results');page.wait_for_function("document.querySelector('#catalog-status').textContent.includes('measured')")
        card = page.locator('[data-plot]').first
        card.locator('[data-select=input]').select_option('lp1054')
        card.locator('[data-select=decoder]').select_option('')
        assert card.locator('.curve-list input').count()==2 and card.locator('tbody tr').count()==4
        text = card.locator('.curve-list').inner_text()
        assert all(s in text for s in ('BP+OSD-CS','Q-BP+OSD-CS','T = 32','λ = 10','precision = float64'))
        checks.append('LP1054 shows distinct binary and correlated OSD curves with exact budgets and precision')
        with page.expect_download() as download:card.get_by_role('button',name='Export visible table').click()
        path = output/'results.csv';download.value.save_as(path)
        assert 'Q-BP+OSD-CS' in path.read_text() and '0.08' in path.read_text()
        checks.append('Visible table and CSV retain both decoder families and physical rates')
        page.locator('[data-nav=builder]').click();page.locator('#build-code').select_option('lp1054')
        page.wait_for_function("document.querySelector('#matrix-note').textContent.includes('465')")
        page.locator('#build-preset').select_option(dataset+':bp4');page.locator('#validate-spec').click()
        assert page.locator('#download-package').is_disabled()
        assert 'study-specific execution path' in page.locator('#builder-feedback').inner_text()
        checks.append('Registered LP matrix preview loads; saved joint OSD cannot silently become plain BP')
        hidden = deepcopy(catalog)
        for s in hidden['result_series']:
            if s['dataset_id']==dataset:
                for point in s['points']:point['x']=.06
        page.evaluate('c=>testRefreshCatalog(c)',hidden)
        assert 'lp1054' not in page.locator('#build-code option').evaluate_all('xs=>xs.map(x=>x.value)')
        assert page.locator('#build-code').input_value()!='lp1054'
        assert page.locator('#build-preset').input_value()!=dataset+':bp4'
        assert 'lp1054' not in card.locator('[data-select=input] option').evaluate_all('xs=>xs.map(x=>x.value)')
        checks.append('Repeated same-rate evidence hides LP1054 everywhere and clears stale code/decoder selections')
        assert not errors
        browser.close()
    report = {'status':'passed','checks':checks,'page_errors':errors,'fixture':'synthetic; not measured campaign evidence'}
    (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    return report
