"""Benchmark hygiene: matched representations, weights and sealed BP failures."""
import importlib.util
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('_osdv2_benchmark', ROOT/'scripts/benchmark_osd_v2.py')
bench = importlib.util.module_from_spec(spec); spec.loader.exec_module(bench)


def test_all_ablation_variants_preserve_candidate_hash_on_nonuniform_channel():
    rng = np.random.default_rng(600)
    h = sparse.csr_matrix(rng.integers(0, 2, (5, 70), dtype=np.uint8))
    p = np.linspace(.01, .3, 70)
    s = np.ones(5, dtype=np.uint8); llr = rng.integers(-1, 2, 70).astype(float)
    values = []
    for depth in (0, 1, 10, 60):
        for name in bench.VARIANTS:
            processor, options = bench.variant(h, p, depth, name)
            value = processor.decode(s, llr, **options)
            values.append((depth, value.candidate_set_sha256))
        assert len({digest for d, digest in values if d == depth}) == 1


def test_toric_generator_rows_have_four_edges_and_one_dependency():
    h = bench.toric(3).toarray()
    assert h.shape == (9, 18) and np.all(h.sum(axis=1) == 4)
    assert not np.any(h.sum(axis=0) % 2)


def test_score_oracle_original_coordinate_prefix_sum_matches_scalar_fold():
    rng = np.random.default_rng(318)
    candidates = rng.integers(0, 2, (100, 130), dtype=np.uint8)
    p = rng.uniform(.001, .999, 130)
    for score in (bench.SCORE_SOURCE, bench.SCORE_ML):
        weights = np.array([__import__('math').log(1/float(v)) if score == bench.SCORE_SOURCE
                            else __import__('math').log1p(-float(v))-__import__('math').log(float(v)) for v in p])
        expected = []
        for row in candidates:
            total = 0.
            for bit, weight in zip(row, weights, strict=True):
                if bit:
                    total += weight
            expected.append(total)
        assert np.array_equal(bench.score_oracle(candidates, p, False, score), expected)


def test_published_evidence_verifies_when_present():
    if not (bench.DEFAULT/'manifest.json').exists():
        pytest.skip('single-CPU qualification not published yet')
    bench.verify(bench.DEFAULT)


def test_published_report_and_measured_memory_contract_when_present():
    path = bench.DEFAULT/'analysis-manifest.json'
    if not path.exists():
        pytest.skip('derived qualified tables not published yet')
    seal = json.loads(path.read_text())
    assert seal['benchmark_manifest_sha256'] == sha256((bench.DEFAULT/'manifest.json').read_bytes()).hexdigest()
    assert seal['script_sha256'] == sha256((ROOT/'scripts/report_osd_v2.py').read_bytes()).hexdigest()
    for name, digest in seal['files'].items():
        assert sha256((bench.DEFAULT/name).read_bytes()).hexdigest() == digest
    result = json.loads((bench.DEFAULT/'benchmark.json').read_text())
    replay = json.loads((bench.DEFAULT/'replay-verification.json').read_text())
    assert replay['status'] == 'passed'
    assert replay['benchmark_manifest_sha256'] == sha256((bench.DEFAULT/'manifest.json').read_bytes()).hexdigest()
    assert replay['analysis_manifest_sha256'] == sha256(path.read_bytes()).hexdigest()
    assert replay['verifier_sha256'] == sha256((ROOT/'scripts/verify_osd_v2.py').read_bytes()).hexdigest()
    assert replay['counts']['full_osd_equivalence_ledgers_replayed'] == 240
    assert replay['counts']['published_pipeline_event_ledgers_verified'] == 2660
    assert len(result['rows']) == 540 and len(result['pipeline_rows']) == 280
    assert result['hardware']['slurm_cpus_per_task'] == '1'
    for measurement in result['memory']:
        assert measurement['peak_rss_bytes'] >= measurement['rss_before_bytes']
        assert measurement['traced_peak_bytes'] >= measurement['traced_retained_bytes']
    for group in {m['group'] for m in result['memory']}:
        rows = {m['variant']:m for m in result['memory'] if m['group'] == group and m['depth'] == 60}
        assert rows['v2_fast']['materialized_bytes'] == 0
        assert rows['v2_materialized']['materialized_bytes'] > 0
        assert rows['v2_fast']['traced_peak_bytes'] < rows['v2_materialized']['traced_peak_bytes']
