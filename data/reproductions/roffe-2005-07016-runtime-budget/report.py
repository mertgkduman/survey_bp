"""Publish exact-policy confirmation and complete per-point iteration tables."""
from collections import defaultdict
import csv
from hashlib import sha256
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bp_study_runtime as rt


def write_csv(path, rows):
    if rows:
        with path.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
            writer.writeheader(); writer.writerows(rows)


def flat(row):
    j = row['job']; c = j['controls']; n = row['shots']
    return {'code': j['code'], 'family': j['decoder']['family'], 'channel': j['decoder']['noise_model'],
            'matched_x_rate': j['matched_x_rate'], 'physical_p': j['physical_p'],
            'iteration_cap': j['decoder']['max_iterations'], 'damping': c['damping'],
            'alpha_mode': c['alpha_mode'], 'alpha': c['alpha'], 'beta_llr': c['beta'],
            'stage': j['stage'], 'roles': ','.join(row.get('roles', [])), 'shots': n,
            'logical_failures': row['failures'], 'ler': row['rate'], 'ci95_low': row['ci95_low'], 'ci95_high': row['ci95_high'],
            'mean_iterations': row['iterations']/n, 'mean_directed_edge_updates': row['directed_edge_updates']/n,
            'mean_decoder_seconds': row['decode_ns']/n/1e9, 'mean_reference_seconds': row['reference_ns']/n/1e9,
            'runtime_ratio': row['runtime_ratio'], 'within_10_percent': .9 <= row['runtime_ratio'] <= 1.1,
            'within_budget_110_percent': row['runtime_ratio'] <= 1.1,
            'summary_sha256': row['summary_sha256'], 'source_directory': row['directory']}


def report(root):
    plan = rt.load(root); receipt = json.loads((root / 'verified.json').read_text())
    if receipt['plan_sha256'] != rt.sha(root / 'plan.json'): raise ValueError('report requires matching independent audit')
    rows = [flat(r) for r in receipt['points']]; tuning = [flat(r) for r in receipt['tuning']]
    write_csv(root / 'iteration-results.csv', rows); write_csv(root / 'tuning-results.csv', tuning)
    lines = ['# Roffe: joint numerical tuning and runtime-matched iteration sweeps', '',
             f'Independent audit: {len(receipt["finished_strata"])}/{receipt["planned_strata"]} completed point workers; {len(rows)} confirmed control/cap measurements and {len(tuning)} retained training measurements.', '',
             'Target: same-CPU mean warmed canonical BP+OSD0 decoder time per shot at original T=n. Candidate timing excludes sampling, truth evaluation, JIT and I/O. Actual time/reference ratios are shown; within10% is a calibration tolerance, not assumed equality. Values above1.1 exceed the budget. Values below.9 can indicate early-convergence saturation, calibration drift or a still-lower cap; inspect each point plan/history.', '',
             'Training jointly searches old-V2C damping, constant or paper-scheduled min-sum scaling, and offset in natural-LLR units. Only fresh confirmation is in the main table. All tuning settings/caps are retained in tuning-results.csv. Different iteration caps/settings are explicit, and no unlike policies are pooled. Binary BP is X-only; joint Q-BP remains depolarizing at1.5p_X.', '',
             '| Code | Decoder/noise | Matched p_X | Physical p | T | d | Scaling | Offset | LER | 95% interval | Mean sweeps | Time / OSD0 | Role |',
             '| --- | --- | ---: | ---: | ---: | ---: | --- | ---: | ---: | --- | ---: | ---: | --- |']
    for r in sorted(rows, key=lambda r: (plan['codes'][r['code']]['n'], r['matched_x_rate'], r['family'], r['roles'], r['iteration_cap'])):
        scale = f'{r["alpha"]:g}×(1−2⁻ᵗ)' if r['alpha_mode'] == 'paper' else f'constant {r["alpha"]:g}'
        ler = f'≤ {r["ci95_high"]:.5g}' if r['logical_failures'] == 0 else f'{r["ler"]:.5g}'
        lines.append(f'| {r["code"]} | {r["family"]}/{r["channel"]} | {r["matched_x_rate"]:g} | {r["physical_p"]:g} | {r["iteration_cap"]} | {r["damping"]:g} | {scale} | {r["beta_llr"]:g} | {ler} | [{r["ci95_low"]:.4g}, {r["ci95_high"]:.4g}] | {r["mean_iterations"]:.4g} | {r["runtime_ratio"]:.4g} | {r["roles"]} |')
    lines += ['', 'Missing point workers remain pending; their calibrated plans and raw progress are retained under results/. A zero-failure completed point is displayed as an upper bound. All20-failure/1e8-shot intervals respect the stopping rule. Timing cohorts and confirmation uncertainty are different quantities; the table does not assert simultaneous superiority or a same-channel comparison between BP and Q-BP.']
    (root / 'RESULTS.md').write_text('\n'.join(lines).rstrip()+'\n')
    publish(root, plan, receipt)
    assessment = {'schema': 'runtime-budget-assessment-v1', 'finished_strata': len(receipt['finished_strata']),
                  'planned_strata': receipt['planned_strata'], 'confirmation_measurements': len(rows),
                  'tuning_measurements': len(tuning), 'confirmed_shots': sum(r['shots'] for r in rows),
                  'confirmed_failures': sum(r['logical_failures'] for r in rows)}
    rt.write_json(root / 'assessment.json', assessment)
    return assessment


