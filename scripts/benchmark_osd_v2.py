"""Matched single-CPU OSD qualification/ablations and BP+OSD benchmarks.

Run --run in a one-CPU allocation; --verify checks sealed fixture/results hashes.
No existing campaign or historical result is modified. Not an LER campaign.
"""
import argparse
from collections import Counter
import ctypes
import gc
from hashlib import sha256
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import resource
import statistics
import subprocess
import sys
import time
import tracemalloc
from types import SimpleNamespace

import numpy as np
from scipy import sparse

from bp_registry.artifacts import load_artifact
from bp_registry.postprocessing.osd import UniformOsd
from bp_registry.postprocessing.osd_v2 import Osd, AffineBasisCache, SCORE_SOURCE, SCORE_ML, VERSION
from bp_registry.postprocessing.bp_osd_v2 import CanonicalBpOsd
from bp_registry.postprocessing.osd_v2 import _digest, _json_digest

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT/'data/benchmarks/osd-v2/qualified'
UPSTREAM = 'd3429964cd4ffe1abfc041c6ec8b8425cb174f40'
SEED = 2026111705
DEPTHS = (0, 1, 10, 60)
VARIANTS = ('v2_fast', 'v2_full', 'v2_materialized', 'v2_no_affine',
            'v2_scan_responses', 'v2_bit_scoring', 'v2_bytes', 'v2_sparse',
            'v2_cache_hit', 'v2_cache_lru', 'v2_block128')


def file_hash(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n')


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); sys.modules[name] = value; spec.loader.exec_module(value)
    return value


