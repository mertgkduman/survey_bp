"""Independent reconciliation of completed confirmation and per-point selections."""
from collections import Counter, defaultdict
import csv
from hashlib import sha256
import json
import math
from pathlib import Path
import statistics

from scipy.stats import beta

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ROOT = REPO / 'data/reproductions/roffe-2005-07016-runtime-budget'


def sha(path):
    with path.open('rb') as stream:
        return __import__('hashlib').file_digest(stream, 'sha256').hexdigest()


def controls_key(c):
    return (float(c['damping']), c['alpha_mode'], float(c['alpha']), float(c['beta']))


def row_controls(r):
    return (r['damping'], r['alpha_mode'], r['alpha'], r['beta_llr'])


def read_rows():
    with (ROOT / 'iteration-results.csv').open() as stream:
        rows = list(csv.DictReader(stream))
    numeric = ('matched_x_rate', 'physical_p', 'damping', 'alpha', 'beta_llr', 'ler', 'ci95_low', 'ci95_high',
               'mean_iterations', 'mean_directed_edge_updates', 'mean_decoder_seconds', 'mean_reference_seconds', 'runtime_ratio')
    for row in rows:
        for field in numeric: row[field] = float(row[field])
        for field in ('iteration_cap', 'shots', 'logical_failures'): row[field] = int(row[field])
    return rows


