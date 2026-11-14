"""Generate same-rate comparisons from audited OSD evidence; no sampling."""
import csv
import json
import math
from pathlib import Path

import runtime as execution

rt = execution.rt


def number(value):
    if value is None:
        return 'not plotted'
    if value and abs(value) < .001:
        exponent = math.floor(math.log10(abs(value)))
        return f'${value/10**exponent:.4g}\\times10^{{{exponent}}}$'
    return f'{value:.4g}'


def report(root):
    plan = rt.load(root); receipt = json.loads((root / 'verified.json').read_text())
    if receipt['plan_sha256'] != rt.sha(root / 'plan.json'):
        raise ValueError('report receipt differs from frozen OSD plan')
    reference = rt.REPO / plan['comparison_inputs']['paper_cs60']
    source = json.loads(reference.read_text())
    previous = json.loads((rt.REPO / plan['comparison_inputs']['prior_confirmation']).read_text())
    baseline = {(r['code'], r['base_arm'], r['role'], r['matched_x_rate']): r for r in previous['points']}
    rows = []
    for r in receipt['points']:
        c = plan['codes'][r['code']]; n = r['shots']
        osd60 = next((p['block_ler_approx'] for p in source['curves']['bp_osd_cs'][str(c['d'])] if p['p'] == r['physical_p']), None)
        a = baseline[r['code'], 'binary_ms', 'baseline', r['physical_p']]
        b = baseline[r['code'], 'binary_ms', 'selected', r['physical_p']]
        q = baseline[r['code'], 'qbp_ms', 'selected', r['physical_p']]
        row = {'code': r['code'], 'n': c['n'], 'distance': c['d'], 'x_only_physical_p': r['physical_p'],
               'arm': r['arm'], 'bp_cap': c['n'], 'osd_order': r['decoder']['postprocessing']['order'],
               'shots': n, 'failures': r['failures'], 'stop_reason': r['stop_reason'],
               'ler': r['rate'], 'ci95_low': r['ci95_low'], 'ci95_high': r['ci95_high'],
               'mean_bp_iterations': r['iterations']/n, 'mean_bp_directed_edge_updates': r['directed_edge_updates']/n,
               'osd_invocation_fraction': r['osd_calls']/n,
               'mean_osd_candidate_evaluations': r['osd_work']['candidate_evaluations']/n,
               'mean_osd_row_xor_words': r['osd_work']['row_xor_words']/n,
               'mean_bp_seconds': r['bp_decode_ns']/n/1e9, 'mean_osd_seconds': r['osd_decode_ns']/n/1e9,
               'mean_total_seconds': r['decode_ns']/n/1e9, 'paper_cs60_x_only_approx': osd60,
               'previous_bp_d0_x_only_ler': a['rate'], 'previous_bp_d05_x_only_ler': b['rate'],
               'previous_qbp_d03_depolarizing_ler': q['rate'], 'qbp_physical_p': q['physical_p'],
               'ledger_sha256': r['ledger_sha256'], 'summary_sha256': r['summary_sha256']}
        rows.append(row)
    if rows:
        with (root / 'results-table.csv').open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n'); writer.writeheader(); writer.writerows(rows)
    complete = len(rows) == len(plan['jobs'])
    lines = ['# Roffe: canonical BP with OSD-0 and CS-10', '',
             f'Audited {len(rows)}/{len(plan["jobs"])} points. Status: {"complete" if complete else "partial; missing points remain unavailable"}. No new sampling is performed by this report.', '',
             'All new curves use X-only noise, canonical undamped flooding min-sum, alpha_t=1-2^-t, float64 and T=n. OSD activates only after original-syndrome nonconvergence; a converged BP output is kept even if independent evaluation later identifies a logical error. Both methods share the previous confirmation physical stream and preserve 20-failure/1e8-shot stopping without pooling.', '',
             'BP sweeps and directed edge updates exclude OSD work. Separate invocation rate, candidate evaluations, elimination word-XOR counts and warmed BP/OSD/total times are in the CSV and workbench. Source CS60 values are approximate paper data. The previous damped Q-BP comparison is depolarizing at1.5p and is not a same-channel ranking.', '']
    index = {(r['code'], r['arm'], r['x_only_physical_p']): r for r in rows}
    for code in sorted(plan['codes'], key=lambda c: plan['codes'][c]['n']):
        c = plan['codes'][code]
        lines += [f'## [[{c["n"]},2,{c["d"]}]]; BP T={c["n"]}', '',
                  '| X rate p | BP d=0 | BP d=.5 | OSD-0 | CS-10 | Paper CS-60≈ | Q-BP d=.3, depolarizing 1.5p |',
                  '| ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
        for p in sorted({j['physical_p'] for j in plan['jobs'] if j['code'] == code}):
            def value(arm):
                item = index.get((code, arm, p))
                return 'pending' if item is None else ('≤ '+number(item['ci95_high']) if item['failures'] == 0 else number(item['ler']))
            paper = next((v['block_ler_approx'] for v in source['curves']['bp_osd_cs'][str(c['d'])] if v['p'] == p), None)
            a = baseline[code, 'binary_ms', 'baseline', p]['rate']; b = baseline[code, 'binary_ms', 'selected', p]['rate']
            q = baseline[code, 'qbp_ms', 'selected', p]['rate']
            lines.append(f'| {p:g} | {number(a)} | {number(b)} | {value("bp_osd0")} | {value("bp_osd_cs10")} | {number(paper)} | {number(q)} |')
        lines += ['']
    lines += ['Complete candidate sets are exposed by the qualified processor API. Shot ledgers bind their set digest, selected candidate, terminal posterior and canonical input; full endpoint replay verifies provenance and work. Timing excludes deterministic warmup, sampling, truth evaluation and ledger I/O. Native/source provenance and benchmark limits are in Spike056.', '',
              'Raw ledgers remain local under results/. All unavailable/upper-bound results are retained honestly; no automatic source-reproduction or superiority verdict is inferred.']
    (root / 'RESULTS.md').write_text('\n'.join(lines)+'\n')
    summary = {'schema': 'canonical-bp-osd-report-v1', 'points': len(rows), 'planned_points': len(plan['jobs']),
               'complete': complete, 'shots': sum(r['shots'] for r in rows), 'failures': sum(r['failures'] for r in rows),
               'verified_sha256': rt.sha(root / 'verified.json'), 'paper_source_sha256': rt.sha(reference)}
    rt.write_json(root / 'assessment.json', summary)
    return summary