class Native:
    def __init__(self, h, depth, probabilities, library):
        self.library = ctypes.CDLL(str(library))
        self.library.osd_create.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p]
        self.library.osd_create.restype = ctypes.c_void_p
        self.library.osd_decode.argtypes = [ctypes.c_void_p]*5
        self.library.osd_decode.restype = ctypes.c_int
        self.library.osd_destroy.argtypes = [ctypes.c_void_p]
        self.library.osd_error.restype = ctypes.c_char_p
        h, p = np.ascontiguousarray(h, dtype=np.uint8), np.ascontiguousarray(probabilities, dtype=np.float64)
        self.n, self.depth = h.shape[1], depth
        self.handle = self.library.osd_create(*h.shape, h.ctypes.data, depth, p.ctypes.data)
        if not self.handle:
            raise ValueError(self.library.osd_error().decode())

    def decode(self, s, llr, trace=False):
        s = np.ascontiguousarray(s, dtype=np.uint8)
        llr = np.ascontiguousarray(llr, dtype=np.float64)
        selected = np.empty(self.n, dtype=np.uint8)
        candidates = np.empty((1+self.n+self.depth*(self.depth-1)//2, self.n), dtype=np.uint8) if trace else None
        count = self.library.osd_decode(self.handle, s.ctypes.data, llr.ctypes.data, selected.ctypes.data,
                                       candidates.ctypes.data if trace else None)
        if count < 0:
            raise ValueError(self.library.osd_error().decode())
        return selected, None if candidates is None else candidates[:count]

    def close(self):
        if self.handle:
            self.library.osd_destroy(self.handle)
            self.handle = None


def build_native(out):
    source = ROOT/'.git/osd-upstream'
    commit = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    assert commit == UPSTREAM
    assert not subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain'], text=True).strip()
    library = ROOT/'.git/osd-v2-reference.so'
    command = ['g++', '-std=c++17', '-O3', '-march=native', '-shared', '-fPIC', '-I'+str(source/'src_cpp'),
               str(out/'reference_weighted.cpp'), '-o', str(library)]
    subprocess.run(command, check=True)
    return library, dict(commit=commit, command=command, library_sha256=file_hash(library),
                         compiler=subprocess.check_output(['g++', '--version'], text=True).splitlines()[0],
                         bridge_sha256=file_hash(out/'reference_weighted.cpp'),
                         source_sha256={name: file_hash(source/name) for name in
                                        ('src_cpp/osd.hpp', 'src_cpp/gf2sparse_linalg.hpp', 'src_cpp/sort.hpp', 'LICENSE')})


def toric(length):
    """Periodic square-lattice X-component check matrix, 2L² qubits/L² checks."""
    m = length*length
    rows, columns = [], []
    for x in range(length):
        for y in range(length):
            row = x*length+y
            rows.extend([row]*4)
            columns.extend([row, x*length+(y-1) % length,
                            m+row, m+((x-1) % length)*length+y])
    return sparse.csr_matrix((np.ones(len(rows), dtype=np.uint8), (rows, columns)), shape=(m, 2*m))


def matrices():
    sources = [('toric9', 'data/reproductions/roffe-2005-07016-bp/codes/toric9.npz'),
               ('toric15', 'data/reproductions/roffe-2005-07016-bp/codes/toric15.npz'),
               ('b1_882', 'data/artifacts/b1-panteleev-kalachev-v3.npz'),
               ('lp1054', 'data/reproductions/panteleev-2012-04068-lifted-product/code.npz')]
    for label, path in sources:
        h = sparse.csr_matrix(load_artifact(ROOT, path).code.hz)
        yield label, h, dict(path=path, sha256=file_hash(ROOT/path))
    yield 'toric31', toric(31), dict(generator='periodic-square-lattice-L31-v1')


def seal_fixtures(out, samples):
    if (out/'fixtures.json').exists():
        metadata = json.loads((out/'fixtures.json').read_text())
        assert file_hash(out/'fixtures.npz') == metadata['npz_sha256']
        return metadata
    rng = np.random.default_rng(SEED)
    arrays, groups = {}, []
    for label, h, source in matrices():
        for channel in ('uniform', 'nonuniform'):
            prefix = label+'_'+channel
            probabilities = np.full(h.shape[1], .08) if channel == 'uniform' else .08*np.linspace(.35, 1.65, h.shape[1])
            processor = Osd(h, method='OSD_0', order=0, channel_probabilities=probabilities)
            cap, alpha = (32, .625) if label == 'lp1054' else (100, 'roffe')
            pipeline = CanonicalBpOsd(processor, max_iterations=cap, alpha=alpha)
            failures, mixed = [], []
            for attempt in range(512):
                error = (rng.random(h.shape[1]) < probabilities).astype(np.uint8)
                s = np.asarray(h @ error % 2, dtype=np.uint8)
                candidate, llr, converged, iterations = pipeline.bp(s)
                if len(mixed) < 16:
                    mixed.append((s.copy(), bool(converged)))
                if not converged and len(failures) < samples:
                    # Native sort ties are controlled before timing via unique,
                    # order-equivalent ranks. Preserve actual posterior too.
                    ordering = np.argsort(llr, kind='stable')
                    ranks = np.empty(h.shape[1], dtype=np.float64); ranks[ordering] = np.arange(h.shape[1])
                    failures.append((s.copy(), llr.copy(), error.copy(), candidate.copy(), ranks))
                if len(failures) == samples and len(mixed) == 16:
                    break
            if len(failures) != samples:
                raise RuntimeError(f'could not seal {samples} real BP failures: {prefix}')
            arrays.update({prefix+'_ptr': h.indptr.astype(np.int64), prefix+'_col': h.indices.astype(np.int64),
                           prefix+'_shape': np.array(h.shape), prefix+'_p': probabilities,
                           prefix+'_s': np.asarray([f[0] for f in failures]),
                           prefix+'_llr': np.asarray([f[1] for f in failures]),
                           prefix+'_truth': np.asarray([f[2] for f in failures]),
                           prefix+'_bp_candidate': np.asarray([f[3] for f in failures]),
                           prefix+'_ranks': np.asarray([f[4] for f in failures]),
                           prefix+'_mixed_s': np.asarray([f[0] for f in mixed]),
                           prefix+'_mixed_converged': np.asarray([f[1] for f in mixed])})
            groups.append(dict(id=prefix, code=label, channel=channel, shape=list(h.shape), nnz=h.nnz,
                               source=source, samples=samples, cap=cap, alpha=alpha,
                               search_attempts=attempt+1, mixed_converged=sum(f[1] for f in mixed)))
            print('sealed actual BP failures', prefix, samples, 'attempts', attempt+1, flush=True)
    np.savez_compressed(out/'fixtures.npz', **arrays)
    metadata = dict(schema='osd-v2-bp-failure-fixtures-v1', seed=SEED, groups=groups,
                    npz_sha256=file_hash(out/'fixtures.npz'),
                    claim='real canonical syndrome nonconvergence, fixed finite qualification samples; no LER inference')
    write_json(out/'fixtures.json', metadata)
    return metadata


def load_group(out, group):
    key = group['id']
    with np.load(out/'fixtures.npz') as data:
        cols, ptr, shape = data[key+'_col'], data[key+'_ptr'], tuple(data[key+'_shape'])
        h = sparse.csr_matrix((np.ones(len(cols), dtype=np.uint8), cols, ptr), shape=shape)
        probabilities = data[key+'_p']
        fixtures = list(zip(data[key+'_s'], data[key+'_ranks'], data[key+'_llr'], strict=True))
        mixed = data[key+'_mixed_s']
    return h, probabilities, fixtures, mixed


def variant(h, probabilities, depth, name, score=SCORE_SOURCE):
    options = dict(matrix_storage='packed')
    mode, materialize = 'fast', False
    if name == 'v2_full':
        mode = 'full'
    elif name == 'v2_materialized':
        materialize = True
    elif name == 'v2_no_affine':
        options['affine_reuse'] = False
    elif name == 'v2_scan_responses':
        options['response_method'] = 'scan'
    elif name == 'v2_bit_scoring':
        options['packed_scoring'] = False
    elif name == 'v2_bytes':
        options.update(candidate_representation='bytes', packed_scoring=False)
    elif name == 'v2_sparse':
        options['matrix_storage'] = 'sparse'
    elif name in ('v2_cache_hit', 'v2_cache_lru'):
        options['cache'] = AffineBasisCache(max_bytes=32*1024*1024, max_entries=16 if name.endswith('hit') else 1)
    elif name == 'v2_block128':
        options['block_size'] = 128
    processor = Osd(h, method='OSD_CS' if depth else 'OSD_0', order=depth,
                    channel_probabilities=probabilities, score=score, **options)
    return processor, dict(evidence_mode=mode, materialize_candidates=materialize)


def score_oracle(candidates, probabilities, uniform, score):
    if uniform:
        return candidates.sum(axis=1, dtype=np.int64)
    weights = np.array([math.log(1/float(p)) if score == SCORE_SOURCE else math.log1p(-float(p))-math.log(float(p)) for p in probabilities])
    # NumPy sequential prefix sums are independent from the production packed
    # set-bit walker. Include zeros at unselected original-coordinate bits.
    return np.cumsum(np.where(candidates, weights, 0.), axis=1)[:, -1]


def qualify(out, metadata, library):
    oracle = module(ROOT/'tests/test_osd_v2.py', '_osdv2_independent_oracle')
    rng = np.random.default_rng(SEED+1)
    checks = Counter()
    for case in range(100):
        m, n = int(rng.integers(1, 8)), int(rng.integers(8, 17))
        h = rng.integers(0, 2, (m, n), dtype=np.uint8)
        s = h @ rng.integers(0, 2, n, dtype=np.uint8) % 2
        llr = rng.integers(-2, 3, n).astype(float)
        _, _, free = oracle.independent_candidates(h, s, llr, 0, full_basis=True)
        for depth in sorted({0, min(3, len(free))}):
            candidates, _, _ = oracle.independent_candidates(h, s, llr, depth)
            p = rng.uniform(.001, .999, n)
            for score in (SCORE_SOURCE, SCORE_ML):
                processor = Osd(h, method='OSD_CS' if depth else 'OSD_0', order=depth, channel_probabilities=p, score=score)
                value = processor.decode(s, llr, evidence_mode='full', materialize_candidates=True)
                weights = oracle.independent_weights(candidates, p, score)
                assert np.array_equal(value.candidates(), candidates)
                assert np.array_equal(value.candidate_weights, weights)
                assert value.selected_index == int(np.argmin(weights))
                checks['tiny_independent_complete_candidate_sets'] += 1
                if score == SCORE_SOURCE:
                    order = np.argsort(llr, kind='stable'); ranks = np.empty(n); ranks[order] = np.arange(n)
                    native = Native(h, depth, p, library)
                    try:
                        winner, native_candidates = native.decode(s, ranks, trace=True)
                        assert np.array_equal(native_candidates, candidates)
                        assert np.array_equal(winner, value.candidate)
                        checks['tiny_native_weighted_complete_sets'] += 1
                    finally:
                        native.close()
    event_path = out/'equivalence-ledgers.jsonl'
    with event_path.open('w') as ledger_file:
        for group in metadata['groups']:
            h, p, fixtures, _ = load_group(out, group)
            dense = h.toarray()
            for depth in DEPTHS:
                native = Native(dense, depth, p, library)
                try:
                    for s, ranks, actual_llr in fixtures:
                        winner, expected = native.decode(s, ranks, trace=True)
                        for score in (SCORE_SOURCE, SCORE_ML):
                            processor, _ = variant(h, p, depth, 'v2_fast', score)
                            result = processor.decode(s, actual_llr, evidence_mode='full', materialize_candidates=True)
                            weights = score_oracle(expected, p, processor.uniform, score)
                            assert np.array_equal(result.candidates(), expected)
                            assert np.array_equal(result.candidate_weights, weights)
                            assert result.selected_index == int(np.argmin(weights))
                            if score == SCORE_SOURCE:
                                assert np.array_equal(result.candidate, winner)
                            if group['channel'] == 'uniform':
                                old = UniformOsd(dense, method='OSD_CS' if depth else 'OSD_0', order=depth).decode(s, actual_llr, error_rate=float(p[0]))
                                assert result.candidate_set_sha256 == old.candidate_set_sha256
                            processor.replay(s, actual_llr, result.ledger)
                            ledger_file.write(json.dumps(dict(group=group['id'], depth=depth, score=score, ledger=result.ledger), sort_keys=True)+'\n')
                            checks['actual_failure_complete_sets_and_weighted_winners'] += 1
                        for name in VARIANTS:
                            processor, options = variant(h, p, depth, name)
                            value = processor.decode(s, actual_llr, **options)
                            # Compare to source-score full result, not the ML loop's last value.
                            reference, _ = variant(h, p, depth, 'v2_fast')
                            target = reference.decode(s, actual_llr)
                            assert value.candidate_set_sha256 == target.candidate_set_sha256
                            assert np.array_equal(value.candidate, target.candidate)
                            checks['matched_ablation_semantic_equivalence'] += 1
                finally:
                    native.close()
            print('qualified native/weighted/all ablations', group['id'], flush=True)
    return dict(status='passed', checks=dict(checks), event_ledger_sha256=file_hash(event_path))


def median(values):
    return float(statistics.median(values))


def benchmark_group(out, group, library, rounds):
    h, p, fixtures, mixed = load_group(out, group)
    rows, pipeline_rows = [], []
    for depth in DEPTHS:
        processors = {name: variant(h, p, depth, name) for name in VARIANTS}
        before = module(ROOT/'data/benchmarks/osd-v2/initial-source/src/bp_registry/postprocessing/osd_v2.py', '_osdv2_before')
        before_processor = before.Osd(h, method='OSD_CS' if depth else 'OSD_0', order=depth, channel_probabilities=p, matrix_storage='packed')
        old = UniformOsd(h.toarray(), method='OSD_CS' if depth else 'OSD_0', order=depth) if group['channel'] == 'uniform' else None
        native = Native(h.toarray(), depth, p, library)
        names = list(processors)+['initial_v2']+(['v1_full'] if old is not None else [])+['native_final']
        times = {name: [] for name in names}
        round_stages = {name: [] for name in names}
        def call(name, fixture):
            s, ranks, llr = fixture
            if name == 'native_final':
                return native.decode(s, ranks)
            if name == 'v1_full':
                return old.decode(s, ranks, error_rate=float(p[0]))
            if name == 'initial_v2':
                return before_processor.decode(s, ranks)
            processor, options = processors[name]
            return processor.decode(s, ranks, **options)
        try:
            for name in names:
                for fixture in fixtures:
                    call(name, fixture)
            for fixture in fixtures:
                assert call('initial_v2', fixture).candidate_set_sha256 == call('v2_fast', fixture).candidate_set_sha256
            for repeat in range(rounds):
                ordered = names[repeat % len(names):]+names[:repeat % len(names)]
                if repeat % 2:
                    ordered.reverse()
                for name in ordered:
                    tick = time.perf_counter_ns()
                    for fixture in fixtures:
                        last = call(name, fixture)
                    times[name].append((time.perf_counter_ns()-tick)/len(fixtures))
                    if hasattr(last, 'timings_ns'):
                        round_stages[name].append(dict(last.timings_ns))
            for name in names:
                sample = call(name, fixtures[0])
                work = getattr(sample, 'work', None)
                stages = getattr(sample, 'timings_ns', None)
                baseline = times['v2_fast']
                row = dict(group=group['id'], code=group['code'], channel=group['channel'], n=h.shape[1], m=h.shape[0],
                           depth=depth, variant=name, ns_per_call_median=median(times[name]),
                           ns_per_call_p25=float(np.quantile(times[name], .25)), ns_per_call_p75=float(np.quantile(times[name], .75)),
                           paired_speed_vs_v2_fast=median([a/b for a, b in zip(baseline, times[name], strict=True)]),
                           round_ns_per_call=times[name], example_work=work, example_stages_ns=stages,
                           round_stages_last_fixture_ns=round_stages[name])
                if name in processors and processors[name][0].cache is not None:
                    row['cache_info'] = processors[name][0].cache.info()
                rows.append(row)
            # Whole-call before/after and ablated BP+OSD, with the identical BP
            # engine, inputs, activation and all actual fallback work retained.
            pipes = {name: CanonicalBpOsd(processors[name][0], max_iterations=group['cap'], alpha=group['alpha'])
                     for name in ('v2_fast', 'v2_cache_hit', 'v2_no_affine')}
            pipe = pipes['v2_fast']
            def pipeline_call(name, s):
                if name != 'v1_full':
                    return pipes[name].decode(s)
                started = time.perf_counter_ns()
                candidate, posterior, converged, iterations = pipe.bp(s)
                bp_ns = time.perf_counter_ns()-started
                tick = time.perf_counter_ns()
                osd = None if converged else old.decode(s, posterior, error_rate=float(p[0]))
                osd_ns = time.perf_counter_ns()-tick
                selected = candidate if osd is None else osd.candidate
                evidence = dict(version='historical-v1-benchmark-wrapper',
                                matrix_sha256=processors['v2_fast'][0].matrix_sha256,
                                channel_sha256=processors['v2_fast'][0].channel_sha256,
                                syndrome_sha256=_digest(s, 'u1'), bp_iterations=int(iterations), bp_converged=bool(converged),
                                bp_directed_edge_updates=2*int(iterations)*h.nnz,
                                posterior_sha256=_digest(posterior, '<f8'), selected_sha256=_digest(selected, 'u1'),
                                osd=None if osd is None else dict(work=osd.work, candidate_set_sha256=osd.candidate_set_sha256))
                evidence['ledger_sha256'] = _json_digest(evidence)
                return SimpleNamespace(candidate=selected, osd=osd, ledger=evidence,
                                       timings_ns=dict(bp=bp_ns, osd=osd_ns, total=time.perf_counter_ns()-started))
            pipeline_sets = {'failure_conditioned': [f[0] for f in fixtures], 'mixed_16_shots': list(mixed)}
            for population, syndromes in pipeline_sets.items():
                pipeline_names = list(pipes)+(['v1_full'] if old is not None else [])
                references = [pipe.decode(s).candidate for s in syndromes]
                for name in pipeline_names:
                    for s, expected in zip(syndromes, references, strict=True):
                        assert np.array_equal(pipeline_call(name, s).candidate, expected)
                latency = {name: [] for name in pipeline_names}
                bp_latency = {name: [] for name in pipeline_names}
                osd_latency = {name: [] for name in pipeline_names}
                work_samples = {}
                for repeat in range(rounds):
                    ordered = pipeline_names[repeat % len(pipeline_names):]+pipeline_names[:repeat % len(pipeline_names)]
                    if repeat % 2:
                        ordered.reverse()
                    for name in ordered:
                        tick = time.perf_counter_ns()
                        results = [pipeline_call(name, s) for s in syndromes]
                        latency[name].append((time.perf_counter_ns()-tick)/len(syndromes))
                        bp_latency[name].append(sum(r.timings_ns['bp'] for r in results)/len(results))
                        osd_latency[name].append(sum(r.timings_ns['osd'] for r in results)/len(results))
                        if repeat == 0:
                            work_samples[name] = (sum(r.osd is not None for r in results), sum(r.ledger['bp_directed_edge_updates'] for r in results))
                            with (out/'pipeline-ledgers.jsonl').open('a') as f:
                                for r in results:
                                    f.write(json.dumps(dict(group=group['id'], depth=depth, population=population, variant=name, ledger=r.ledger), sort_keys=True)+'\n')
                for name in pipeline_names:
                    osd_calls, directed = work_samples[name]
                    pipeline_rows.append(dict(group=group['id'], depth=depth, population=population, variant=name,
                                              shots=len(syndromes), osd_calls=osd_calls, bp_directed_edge_updates=directed,
                                              total_ns_median=median(latency[name]), bp_ns_median=median(bp_latency[name]),
                                              osd_ns_median=median(osd_latency[name]), rounds_total_ns=latency[name],
                                              paired_speed_vs_v2_fast=median([a/b for a, b in zip(latency['v2_fast'], latency[name], strict=True)]),
                                              claim='fixed replay latency, not a Monte Carlo LER estimate'))
        finally:
            native.close()
        print('benchmarked', group['id'], 'OSD'+str(depth), flush=True)
    return rows, pipeline_rows


def storage_crossover(out, metadata, rounds):
    rows = []
    for group in metadata['groups']:
        if group['channel'] != 'uniform':
            continue
        h, p, fixtures, _ = load_group(out, group)
        for storage in ('sparse', 'packed', 'v1_dense_and_packed'):
            setup, calls = [], []
            for _ in range(rounds):
                tick = time.perf_counter_ns()
                processor = (UniformOsd(h.toarray(), method='OSD_CS', order=10) if storage.startswith('v1') else
                             Osd(h, method='OSD_CS', order=10, channel_probabilities=p, matrix_storage=storage))
                setup.append(time.perf_counter_ns()-tick)
                kwargs = dict(error_rate=float(p[0])) if storage.startswith('v1') else {}
                processor.decode(fixtures[0][0], fixtures[0][1], **kwargs)
                tick = time.perf_counter_ns()
                result = processor.decode(fixtures[0][0], fixtures[0][1], **kwargs)
                calls.append(time.perf_counter_ns()-tick)
            rows.append(dict(code=group['code'], n=h.shape[1], m=h.shape[0], nnz=h.nnz,
                             storage=storage, constructor_ns_median=median(setup), decode_ns_median=median(calls),
                             retained_matrix_bytes=(processor.check_matrix.nbytes+processor.packed_matrix.nbytes if storage.startswith('v1') else processor.retained_matrix_bytes),
                             validation_ns=None if storage.startswith('v1') else result.timings_ns['candidate_validation'],
                             pack_ns=None if storage.startswith('v1') else result.timings_ns['pack_matrix']))
    return rows


def memory_measure(out, group, name, depth):
    h, p, fixtures, _ = load_group(out, group)
    processor, options = variant(h, p, depth, name)
    processor.decode(fixtures[0][0], fixtures[0][1], **options)  # JIT and page warmup
    gc.collect()
    def status():
        return {line.split(':')[0]: int(line.split()[1])*1024 for line in Path('/proc/self/status').read_text().splitlines()
                if line.startswith(('VmRSS:', 'VmHWM:'))}
    reset = True
    try:
        Path('/proc/self/clear_refs').write_text('5')  # Linux reset of process RSS high-water mark
    except OSError:
        reset = False
    before = status()
    tracemalloc.start()
    value = processor.decode(fixtures[0][0], fixtures[0][1], **options)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    after = status()
    return dict(group=group['id'], variant=name, depth=depth,
                rss_before_bytes=before['VmRSS'], peak_rss_bytes=after['VmHWM'],
                peak_rss_increment_bytes=max(0, after['VmHWM']-before['VmRSS']), reset_rss_hwm=reset,
                traced_peak_bytes=peak, traced_retained_bytes=current,
                lifetime_peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                exact_candidate_block_bytes=value.work['candidate_block_peak_bytes'],
                materialized_bytes=value.work['candidate_materialized_bytes'],
                retained_matrix_bytes=processor.retained_matrix_bytes,
                scope='fresh process, warm decode; traced Python/NumPy memory is not all native allocation')


def run(out, rounds, samples):
    out.mkdir(parents=True, exist_ok=True)
    affinity = sorted(os.sched_getaffinity(0))
    os.sched_setaffinity(0, {affinity[0]})
    started = time.time()
    library, native_build = build_native(out)
    metadata = seal_fixtures(out, samples)
    qualification = qualify(out, metadata, library)
    rows, pipeline_rows = [], []
    (out/'pipeline-ledgers.jsonl').write_text('')
    for group in metadata['groups']:
        a, b = benchmark_group(out, group, library, rounds)
        rows.extend(a); pipeline_rows.extend(b)
        write_json(out/'timing-progress.json', dict(rows=rows, pipeline_rows=pipeline_rows))
    crossover = storage_crossover(out, metadata, rounds)
    memory = []
    for group in (metadata['groups'][0], metadata['groups'][-1]):
        for depth in DEPTHS:
            for name in ('v2_fast', 'v2_materialized', 'v2_bytes', 'v2_full'):
                command = [sys.executable, str(Path(__file__).resolve()), '--memory', group['id'], name, str(depth), '--output', str(out)]
                value = subprocess.check_output(command, text=True)
                memory.append(json.loads(value))
                print('memory', group['id'], depth, name, flush=True)
    inputs = ['scripts/benchmark_osd_v2.py', 'src/bp_registry/postprocessing/osd_v2.py',
              'src/bp_registry/postprocessing/bp_osd_v2.py', 'src/bp_registry/postprocessing/osd.py',
                  'src/bp_registry/canonical/compiled.py', 'src/bp_registry/compiled_contracts.py',
                  'src/bp_registry/check_numerics.py', 'src/bp_registry/resolution.py', 'tests/test_osd_v2.py',
                  'data/benchmarks/osd-v2/initial-source/src/bp_registry/postprocessing/osd_v2.py']
    result = dict(schema='osd-v2-matched-benchmark-v1', status='passed', implementation=VERSION,
                  seed=SEED, rounds=rounds, samples_per_stratum=samples, warm_jit_excluded=True,
                  constructor_excluded_from_decode=True, thread_count=1,
                  hardware=dict(host=platform.node(), platform=platform.platform(),
                                cpu_model=next(line.split(':', 1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name')),
                                affinity=[affinity[0]], available_affinity=affinity,
                                slurm_job_id=os.environ.get('SLURM_JOB_ID'),
                                slurm_cpus_per_task=os.environ.get('SLURM_CPUS_PER_TASK')),
                  software=dict(python=sys.version, numpy=np.__version__,
                                git_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()),
                  native_build=native_build, qualification=qualification,
                  source_sha256={name: file_hash(ROOT/name) for name in inputs},
                  fixtures_npz_sha256=metadata['npz_sha256'], rows=rows, pipeline_rows=pipeline_rows,
                  storage_crossover=crossover, memory=memory,
                  elapsed_seconds=time.time()-started,
                  limits=['Fixed small benchmark corpus; no LER, threshold, universal speedup or historic native claim.',
                          'OSD standalone variants use identical unique order-equivalent ranks; actual posteriors qualified separately.',
                          'Native final-only omits candidate hashing/mandatory ledger; native trace used only for qualification.',
                          'Warm and cold basis reuse have different scopes; realistic changing-order cache hit rates are recorded.',
                          'Packing ablation compares byte/bit candidate XOR with packed candidate XOR at the same bitwise scoring rule.',
                          'RSS process high-water reset is OS-dependent; traced memory may omit native allocations.'])
    write_json(out/'benchmark.json', result)
    publish(out, result)
    print('BENCHMARK COMPLETE', len(rows), 'standalone rows', len(pipeline_rows), 'pipeline rows', flush=True)


def publish(out, result):
    import csv
    with (out/'timings.csv').open('w') as f:
        fields = ['group', 'depth', 'variant', 'ns_per_call_median', 'ns_per_call_p25', 'ns_per_call_p75', 'paired_speed_vs_v2_fast']
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore'); writer.writeheader(); writer.writerows(result['rows'])
    with (out/'pipeline.csv').open('w') as f:
        fields = ['group', 'depth', 'population', 'variant', 'shots', 'osd_calls', 'bp_directed_edge_updates', 'total_ns_median', 'bp_ns_median', 'osd_ns_median', 'paired_speed_vs_v2_fast']
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore'); writer.writeheader(); writer.writerows(result['pipeline_rows'])
    lines = ['# OSD v2 matched benchmark', '',
             f"Single CPU: {result['hardware']['cpu_model']}; Slurm {result['hardware']['slurm_job_id']}. "
             f"{result['rounds']} alternating rounds, {result['samples_per_stratum']} actual BP failures per stratum. "
             'Warm calls exclude construction/JIT; every v2 call includes mandatory evidence. Times are medians in microseconds.', '',
             '| Code / channel | OSD | v1 full | v2 fast | v2 full | No affine | Warm cache | Native final |',
             '|---|---:|---:|---:|---:|---:|---:|---:|']
    by = {(r['group'], r['depth'], r['variant']): r for r in result['rows']}
    for group in sorted({r['group'] for r in result['rows']}):
        for depth in DEPTHS:
            values = []
            for name in ('v1_full', 'v2_fast', 'v2_full', 'v2_no_affine', 'v2_cache_hit', 'native_final'):
                row = by.get((group, depth, name)); values.append('—' if row is None else f"{row['ns_per_call_median']/1000:.1f}")
            lines.append(f'| {group} | {depth} | '+' | '.join(values)+' |')
    lines.extend(['', 'All variants, paired round statistics, stage timings and typed work: [benchmark.json](benchmark.json) and [timings.csv](timings.csv).',
                  'Whole BP+OSD and activation rates: [pipeline.csv](pipeline.csv). Memory and storage/crossover measurements are in benchmark.json.', '',
                  '## Qualification', '', json.dumps(result['qualification']['checks'], sort_keys=True), '',
                  '## Limits', ''])
    lines.extend('- '+s for s in result['limits'])
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n')
    sealed = ['benchmark.json', 'fixtures.json', 'fixtures.npz', 'equivalence-ledgers.jsonl',
              'pipeline-ledgers.jsonl', 'timings.csv', 'pipeline.csv', 'RESULTS.md', 'reference_weighted.cpp']
    write_json(out/'manifest.json', dict(schema='osd-v2-benchmark-seal-v1', files={name: file_hash(out/name) for name in sealed}))


def verify(out, historical=False):
    manifest = json.loads((out/'manifest.json').read_text())
    for name, digest in manifest['files'].items():
        if file_hash(out/name) != digest:
            raise ValueError(f'benchmark evidence changed: {name}')
    result = json.loads((out/'benchmark.json').read_text())
    for name, digest in result['source_sha256'].items():
        if file_hash(ROOT/name) != digest:
            snapshot = out/'initial-source'/name
            if not historical or not snapshot.exists() or file_hash(snapshot) != digest:
                raise ValueError(f'implementation changed since benchmark: {name}')
    if result['status'] != 'passed' or result['qualification']['status'] != 'passed':
        raise ValueError('unqualified benchmark')
    print(json.dumps(dict(status='passed', sealed_files=len(manifest['files']), rows=len(result['rows']),
                          equivalence=result['qualification']['checks']), sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=DEFAULT)
    parser.add_argument('--run', action='store_true'); parser.add_argument('--verify', action='store_true')
    parser.add_argument('--historical', action='store_true')
    parser.add_argument('--memory', nargs=3); parser.add_argument('--rounds', type=int, default=9)
    parser.add_argument('--samples', type=int, default=3)
    args = parser.parse_args()
    if args.memory:
        group_id, name, depth = args.memory
        metadata = json.loads((args.output/'fixtures.json').read_text())
        group = next(g for g in metadata['groups'] if g['id'] == group_id)
        print(json.dumps(memory_measure(args.output, group, name, int(depth)), sort_keys=True))
    elif args.run:
        run(args.output, args.rounds, args.samples)
    elif args.verify:
        verify(args.output, args.historical)
    else:
        parser.error('choose --run, --verify or --memory')


if __name__ == '__main__':
    main()
