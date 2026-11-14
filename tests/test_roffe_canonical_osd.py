"""Canonical-only BP handoff, optional OSD, audited resume and frozen dispatch."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('_test_canonical_osd_campaign', REPO / 'data/reproductions/roffe-2005-07016-osd/run.py')
campaign = importlib.util.module_from_spec(spec); spec.loader.exec_module(campaign)
execution = campaign.execution
rt = campaign.rt


def test_exact_two_processor_inventory_and_original_paper_configuration():
    plan = campaign.design(); original = rt.load(campaign.ORIGINAL)
    assert len(plan['jobs']) == len({j['id'] for j in plan['jobs']}) == 218
    assert {j['arm'] for j in plan['jobs']} == {'bp_osd0', 'bp_osd_cs10'}
    assert {j['seed'] for j in plan['jobs']} == {2026111413}
    assert all(j['workers'] == 1 and j['target_block_failures'] == 20 and j['max_shots'] == 100000000 for j in plan['jobs'])
    for old in original['jobs']:
        if old['arm'] != 'binary_ms':
            continue
        jobs = [j for j in plan['jobs'] if j['code'] == old['code'] and j['physical_p'] == old['physical_p']]
        assert len(jobs) == 2
        assert {(j['decoder']['postprocessing']['method'], j['decoder']['postprocessing']['order']) for j in jobs} == {('OSD_0', 0), ('OSD_CS', 10)}
        assert all({k: v for k, v in j['decoder'].items() if k != 'postprocessing'} == old['decoder'] for j in jobs)


def test_canonical_bp_candidate_work_and_sample_stream_are_unchanged():
    plan = campaign.design()
    jobs = [deepcopy(next(j for j in plan['jobs'] if j['code'] == 'toric9' and j['physical_p'] == .04 and j['arm'] == arm))
            for arm in ('bp_osd0', 'bp_osd_cs10')]
    for j in jobs:
        j['decoder'].update(max_iterations=5, iterations_per_branch=5)
    states = [execution.state(j) for j in jobs]
    for shot in range(10):
        a, b = [execution.event(s, shot) for s in states]
        old = rt.event(states[0][0], shot)
        assert a['error_sha256'] == b['error_sha256'] == old['error_sha256']
        assert a['syndrome_sha256'] == b['syndrome_sha256'] == old['syndrome_sha256']
        assert a['bp_candidate_sha256'] == b['bp_candidate_sha256'] == old['candidate_sha256']
        assert a['terminal_posterior_sha256'] == b['terminal_posterior_sha256']
        assert a['iterations'] == b['iterations'] == old['iterations']
        assert a['directed_edge_updates'] == old['directed_edge_updates']
        for r in (a, b):
            assert r['outcome'] != 'type_i'
            assert r['osd_invoked'] == (old['outcome'] == 'type_i')


def test_converged_bp_bypasses_osd_even_when_evaluator_reports_logical_failure(monkeypatch):
    job = deepcopy(campaign.design()['jobs'][0]); value = execution.state(job)
    monkeypatch.setattr(rt.parent.base, '_sample', lambda seed, rate, shot, n, **kw: np.zeros(n, dtype=np.uint8))
    monkeypatch.setattr(rt.parent, 'outcome', lambda *args, **kwargs: ('type_ii', None))
    monkeypatch.setattr(value[1], 'decode', lambda *a, **kw: pytest.fail('converged BP cannot invoke OSD based on hidden truth'))
    r = execution.event(value, 0)
    assert r['bp_converged'] and not r['osd_invoked'] and r['outcome'] == 'type_ii'
    assert r['iterations'] == 1 and r['osd_decode_ns'] == 0 and not any(r['osd_work'].values())
    assert r['candidate_sha256'] == r['bp_candidate_sha256']


def test_full_paper_budget_controller_matches_frozen_bp_route_across_codes_and_rates():
    plan = campaign.design()
    for code in plan['codes']:
        for p in (.01, .04, .1):
            job = next(j for j in plan['jobs'] if j['code'] == code and j['physical_p'] == p and j['arm'] == 'bp_osd0')
            value, processor = execution.state(job)
            for shot in (0, 3):
                truth = rt.parent.base._sample(job['seed'], round(p*100000), shot, job['n'], depolarizing=False)
                syndrome = rt.parent.base._syndrome(value[2][1], truth)
                a, _, converged, iterations = execution.decode_bp(value, syndrome)
                b, reference_converged, reference_iterations = rt.decode(value, syndrome)
                assert np.array_equal(a, b) and converged == reference_converged and iterations == reference_iterations


def test_real_two_method_ledgers_resume_exactly_and_reject_tampered_extra_work(tmp_path, monkeypatch):
    plan = campaign.design(); jobs = []
    for arm in ('bp_osd0', 'bp_osd_cs10'):
        j = deepcopy(next(j for j in plan['jobs'] if j['code'] == 'toric9' and j['physical_p'] == .04 and j['arm'] == arm))
        j.update(id='qualification-'+arm, max_shots=8, target_block_failures=20)
        jobs.append(j)
    plan = {**plan, 'jobs': jobs}; (tmp_path / 'plan.json').write_text(json.dumps(plan))
    monkeypatch.setattr(rt, 'load', lambda _: plan)
    for index in range(2):
        a = execution.execute(tmp_path, index)
        assert a['shots'] == 8 and a['osd_calls'] > 0
        path = tmp_path / 'results' / jobs[index]['id'] / 'summary.json'; before = path.read_bytes()
        assert execution.execute(tmp_path, index) == a and path.read_bytes() == before
    receipt = execution.collect(tmp_path, require_complete=True)
    assert len(receipt['points']) == 2
    p = tmp_path / 'results' / jobs[0]['id'] / 'summary.json'; altered = json.loads(p.read_text())
    altered['osd_work']['candidate_evaluations'] += 1; p.write_text(json.dumps(altered))
    with pytest.raises(ValueError, match='terminal summary'):
        execution.collect(tmp_path)


def test_admission_requires_matching_passed_source_qualification(tmp_path, monkeypatch):
    p = tmp_path / 'failed.json'; p.write_text(json.dumps({'status': 'failed'}))
    monkeypatch.setattr(campaign, 'QUALIFICATION', p)
    with pytest.raises(ValueError, match='matching passed'):
        campaign.design()


def test_dispatch_one_cpu_per_point_idempotent_and_complete_audit_dependency(tmp_path, monkeypatch):
    plan = campaign.design(); monkeypatch.setattr(campaign, 'ROOT', tmp_path)
    monkeypatch.setattr(rt, 'load', lambda _: plan); calls = []
    def submit(argv, **kwargs):
        calls.append(argv); return SimpleNamespace(stdout=f'{9000+len(calls)}\n', stderr='')
    monkeypatch.setattr(campaign.subprocess, 'run', submit)
    campaign.submit(); campaign.submit()
    assert len(calls) == 2
    assert '--array=0-217%218' in calls[0] and '--cpus-per-task=1' in calls[0]
    assert '--dependency=afterok:9001' in calls[1] and calls[1][-1].endswith('--collect --complete')
    assert any('OMP_NUM_THREADS=1,OPENBLAS_NUM_THREADS=1,MKL_NUM_THREADS=1' in a for a in calls[0])


def test_incomplete_campaign_and_invalid_channels_do_not_advance(tmp_path, monkeypatch):
    plan = campaign.design(); (tmp_path / 'plan.json').write_text(json.dumps(plan))
    monkeypatch.setattr(rt, 'load', lambda _: plan)
    with pytest.raises(ValueError, match='cannot publish complete'):
        execution.collect(tmp_path, require_complete=True)
    job = deepcopy(plan['jobs'][0]); job['decoder']['noise_model'] = 'depolarizing'
    with pytest.raises(ValueError, match='binary X-only'):
        execution.state(job)
