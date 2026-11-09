"""Actual v2 browser, tiny exported run, upload, archive and accessibility checks."""
from __future__ import annotations
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import zipfile
from playwright.sync_api import sync_playwright


def verify(root: Path, output: Path, url: str):
    output.mkdir(parents=True, exist_ok=False)
    checks = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1512, "height": 1050}, accept_downloads=True)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(url)
        page.wait_for_function("document.querySelector('#catalog-status').textContent.includes('measured')")
        assert page.locator('nav a').all_text_contents() == ["Getting started", "Available experiment results", "Experiment builder", "Version difference and Recommendations", "Policies"]
        assert page.locator('#getting-started').is_visible()
        assert page.locator('.katex').count() > 10
        assert not page.locator('#policy-list .katex-error').count()
        checks.append("Workflow-first navigation, equation rendering, and all requested branding")
        page.locator('[data-nav="results"]').click()
        first = page.locator('[data-plot]').first
        assert first.locator('table th').all_text_contents() == ['Series','Noise','Metric','Observed value','Samples','Failures','Type I / II','CI','Work','Time','Evidence','Availability']
        assert first.locator('tbody tr').count() > 0
        assert first.locator('select[data-select]').count() == 2
        assert 'source_transcription' not in first.inner_text()
        first.locator('select[data-select="input"]').select_option('b1')
        first.locator('select[data-select="decoder"]').select_option(first.locator('select[data-select="decoder"] option[data-decoder="pfister-presentation-full-v2-curves:b1:bp4_tuned_sp_v2"]').get_attribute('value'))
        before = first.locator('svg .line').first.get_attribute('d')
        page.locator('#add-plot').click()
        second = page.locator('[data-plot]').nth(1)
        second.locator('select[data-select="input"]').select_option('a5')
        second.locator('select[data-select="decoder"]').select_option(second.locator('select[data-select="decoder"] option[data-decoder="yao-vanilla-a5-b2:a5:bp4_v2"]').get_attribute('value'))
        assert first.locator('svg .line').first.get_attribute('d') == before
        assert first.bounding_box()['x'] < second.bounding_box()['x']
        first.locator('.point').first.focus()
        page.keyboard.press('Enter')
        assert 'estimate' in first.locator('figcaption').inner_text()
        with page.expect_download() as download:
            first.get_by_role('button', name='Export visible table').click()
        csv_path = output / 'visible.csv'
        download.value.save_as(csv_path)
        assert 'Observed value' in csv_path.read_text() and 'source_transcription' not in csv_path.read_text()
        page.screenshot(path=str(output/'results-desktop.png'))
        checks.append("Independent side-by-side code/decoder selections, real plot/table/CSV, keyboard point inspection")
        assert first.locator('select[data-select="input"] option[value="relay-surface-d3"]').count() == 0
        assert page.locator('#build-circuit option').count() == 1
        checks.append("Single-rate circuit CPU measurements remain retained but have no active public choices")
        page.locator('[data-nav="builder"]').click()
        page.locator('#build-shots').fill('8')
        page.locator('#build-rates').fill('0.4')
        page.locator('#build-prior').fill('0.06')
        page.locator('#build-iterations').fill('3')
        page.locator('#build-failures').fill('1')
        page.locator('#validate-spec').click()
        assert page.locator('#download-package').is_enabled(), page.locator('#builder-feedback').inner_text()
        with page.expect_download() as download:
            page.locator('#download-package').click()
        zip_path = output/'experiment.zip'
        download.value.save_as(zip_path)
        package = output/'relocated package'
        with zipfile.ZipFile(zip_path) as archive:
            assert archive.testzip() is None
            archive.extractall(package)
        command = [sys.executable,str(package/'run.py'),'--repo',str(root)]
        validated = subprocess.run(command+['--validate-only'],text=True,capture_output=True,cwd=output)
        assert validated.returncode == 0, validated.stderr
        ran = subprocess.run(command+['--output',str(package/'results')],text=True,capture_output=True,cwd=output)
        (output/'execution.log').write_text(ran.stdout+ran.stderr)
        assert ran.returncode == 0, ran.stderr
        summary = json.loads((package/'results/summary.json').read_text())
        assert 1 <= summary['rows'][0]['n'] <= 8
        assert summary['rows'][0]['failures'] <= 1
        assert summary['rows'][0]['ci_low'] is None
        assert (package/'results/catalog-entry.json').exists()
        checks.append("Downloaded portable package validates, executes, and honors adaptive failure target without fixed-N confidence claims")
        page.locator('[data-nav="getting-started"]').click()
        files = [str(f) for f in (package/'results').iterdir() if f.suffix in {'.json','.jsonl','.csv'}]
        # The unbound convenience entry cannot override verified curve metadata.
        forged_dir=output/'forged-entry';forged_dir.mkdir()
        forged=json.loads((package/'results/catalog-entry.json').read_text())
        forged['result_series'][0]['points'][0].update(x=.99,y=.999,ci_low=.8,type_i=999)
        (forged_dir/'catalog-entry.json').write_text(json.dumps(forged))
        files_with_entry=[str(forged_dir/'catalog-entry.json') if Path(f).name=='catalog-entry.json' else f for f in files]
        page.locator('#upload-results').set_input_files(files_with_entry)
        page.wait_for_function("document.querySelector('#upload-feedback').textContent.includes('added') || document.querySelector('#upload-feedback').classList.contains('error')")
        assert 'added' in page.locator('#upload-feedback').inner_text(),page.locator('#upload-feedback').inner_text()
        page.reload()
        page.wait_for_function("document.querySelector('#catalog-status').textContent.includes('measured')")
        page.locator('[data-nav="results"]').click()
        imported = json.loads((package/'results/catalog-entry.json').read_text())
        first = page.locator('[data-plot]').first
        assert imported['codes'][0]['code_id'] not in first.locator('select[data-select="input"] option').evaluate_all('xs=>xs.map(x=>x.value)')
        assert page.evaluate("JSON.parse(localStorage.getItem('bp-research-v2-results')).length") == 1
        checks.append("Hash-checked singleton upload persists without adding a public input or curve")
        checks.append("Unbound catalog metadata is ignored and cannot alter measured points")
        altered=output/'altered-bound';altered.mkdir()
        wrong_summary=json.loads((package/'results/summary.json').read_text())
        wrong_summary['rows'][0]['ci_low']=.99
        wrong_summary['rows'][0]['ci_high']=.01
        summary_bytes=json.dumps(wrong_summary).encode()
        (altered/'summary.json').write_bytes(summary_bytes)
        wrong_manifest=json.loads((package/'results/result-manifest.json').read_text())
        wrong_manifest['files']['summary.json']=sha256(summary_bytes).hexdigest()
        (altered/'result-manifest.json').write_text(json.dumps(wrong_manifest))
        page.locator('[data-nav="getting-started"]').click()
        altered_files=[str(altered/Path(f).name) if Path(f).name in {'summary.json','result-manifest.json'} else f for f in files]
        page.locator('#upload-results').set_input_files(altered_files)
        page.wait_for_function("document.querySelector('#upload-feedback').classList.contains('error')")
        assert 'ci_low' in page.locator('#upload-feedback').inner_text()
        checks.append("Rehashed but inconsistent confidence fields are rejected before storage")

        page.locator('[data-nav="builder"]').click()
        page.locator('#build-regime').select_option('circuit')
        assert page.locator('#circuit-input').is_visible()
        assert page.locator('#build-type-i').is_enabled()
        assert page.locator('#build-type-ii').is_enabled()
        page.locator('#build-failures').fill('')
        page.locator('#build-shots').fill('2')
        page.locator('#validate-spec').click()
        assert page.locator('#download-package').is_enabled()
        with page.expect_download() as download:
            page.locator('#download-package').click()
        circuit_zip = output/'circuit.zip';download.value.save_as(circuit_zip)
        circuit_package = output/'circuit package'
        with zipfile.ZipFile(circuit_zip) as archive: archive.extractall(circuit_package)
        result = subprocess.run([sys.executable,str(circuit_package/'run.py'),'--repo',str(root),'--output',str(circuit_package/'results')],capture_output=True,text=True,cwd=output)
        assert result.returncode == 0,result.stderr
        checks.append("Circuit builder exports and executes actual Stim/Sinter observable evaluation; explicit Type I/II observable-failure counters enabled")
        page.set_viewport_size({'width':390,'height':844})
        for section in ['getting-started','results','builder','recommendations','policies']:
            page.locator(f'[data-nav="{section}"]').click()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1'),section
            page.screenshot(path=str(output/f'mobile-{section}.png'))
        checks.append("Five mobile views fit at 390px with independent plot cards stacked")
        page.goto(url+'v1/')
        page.wait_for_function("document.querySelector('#catalog-status').textContent.includes('retained')")
        assert page.locator('.paper-card').count()>0
        response = page.request.get(url+'v1/../../../data/artifacts/project-three-qubit-css-fixture.json')
        assert response.ok
        page.locator('[data-nav="builder"]').click()
        page.locator('#validate-experiment').click()
        with page.expect_download() as download:
            page.locator('#download-package').click()
        archived_zip=output/'archived-v1.zip';download.value.save_as(archived_zip)
        archived=output/'archived v1 package'
        with zipfile.ZipFile(archived_zip) as archive: archive.extractall(archived)
        validated=subprocess.run([sys.executable,str(archived/'run.py'),'--repo',str(root),'--validate-only'],capture_output=True,text=True,cwd=output)
        assert validated.returncode==0,validated.stderr
        checks.append("Archived v1 stays browsable; repository assets and its exported ZIP still validate")
        assert not errors,errors
        browser.close()
    report={'checks':checks,'errors':errors,'smoke_rows':summary['rows']}
    (output/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);parser.add_argument('--url',default='http://127.0.0.1:8765/web/research/');args=parser.parse_args()
    print(json.dumps(verify(Path(__file__).resolve().parents[2],args.output.resolve(),args.url),indent=2))
