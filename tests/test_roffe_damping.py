"""Paper-budget min-sum damping, honest tuning, fresh confirmation and dispatch."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('_test_roffe_damping', REPO / 'data/reproductions/roffe-2005-07016-damping/run.py')
tune = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tune)
rt = tune.rt


def test_training_preserves_all_paper_grids_budgets_and_immutable_original():
    original = rt.load(tune.ORIGINAL)
    plan = tune.design()
    assert rt.sha(tune.ORIGINAL / 'plan.json') == 'eb16126dfa9eef45bb24eeddd70c5b287259e376b52a1531efcbf6126da9dcc3'
    assert len(plan['jobs']) == len({j['id'] for j in plan['jobs']}) == 1526
    assert sum(j['max_shots'] for j in plan['jobs']) == 1562624
    assert {j['seed'] for j in plan['jobs']} == {tune.TUNING_SEED}
    assert tune.TUNING_SEED != tune.CONFIRMATION_SEED != original['jobs'][0]['seed']
    for old in original['jobs']:
        jobs = [j for j in plan['jobs'] if j['code'] == old['code'] and j['base_arm'] == old['arm'] and j['physical_p'] == old['physical_p']]
        assert {j['decoder']['v2c_damping'] for j in jobs} == set(tune.DAMPING)
        for job in jobs:
            assert {**job['decoder'], 'v2c_damping': 0.} == old['decoder']
            assert job['decoder']['max_iterations'] == plan['codes'][job['code']]['n']
            assert job['workers'] == 1 and job['max_shots'] == 1024 < job['target_block_failures']
            assert job['source_target'] is None


@pytest.mark.parametrize('family', ['binary_ms', 'qbp_ms'])
def test_minsum_damping_is_old_v2c_weight_and_physical_samples_are_paired(family):
    a = deepcopy(next(j for j in tune.design()['jobs'] if j['code'] == 'toric9' and j['base_arm'] == family and j['decoder']['v2c_damping'] == 0.))
    a['decoder'].update(max_iterations=5, iterations_per_branch=5)
    b = deepcopy(a)
    b['decoder']['v2c_damping'] = .5
    va, vb = rt.state(a), rt.state(b)
    ra, rb = rt.event(va, 7), rt.event(vb, 7)
    assert ra['error_sha256'] == rb['error_sha256']
    assert ra['syndrome_sha256'] == rb['syndrome_sha256']
    for g0, g5 in zip(va[3], vb[3], strict=True):
        syndrome = np.ones(len(g0.row_ptr)-1, dtype=np.uint8)
        if family == 'qbp_ms':
            old = g0.initial_v2c()
            fresh = g0.sweep(old, syndrome).v2c
            damped = g5.sweep(old, syndrome).v2c
        else:
            p = a['physical_p']
            old = np.full(g0.table.edge_count, np.log((1-p)/p))
            fresh = g0.sweep(old, syndrome, error_rate=p).new_v2c
            damped = g5.sweep(old, syndrome, error_rate=p).new_v2c
        assert np.allclose(damped, .5*old + .5*fresh)
    for job, event in ((a, ra), (b, rb)):
        assert event['directed_edge_updates'] == 2*job['graph_edges']*event['iterations']
        assert event['iterations'] <= 5


def rows_fixture(monkeypatch):
    plan = tune.design()
    monkeypatch.setattr(tune, 'TUNING_SHOTS', 8)
    rows = [{**j, 'iterations': (80 if j['decoder']['v2c_damping'] == 0 else 8)} for j in plan['jobs']]
    def events(root, row):
        failures = 2 if row['decoder']['v2c_damping'] == 0. else 4
        return [{'outcome': 'type_i' if i < failures else 'exact_success',
                 'error_sha256': f'{row["matched_x_rate"]}:{i}'} for i in range(8)]
    monkeypatch.setattr(tune, 'read_events', events)
    return plan, rows, events


def test_dynamic_grid_selection_prioritizes_ler_over_speed(monkeypatch, tmp_path):
    plan, rows, _ = rows_fixture(monkeypatch)
    selected, tail = tune.select_rows(plan, rows, tmp_path)
    assert len(selected) == 8 and {e['damping'] for e in selected} == {0.}
    assert {e['code']: len(e['rates']) for e in selected} == {'toric9': 25, 'toric11': 28, 'toric13': 28, 'toric15': 28}
    assert tail == .05/(2*7*6*218)
    assert all(e['mean_ler'] == .25 for e in selected)


def test_selection_rejects_unpaired_samples_and_missing_source_rates(monkeypatch, tmp_path):
    plan, rows, events = rows_fixture(monkeypatch)
    def unpaired(root, row):
        batch = events(root, row)
        if row['decoder']['v2c_damping'] == .1:
            batch[0]['error_sha256'] = 'wrong-sample'
        return batch
    monkeypatch.setattr(tune, 'read_events', unpaired)
    with pytest.raises(ValueError, match='identical physical samples'):
        tune.select_rows(plan, rows, tmp_path)
    monkeypatch.setattr(tune, 'read_events', events)
    with pytest.raises(ValueError, match='exact source rate grid'):
        tune.select_rows(plan, rows[1:], tmp_path)


@pytest.mark.parametrize('damping,points', [(0., 218), (.5, 436)])
def test_confirmation_is_fresh_capped_has_controls_and_deduplicates(damping, points):
    plan = tune.design()
    entries = [{'code': code, 'base_arm': family, 'damping': damping}
               for code in plan['codes'] for family in ('binary_ms', 'qbp_ms')]
    confirmed = tune.confirmation_design(plan, {'selected': entries}, 'a'*64)
    assert len(confirmed['jobs']) == len({j['id'] for j in confirmed['jobs']}) == points
    for job in confirmed['jobs']:
        assert job['seed'] == tune.CONFIRMATION_SEED != tune.TUNING_SEED
        assert job['target_block_failures'] == 20 and job['max_shots'] == 100000000
        assert job['workers'] == 1
        assert job['decoder']['max_iterations'] == plan['codes'][job['code']]['n']
        assert job['selection_sha256'] == 'a'*64
    assert {j['role'] for j in confirmed['jobs']} == ({'selected'} if damping == 0. else {'selected', 'baseline'})
    with pytest.raises(ValueError, match='cover every'):
        tune.confirmation_design(plan, {'selected': entries[:-1]}, 'a'*64)
    entries[0]['damping'] = .9
    with pytest.raises(ValueError, match='unmeasured'):
        tune.confirmation_design(plan, {'selected': entries}, 'a'*64)


def dispatch_setup(monkeypatch, tmp_path):
    plan = tune.design()
    (tmp_path / 'confirmation').mkdir()
    monkeypatch.setattr(tune, 'ROOT', tmp_path)
    monkeypatch.setattr(rt, 'load', lambda root: plan)
    return plan


def test_one_cpu_dispatch_is_bounded_idempotent_and_gated(monkeypatch, tmp_path):
    dispatch_setup(monkeypatch, tmp_path)
    calls = []
    def queue(argv, **kwargs):
        calls.append(argv)
        return SimpleNamespace(stdout=f'{9000+len(calls)}\n', stderr='')
    monkeypatch.setattr(tune.subprocess, 'run', queue)
    tune.submit()
    tune.submit()
    assert len(calls) == 2
    assert '--array=0-1525%392' in calls[0] and '--cpus-per-task=1' in calls[0]
    assert '--mem=2G' in calls[0] and 392+6 <= 400
    assert '--dependency=afterok:9001' in calls[1]
    assert calls[1][-1].endswith('--stage tuning --advance')
    assert any('OMP_NUM_THREADS=1,OPENBLAS_NUM_THREADS=1,MKL_NUM_THREADS=1' in c for c in calls[0])


def test_partial_dispatch_repairs_continuation_without_duplicate_array(monkeypatch, tmp_path):
    dispatch_setup(monkeypatch, tmp_path)
    calls = []
    def queue(argv, **kwargs):
        calls.append(argv)
        if len(calls) == 2:
            raise RuntimeError('controller submission failed')
        return SimpleNamespace(stdout=f'{9000+len(calls)}\n', stderr='')
    monkeypatch.setattr(tune.subprocess, 'run', queue)
    with pytest.raises(RuntimeError):
        tune.submit()
    tune.submit()
    assert len(calls) == 3
    assert sum(any(x.startswith('--array=') for x in c) for c in calls) == 1


def test_preflight_never_submits_continuation_or_writes_receipt(monkeypatch, tmp_path):
    dispatch_setup(monkeypatch, tmp_path)
    calls = []
    monkeypatch.setattr(tune.subprocess, 'run', lambda argv, **kwargs: (calls.append(argv) or SimpleNamespace(stdout='', stderr='accepted')))
    tune.submit(test_only=True)
    assert len(calls) == 1 and '--test-only' in calls[0]
    assert not (tmp_path / 'dispatch.json').exists()


def test_training_never_registered_and_empty_confirmation_is_supported():
    sources = json.loads((REPO / 'research/catalog/sources.json').read_text())
    assert 'data/reproductions/roffe-2005-07016-damping/confirmation/catalog.json' in sources['normalized_catalogs']
    assert 'data/reproductions/roffe-2005-07016-damping/catalog.json' not in sources['normalized_catalogs']
