"""Verify preservation of the full earlier CSV and summarize the audited snapshot."""
import csv
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import time
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
STUDY=ROOT/'data/reproductions/priortilt-2611-13373'
previous={r['point']:r for r in csv.DictReader((HERE/'previous-comparison.csv').open())}
current={r['point']:r for r in csv.DictReader((HERE/'comparison-snapshot.csv').open())}
assert all(current[k]==v for k,v in previous.items())
assert (STUDY/'comparison.csv').read_bytes()==(HERE/'previous-comparison.csv').read_bytes()
a=json.loads((HERE/'assessment.json').read_text());w=json.loads((HERE/'resource-check.json').read_text())
assert len(current)==a['snapshot_points'] and set(current)=={c['point'] for c in a['checks']}
parallel={k for k in current if (STUDY/'results'/k/'parallel-work.json').exists()}
assert parallel<={c['point'] for c in w['checks']}
status=[]
plan=json.loads((STUDY/'plan.json').read_text())
for j in plan['jobs']:
    p=STUDY/'results'/j['id']
    status.append({'point':j['id'],'sampling_complete':(p/'complete.json').exists(),'full_audit_complete':(p/'audit.json').exists(),'in_status_snapshot':j['id'] in current})
methods={m:sum(r['method']==m for r in current.values()) for m in ('priortilt','relay','beam')}
groups={}
for r in current.values():groups.setdefault((r['code'],r['p']),{})[r['method']]=float(r['ler_per_cycle'])
full=[v for v in groups.values() if len(v)==3]
ratios={m:[v[m]/v['priortilt'] for v in full] for m in ('relay','beam')}
summary={'timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
         'unchanged_full_previous_csv_rows':len(previous),'status_snapshot_points':len(current),'methods':methods,
         'shots':a['complete_pair_shots'],'errors':a['complete_pair_errors'],
         'paper_values_inside_pointwise_local95':sum(c['paper_inside'] for c in a['checks']),
         'local_over_paper_range':[min(c['local_over_paper'] for c in a['checks']),max(c['local_over_paper'] for c in a['checks'])],
         'fully_compared_strata':len(full),'priortilt_lowest_estimate_strata':sum(min(v,key=v.get)=='priortilt' for v in full),
         'relay_over_priortilt_ler_range':[min(ratios['relay']),max(ratios['relay'])],
         'beam_over_priortilt_ler_range':[min(ratios['beam']),max(ratios['beam'])],
         'parallel_work_points':len(w['checks']),'sealed_parallel_stages_declared_in_work_receipts':sum(c['stages'] for c in w['checks']),
         'inherited_marker_digests_preserved_in_audits':sum(c['inherited_marker_digests_preserved_in_full_audit'] for c in w['checks']),
         'inherited_markers_sampled_and_rehashed':sum(c['inherited_markers_sampled'] for c in w['checks']),
         'canonical_markers_npz_noise_sampled':sum(c['canonical_markers_npz_noise_sampled'] for c in w['checks']),
         'stage_markers_npz_noise_sampled':sum(c['stage_markers_npz_noise_sampled'] for c in w['checks']),
         'resource_check_scope':w['scope'],
         'computed_shots':sum(c['computed']['shots'] for c in w['checks']),
         'retained_shots':sum(c['retained']['shots'] for c in w['checks']),
         'speculative_shots':sum(c['speculative']['shots'] for c in w['checks']),
         'points':status}
(HERE/'snapshot-check.json').write_text(json.dumps(summary,indent=2)+'\n')
text=['# Audited PriorTilt results at every paper rate','',
      'LER per syndrome cycle = (X-memory observable error rate + Z-memory observable error rate) / cycles. This uses the released observable-only scoring convention; nonconvergence is recorded separately. Local intervals are pointwise at-least-95% simultaneous X/Z bounds, not simultaneous coverage across this entire table. Source values are from the authors\' released Fig. 1 counts.','',
      '| Code | p | Local PriorTilt LER/cycle (95%) | Paper PriorTilt LER/cycle | Relay / PriorTilt | Beam / PriorTilt |',
      '|---|---:|---:|---:|---:|---:|']
for r in current.values():
    if r['method']!='priortilt':continue
    v=groups[r['code'],r['p']];p=v['priortilt']
    ratio=lambda m:f'{v[m]/p:.3f}' if m in v else 'awaiting full audit'
    text.append(f"| {r['code']} | {r['p']} | {p:.8g} [{float(r['ci95_low']):.8g}, {float(r['ci95_high']):.8g}] | {float(r['paper_ler_per_cycle']):.8g} | {ratio('relay')} | {ratio('beam')} |")
text+=['','Ratios compare local point estimates at the published algorithm settings. They do not imply matched latency or statistically strict superiority at every point. The rarest rates can stop at 100 million shots per basis before reaching 20 errors.','',f"{len(current)}/39 points in this checked status snapshot; all {summary['paper_values_inside_pointwise_local95']} corresponding paper ordinates lie within their local intervals. All {len(previous)} earlier full CSV rows are identical."]
text+=['', 'Scope: matching completed full-worker audit/complete receipts, manifest/policy/frozen-identity checks, independent aggregate reconciliation and sampled on-disk bindings. A fresh full raw-ledger rehash was deliberately not completed for this status check. The main publication remains at its prior 28-point snapshot pending the scheduled final collector.']
(HERE/'PRIORTILT-TABLE.md').write_text('\n'.join(text)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='points'},indent=2))
