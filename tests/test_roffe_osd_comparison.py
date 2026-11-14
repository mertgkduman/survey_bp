"""Qualified source extraction and channel-aware joins without invented data."""
from copy import deepcopy
import csv
import importlib.util
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / 'data/reproductions/roffe-2005-07016-osd-comparison'
ARCHIVE = REPO / '.git/roffe-source/source.tar'
spec = importlib.util.spec_from_file_location('_test_roffe_osd_comparison', ROOT / 'compare.py')
comparison = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparison)


def fixtures():
    return (json.loads((ROOT / 'source_points.json').read_text()),
            json.loads((comparison.DAMPING / 'confirmation/verified.json').read_text()))


@pytest.mark.skipif(not ARCHIVE.exists(), reason='exact source archive is a local cache; numerical source artifact remains tested')
def test_all_main_panel_curves_reextract_exactly_without_inset_duplicates():
    source = comparison.extract(ARCHIVE)
    assert source == json.loads((ROOT / 'source_points.json').read_text())
    assert {d: len(p) for d, p in source['curves']['bp_osd_cs'].items()} == {'9': 25, '11': 28, '13': 28, '15': 27}
    assert sum(map(len, source['curves']['bp'].values())) == 109
    assert sum(map(len, source['curves']['bp_osd_cs'].values())) == 108
    assert source['combination_sweep_lambda'] == 60 and source['source_channel'] == 'x_only'


def test_source_pins_reject_other_revisions(tmp_path):
    wrong = tmp_path / 'source.tar'; wrong.write_bytes(b'wrong revision')
    with pytest.raises(ValueError, match='pinned arXiv'):
        comparison.extract(wrong)
    with pytest.raises(ValueError, match='qualified revision'):
        comparison.extract_figure(b'changed figure')


def test_log_axis_calibration_and_independent_ordinate_spot_checks():
    source, _ = fixtures()
    assert comparison.probability(2.716649) == 1.
    assert comparison.probability(2.716649-.458176) == pytest.approx(.01)
    expected = {'9': 6.54697e-7, '11': 4.45996e-8, '13': 2.29999e-9, '15': 1.94598e-7}
    for distance, value in expected.items():
        point = source['curves']['bp_osd_cs'][distance][0]
        assert point['p'] == (.02 if distance == '15' else .01)
        assert point['block_ler_approx'] == pytest.approx(value, rel=1e-5)
        assert point['drawn_errorbar_low_approx'] <= point['block_ler_approx'] <= point['drawn_errorbar_high_approx']


def test_all_confirmation_results_join_at_exact_rates_with_explicit_missing_value():
    source, receipt = fixtures()
    rows = comparison.join(source, receipt)
    assert len(rows) == 109
    assert sum(r['paper_bp_osd_cs_ler_approx'] is not None for r in rows) == 108
    missing = next(r for r in rows if r['code'] == 'toric15' and r['x_only_physical_p'] == .01)
    assert missing['paper_bp_osd_cs_status'] == 'not_plotted'
    assert missing['paper_bp_osd_cs_ler_approx'] is None
    assert missing['bp_damped_ler_over_paper_osd_cs'] is None
    for r in rows:
        assert r['qbp_depolarizing_physical_p'] == 1.5*r['x_only_physical_p']
        assert r['paper_bp_osd_cs_shots'] is r['paper_bp_osd_cs_mean_iterations'] is r['paper_errorbar_confidence_level'] is None
        assert r['bp_iteration_cap'] == r['n']
        for prefix in ('bp_undamped', 'bp_damped', 'qbp_undamped', 'qbp_damped'):
            assert r[prefix+'_shots']*r[prefix+'_ler'] == pytest.approx(20)
    r = next(r for r in rows if r['code'] == 'toric9' and r['x_only_physical_p'] == .02)
    assert r['paper_bp_osd_cs_ler_approx'] == pytest.approx(3.27116e-5, rel=1e-5)
    assert r['bp_damped_ler'] == pytest.approx(20/275)
    assert r['qbp_damped_ler'] == pytest.approx(20/3548)


def test_join_rejects_missing_duplicates_and_wrong_channel():
    source, receipt = fixtures()
    for points in (receipt['points'][:-1], receipt['points']+[receipt['points'][0]]):
        with pytest.raises(ValueError, match='confirmation inventory'):
            comparison.join(source, {**receipt, 'points': points})
    bad = deepcopy(receipt)
    next(r for r in bad['points'] if r['base_arm'] == 'qbp_ms')['physical_p'] = .01
    with pytest.raises(AssertionError):
        comparison.join(source, bad)


def test_complete_csv_preserves_undefined_source_counts_and_work():
    with (ROOT / 'comparison-table.csv').open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 109
    assert sum(bool(r['paper_bp_osd_cs_ler_approx']) for r in rows) == 108
    assert all(not r['paper_bp_osd_cs_shots'] and not r['paper_bp_osd_cs_mean_iterations'] for r in rows)
    missing = next(r for r in rows if r['paper_bp_osd_cs_status'] == 'not_plotted')
    assert missing['code'] == 'toric15' and not missing['paper_drawn_errorbar_low_approx']
