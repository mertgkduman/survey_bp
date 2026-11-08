"""Public summary claims must be bound to deterministic replay, not just hashes."""
from copy import deepcopy
import json
from pathlib import Path
import shutil

import pytest

from bp_registry.runner import run_quaternary, verify_quaternary_run

SOURCE = Path('.planning/spikes/011-execution-consistency/quaternary_experiment_v3-budget-counterexample/input.json')
LOCATIONS = {'output', 'ledger_path', 'manifest_path'}


def fixture(schema):
    if schema == 1:
        return json.loads(Path('data/manifests/quaternary-five-qubit-tracer.json').read_text())
    data = json.loads(SOURCE.read_text())
    data['schema_version'] = f'quaternary_experiment_v{schema}'
    data.pop('numerical_profile', None)
    return data


def write_result(output, result):
    (output / 'result.json').write_text(json.dumps(result))


@pytest.mark.parametrize('field', ['termination', 'outcome', 'numerical_profile', 'run_fidelity'])
def test_audited_summary_counterexamples_are_rejected(field, tmp_path):
    result = run_quaternary(fixture(4), tmp_path)
    result[field] = 'fabricated_claim'
    write_result(tmp_path, result)
    with pytest.raises(ValueError, match='summary.*differs'):
        verify_quaternary_run(tmp_path)
    assert not list(tmp_path.glob('qbp-replay-*'))


@pytest.mark.parametrize('schema', [1, 2, 3, 4])
@pytest.mark.parametrize('operation', ['alter', 'omit'])
def test_every_deterministic_summary_field_is_verified(schema, operation, tmp_path):
    original = run_quaternary(fixture(schema), tmp_path)
    assert verify_quaternary_run(tmp_path)['verified']
    for field in original.keys() - LOCATIONS:
        changed = deepcopy(original)
        if operation == 'omit':
            del changed[field]
        else:
            changed[field] = 'fabricated_claim'
        write_result(tmp_path, changed)
        with pytest.raises(ValueError):
            verify_quaternary_run(tmp_path)
        assert not list(tmp_path.glob('qbp-replay-*'))


@pytest.mark.parametrize('change', ['extra', 'nested', 'type', 'downgrade'])
def test_summary_shape_nested_values_types_and_accounting_are_verified(change, tmp_path):
    result = run_quaternary(fixture(4), tmp_path)
    if change == 'extra':
        result['claimed_source_reproduction'] = True
    elif change == 'nested':
        result['component_fidelity']['kernel'] = 'fabricated_fidelity'
    elif change == 'type':
        result['final_row_count'] = True  # Python equality considers True == 1.
    else:
        del result['work_accounting_version']
    write_result(tmp_path, result)
    with pytest.raises(ValueError):
        verify_quaternary_run(tmp_path)


@pytest.mark.parametrize('schema', [1, 4])
def test_relocated_bundle_verifies_without_trusting_stale_output_paths(schema, tmp_path):
    original = tmp_path / 'original'
    result = run_quaternary(fixture(schema), original)
    copied = tmp_path / 'copy'
    shutil.copytree(original, copied)
    result['manifest_path'] = str(copied / 'manifest.json')
    write_result(copied, result)
    shutil.rmtree(original)
    assert verify_quaternary_run(copied)['verified']
    assert not list(copied.glob('qbp-replay-*'))


@pytest.mark.parametrize('schema', [2, 3])
def test_historical_receipts_still_replay_and_reject_summary_tampering(schema, tmp_path):
    historical = SOURCE.parent.parent / f'quaternary_experiment_v{schema}-budget-counterexample'
    shutil.copytree(historical, tmp_path / 'copy')
    copied = tmp_path / 'copy'
    assert verify_quaternary_run(copied)['verified']
    result = json.loads((copied / 'result.json').read_text())
    result['outcome'] = 'fabricated_claim'
    write_result(copied, result)
    with pytest.raises(ValueError, match='summary.*differs'):
        verify_quaternary_run(copied)
