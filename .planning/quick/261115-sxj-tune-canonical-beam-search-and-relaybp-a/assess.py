"""Interpret the completed-worker audit without pooling unlike configurations."""
from collections import Counter
import gzip
import json
from pathlib import Path

REPO=Path(__file__).resolve().parents[3]
ROOT=REPO/'data/reproductions/roffe-2005-07016-search'
with gzip.open(ROOT/'verified.json.gz','rt') as stream:receipt=json.load(stream)
source=json.loads((ROOT.with_name('roffe-2005-07016-osd-fast')/'verified.json').read_text())
osd={(r['code'],r['physical_p']):r for r in source['points'] if r['arm']=='bp_osd0'}
data={'status':'partial_completed_worker_audit','audited_workers':len(receipt['finished_strata']),
      'planned_workers':receipt['planned_strata'],'confirmation_measurements':len(receipt['points']),
      'shots':sum(r['shots'] for r in receipt['points']),'failures':sum(r['failures'] for r in receipt['points']),
      'training_measurements':len(receipt['tuning']),'budget_counts':{},'length242_examples':[],
      'scope':'same-channel X-only; pointwise20-failure estimates, no pooled control curves or global ranking; stronger follow-up has independent seeds'}
for budget in (.5,1.,2.,4.):
    rows=[r for r in receipt['points'] if budget in r['budgets']]
    data['budget_counts'][str(budget)]={'selected_points':len(rows),'actual_under110_percent':sum(r['runtime_ratio']<=budget*1.1 for r in rows)}
for row in receipt['points']:
    j=row['job']
    if j['code']=='toric11' and j['physical_p'] in (.01,.02):
        old=osd.get((j['code'],j['physical_p']))
        data['length242_examples'].append({'method':j['method'],'p':j['physical_p'],'ler':row['rate'],
                                           'ci95_low':row['ci95_low'],'ci95_high':row['ci95_high'],
                                           'shots':row['shots'],'failures':row['failures'],'runtime_ratio':row['runtime_ratio'],
                                           'budgets':row['budgets'],'osd0_ler':old['rate'] if old else None,
                                           'source_directory':row['directory'],'summary_sha256':row['summary_sha256']})
Path(__file__).with_name('assessment.json').write_text(json.dumps(data,sort_keys=True,indent=2)+'\n')
lines=['# Beam search and RelayBP: first audited results','',
       f'{data["audited_workers"]}/{data["planned_workers"]} completed method/rate workers audited in this snapshot; {data["confirmation_measurements"]} fresh configurations, {data["shots"]:,} shots and {data["failures"]:,} logical failures. Training is separate.','',
       'The initial search substantially improves on the earlier tuned ordinary-BP results at the low-rate examples, while OSD-0 still has lower LER. These are X-only comparisons on the original Roffe code/rate grid. Actual latency ratios normalize to contemporaneous same-CPU OSD-0 references; raw timings across hosts are not directly comparable.','',
       '| Length | p | Method | LER | 95% interval | Mean time / OSD0 | OSD0 LER |',
       '| ---: | ---: | --- | ---: | --- | ---: | ---: |']
for row in data['length242_examples']:
    lines.append(f'| 242 | {row["p"]:g} | {row["method"]} | {row["ler"]:.5g} | [{row["ci95_low"]:.5g}, {row["ci95_high"]:.5g}] | {row["runtime_ratio"]:.3f} | {row["osd0_ler"]:.5g} |')
lines+=['','The earlier runtime-budget selected BP estimate at length242/p=.02 was .16129 (see the previous quick-task findings). Initial beam/RelayBP LERs around4.0e-4/2.7e-4 are much lower, but remain above OSD0 at8.87e-6. Pointwise20-failure intervals limit fine rankings.','',
        'Several latency targets initially select the same fast configuration:512-shot coarse zero-failure ties sent only the fastest candidates to the larger finalist stage. This limits the explored accuracy/runtime frontier; it does not establish saturation or OSD-level performance.','',
        'A separately frozen follow-up preserves the original study and retains training-only candidates near each of0.5/1/2/4 times the reference budget, both one- and four-solution arms, and previous fast winners. It uses new finalist/confirmation seeds2026111562/2026111563. The adaptive design timing is explicit; parent confirmation outcomes are not read by its selector. Array61870314 follows corresponding parent workers; collector61870315 also requires the complete original audit61869372. Results remain pending.','',
        '![Measured LER versus relative latency](ler-latency.png)','',
        'Complete settings and every fresh point are in the main study RESULTS.md/results-table.csv. All raw event ledgers remain on the HPC filesystem; the independent receipt and tuning table are losslessly compressed. Exact-control catalog grouping preserves central multi-rate filtering.']
Path(__file__).with_name('FINDINGS.md').write_text('\n'.join(lines)+'\n')
print(json.dumps(data,indent=2))