def main():
    plan = json.loads((ROOT / 'plan.json').read_text()); plan_sha = sha(ROOT / 'plan.json')
    assert len({plan['protocol'][k] for k in ('tuning_seed', 'finalist_seed', 'confirmation_seed')}) == 3
    for path, digest in plan['implementation_sha256'].items():
        assert sha(REPO / path) == digest, path
    rows = read_rows(); index = {}; monotone = defaultdict(list)
    for row in rows:
        directory = REPO / row['source_directory']
        assert sha(directory / 'summary.json') == row['summary_sha256']
        s = json.loads((directory / 'summary.json').read_text())
        manifest = json.loads((directory / 'manifest.json').read_text()); job = manifest['job']
        assert manifest['campaign_plan_sha256'] == plan_sha
        assert s['manifest_sha256'] == sha(directory / 'manifest.json')
        assert job['stage'] == 'confirmation' and job['seed'] == plan['protocol']['confirmation_seed']
        assert row['iteration_cap'] == job['decoder']['max_iterations'] == job['decoder']['iterations_per_branch']
        assert row_controls(row) == controls_key(job['controls'])
        assert row['family'] == job['decoder']['family'] and row['physical_p'] == job['physical_p']
        assert row['shots'] == s['shots'] and row['logical_failures'] == s['failures']
        assert s['failures'] == s['counts']['type_i']+s['counts']['type_ii'] and sum(s['counts'].values()) == s['shots']
        n, k = row['shots'], row['logical_failures']; target = k == plan['protocol']['target_failures']
        assert target or n == plan['protocol']['max_shots']
        assert row['ler'] == k/n
        low = 0. if k == 0 else float(beta.ppf(.025, k, n-k+1))
        high = 1. if k == n else float(beta.ppf(.975, k if target else k+1, n-k))
        assert (row['ci95_low'], row['ci95_high']) == (low, high)
        assert row['mean_iterations'] == s['iterations']/n
        assert s['directed_edge_updates'] == 2*job['graph_edges']*s['iterations']
        assert row['mean_directed_edge_updates'] == s['directed_edge_updates']/n
        assert row['mean_decoder_seconds'] == s['decode_ns']/n/1e9
        assert row['mean_reference_seconds'] == s['reference_ns']/n/1e9
        assert row['runtime_ratio'] == s['decode_ns']/s['reference_ns']
        assert (row['within_10_percent'] == 'True') == (.9 <= row['runtime_ratio'] <= 1.1)
        key = (row['code'], row['family'], row['matched_x_rate'], row_controls(row), row['iteration_cap'])
        assert key not in index, key
        index[key] = row; monotone[key[:-1]].append(row)
    for key, values in monotone.items():
        ordered = sorted(values, key=lambda r: r['iteration_cap'])
        # With the same physical prefix and first-valid-syndrome stopping,
        # extra sweeps can only repair previously nonconvergent failures.
        assert all(a['ler'] >= b['ler'] for a, b in zip(ordered, ordered[1:])), key

    comparisons, histograms = [], defaultdict(Counter)
    for job in plan['jobs']:
        point = ROOT / 'results' / job['id']; selection_path = point / 'point-plan.json'
        selection = json.loads(selection_path.read_text()); verified = json.loads((point / 'verified.json').read_text())
        assert verified['point_plan_sha256'] == sha(selection_path) and verified['campaign_plan_sha256'] == plan_sha
        assert selection['campaign_plan_sha256'] == plan_sha
        candidates = selection['finalists']; eligible = [c for c in candidates if c['runtime_ratio'] <= 1.1]
        if eligible:
            def criterion(c):
                token = sha256(json.dumps(c['job']['controls'], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
                return (c['failures']/c['shots'], c['iterations']/c['shots'], c['runtime_ratio'], token)
        else:
            def criterion(c): return (c['runtime_ratio'], c['failures']/c['shots'], c['iterations']/c['shots'])
        winner = min(eligible or candidates, key=criterion)
        assert winner == selection['winner']
        assert all(c['job']['seed'] == plan['protocol']['finalist_seed'] for c in candidates)
        prefix = (job['code'], job['decoder']['family'], job['matched_x_rate'])
        previous = selection['baseline_match']; controls = previous['job']['controls']
        def fetch(c, cap): return index[prefix+(controls_key(c), cap)]
        base_n = fetch(controls, job['n']); base_match = fetch(controls, previous['job']['decoder']['max_iterations'])
        tuned_n = fetch(winner['job']['controls'], job['n'])
        tuned_match = fetch(winner['job']['controls'], winner['job']['decoder']['max_iterations'])
        entry = {'code': job['code'], 'n': job['n'], 'family': job['decoder']['family'], 'matched_x_rate': job['matched_x_rate'],
                 'physical_p': job['physical_p'], 'previous_n': base_n, 'previous_matched': base_match,
                 'joint_n': tuned_n, 'joint_matched': tuned_match,
                 'calibration_ratio': winner['runtime_ratio'], 'controls': winner['job']['controls'],
                 'baseline_calibration_ratio': previous['runtime_ratio']}
        comparisons.append(entry)
        family = job['decoder']['family']; c = winner['job']['controls']
        histograms[family+'_damping'][str(c['damping'])] += 1
        histograms[family+'_scaling'][f'{c["alpha_mode"]}:{c["alpha"]}'] += 1
        histograms[family+'_offset'][str(c['beta'])] += 1
    summary = {}
    for family in ('binary_css', 'bp4'):
        selected = [c for c in comparisons if c['family'] == family]
        same_ler = [c for c in selected if c['joint_n']['ler'] == c['previous_n']['ler']]
        extended = [c for c in selected if c['previous_matched']['iteration_cap'] > c['n']]
        reduced = [c for c in selected if c['previous_matched']['iteration_cap'] < c['n']]
        summary[family] = {
            'strata': len(selected), 'baseline_extended_caps': len(extended), 'baseline_reduced_caps': len(reduced),
            'extensions_with_lower_ler': sum(c['previous_matched']['ler'] < c['previous_n']['ler'] for c in extended),
            'same_n_joint_lower_ler': sum(c['joint_n']['ler'] < c['previous_n']['ler'] for c in selected),
            'same_n_joint_equal_ler': sum(c['joint_n']['ler'] == c['previous_n']['ler'] for c in selected),
            'same_n_joint_higher_ler': sum(c['joint_n']['ler'] > c['previous_n']['ler'] for c in selected),
            'joint_matched_lower_ler': sum(c['joint_matched']['ler'] < c['previous_matched']['ler'] for c in selected),
            'median_same_n_ler_ratio': statistics.median(c['joint_n']['ler']/c['previous_n']['ler'] for c in selected),
            'median_same_n_iteration_ratio': statistics.median(c['joint_n']['mean_iterations']/c['previous_n']['mean_iterations'] for c in selected),
            'same_ler_strata': len(same_ler),
            'same_ler_lower_mean_iterations': sum(c['joint_n']['mean_iterations'] < c['previous_n']['mean_iterations'] for c in same_ler),
            'same_ler_median_iteration_ratio': statistics.median(c['joint_n']['mean_iterations']/c['previous_n']['mean_iterations'] for c in same_ler),
            'median_matched_ler_ratio': statistics.median(c['joint_matched']['ler']/c['previous_matched']['ler'] for c in selected),
            'calibrated_within_10_percent': sum(.9 <= c['calibration_ratio'] <= 1.1 for c in selected),
            'confirmed_within_10_percent': sum(.9 <= c['joint_matched']['runtime_ratio'] <= 1.1 for c in selected),
            'confirmed_within_budget_110_percent': sum(c['joint_matched']['runtime_ratio'] <= 1.1 for c in selected),
            'confirmed_runtime_ratio_median': statistics.median(c['joint_matched']['runtime_ratio'] for c in selected),
            'confirmed_runtime_ratio_range': [min(c['joint_matched']['runtime_ratio'] for c in selected), max(c['joint_matched']['runtime_ratio'] for c in selected)],
            'nonzero_offset_selected': sum(c['controls']['beta'] > 0 for c in selected),
            'constant_scaling_selected': sum(c['controls']['alpha_mode'] == 'constant' for c in selected)}
    verified_summary = json.loads((ROOT / 'assessment.json').read_text())
    assert verified_summary['confirmed_shots'] == sum(r['shots'] for r in rows)
    assert verified_summary['confirmed_failures'] == sum(r['logical_failures'] for r in rows)
    assert verified_summary['confirmation_measurements'] == len(rows) and len(comparisons) == 218
    with (ROOT / 'tuning-results.csv').open() as stream:
        training = Counter(r['stage'] for r in csv.DictReader(stream))
    assert sum(training.values()) == verified_summary['tuning_measurements']
    result = {'status': 'passed', 'totals': verified_summary, 'families': summary,
              'selected_controls': {k: dict(v) for k, v in histograms.items()}, 'training_stages': dict(training),
              'claim_limit': 'Descriptive20-failure fresh results; fixed-control extra-cap comparison uses nested shared physical prefixes; different-control estimates do not establish simultaneous superiority. BP X-only and QBP depolarizing1.5p remain separate. Actual timing and calibration are distinct.',
              'at_p_002': [c for c in comparisons if c['matched_x_rate'] == .02],
              'at_p_004': [c for c in comparisons if c['matched_x_rate'] == .04]}
    (HERE / 'assessment.json').write_text(json.dumps(result, indent=2)+'\n')
    (HERE / 'point-comparisons.json').write_text(json.dumps(comparisons, indent=2)+'\n')
    print(json.dumps({'families': summary, 'controls': result['selected_controls'], 'training': dict(training)}, indent=2))


if __name__ == '__main__': main()
