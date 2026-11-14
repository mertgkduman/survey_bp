"""Versioned compiled traversal retains canonical terminal-state semantics."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, REPO / path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


campaign = module('_test_fast_osd_campaign', 'data/reproductions/roffe-2005-07016-osd-fast/run.py')
slow = module('_test_scalar_osd_campaign', 'data/reproductions/roffe-2005-07016-osd/run.py')
fast = campaign.execution


def test_qualified_version_has_all_paper_points_and_separate_execution_identity():
    plan, baseline = campaign.design(), slow.design()
    assert len(plan['jobs']) == 218
    assert plan['study_id'] != baseline['study_id']
    assert {j['decoder']['execution_backend'] for j in plan['jobs']} == {fast.BP_VERSION}
    for a, b in zip(plan['jobs'], baseline['jobs'], strict=True):
        a = deepcopy(a); del a['decoder']['execution_backend']
        assert a == b
    proof = json.loads(campaign.BP_QUALIFICATION.read_text())
    assert proof['exact_terminal_state_comparisons'] == 436 and proof['complete_event_comparisons'] == 192
    assert not proof['failures'] and proof['stopping']['True'] > 0 and proof['stopping']['False'] > 0


@pytest.mark.parametrize('arm', ['bp_osd0', 'bp_osd_cs10'])
def test_compiled_events_preserve_all_non_timing_fields_and_do_not_patch_scalar_runtime(arm):
    job = next(j for j in campaign.design()['jobs'] if j['code'] == 'toric9' and j['physical_p'] == .04 and j['arm'] == arm)
    a, b = fast.state(job), slow.execution.state(job)
    assert slow.execution.decode_bp is not fast.decode_bp
    for shot in range(8):
        x, y = fast.event(a, shot), slow.execution.event(b, shot)
        assert {k: v for k, v in x.items() if k not in slow.execution.TIMING_FIELDS} == {k: v for k, v in y.items() if k not in slow.execution.TIMING_FIELDS}
    candidate, posterior, converged, iterations = fast.decode_bp(a[0], np.zeros(job['n']//2, dtype=np.uint8))
    assert converged and iterations == 1 and not candidate.flags.writeable and not posterior.flags.writeable
    with pytest.raises(ValueError, match='syndrome'):
        fast.decode_bp(a[0], np.array([2], dtype=np.uint8))


def test_fast_complete_ledger_resume_and_endpoint_replay(tmp_path, monkeypatch):
    plan = campaign.design(); jobs = []
    for arm in ('bp_osd0', 'bp_osd_cs10'):
        job = deepcopy(next(j for j in plan['jobs'] if j['code'] == 'toric9' and j['physical_p'] == .04 and j['arm'] == arm))
        job.update(max_shots=8, target_block_failures=20); jobs.append(job)
    plan = {**plan, 'jobs': jobs}; (tmp_path / 'plan.json').write_text(json.dumps(plan))
    monkeypatch.setattr(fast.rt, 'load', lambda _: plan)
    for index in range(2):
        first = fast.execute(tmp_path, index)
        assert first['shots'] == 8 and first['osd_calls'] > 0
        assert fast.execute(tmp_path, index) == first
    assert len(fast.collect(tmp_path, require_complete=True)['points']) == 2


def test_unsupported_policy_and_unqualified_controller_cannot_be_submitted(tmp_path, monkeypatch):
    job = deepcopy(campaign.design()['jobs'][0]); job['decoder']['v2c_damping'] = .5
    with pytest.raises(ValueError, match='undamped binary'):
        fast.state(job)
    path = tmp_path / 'bad.json'; path.write_text(json.dumps({'status': 'failed'}))
    monkeypatch.setattr(campaign, 'BP_QUALIFICATION', path)
    with pytest.raises(ValueError, match='matching qualification'):
        campaign.design()


def test_storage_guard_preserves_checkpoint_before_chunk_write(tmp_path, monkeypatch):
    job = campaign.design()['jobs'][0]
    ledger = fast.Ledger(tmp_path, job)
    monkeypatch.setattr(fast.os, 'statvfs', lambda _: SimpleNamespace(f_bavail=1, f_frsize=4096))
    with pytest.raises(RuntimeError, match='preserve checkpoint'):
        ledger.commit([])
    assert not list(tmp_path.glob('*.gz')) and ledger.shots == 0
