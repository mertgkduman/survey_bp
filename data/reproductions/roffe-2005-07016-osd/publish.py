"""Normalize audited compound BP/OSD evidence with explicitly separate work."""
from collections import defaultdict
import json
from pathlib import Path

import runtime as execution

rt = execution.rt


def publish(root):
    plan = rt.load(root); receipt = json.loads((root / 'verified.json').read_text())
    if receipt.get('schema') != 'canonical-bp-osd-verification-v1' or receipt['plan_sha256'] != rt.sha(root / 'plan.json'):
        raise ValueError('OSD verification differs from the frozen campaign')
    relative = root.relative_to(rt.REPO).as_posix(); dataset = plan['study_id']
    groups = defaultdict(list)
    for row in receipt['points']:
        groups[row['code'], row['arm']].append(row)
    series, decoders = [], []
    for (code, arm), rows in sorted(groups.items()):
        config = rows[0]['decoder']; processor = config['postprocessing']
        label = 'BP+OSD-0' if processor['method'] == 'OSD_0' else 'BP+OSD-CS10'
        identifier = f'{dataset}:{code}:{arm}'
        points = []
        for row in sorted(rows, key=lambda r: r['physical_p']):
            n = row['shots']
            points.append({'x': row['physical_p'], 'y': row['rate'], 'n': n, 'failures': row['failures'],
                           'ci_low': row['ci95_low'], 'ci_high': row['ci95_high'],
                           'status': 'complete' if row['failures'] else 'upper_bound',
                           'mean_iterations': row['iterations']/n, 'iteration_unit': 'BP sweeps',
                           'mean_directed_edge_updates': row['directed_edge_updates']/n,
                           'mean_work': row['iterations']/n, 'work_unit': 'iterations',
                           'mean_seconds': row['decode_ns']/n/1e9,
                           'mean_bp_seconds': row['bp_decode_ns']/n/1e9,
                           'mean_osd_seconds': row['osd_decode_ns']/n/1e9,
                           'osd_invocation_fraction': row['osd_calls']/n,
                           'mean_osd_candidate_evaluations': row['osd_work']['candidate_evaluations']/n,
                           'mean_osd_row_xor_words': row['osd_work']['row_xor_words']/n,
                           'type_i': row['counts']['type_i'], 'type_ii': row['counts']['type_ii'],
                           'runtime_scope': 'warmed canonical BP plus complete OSD call; separate stage timings retained',
                           'metadata': {'cohort_kind': 'canonical_osd_validation', 'seed': row['seed'],
                                        'matched_x_rate': row['matched_x_rate'], 'channel': 'x_only',
                                        'sampling_method': 'iid_failure_target_or_shot_cap', 'stop_reason': row['stop_reason'],
                                        'target_failures': row['target_block_failures'], 'max_shots': row['max_shots'],
                                        'uncertainty_method': 'exact_negative_binomial_interval' if row['stop_reason'] == 'target_block_failures' else 'exact_binomial_interval_at_shot_cap',
                                        'work_scope': 'iterations/edge updates are BP stage only; OSD cost separate',
                                        'mean_osd_work': {k: v/n for k, v in row['osd_work'].items()},
                                        'denominator_definition': 'all retained iid shots; either nontrivial original logical residual',
                                        'ledger_sha256': row['ledger_sha256'], 'summary_sha256': row['summary_sha256'],
                                        'source_evidence_path': f'{relative}/results/{row["id"]}/summary.json'}})
        series.append({'series_id': identifier, 'dataset_id': dataset, 'code_id': code, 'decoder_id': identifier,
                       'source_decoder_id': arm, 'label': label, 'channel_kind': 'x_only', 'points': points})
        decoders.append({'decoder_id': identifier, 'label': label, 'evidence_status': 'canonical_adaptation',
                         'asset': {'path': f'{relative}/plan.json', 'kind': 'decoder_source', 'label': 'Frozen canonical BP/OSD configuration'},
                         'configuration': {'settings_status': 'exact_campaign_arm', 'source_path': f'{relative}/plan.json',
                                           'source_arm_id': arm, 'effective_configuration': config}})
    result = {'schema': 'research-catalog-extension-v1', 'papers': plan.get('catalog_papers', []),
              'datasets': [{'dataset_id': dataset, 'label': plan['label'], 'paper_id': plan['paper_id'],
                            'source_path': f'{relative}/verified.json', 'evidence_status': 'canonical_adaptation',
                            'caveat': plan['claim_limit'], 'points': [p for s in series for p in s['points']],
                            'assets': [{'path': f'{relative}/{name}', 'kind': 'json', 'label': label} for name, label in
                                       [('plan.json', 'Frozen BP/OSD design'), ('verified.json', 'Audited BP/OSD measurements')]]}],
              'decoders': decoders, 'result_series': series,
              'experiments': [{'experiment_id': dataset, 'dataset_id': dataset, 'dataset_ids': [dataset],
                               'paper_ids': [plan['paper_id']], 'code_ids': sorted({c for c, _ in groups}),
                               'decoder_ids': [d['decoder_id'] for d in decoders], 'evidence_status': 'canonical_adaptation',
                               'description': plan['claim_limit'], 'reproduction_recipe': {
                                   'kind': 'source_command', 'study_path': f'{relative}/plan.json',
                                   'decoder_path': f'{relative}/plan.json', 'original_instruction_path': plan['instruction_path'],
                                   'commands': [f'PYTHONPATH=src .venv/bin/python {relative}/run.py --collect'],
                                   'budget_note': 'Collection audits retained evidence. Frozen simulations require explicit point indices.'}}]}
    rt.write_json(root / 'catalog.json', result)
    return result
