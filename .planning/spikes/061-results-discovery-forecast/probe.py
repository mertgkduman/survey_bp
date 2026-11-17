"""Inspect the real existing workbench; no product edits or simulations."""
import json
from pathlib import Path
import subprocess

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT/'.planning/spikes'
TARGETS = {
    'discovery': BASE/'061-results-discovery-forecast',
    'comparisons': BASE/'062-paper-comparison-forecast',
    'controls': BASE/'063-workbench-controls-forecast',
}
URL = 'http://127.0.0.1:8883/web/research/'


def geometry(page):
    return page.evaluate('''()=>{
      const card=document.querySelector('[data-plot]'), chart=card?.querySelector('.chart'),
        table=card?.querySelector('.table-wrap'), curves=card?.querySelector('.curve-list');
      const rect=n=>n?({top:n.getBoundingClientRect().top,height:n.getBoundingClientRect().height}):null;
      return {viewport:innerHeight,card:rect(card),chart:rect(chart),curves:rect(curves),
        table:table?{...rect(table),scrollWidth:table.scrollWidth,clientWidth:table.clientWidth}:null,
        documentHeight:document.documentElement.scrollHeight};
    }''')


def main():
    findings, errors = {}, []
    catalog_bytes = (ROOT/'web/research/catalog.json').read_bytes()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width':1512,'height':1050})
        page.set_default_timeout(120000)
        page.route('**/catalog.json',lambda route:route.fulfill(body=catalog_bytes,content_type='application/json'))
        page.on('pageerror', lambda err:errors.append(str(err)))
        page.goto(URL+'#results',wait_until='domcontentloaded',timeout=120000)
        page.wait_for_function("document.querySelector('#catalog-status').textContent.includes('measured')")
        findings['catalog'] = page.evaluate('''async()=>{
          const c=await(await fetch('catalog.json')).json(),d=DecoderDisplay.labels(c),
            active=ResearchCurves.active(c,d),figures=ResearchFigures.views(c,d);
          return {rawSeries:c.result_series.length,activeCurves:active.curves.length,
            activePoints:active.curves.reduce((n,s)=>n+s.points.length,0),
            activeCodes:active.codes.map(c=>({id:c.code_id,label:c.label})),
            activeCircuits:active.circuits.map(c=>c.circuit_id),
            paperOptions:[...document.querySelectorAll('[data-paper]')].map(b=>({id:b.dataset.paper,label:b.textContent})),
            activeEvidence:[...new Set(active.curves.map(c=>c.evidence))],
            figures:figures.map(f=>({id:f.figure_id,label:f.label,paper:f.paper_id,
              paperCurves:f.curves.filter(c=>c.paper_group==='paper').length,
              additionalCurves:f.curves.filter(c=>c.paper_group==='additional').length})),
            freshnessWords:[...document.querySelectorAll('time,[data-updated]')].map(n=>n.textContent),
            containsPriorTilt:JSON.stringify(c).includes('priortilt')||JSON.stringify(c).includes('2611.13373'),
            containsOsdV2:JSON.stringify(c).includes('weighted-streaming-osd-v2')};
        }''')
        assert not findings['catalog']['containsPriorTilt']
        assert not findings['catalog']['containsOsdV2']
        findings['customGeometry'] = geometry(page)
        card = page.locator('[data-plot]').first
        checked = set(card.locator('.curve-list input:checked').evaluate_all('xs=>xs.map(x=>x.dataset.curve)'))
        card.locator('.curve-picker input').focus()
        offered = set(card.locator('.curve-options [role=option]').evaluate_all('xs=>xs.map(x=>x.dataset.curve)'))
        findings['duplicatePickerExcludesVisible'] = checked.isdisjoint(offered)
        assert findings['duplicatePickerExcludesVisible']
        page.keyboard.press('Escape')
        page.screenshot(path=str(TARGETS['discovery']/'current-custom.png'))

        page.locator('[data-paper="yao-2312-10950-v2"]').click()
        findings['yao'] = {'figures':page.locator('[data-figure]').count(),'geometry':geometry(page)}
        assert findings['yao']['figures'] == 7
        figure = page.locator('[data-figure="yao-fig-3"]')
        findings['yao']['paperDefault'] = figure.locator('[data-group=paper]').is_checked()
        findings['yao']['additionalDefault'] = figure.locator('[data-group=additional]').is_checked()
        figure.locator('[data-group=additional]').check()
        findings['yao']['additionalRows'] = figure.locator('tbody tr').count()
        findings['yao']['expandedCurveCount'] = figure.locator('.curve-list input').count()
        findings['yao']['lineColors'] = figure.locator('path.line').evaluate_all('xs=>xs.map(x=>x.getAttribute("stroke"))')
        findings['yao']['metricChoices'] = figure.locator('.metric option').all_text_contents()
        page.screenshot(path=str(TARGETS['comparisons']/'yao-current.png'))

        page.locator('[data-paper="mackay-0304161-v3"]').click()
        figure = page.locator('[data-figure="mackay-fig-15"]')
        findings['mackay'] = {'rowsDefault':figure.locator('tbody tr').count(),
            'paperGroupDisabled':figure.locator('[data-group=paper]').is_disabled(),
            'additionalDefault':figure.locator('[data-group=additional]').is_checked(),
            'emptyMessage':figure.inner_text()[-1000:]}
        assert findings['mackay']['rowsDefault'] == 0
        figure.locator('[data-group=additional]').check()
        findings['mackay']['rowsAfterAdditional'] = figure.locator('tbody tr').count()
        assert findings['mackay']['rowsAfterAdditional'] > 0
        page.locator('[data-paper="panteleev-2012-04068-v2"]').click()
        figure = page.locator('[data-figure="lp1054-example-4"]')
        findings['lp'] = {'rowsDefault':figure.locator('tbody tr').count(),
                           'paperGroupDisabled':figure.locator('[data-group=paper]').is_disabled()}
        page.screenshot(path=str(TARGETS['comparisons']/'lp-default-empty.png'))

        page.locator('[data-paper="roffe-2005-07016-v2"]').click()
        figure = page.locator('[data-figure="roffe-fig-3"]')
        findings['roffeGeometry'] = geometry(page)
        findings['roffeTable'] = {'columns':figure.locator('th').all_text_contents(),
            'curveCount':figure.locator('.curve-list input').count(),
            'originalSourceDatasetRows':figure.locator('tbody tr').evaluate_all('xs=>xs.filter(x=>x.textContent.includes("source_transcription")).length')}
        findings['roffeColors'] = figure.locator('path.line').evaluate_all('xs=>xs.map(x=>x.getAttribute("stroke"))')
        findings['savedUrlBeforeReload'] = page.url
        page.reload()
        page.wait_for_function("document.querySelector('#catalog-status').textContent.includes('measured')")
        findings['paperAfterReload'] = page.locator('[data-paper][aria-pressed=true]').get_attribute('data-paper')
        assert findings['paperAfterReload'] == ''

        page.locator('[data-nav=builder]').click()
        findings['builder'] = {'families':page.locator('#build-family option').all_text_contents(),
            'variants':page.locator('#build-variant option').all_text_contents(),
            'circuits':page.locator('#build-circuit option').all_text_contents(),
            'codeOptions':page.locator('#build-code option').all_text_contents(),
            'presetCount':page.locator('#build-preset option').count(),
            'beforeMinSum':{name:page.locator('#'+name).input_value() for name in
                           ('build-format','build-scope','build-hard','build-shortcut')}}
        page.locator('#build-rule').select_option('min_sum')
        findings['builder']['afterMinSum'] = {name:page.locator('#'+name).input_value() for name in
                           ('build-format','build-scope','build-hard','build-shortcut')}
        assert findings['builder']['beforeMinSum']['build-format'] == 'float64'
        assert findings['builder']['afterMinSum']['build-format'] == 'int8'
        options = page.locator('#build-preset option').evaluate_all('xs=>xs.map(x=>({id:x.value,label:x.textContent}))')
        osd = next((x for x in options if 'OSD' in x['label']),None)
        if osd:
            page.locator('#build-preset').select_option(osd['id'])
            findings['builder']['osdPreset'] = osd
            findings['builder']['osdFeedback'] = page.locator('#builder-feedback').inner_text()
            findings['builder']['savedNote'] = page.locator('#saved-note').inner_text()
            findings['builder']['osdPackageEnabled'] = page.locator('#download-package').is_enabled()
        page.screenshot(path=str(TARGETS['controls']/'builder-current.png'))
        (TARGETS['discovery']/'current-observations.json').write_text(json.dumps(findings,indent=2)+'\n')

        # Earlier user-directed v2, with the same current catalog for a fair UI
        # comparison. This is historical source, not a proposed mock-up.
        old = browser.new_page(viewport={'width':1512,'height':1050})
        old.set_default_timeout(120000)
        old.on('pageerror', lambda err:errors.append(str(err)))
        old.route('**/catalog.json',lambda route:route.fulfill(body=catalog_bytes,content_type='application/json'))
        def historical_handler(body,kind):
            def fulfill(route):
                route.fulfill(body=body,content_type='text/html' if kind=='index.html' else 'text/css' if kind.endswith('.css') else 'text/javascript')
            return fulfill
        for filename in ('index.html','app.js','style.css'):
            content = subprocess.check_output(['git','show','781055fb^:web/research/'+filename],cwd=ROOT)
            pattern = '**/web/research/' if filename == 'index.html' else '**/web/research/'+filename
            old.route(pattern,historical_handler(content,filename))
        old.goto(URL+'#results',wait_until='domcontentloaded',timeout=120000)
        old.wait_for_function("document.querySelector('#catalog-status').textContent.includes('measured')")
        findings['beforePaperUpdate'] = {'paperButtons':old.locator('[data-paper]').count(),
                                        'geometry':geometry(old),'scope':'pre-781055fb index/app/style, same current catalog and shared helper versions'}
        old.screenshot(path=str(TARGETS['discovery']/'before-paper-update.png'))
        browser.close()
    assert not errors, errors
    findings['pageErrors'] = errors
    findings['catalog_sha256'] = __import__('hashlib').sha256(catalog_bytes).hexdigest()
    findings['scope'] = 'Existing live/historical HTML only; no mock-up, simulations or production edits.'
    (TARGETS['discovery']/'browser-observations.json').write_text(json.dumps(findings,indent=2)+'\n')
    print(json.dumps(findings,indent=2))


if __name__ == '__main__':
    main()