def publish(root, plan, receipt):
    relative = root.relative_to(rt.REPO).as_posix(); dataset = plan['study_id']
    groups = defaultdict(list)
    for row in receipt['points']:
        j = row['job']; configuration = json.dumps(j['decoder'], sort_keys=True)
        groups[j['code'], configuration].append(row)
    decoders, series = [], []
    for (code, encoded), rows in sorted(groups.items()):
        config = json.loads(encoded); token = sha256(encoded.encode()).hexdigest()[:16]
        identifier = f'{dataset}:{code}:{token}'
        label = f'{"Q-BP" if config["family"] == "bp4" else "BP"}, MS, d={config["v2c_damping"]:g}, alpha={config["alpha"]:g}, beta={config["beta"]:g}, T={config["max_iterations"]}'
        points = []
        for row in sorted(rows, key=lambda r: r['job']['physical_p']):
            j, n = row['job'], row['shots']
            points.append({'x': j['physical_p'], 'y': row['rate'], 'n': n, 'failures': row['failures'],
                           'ci_low': row['ci95_low'], 'ci_high': row['ci95_high'],
                           'status': 'upper_bound' if row['failures'] == 0 else 'complete',
                           'mean_iterations': row['iterations']/n, 'iteration_unit': 'BP sweeps',
                           'mean_directed_edge_updates': row['directed_edge_updates']/n,
                           'mean_work': row['iterations']/n, 'work_unit': 'iterations',
                           'mean_seconds': row['decode_ns']/n/1e9,
                           'runtime_scope': 'warm compiled canonical BP; observed reference ratio in metadata',
                           'type_i': row['counts']['type_i'], 'type_ii': row['counts']['type_ii'],
                           'metadata': {'cohort_kind': 'runtime_budget_fresh_confirmation', 'seed': j['seed'],
                                        'sampling_method': 'iid_failure_target_or_shot_cap', 'stop_reason': row['stop_reason'],
                                        'runtime_ratio_to_bp_osd0': row['runtime_ratio'], 'roles': row['roles'],
                                        'matched_x_rate': j['matched_x_rate'], 'point_plan_sha256': row['point_plan_sha256'],
                                        'denominator_definition': 'all retained iid shots; any original logical residual',
                                        'source_evidence_path': row['directory']+'/summary.json',
                                        'summary_sha256': row['summary_sha256'], 'ledger_sha256': row['ledger_sha256']}})
        series.append({'series_id': identifier, 'dataset_id': dataset, 'code_id': code, 'decoder_id': identifier,
                       'source_decoder_id': identifier, 'channel_kind': config['noise_model'], 'label': label, 'points': points})
        decoders.append({'decoder_id': identifier, 'label': label, 'evidence_status': 'canonical_adaptation',
                         'asset': {'path': relative+'/plan.json', 'kind': 'decoder_source', 'label': 'Frozen runtime-budget protocol'},
                         'configuration': {'settings_status': 'exact_campaign_arm', 'source_path': relative+'/plan.json',
                                           'effective_configuration': config}})
    extension = {'schema': 'research-catalog-extension-v1', 'papers': plan.get('catalog_papers', []),
                 'datasets': [{'dataset_id': dataset, 'label': plan['label'], 'paper_id': plan['paper_id'],
                               'source_path': relative+'/verified.json', 'evidence_status': 'canonical_adaptation',
                               'caveat': plan['claim_limit'], 'points': [p for s in series for p in s['points']]}],
                 'decoders': decoders, 'result_series': series, 'experiments': []}
    rt.write_json(root / 'catalog.json', extension)
