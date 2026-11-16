"""Real paper navigation, grouped visibility, scoped exports and stale refresh."""
import argparse
import csv
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]


def verify(output,url):
    output.mkdir(parents=True,exist_ok=False);checks=[];errors=[]
    catalog=json.loads((ROOT/'web/research/catalog.json').read_text())
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page(accept_downloads=True,viewport={'width':1500,'height':1100})
        page.on('pageerror',lambda e:errors.append(str(e)))
        app=(ROOT/'web/research/app.js').read_text().replace('\nload();','\nwindow.testRefreshCatalog=c=>{S.catalog=c;fillSavedChoices();renderCards();availability();};\nload();')
        page.route('**/app.js',lambda r:r.fulfill(body=app,content_type='text/javascript'))
        page.goto(url+'#results');page.wait_for_function("document.querySelector('#catalog-status').textContent.includes('measured')")
        custom_input=page.locator('[data-plot]').first.locator('[data-select=input]').input_value()
        page.locator('[data-paper="yao-2312-10950-v2"]').click()
        assert page.locator('[data-figure]').count()==7
        assert [x.split(' · ')[0] for x in page.locator('[data-figure] .card-heading h3').all_text_contents()]==[f'Fig. {i}' for i in range(2,9)]
        assert page.locator('#paper-heading a').get_attribute('href')=='https://arxiv.org/abs/2312.10950v2'
        cards=page.locator('[data-figure]')
        for i in range(cards.count()):
            card=cards.nth(i)
            assert card.locator('[data-group=paper]').is_checked()
            assert not card.locator('[data-group=additional]').is_checked()
            assert card.locator('tbody tr').count()>0
        checks.append('Clickable Yao title opens seven separately named figures with paper reproductions on and additional curves off')

        card=page.locator('[data-figure=yao-fig-3]');other=page.locator('[data-figure=yao-fig-7]')
        original_rows=card.locator('tbody tr').count();other_rows=other.locator('tbody tr').count()
        original_axes=card.locator('.y-tick').all_text_contents()
        card.locator('[data-group=additional]').check()
        assert card.locator('tbody tr').count()>original_rows
        assert other.locator('tbody tr').count()==other_rows
        first_curve=card.locator('.curve-list input:checked').first.get_attribute('data-curve')
        card.locator(f'.curve-list input[data-curve="{first_curve}"]').uncheck()
        assert card.locator('[data-group=paper]').evaluate('(x)=>x.indeterminate')
        card.locator('[data-group=paper]').check()
        assert not card.locator('[data-group=paper]').evaluate('(x)=>x.indeterminate')
        card.locator('[data-group=additional]').uncheck()
        assert card.locator('tbody tr').count()==original_rows
        assert card.locator('.y-tick').all_text_contents()==original_axes
        checks.append('Per-figure group toggles, individual mixed state and automatic axes agree without changing other figures')

        with page.expect_download() as download:card.get_by_role('button',name='Download run settings',exact=True).click()
        path=output/'figure3-settings.json';download.value.save_as(path);receipt=json.loads(path.read_text())
        assert receipt['figure_label']=='Fig. 3 · B1' and receipt['paper_id']=='yao-2312-10950-v2'
        assert all(s['paper_group']=='paper' for s in receipt['series'])
        assert all(p.get('source_figure') in (None,'3') for s in receipt['series'] for p in s['points'])
        with page.expect_download() as download:card.get_by_role('button',name='Export visible table',exact=True).click()
        path=output/'figure3.csv';download.value.save_as(path)
        with path.open() as f:assert len(list(csv.reader(f)))-1==original_rows
        card.locator('[data-group=paper]').uncheck()
        assert card.locator('tbody tr').count()==0
        assert card.get_by_role('button',name='Export visible table',exact=True).is_disabled()
        assert card.get_by_role('button',name='Download run settings',exact=True).is_disabled()
        card.locator('[data-group=paper]').check()
        checks.append('Figure-labelled settings and CSV contain only visible scoped evidence; both groups off safely disables exports')

        page.locator('[data-paper="roffe-2005-07016-v2"]').click()
        card=page.locator('[data-figure=roffe-fig-3]')
        assert card.count()==1 and card.locator('[data-group=paper]').is_checked()
        assert card.locator('[data-select=input] option').count()==5
        assert 'CS-60' in card.locator('.figure-note').inner_text()
        card.locator('[data-select=input]').select_option('toric9')
        assert 'toric9'==card.locator('[data-select=input]').input_value()
        assert card.locator('tbody tr').count()>0
        assert all('X-only' in x for x in card.locator('tbody tr td:nth-child(2)').all_text_contents())
        without_code=json.loads(json.dumps(catalog))
        without_code['result_series']=[s for s in without_code['result_series'] if s['code_id']!='toric9']
        page.evaluate('c=>testRefreshCatalog(c)',without_code)
        assert card.locator('[data-select=input]').input_value()=='__figure__'
        assert card.locator('[data-group=paper]').is_checked()
        assert not card.locator('[data-group=additional]').is_checked()
        page.evaluate('c=>testRefreshCatalog(c)',catalog)
        checks.append('Roffe Fig. 3 includes four labelled toric codes; canonical regular BP is default while CS10/OSD0 and tuning stay additional')

        page.locator('[data-paper="mackay-0304161-v3"]').click()
        card=page.locator('[data-figure=mackay-fig-15]')
        assert 'inferred' in card.locator('.figure-note').inner_text()
        assert card.locator('[data-group=paper]').is_disabled() and card.locator('tbody tr').count()==0
        card.locator('[data-group=additional]').check();assert card.locator('tbody tr').count()>0
        page.locator('[data-paper="panteleev-2012-04068-v2"]').click()
        card=page.locator('[data-figure=lp1054-example-4]')
        assert 'no LER figure' in card.locator('.figure-note').inner_text()
        assert card.locator('[data-group=paper]').is_disabled()
        card.locator('[data-group=additional]').check();assert card.locator('tbody tr').count()>0
        checks.append('MacKay inferred settings and LP Example 4 remain explicitly additional; no invented exact-reproduction figure')

        page.locator('[data-paper=""]').click()
        assert page.locator('[data-figure]').count()==0
        assert page.locator('[data-plot]').first.locator('[data-select=input]').input_value()==custom_input
        page.locator('[data-paper="yao-2312-10950-v2"]').click()
        # An actual new catalog member from an import defaults to Additional.
        extended=json.loads(json.dumps(catalog));source=next(s for s in extended['result_series'] if s['dataset_id']=='yao-vanilla-a5-b2' and s['code_id']=='a5')
        new=json.loads(json.dumps(source));new.update(series_id='paper-browser-import',decoder_id='paper-browser-import',dataset_id='paper-browser-import',source_decoder_id='new-policy')
        decoder=json.loads(json.dumps(next(d for d in extended['decoders'] if d['decoder_id']==source['decoder_id'])));decoder['decoder_id']='paper-browser-import'
        extended['datasets'].append({'dataset_id':'paper-browser-import','paper_id':'yao-2312-10950-v2','evidence_status':'canonical_adaptation'})
        extended['decoders'].append(decoder);extended['result_series'].append(new)
        page.evaluate('c=>testRefreshCatalog(c)',extended)
        card=page.locator('[data-figure=yao-fig-7]')
        assert not card.locator('[data-group=additional]').is_checked()
        assert card.locator('[data-group=paper]').is_checked()
        empty=json.loads(json.dumps(extended))
        for s in empty['result_series']:
            for point in s['points']:point['x']=.06
        page.evaluate('c=>testRefreshCatalog(c)',empty)
        assert page.locator('[data-figure]').count()==0
        assert page.locator('[data-paper]').count()==1
        assert page.locator('#build-code').input_value()=='custom'
        assert page.locator('[data-plot] tbody tr').count()==0
        checks.append('Custom plots survive switching; new imports stay additional; empty refresh removes stale paper/figure/input selections')
        page.set_viewport_size({'width':390,'height':850})
        page.evaluate('c=>testRefreshCatalog(c)',catalog)
        page.locator('[data-paper="yao-2312-10950-v2"]').click()
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        page.screenshot(path=str(output/'mobile.png'),full_page=False)
        page.set_viewport_size({'width':1500,'height':1100})
        page.screenshot(path=str(output/'desktop.png'),full_page=False)
        checks.append('Paper options and separate figure cards fit mobile and desktop layouts')
        assert not errors,errors;browser.close()
    report={'checks':checks,'errors':errors,'simulations':0}
    (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--url',default='http://127.0.0.1:8877/web/research/')
    args=parser.parse_args();print(json.dumps(verify(args.output,args.url),indent=2))
