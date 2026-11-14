"""Fast summary/endpoint check, explicitly distinct from a full-ledger audit."""
import datetime
import gzip
import importlib.util
import json
from pathlib import Path

from scipy.stats import beta

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ROOT = REPO / 'data/reproductions/roffe-2005-07016-osd-fast'
spec = importlib.util.spec_from_file_location('_current_osd_check', ROOT / 'run.py')
campaign = importlib.util.module_from_spec(spec); spec.loader.exec_module(campaign)
execution, rt = campaign.execution, campaign.rt


def check():
    plan = rt.load(ROOT)
    rows, missing = [], []
    for job in plan['jobs']:
        directory = ROOT / 'results' / job['id']; path = directory / 'summary.json'
        if not path.exists():
            missing.append({k: job[k] for k in ('id', 'code', 'arm', 'physical_p')})
            continue
        summary = json.loads(path.read_text())
        n, k = summary['shots'], summary['failures']
        assert json.loads((directory / 'manifest.json').read_text()) == rt.manifest(ROOT, job)
        assert summary['manifest_sha256'] == rt.sha(directory / 'manifest.json')
        assert 0 < n <= job['max_shots'] and 0 <= k <= job['target_block_failures']
        assert sum(summary['counts'].values()) == n and summary['counts']['type_i'] == 0
        assert k == summary['counts']['type_i']+summary['counts']['type_ii']
        target = k == job['target_block_failures']
        assert target or n == job['max_shots']
        assert summary['stop_reason'] == ('target_block_failures' if target else 'max_shots')
        lo = 0. if k == 0 else float(beta.ppf(.025, k, n-k+1))
        hi = 1. if k == n else float(beta.ppf(.975, k if target else k+1, n-k))
        assert (summary['rate'], summary['ci95_low'], summary['ci95_high']) == (k/n, lo, hi)
        assert summary['decode_ns'] == summary['bp_decode_ns']+summary['osd_decode_ns']
        assert summary['directed_edge_updates'] == 2*job['graph_edges']*summary['iterations']
        expected_candidates = 1 if job['arm'] == 'bp_osd0' else 1+job['non_pivot_count']+45
        assert summary['osd_work']['candidate_evaluations'] == expected_candidates*summary['osd_calls']
        first = directory / 'shots-000000000.jsonl.gz'
        last = directory / f'shots-{((n-1)//execution.BATCH)*execution.BATCH:09d}.jsonl.gz'
        with gzip.open(first, 'rt') as stream:
            initial = json.loads(next(stream))
        with gzip.open(last, 'rt') as stream:
            terminal = json.loads(list(stream)[-1])
        assert initial['shot'] == 0 and terminal['shot'] == n-1
        state = execution.state(job); execution.warm(state)
        for stored in (initial, terminal):
            replay = execution.event(state, stored['shot'])
            assert {key: value for key, value in replay.items() if key not in execution.execution.TIMING_FIELDS} == {
                key: value for key, value in stored.items() if key not in execution.execution.TIMING_FIELDS}
        rows.append({**job, **summary, 'summary_sha256': rt.sha(path)})
        print('checked', len(rows), job['id'], flush=True)
    result = {'timestamp_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'schema': 'osd-terminal-summary-endpoint-check-v1', 'status': 'passed',
              'audit_scope': 'frozen plan/manifests, terminal summary arithmetic/CI/work/stopping and exact two-endpoint replay; full interior-ledger re-read is pending in Slurm; not a publication receipt',
              'plan_sha256': rt.sha(ROOT / 'plan.json'), 'points': rows, 'missing': missing,
              'shots': sum(r['shots'] for r in rows), 'failures': sum(r['failures'] for r in rows),
              'endpoint_replays': 2*len(rows)}
    rt.write_json(HERE / 'checked-snapshot.json', result)
    print({k: result[k] for k in ('status', 'shots', 'failures', 'endpoint_replays')}, flush=True)


if __name__ == '__main__':
    check()
