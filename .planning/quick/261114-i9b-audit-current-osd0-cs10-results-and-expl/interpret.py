"""Source-rate comparison for the explicitly scoped terminal snapshot."""
from collections import Counter
import csv
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ROOT = REPO / 'data/reproductions/roffe-2005-07016-osd-fast'


def main():
    snapshot = json.loads((HERE / 'checked-snapshot.json').read_text())
    plan = json.loads((ROOT / 'plan.json').read_text())
    source = json.loads((REPO / plan['comparison_inputs']['paper_cs60']).read_text())
    prior = json.loads((REPO / plan['comparison_inputs']['prior_confirmation']).read_text())['points']
    current = {(r['code'], r['arm'], r['physical_p']): r for r in snapshot['points']}
    rows, coverage = [], Counter()
    lines = ['# Roffe OSD results check', '',
             f'Terminal snapshot: {len(snapshot["points"])}/218 points, {snapshot["shots"]:,} shots, {snapshot["failures"]:,} logical failures. Frozen manifests, summary arithmetic, stopping, work, exact confidence intervals and all {snapshot["endpoint_replays"]} endpoint replays pass.', '',
             '**Audit scope:** this snapshot checks terminal summaries and endpoints. It does not re-read every interior ledger row. The full-ledger publication refresh runs as Slurm61820674; complete collector61820676 is serialized behind it and the simulation array. The workbench retains the previously fully audited173-point OSD snapshot until that refresh passes. Unfinished points are pending, with no provisional rate treated as a final result.', '',
             'All columns below use X-only noise. New methods use canonical min-sum with T=n, undamped BP, and either OSD-0 or CS-10 after nonconvergence. The paper reference is approximate Figure3 CS-60. It is a different search depth, so this is a comparison rather than a CS-60 reproduction. Damped BP uses d=.5.', '',
             'The 20-failure confidence intervals are wide (typically roughly0.61–1.48 times the estimate); the two100M-shot length242/p=.01 points instead use exact binomial intervals. Overlapping intervals do not establish equality or a paired-test result.', '']
    for code in sorted(plan['codes'], key=lambda c: plan['codes'][c]['n']):
        c = plan['codes'][code]
        lines += [f'## [[{c["n"]},2,{c["d"]}]]', '',
                  '| X error rate | BP | Damped BP | OSD-0 | CS-10 | Paper CS-60≈ |',
                  '| ---: | ---: | ---: | ---: | ---: | ---: |']
        for p in sorted({j['physical_p'] for j in plan['jobs'] if j['code'] == code}):
            old = [next(r for r in prior if r['code'] == code and r['base_arm'] == 'binary_ms' and r['role'] == role and r['matched_x_rate'] == p)
                   for role in ('baseline', 'selected')]
            paper = next((r['block_ler_approx'] for r in source['curves']['bp_osd_cs'][str(c['d'])] if r['p'] == p), None)
            row = {'code': code, 'n': c['n'], 'x_only_p': p, 'bp': old[0]['rate'], 'damped_bp': old[1]['rate'], 'paper_cs60_approx': paper}
            for arm in ('bp_osd0', 'bp_osd_cs10'):
                r = current.get((code, arm, p))
                for key in ('rate', 'ci95_low', 'ci95_high', 'shots', 'failures'):
                    row[arm+'_'+key] = r[key] if r else None
                if r and paper is not None:
                    coverage[arm+'_available'] += 1
                    coverage[arm+'_inside_ci'] += r['ci95_low'] <= paper <= r['ci95_high']
            rows.append(row)
            def fmt(value):
                return 'pending / unavailable' if value is None else f'{value:.5g}'
            lines.append('| '+f'{p:g} | '+' | '.join(fmt(row[k]) for k in ('bp', 'damped_bp', 'bp_osd0_rate', 'bp_osd_cs10_rate', 'paper_cs60_approx'))+' |')
        lines.append('')
    with (HERE / 'comparison-check.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n'); writer.writeheader(); writer.writerows(rows)
    (HERE / 'COMPARISON.md').write_text('\n'.join(lines).rstrip()+'\n')
    result = {'status': 'checked_summary_and_endpoints; full_interior_audit_pending',
              'points': len(snapshot['points']), 'shots': snapshot['shots'], 'failures': snapshot['failures'],
              'paper_approx_pointwise_ci_coverage': dict(coverage),
              'claim_limit': 'CS60 has a different search depth and unavailable source uncertainty; interval containment is descriptive, not a global reproduction test',
              'at_p_002': [r for r in rows if r['x_only_p'] == .02], 'at_p_004': [r for r in rows if r['x_only_p'] == .04]}
    (HERE / 'assessment.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
