"""V2 curve naming, search, hover and visibility checks; no new simulation runs."""
import argparse
import csv
import json
from pathlib import Path
from playwright.sync_api import sync_playwright


def verify(output, url):
    output.mkdir(parents=True,exist_ok=False)
    checks=[];errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page(viewport={'width':1512,'height':1100},accept_downloads=True)
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(url)
        page.wait_for_function("document.querySelector('#catalog-status').textContent.includes('measured')")
        page.locator('[data-nav="results"]').click()
        card=page.locator('[data-plot]').first
        text=card.locator('.curve-list').inner_text()
        assert 'Q-BP, SP' in text and 'd = 0' in text and 'T = 100' in text
        assert 'Yao vanilla' not in text
        options=card.locator('select[data-select="decoder"] option').evaluate_all('nodes=>nodes.map(n=>n.dataset.decoder||n.value)')
        assert not any(x.endswith(':binary_v1') or x.endswith(':bp4_v1') for x in options)
        checks.append('Parameter-based decoder labels; retired canonical clipping absent from selectors')
        picker=card.locator('.curve-picker input')
        picker.focus()
        assert card.locator('[role=option]').count()>1
        picker.fill('q-bp')
        assert all(t.lower().startswith('q-bp') for t in card.locator('[role=option]').all_text_contents())
        page.keyboard.press('ArrowDown')
        active=picker.get_attribute('aria-activedescendant')
        assert active and page.locator('#'+active).get_attribute('aria-selected')=='true'
        page.keyboard.press('ArrowDown')
        chosen=page.locator('#'+picker.get_attribute('aria-activedescendant')).get_attribute('data-decoder')
        page.keyboard.press('Enter')
        assert card.locator(f'.curve-group[data-decoder="{chosen}"]').count()==1
        assert card.locator('.curve-group').count()==2
        assert picker.get_attribute('aria-expanded')=='false'
        checks.append('Focus opens available curves; case-insensitive prefix search and keyboard selection add a curve')
        # A second independently selected curve keeps both the plot and details visible.
        groups=card.locator('.curve-group')
        first_decoder=groups.first.get_attribute('data-decoder')
        before_rows=card.locator('tbody tr').count()
        card.locator('.curve-hit').first.press('Enter')
        assert card.locator(f'.curve-group[data-decoder="{first_decoder}"]').get_attribute('data-visible')=='false'
        assert card.locator('tbody tr').count()<before_rows
        assert card.locator('.run-details h4').count()==1
        assert card.locator('.curve-list input:not(:checked)').count()==1
        hidden_id=card.locator(f'.curve-group[data-decoder="{first_decoder}"]').get_attribute('data-curve')
        hidden_label=card.locator(f'.curve-list input[data-curve="{hidden_id}"]').locator('..')
        page.locator('h2#results-heading').click()
        hidden_label.hover()
        ghost=card.locator(f'.curve-group[data-decoder="{first_decoder}"]')
        assert ghost.get_attribute('opacity')=='0.25'
        assert 'preview' in ghost.get_attribute('class')
        assert card.locator('tbody tr').count()<before_rows
        page.locator('h2#results-heading').hover()
        assert ghost.get_attribute('opacity')=='0'
        checks.append('Curve click/keyboard toggle updates table and reproduction details; hidden-curve preview is faint and does not add rows')
        with page.expect_download() as d:
            card.get_by_role('button',name='Download run settings').click()
        receipt=output/'visible-settings.json';d.value.save_as(receipt)
        assert len(json.loads(receipt.read_text())['series'])==1
        with page.expect_download() as d:
            card.get_by_role('button',name='Export visible table').click()
        csv_path=output/'visible.csv';d.value.save_as(csv_path)
        assert first_decoder not in csv_path.read_text()
        with csv_path.open(newline='') as stream:
            assert len(list(csv.reader(stream)))-1==card.locator('tbody tr').count()
        hidden_label.locator('input').check()
        assert card.locator('tbody tr').count()==before_rows
        checks.append('Run settings and CSV include only enabled curves; legend restores a hidden curve')
        page.locator('#add-plot').click()
        second=page.locator('[data-plot]').nth(1)
        assert card.bounding_box()['x']<second.bounding_box()['x']
        second_state=second.locator('select[data-select="input"]').input_value()
        card.locator('select[data-select="input"]').select_option('b1')
        assert second.locator('select[data-select="input"]').input_value()==second_state
        code_options=card.locator('select[data-select="decoder"] option').evaluate_all('nodes=>nodes.map(n=>n.dataset.decoder||n.value)')
        assert not any(x.endswith(':bp4_vanilla_ms_q8') for x in code_options)
        assert any('pfister-presentation-ms-both-changes' in x for x in code_options)
        page.screenshot(path=str(output/'desktop.png'))
        checks.append('Plot states remain independent; corrected Q8 remains available while retired BP4 state clipping is removed')
        page.locator('[data-nav="builder"]').click()
        saved=page.locator('#build-preset option').all_text_contents()[1:]
        assert saved and all(' = ' in name for name in saved)
        assert not any('Yao vanilla:' in name for name in saved)
        values=page.locator('#build-preset option').evaluate_all('nodes=>nodes.map(n=>n.dataset.decoder||n.value)')
        assert not any(x.endswith(':bp4_v1') or x.endswith(':binary_v1') for x in values)
        checks.append('Saved-specification names share the same parameter labels and retirement filtering')
        page.set_viewport_size({'width':390,'height':844})
        page.locator('[data-nav="results"]').click()
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        card.locator('.curve-picker input').focus()
        assert card.locator('[role=listbox]').is_visible()
        card.locator('.curve-picker input').fill('no-such-prefix')
        assert 'No curve' in card.locator('[role=listbox]').inner_text()
        page.keyboard.press('Escape')
        assert not card.locator('[role=listbox]').is_visible()
        page.screenshot(path=str(output/'mobile.png'))
        checks.append('Mobile layout, no-match state, Escape dismissal and accessible combobox state work')
        assert not errors,errors
        browser.close()
    report={'checks':checks,'errors':errors}
    (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True,type=Path);parser.add_argument('--url',default='http://127.0.0.1:8765/web/research/');args=parser.parse_args();print(json.dumps(verify(args.output.resolve(),args.url),indent=2))
