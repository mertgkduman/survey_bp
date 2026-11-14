"""Joint canonical controls, runtime brackets, independent cap cohorts and audits."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / 'data/reproductions/roffe-2005-07016-runtime-budget'
spec = importlib.util.spec_from_file_location('_test_runtime_budget_driver', ROOT / 'run.py')
campaign = importlib.util.module_from_spec(spec); spec.loader.exec_module(campaign)
r, rt = campaign.execution, campaign.rt


def original(family='binary_ms', p=.04):
    return next(j for j in rt.load(r.ORIGINAL)['jobs'] if j['code'] == 'toric9' and j['arm'] == family and j['matched_x_rate'] == p)


def test_joint_inventory_and_qualified_frozen_protocol():
    plan = campaign.design()
    assert len(plan['jobs']) == 218 and len(r.coarse_grid()) == 80
    assert len({r.identity(c) for c in r.coarse_grid()}) == 80
    assert r.baseline(original()) in r.coarse_grid() and r.baseline(original('qbp_ms')) in r.coarse_grid()
    assert r.TUNING_SEED != r.CONFIRMATION_SEED
    assert plan['protocol']['coarse_controls'] == r.coarse_grid()
    assert all(j['workers'] == 1 and j['n'] in (162, 242, 338, 450) for j in plan['jobs'])
    proof = json.loads(campaign.QUALIFICATION.read_text())
    assert proof['status'] == 'passed' and proof['exact_terminal_comparisons'] == 144
    assert proof['stopping_cases']['converged'] and proof['stopping_cases']['capped']
    for c in r.neighbors({'damping': .95, 'alpha_mode': 'constant', 'alpha': 1., 'beta': 0.}):
        assert 0 <= c['damping'] <= .95 and 0 < c['alpha'] <= 1 and 0 <= c['beta'] <= 1.5


def test_all_three_controls_reach_canonical_sweep_operands():
    base = rt.state(original())
    policy = base[3][0].policy
    values = r.engine.coefficients(policy, {'damping': .3, 'alpha_mode': 'paper', 'alpha': .75, 'beta': .25})
    np.testing.assert_array_equal(values[0], [.3, .7, .375, .25])
    np.testing.assert_array_equal(values[1], [.3, .7, .5625, .25])
    fixed = r.engine.coefficients(policy, {'damping': .5, 'alpha_mode': 'constant', 'alpha': .75, 'beta': .5})
    np.testing.assert_array_equal(fixed, [[.5, .5, .75, .5]])


@pytest.mark.parametrize('family', ['binary_ms', 'qbp_ms'])
@pytest.mark.parametrize('mode', ['constant', 'paper'])
def test_terminal_beliefs_candidates_and_stopping_are_exact_canonical(family, mode):
    job = original(family, .08); base = rt.state(job)
    c = {'damping': .3, 'alpha_mode': mode, 'alpha': .75, 'beta': .25}
    prepared = r.engine.Prepared(base, c)
    for shot in (0, 1, 7):
        _, syndrome = r.sample(base, r.TUNING_SEED, shot)
        a, b = prepared.decode(syndrome, 9), prepared.public_reference(syndrome, 9)
        assert all(np.array_equal(x, y) for x, y in zip(a, b))
    result = prepared.decode(np.zeros(len(prepared.graph.row_ptr)-1, dtype=np.uint8), 9)
    assert result[2] and result[3] == 1 and not result[0].flags.writeable
    with pytest.raises(ValueError, match='positive integer'):
        prepared.decode(np.zeros(len(prepared.graph.row_ptr)-1, dtype=np.uint8), 0)


def fake(cap, ratio, failures=2, iterations=None, controls=None):
    return {'job': {'decoder': {'max_iterations': cap}, 'controls': controls or {'a': 1}},
            'runtime_ratio': ratio, 'failures': failures, 'shots': 100,
            'iterations': cap*100 if iterations is None else iterations, 'nonconverged': 10}


def protocol():
    return {'runtime_tolerance': .1, 'max_cap_factor': 256, 'cap_refinements': 4}


def test_doubling_and_integer_refinement_retain_every_budget_point():
    best, history = r.search_caps(100, lambda cap: fake(cap, cap/300), protocol())
    assert best['job']['decoder']['max_iterations'] == 300 and best['runtime_ratio'] == 1
    assert {100, 200, 400, 300} <= {v['job']['decoder']['max_iterations'] for v in history}


def test_already_over_budget_and_unattainable_or_guard_limited_matches_are_honest():
    best, history = r.search_caps(80, lambda cap: fake(cap, cap/20), protocol())
    assert best['job']['decoder']['max_iterations'] == 20
    assert any(v['job']['decoder']['max_iterations'] == 80 and v['runtime_ratio'] == 4 for v in history)
    best, history = r.search_caps(100, lambda cap: {**fake(cap, .1), 'nonconverged': 0}, protocol())
    assert len(history) == 1 and best['runtime_ratio'] == .1
    best, history = r.search_caps(100, lambda cap: fake(cap, 2+cap), protocol())
    assert best['job']['decoder']['max_iterations'] == 1 and best['runtime_ratio'] > 1.1
    p = {**protocol(), 'max_cap_factor': 2}
    best, history = r.search_caps(100, lambda cap: fake(cap, cap/10000), p)
    assert max(v['job']['decoder']['max_iterations'] for v in history) == 200 and best['runtime_ratio'] < .9


def test_selection_prioritizes_ler_then_iterations_and_excludes_over_budget():
    a, b, bad = fake(100, .95, 4, 10), fake(200, 1.02, 3, 50), fake(500, 2, 0, 1)
    assert r.choose([a, b, bad], .1) is b
    b['failures'] = 4
    assert r.choose([a, b, bad], .1) is a
    a['runtime_ratio'] = 1.5; b['runtime_ratio'] = 1.3
    assert r.choose([a, b, bad], .1) is b


def test_confirmation_caps_keep_old_damping_and_joint_settings_separate():
    j = {**original(), 'n': 162}
    a = fake(486, 1, controls=r.baseline(j))
    b = fake(324, 1, controls={'damping': .7, 'alpha_mode': 'constant', 'alpha': .75, 'beta': .25})
    entries = r.confirmation_specs(j, a, b, [])
    assert {162, 324, 486, 648} <= {e['cap'] for e in entries if e['controls'] == a['job']['controls']}
    assert all(e['roles'] in (['previous_damping'], ['joint_selected']) for e in entries)
    assert len(r.confirmation_specs(j, a, a, [])) == 4


def test_compiled_cache_reloads_in_another_process(tmp_path):
    script = '''import importlib.util,numpy as np
from pathlib import Path
p=Path('data/reproductions/roffe-2005-07016-runtime-budget/runtime.py')
s=importlib.util.spec_from_file_location('_cache_runtime_test',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
j=next(j for j in m.rt.load(m.ORIGINAL)['jobs'] if j['code']=='toric9' and j['arm']=='qbp_ms')
b=m.rt.state(j);p=m.engine.Prepared(b,m.baseline(j));s=np.zeros(len(p.graph.row_ptr)-1,dtype=np.uint8)
assert p.decode(s,4)[3]==1
'''
    import os
    env = {**os.environ, 'NUMBA_CACHE_DIR': str(tmp_path / 'cache'), 'PYTHONPATH': str(REPO / 'src')}
    for _ in range(2):
        subprocess.run([sys.executable, '-c', script], cwd=REPO, env=env, check=True, capture_output=True, text=True)


def test_real_small_pipeline_resume_full_audit_and_exact_policy_catalog(monkeypatch):
    with tempfile.TemporaryDirectory(prefix='runtime-budget-test-', dir=REPO / '.git') as directory:
        root = Path(directory); plan = campaign.design()
        jobs = [j for j in plan['jobs'] if j['code'] == 'toric9' and j['arm'] == 'binary_ms' and j['matched_x_rate'] in (.04, .05)]
        plan['jobs'] = jobs; p = plan['protocol']
        p.update(reference_shots=4, reference_repeats=1, tuning_shots=4, refine_candidates=0, finalist_shots=4, finalist_candidates=1,
                 max_cap_factor=1, cap_refinements=0, max_shots=8, target_failures=20,
                 coarse_controls=[r.baseline(jobs[0])])
        rt.freeze(root, plan, campaign.extra())
        for i in range(2):
            receipt = r.execute(root, i)
            assert receipt['points'] and all(row['shots'] == 8 for row in receipt['points'])
            point = root / 'results' / jobs[i]['id']; before = (point / 'point-plan.json').read_bytes()
            assert r.execute(root, i) == receipt
            assert (point / 'point-plan.json').read_bytes() == before
            for row in receipt['points']:
                assert row['job']['seed'] == r.CONFIRMATION_SEED
                assert row['job']['controls'] == r.baseline(jobs[i])
            selection = json.loads((point / 'point-plan.json').read_text())
            assert {row['job']['seed'] for row in selection['history']} == {r.TUNING_SEED, r.VALIDATION_SEED}
        complete = campaign.collect(root, complete=True)
        assert len(complete['finished_strata']) == 2
        report = r.module('_runtime_report_test', ROOT / 'report.py'); assessment = report.report(root)
        assert assessment['confirmed_shots'] == sum(v['shots'] for v in complete['points'])
        extension = json.loads((root / 'catalog.json').read_text())
        assert all(len({p['x'] for p in s['points']}) == len(s['points']) for s in extension['result_series'])
        assert all('execution_backend' in d['configuration']['effective_configuration'] for d in extension['decoders'])
        row = complete['points'][0]; path = rt.REPO / row['directory'] / 'summary.json'
        altered = json.loads(path.read_text()); altered['iterations'] += 1; path.write_text(json.dumps(altered))
        with pytest.raises(ValueError, match='audit mismatch'):
            campaign.collect(root)


def test_dispatch_is_one_cpu_per_point_idempotent_and_dependency_complete(tmp_path, monkeypatch):
    plan = campaign.design(); monkeypatch.setattr(campaign, 'ROOT', tmp_path)
    monkeypatch.setattr(rt, 'load', lambda _: plan); calls = []
    def submit(argv, **kw):
        calls.append(argv); return SimpleNamespace(stdout=f'{9900+len(calls)}\n', stderr='')
    monkeypatch.setattr(campaign.subprocess, 'run', submit)
    campaign.submit(); campaign.submit()
    assert len(calls) == 2 and '--cpus-per-task=1' in calls[0] and '--array=0-217%218' in calls[0]
    assert '--dependency=afterok:9901' in calls[1] and calls[1][-1].endswith('--collect --complete')
    assert 'NUMBA_CACHE_DIR' in calls[0][-1]
