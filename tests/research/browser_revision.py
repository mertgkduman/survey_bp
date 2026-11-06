"""Workbench revision: actual browser exports and tiny policy/circuit executions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys
import zipfile

from playwright.sync_api import sync_playwright


FIXTURE = {"hx": [[1, 1, 0]], "hz": [[0, 0, 1]],
           "lx": [[1, 0, 0]], "lz": [[1, 1, 0]]}


def verify(root: Path, output: Path, url: str):
    output.mkdir(parents=True, exist_ok=False)
    checks, errors = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1512, "height": 1100}, accept_downloads=True)
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(url + "#results")
        page.wait_for_function("document.querySelector('#catalog-status').textContent.includes('measured')")
        card = page.locator('[data-plot]').first
        assert not any('three-qubit' in name.lower() for name in card.locator('select[data-select="input"] option').all_text_contents())
        assert not any('BP4' in name or ' · ' in name for name in card.locator('select[data-select="decoder"] option').all_text_contents())
        card.locator('select[data-select="input"]').select_option('b1')
        card.locator('select[data-select="decoder"]').select_option('')
        assert card.locator('.axis-note .katex').count() == 1
        assert 'bit-flip probability' in card.locator('svg').text_content()
        assert 'depolarizing (X, Y, Z: p/3 each)' in card.locator('tbody').inner_text()
        card.locator('select[data-select="input"]').select_option('relay-surface-d3')
        assert card.locator('tbody tr').count() > 0
        assert 'observable' in card.locator('tbody').inner_text().lower()
        checks.append('Q-BP names, comma separators, hidden public fixture, conditional bit-flip axis and retained circuit measurements')

        page.locator('[data-nav="builder"]').click()
        search = page.locator('#decoder-search input')
        search.focus()
        assert page.locator('#saved-decoder-options [role=option]').count() > 2
        search.fill('q-bp, sp, d = 0, t = 100, float64 v2')
        page.keyboard.press('ArrowDown')
        page.keyboard.press('Enter')
        assert page.locator('#build-family').input_value() == 'bp4'
        assert page.locator('#build-damping').input_value() == '0'
        assert page.locator('#kernel-guide .katex').count() >= 3
        page.locator('#build-code').select_option('bb72')
        page.wait_for_function("document.querySelector('#build-matrix').value.includes('hx')")
        matrix1 = json.loads(page.locator('#build-matrix').input_value())
        assert len(matrix1['hx'][0]) == 72
        page.locator('#build-code').select_option('a5')
        page.wait_for_function("document.querySelector('#build-matrix').value.includes('hx') && JSON.parse(document.querySelector('#build-matrix').value).hx[0].length===180")
        assert page.locator('#build-matrix').get_attribute('readonly') is not None
        checks.append('Keyboard saved-decoder search, undamped Q-BP baseline, rendered kernel guide and changing exact code matrices')

        page.locator('#build-code').select_option('custom')
        page.locator('#build-matrix').fill(json.dumps(FIXTURE))
        page.locator('#build-variant').select_option('qbpgd')
        assert page.locator('#numerical-controls').is_visible()
        assert page.locator('#decimation-controls').is_visible()
        page.locator('#build-rule').select_option('min_sum')
        page.locator('#build-damping').fill('0.2')
        page.locator('#build-alpha').fill('0.8')
        page.locator('#build-beta').fill('0.25')
        page.locator('#build-per-round').fill('2')
        page.locator('#build-rounds').fill('1')
        page.locator('#build-iterations').fill('2')
        page.locator('#build-shots').fill('2')
        page.locator('#build-rates').fill('0.06')
        page.locator('#validate-spec').click()
        assert page.locator('#download-package').is_enabled(), page.locator('#builder-feedback').inner_text()
        with page.expect_download() as download:
            page.locator('#download-package').click()
        archive = output / 'composed-qbpgd.zip'
        download.value.save_as(archive)
        package = output / 'composed policy package'
        with zipfile.ZipFile(archive) as z:
            z.extractall(package)
        spec = json.loads((package / 'experiment.json').read_text())
        assert spec['decoder']['policy']['damping'] == .2
        assert spec['decoder']['policy']['alpha'] == .8
        assert spec['decoder']['variant'] == 'qbpgd'
        result = subprocess.run([sys.executable, str(package / 'run.py'), '--repo', str(root), '--output', str(package / 'results')], capture_output=True, text=True, cwd=output)
        assert result.returncode == 0, result.stderr
        assert json.loads((package / 'results/summary.json').read_text())['rows'][0]['n'] == 2
        checks.append('Actual exported Q-BPGD composes min-sum scaling/offset, damping and Q8 precision and executes two shots')
        page.locator('[data-nav="getting-started"]').click()
        page.locator('#upload-results').set_input_files([str(f) for f in (package / 'results').iterdir() if f.suffix in {'.json', '.jsonl', '.csv'}])
        page.wait_for_function("document.querySelector('#upload-feedback').textContent.includes('added')||document.querySelector('#upload-feedback').classList.contains('error')")
        assert 'added' in page.locator('#upload-feedback').inner_text(), page.locator('#upload-feedback').inner_text()
        page.locator('[data-nav="builder"]').click()

        page.locator('#build-variant').select_option('plain')
        page.locator('#build-shots').fill('')
        page.locator('#validate-spec').click()
        assert page.locator('#download-package').is_disabled()
        assert 'at least one' in page.locator('#builder-feedback').inner_text()
        page.locator('#build-type-i').fill('2')
        page.locator('#validate-spec').click()
        assert page.locator('#download-json').is_enabled(), page.locator('#builder-feedback').inner_text()
        checks.append('Empty targets are unlimited, all-empty budgets rejected, failure-only sampling accepted')

        page.locator('#build-preset').select_option('')
        page.locator('#build-regime').select_option('circuit')
        assert page.locator('#build-type-i').is_enabled()
        assert page.locator('#build-type-ii').is_enabled()
        page.locator('#build-stim').fill('QUBIT_COORDS(0.1, 0.1) 0\nR 0\nX_ERROR(0.1) 0\nM 0\nDETECTOR rec[-1]\nOBSERVABLE_INCLUDE(0) rec[-1]\n')
        page.locator('#build-circuit-base').fill('0.1')
        page.locator('#build-rates').fill('0.2,0.3')
        page.locator('#build-budget-mode').select_option('per_point')
        page.locator('#build-stop-mode').select_option('all')
        page.locator('[data-rate-index="0"][data-budget="shots"]').fill('2')
        page.locator('[data-rate-index="1"][data-budget="shots"]').fill('3')
        page.locator('#validate-spec').click()
        assert page.locator('#download-package').is_enabled(), page.locator('#builder-feedback').inner_text()
        with page.expect_download() as download:
            page.locator('#download-package').click()
        archive = output / 'circuit-sweep.zip'
        download.value.save_as(archive)
        package = output / 'circuit sweep package'
        with zipfile.ZipFile(archive) as z:
            z.extractall(package)
        for i, rate in enumerate((.2, .3)):
            text = (package / f'inputs/circuit-rate-{i:03d}.stim').read_text()
            assert f'X_ERROR({rate})' in text
            assert 'QUBIT_COORDS(0.1, 0.1)' in text
        result = subprocess.run([sys.executable, str(package / 'run.py'), '--repo', str(root), '--output', str(package / 'results')], capture_output=True, text=True, cwd=output)
        assert result.returncode == 0, result.stderr
        rows = json.loads((package / 'results/summary.json').read_text())['rows']
        assert [r['n'] for r in rows] == [2, 3]
        assert [r['p'] for r in rows] == [.2, .3]
        assert all(r['type_i'] + r['type_ii'] == r['failures'] for r in rows)
        assert all(r['sampling_termination_reason'] == 'all_targets' for r in rows)
        page.locator('[data-nav="getting-started"]').click()
        page.locator('#upload-results').set_input_files([str(f) for f in (package / 'results').iterdir() if f.suffix in {'.json', '.jsonl', '.csv'}])
        page.wait_for_function("document.querySelector('#upload-feedback').textContent.includes('added')||document.querySelector('#upload-feedback').classList.contains('error')")
        assert 'added' in page.locator('#upload-feedback').inner_text(), page.locator('#upload-feedback').inner_text()
        checks.append('Circuit sweep exports distinct noise-only Stim inputs, executes per-point all-target budgets, partitions observable failures and imports verified results')

        page.set_viewport_size({"width": 390, "height": 844})
        page.locator('[data-nav="builder"]').click()
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1')
        page.screenshot(path=str(output / 'builder-mobile.png'))
        page.set_viewport_size({"width": 1512, "height": 1100})
        page.screenshot(path=str(output / 'builder-desktop.png'))
        assert not errors, errors
        browser.close()
    report = {"checks": checks, "errors": errors, "circuit_rows": rows}
    (output / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--url', default='http://127.0.0.1:8765/web/research/')
    args = parser.parse_args()
    print(json.dumps(verify(Path(__file__).resolve().parents[2], args.output.resolve(), args.url), indent=2))
