"""Validate request preparation without sending issues or running simulations."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import zipfile

from playwright.sync_api import sync_playwright

from bp_registry.research.contracts import validate_experiment

ROOT = Path(__file__).resolve().parents[2]


def verify(output, url):
    output.mkdir(parents=True, exist_ok=False)
    checks, errors = [], []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1512, 'height': 1100}, accept_downloads=True)
        page.on('pageerror', lambda e: errors.append(str(e)))
        # Never contact GitHub or submit an issue during verification.
        page.context.route('https://github.com/**', lambda route: route.fulfill(body='Test request draft', content_type='text/plain'))
        page.goto(url + '#builder')
        page.wait_for_function("document.querySelector('#catalog-status').textContent.includes('measured')")
        request = page.get_by_role('button', name='Request experiment results', exact=True)
        assert request.is_disabled()
        assert page.locator('#experiment-request').is_hidden()
        assert request.locator('..').get_by_role('button', name='Download experiment package').count() == 1
        page.locator('#build-code').select_option('bb72')
        page.locator('#build-rates').fill('0.05,0.08')
        page.locator('#validate-spec').click()
        assert request.is_enabled()
        request.click()
        page.wait_for_function("!document.querySelector('#experiment-request').hidden")
        assert request.get_attribute('aria-expanded') == 'true'
        assert page.locator('#request-heading').evaluate('n=>document.activeElement===n')
        href = page.locator('#open-request').get_attribute('href')
        parsed = urlparse(href)
        assert parsed.scheme == 'https' and parsed.netloc == 'github.com'
        assert parsed.path == '/mertgkduman/survey_bp/issues/new'
        query = parse_qs(parsed.query)
        assert query['title'][0].startswith('Experiment results: ')
        assert 'Attach the downloaded file:' in query['body'][0]
        with page.expect_download() as d:
            page.locator('#download-request').click()
        spec_path = output / 'requested-experiment.json'
        d.value.save_as(spec_path)
        content = spec_path.read_bytes()
        spec = json.loads(content)
        assert spec['problem']['code']['kind'] == 'embedded_css'
        assert len(spec['problem']['code']['hx'][0]) == 72
        assert [row['physical_p'] for row in spec['rate_points']] == [.05, .08]
        assert sha256(content).hexdigest() in query['body'][0]
        validate_experiment(spec, repository=ROOT)  # algebra/input validation, no sampling
        with page.expect_popup() as opened:
            page.locator('#open-request').click()
        opened.value.wait_for_load_state()
        assert opened.value.url == href
        opened.value.close()
        assert 'Request prepared' in page.locator('#builder-feedback').inner_text()
        with page.expect_download() as d:
            page.locator('#download-package').click()
        archive = output / 'experiment.zip'
        d.value.save_as(archive)
        with zipfile.ZipFile(archive) as z:
            assert z.read('experiment.json') == content
        checks.append('Validated request action, focused review panel, GitHub draft navigation, exact embedded matrices/hash, and byte-identical package specification')

        # Every subsequent edit/validation invalidates the old draft.
        page.locator('#build-shots').fill('')
        assert request.is_disabled()
        assert page.locator('#experiment-request').is_hidden()
        assert page.locator('#open-request').get_attribute('href') is None
        page.locator('#validate-spec').click()
        assert request.is_disabled()
        assert 'at least one' in page.locator('#builder-feedback').inner_text()
        page.locator('#build-shots').fill('10')
        page.locator('#validate-spec').click()
        assert request.is_enabled()
        # A pending registered-matrix fetch cannot restore an edited request.
        page.evaluate('''()=>{const original=window.fetch;window.holdMatrix=()=>{};window.fetch=(...args)=>String(args[0]).includes('inputs/bb72.json')?new Promise(resolve=>{window.holdMatrix=()=>original(...args).then(resolve);}):original(...args);}''')
        request.click()
        page.locator('#build-seed').fill('123')
        page.evaluate('holdMatrix()')
        page.wait_for_timeout(300)
        assert page.locator('#experiment-request').is_hidden()
        assert request.is_disabled()
        checks.append('Edits and invalid configurations clear/disable requests; delayed matrix materialization cannot resurrect a stale draft')

        page.locator('#build-regime').select_option('circuit')
        stim = '# full custom Stim input\n' + '# retained input detail\n' * 3000 + 'R 0\nX_ERROR(0.1) 0\nM 0\nDETECTOR rec[-1]\nOBSERVABLE_INCLUDE(0) rec[-1]\n'
        page.locator('#build-stim').fill(stim)
        page.locator('#build-circuit-base').fill('0.1')
        page.locator('#build-rates').fill('0.1,0.2')
        page.locator('#validate-spec').click()
        assert request.is_enabled(), page.locator('#builder-feedback').inner_text()
        request.click()
        page.wait_for_function("!document.querySelector('#experiment-request').hidden")
        assert len(page.locator('#open-request').get_attribute('href')) < 3000
        with page.expect_download() as d:
            page.locator('#download-request').click()
        circuit_path = output / 'requested-circuit.json'
        d.value.save_as(circuit_path)
        circuit = json.loads(circuit_path.read_bytes())
        assert circuit['problem']['circuit']['text'] == stim
        assert circuit['sampling']['seed'] == 123
        validate_experiment(circuit, repository=ROOT)
        checks.append('Long custom Stim stays complete in the downloadable specification while the GitHub draft URL stays short')

        page.locator('#custom-spec').evaluate("n=>n.closest('details').open=true")
        page.locator('#custom-spec').fill(json.dumps(spec))
        page.locator('#apply-spec').click()
        assert request.is_enabled()
        request.click()
        page.wait_for_function("!document.querySelector('#experiment-request').hidden")
        with page.expect_download() as d:
            page.locator('#download-request').click()
        exact_path = output / 'requested-exact.json'
        d.value.save_as(exact_path)
        assert json.loads(exact_path.read_bytes()) == spec
        page.locator('#reset-spec').click()
        assert request.is_disabled() and page.locator('#experiment-request').is_hidden()
        checks.append('Exact custom JSON requests preserve every field; return-to-builder reset invalidates the request')

        # Failure to materialize an input reports an error without a usable draft.
        page.locator('#build-code').select_option('a5')
        page.locator('#validate-spec').click()
        page.route('**/inputs/a5.json', lambda route: route.fulfill(status=503, body='Unavailable'))
        request.click()
        page.wait_for_function("document.querySelector('#builder-feedback').className==='error'")
        assert page.locator('#experiment-request').is_hidden()
        assert page.locator('#open-request').get_attribute('href') is None
        page.unroute('**/inputs/a5.json')
        page.set_viewport_size({'width': 390, 'height': 844})
        page.locator('#validate-spec').click()
        request.click()
        page.wait_for_function("!document.querySelector('#experiment-request').hidden")
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        page.screenshot(path=str(output / 'request-mobile.png'))
        checks.append('Input fetch failures leave no stale request link; successful request panel fits mobile width')
        assert not errors, errors
        browser.close()
    report = {'checks': checks, 'errors': errors, 'issues_submitted': 0, 'simulations': 0}
    (output / 'verification.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--url', default='http://127.0.0.1:8876/web/research/')
    args = parser.parse_args()
    print(json.dumps(verify(args.output.resolve(), args.url), indent=2))
