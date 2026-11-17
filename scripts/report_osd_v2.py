"""Derive reviewable tables from sealed OSD v2 measurements; no new timing."""
import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT/'data/benchmarks/osd-v2/qualified'


def sha(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def ratio(before, after, field='round_ns_per_call'):
    a, b = before[field], after[field]
    if len(a) != len(b) or not a:
        raise ValueError('matched nonempty timing rounds required')
    return float(statistics.median([x/y for x, y in zip(a, b, strict=True)]))


def derive(out):
    r = json.loads((out/'benchmark.json').read_text())
    manifest = json.loads((out/'manifest.json').read_text())
    for name, digest in manifest['files'].items():
        if sha(out/name) != digest:
            raise ValueError(f'benchmark seal mismatch: {name}')
    rows = {(x['group'], x['depth'], x['variant']): x for x in r['rows']}
    groups = sorted({x['group'] for x in r['rows']})
    hardware = r['hardware']
    lines = ['# Qualified OSD v2: implementation and performance', '',
             f"Measured on **one CPU**, {hardware['cpu_model']}, Slurm {hardware['slurm_job_id']}; "
             f"{r['rounds']} alternating matched rounds, three actual canonical BP failures per code/channel. "
             'Five matrices (n=162, 450, 882, 1054, 1922), two channels, OSD0/CS1/CS10/CS60. '
             'All v2 timings include mandatory candidate/weight hashing, original-H validation, '
             'stage/work counters and ledger construction. Construction/JIT are separate.', '',
             'The new processor adds nonuniform scoring, sparse ownership, bounded cache reuse and '
             'streamed evidence. Affine reuse and packed XOR/popcount were already present in v1; '
             'their ablation gains are not new algorithmic discoveries. Full and fast evidence '
             'preserve the same candidate sequence, first winner and digest.', '',
             '## Independent qualification', '', '| Check | Comparisons |', '|---|---:|']
    for name, count in r['qualification']['checks'].items():
        lines.append(f'| {name} | {count} |')
    lines += ['', 'Counts are comparisons with overlapping fixtures, not independent statistical trials. '
              'The dense oracle independently solves each candidate; native weighted and full-candidate '
              'comparisons use the unmodified pinned C++ algorithm through a vector-prior bridge. '
              'Both source log-inverse-p and separately named Bernoulli likelihood scores are checked. '
              'Native qsort ties are controlled with the same stable-order-equivalent ranks for both timed interfaces. '
              'Equivalence is also checked on the original BP posteriors. No LER inference is made.', '',
              '## Before and after', '',
              'Warm standalone medians, microseconds. v1 includes full candidate materialization/digest, '
              'but lacks the v2 ledger/timing/weighted evidence contract. Native timings return the '
              'winner only; candidate tracing is enabled for qualification separately.', '',
              '| Code/channel | Method | v1 full | Initial v2 | Qualified v2 fast | Native final | Paired v1/v2 speed |',
              '|---|---:|---:|---:|---:|---:|---:|']
    for group in groups:
        for depth in (10, 60):
            base = rows[group, depth, 'v2_fast']
            cells = []
            for name in ('v1_full', 'initial_v2', 'v2_fast', 'native_final'):
                x = rows.get((group, depth, name)); cells.append('—' if x is None else f"{x['ns_per_call_median']/1000:.1f}")
            old = rows.get((group, depth, 'v1_full'))
            gain = '—' if old is None else f'{ratio(old, base):.2f}×'
            lines.append(f'| {group} | CS{depth} | '+' | '.join(cells)+f' | {gain} |')
    lines += ['', '**No blanket speedup:** small uniform inputs and OSD0 often remain slower than v1. '
              'The richer evidence contract has a measurable cost. On LP1054 uniform inputs the '
              'qualified CS10/CS60 calls improve on v1, while the toric31 uniform comparisons '
              'remain mixed. Read each row rather than pooling distinct workloads.', '',
              '## Matched component ablations', '',
              'Each entry is the median paired per-stratum ratio across ten code/channel strata, '
              'with the stratum minimum–maximum in parentheses. A speed ratio greater than 1 favors '
              'the retained implementation. Full-check and materialization rows are cost ratios '
              'relative to fast streamed evidence. All retain mandatory digests and ledgers.', '',
              '| Comparison | OSD0 | CS1 | CS10 | CS60 |', '|---|---:|---:|---:|---:|']
    comparisons = [('Affine reuse speed', 'v2_no_affine', 'v2_fast'),
                   ('Live-coefficient response speed', 'v2_scan_responses', 'v2_fast'),
                   ('Packed vs byte candidate XOR speed, same bit scoring', 'v2_bytes', 'v2_bit_scoring'),
                   ('Popcount/set-bit vs all-bit scoring speed', 'v2_bit_scoring', 'v2_fast'),
                   ('512 vs 128 candidate block speed', 'v2_block128', 'v2_fast'),
                   ('Incremental optimization vs initial v2 speed', 'initial_v2', 'v2_fast'),
                   ('Repeated-order cache speed', 'v2_fast', 'v2_cache_hit'),
                   ('Changing-order one-entry cache speed', 'v2_fast', 'v2_cache_lru'),
                   ('Full original-H validation cost', 'v2_full', 'v2_fast'),
                   ('Candidate materialization cost', 'v2_materialized', 'v2_fast')]
    ablations = []
    for label, before_name, after_name in comparisons:
        cells = []
        for depth in (0, 1, 10, 60):
            gains = [ratio(rows[g, depth, before_name], rows[g, depth, after_name]) for g in groups]
            record = dict(comparison=label, depth=depth, strata=len(gains), median=float(statistics.median(gains)),
                          minimum=min(gains), maximum=max(gains))
            ablations.append(record)
            cells.append(f"{record['median']:.2f} ({record['minimum']:.2f}–{record['maximum']:.2f})")
        lines.append('| '+label+' | '+' | '.join(cells)+' |')
    lines += ['', 'OSD0 bypasses the affine cache and does not construct single responses; ratios '
              'near 1 there are measurement variation, not basis-reuse gains. Cache-hit results '
              'require repeated exact column orders. The one-entry cache cycles through changing '
              'actual failure orders and exposes miss/transform/copy overhead. It is **disabled by default**.', '',
              '## Whole canonical BP+OSD calls', '',
              'External whole-call medians, microseconds, include canonical BP, fallback activation '
              'and a per-call ledger. v1 uses the same canonical BP engine with a historical-evidence '
              'wrapper. v2 has the richer versioned evidence described above. Each sample reruns BP; '
              'OSD-only timings must not be substituted for these values.', '',
              '| Code/channel | Method | Population | OSD calls/shots | v1 full | v2 fast | Cached v2 | No affine v2 |',
              '|---|---:|---|---:|---:|---:|---:|---:|']
    pipes = {(x['group'], x['depth'], x['population'], x['variant']): x for x in r['pipeline_rows']}
    for group in ('toric9_uniform', 'lp1054_uniform', 'lp1054_nonuniform', 'toric31_nonuniform'):
        for depth in (0, 10, 60):
            for population in ('failure_conditioned', 'mixed_16_shots'):
                base = pipes[group, depth, population, 'v2_fast']
                cells = []
                for name in ('v1_full', 'v2_fast', 'v2_cache_hit', 'v2_no_affine'):
                    value = pipes.get((group, depth, population, name))
                    cells.append('—' if value is None else f"{value['total_ns_median']/1000:.1f}")
                lines.append(f"| {group} | {depth} | {population} | {base['osd_calls']}/{base['shots']} | "+' | '.join(cells)+' |')
    lines += ['', 'The mixed population is the first 16 sampled syndromes before failure selection. '
              'Some strata have 16/16 failures; the activation fraction is therefore shown explicitly. '
              'These bounded fixed samples do not estimate operational LER, average production latency '
              'or a threshold. All 280 measured pipeline rows are available in pipeline.csv.', '',
              '## Sparse/packed storage crossover', '',
              'OSD-CS10, same first failure per code. Retained bytes include the exact canonical CSR '
              'key (shared by CSR views), and packed original H if selected. v1 retains dense H plus '
              'packed H. Construction includes channel-weight caching in v2. `auto` picks storage '
              'by byte count; measured decode speed can favor packed rows even when CSR saves memory.', '',
              '| Code | Original storage | Retained matrix bytes | Constructor µs | Decode µs |',
              '|---|---|---:|---:|---:|']
    for x in r['storage_crossover']:
        lines.append(f"| {x['code']} | {x['storage']} | {x['retained_matrix_bytes']:,} | {x['constructor_ns_median']/1000:.1f} | {x['decode_ns_median']/1000:.1f} |")
    lines += ['', 'A packed elimination backend is used after sparse ingestion because elimination '
              'can fill in. This experiment profiles original storage, construction and validation '
              'crossover; it does not claim a universal sparse-elimination crossover.', '',
              '## Peak memory', '',
              'Fresh child processes, JIT/page warmup before measurement. Linux RSS high-water reset '
              'availability is recorded in raw data. The traced peak captures Python/NumPy allocation '
              'and may omit native allocation; process RSS is independently measured. A zero RSS '
              'increment reflects resident-page reuse/granularity, not zero allocation.', '',
              '| Stratum | Method | Mode | Traced peak bytes | Process peak RSS MiB | RSS increment bytes | Materialized bytes |',
              '|---|---:|---|---:|---:|---:|---:|']
    for x in r['memory']:
        lines.append(f"| {x['group']} | {x['depth']} | {x['variant']} | {x['traced_peak_bytes']:,} | {x['peak_rss_bytes']/2**20:.2f} | {x['peak_rss_increment_bytes']:,} | {x['materialized_bytes']:,} |")
    lines += ['', '## Stage timing and provenance cost', '',
              'Median instrumented stage timings for the last fixed fixture of each round, '
              'microseconds. “Provenance” sums candidate/weight hashing and ledger/snapshot construction; '
              'full original-H checking is shown separately. Input/sort/packing and wrapper gaps '
              'remain in total. The external latency tables are authoritative for whole calls.', '',
              '| Stratum / mode | CS | Factor/transform | Responses/store | Generate/score | Original-H check | Provenance | Instrumented total |',
              '|---|---:|---:|---:|---:|---:|---:|---:|']
    for group in ('toric9_uniform', 'lp1054_uniform', 'toric31_nonuniform'):
        for depth in (10, 60):
            for name in ('v2_fast', 'v2_full', 'v2_cache_hit'):
                samples = rows[group, depth, name]['round_stages_last_fixture_ns']
                stage = lambda keys: statistics.median([sum(s[k] for k in keys) for s in samples])/1000
                values = [stage([k]) for k in ('factor_or_transform', 'responses_and_cache_store', 'enumerate_score', 'candidate_validation')]
                values += [stage(['candidate_hash', 'weight_hash', 'ledger_and_snapshots']), stage(['total'])]
                lines.append(f'| {group}/{name} | {depth} | '+' | '.join(f'{v:.1f}' for v in values)+' |')
    lines += ['', '## Scope and decisions', '',
              '- Retain uniform integer popcount and exact v1 candidate digests; weighted scores are separately encoded and source/ML conventions cannot be pooled.',
              '- Use packed elimination and live-coefficient response construction; keep sparse original storage as an explicit memory/latency choice.',
              '- Keep the exact-order cache opt-in: warm reuse is valuable, changing-order misses can erase it. Its payload budget charges key bytes per entry conservatively, including shared immutable keys.',
              '- Use 512-candidate streaming blocks by default. Pair storage stays bounded by block size; weights remain O(candidate count) through their digest stage.',
              '- Fast evidence is the default; it retains full ordered digests and replay. Use full evidence when checking every candidate is needed, and materialize only for inspection/qualification.',
              '- Affine reuse/packing are inherited foundations; new response, cache, ownership and streaming gains are separated from them. Small-input/OSD0 regressions remain explicit.',
              '- Both benchmark runs, source snapshots, raw timing rounds, fixtures, ledgers, work, peak-memory measurements and source/build identities are retained. Historical simulations and v1 are unchanged.', '',
              'All source and raw evidence identities: [manifest.json](manifest.json), [benchmark.json](benchmark.json). '
              'Full timing and pipeline tables: [timings.csv](timings.csv), [pipeline.csv](pipeline.csv). '
              'Algorithm/API contract: [docs/osd-v2.md](../../../../docs/osd-v2.md).']
    path = out/'QUALIFICATION.md'; path.write_text('\n'.join(lines)+'\n')
    for name, records in [('ablations.csv', ablations), ('memory.csv', r['memory']), ('storage.csv', r['storage_crossover'])]:
        with (out/name).open('w') as f:
            writer = csv.DictWriter(f, fieldnames=list(records[0])); writer.writeheader(); writer.writerows(records)
    analysis_files = ['QUALIFICATION.md', 'ablations.csv', 'memory.csv', 'storage.csv']
    (out/'analysis-manifest.json').write_text(json.dumps(dict(schema='osd-v2-derived-report-v1',
        benchmark_manifest_sha256=sha(out/'manifest.json'), script_sha256=sha(Path(__file__)),
        files={name: sha(out/name) for name in analysis_files}), indent=2, sort_keys=True)+'\n')
    return path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', type=Path, default=DEFAULT)
    args = parser.parse_args(); print(derive(args.output))
