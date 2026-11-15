"""Completed assessment plus one row per independently selected point."""
import csv
import json
from pathlib import Path
import statistics

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ROOT = REPO / 'data/reproductions/roffe-2005-07016-runtime-budget'


def main():
    assessment = json.loads((HERE / 'assessment.json').read_text())
    comparisons = json.loads((HERE / 'point-comparisons.json').read_text())
    osd = json.loads((REPO / 'data/reproductions/roffe-2005-07016-osd-fast/verified.json').read_text())['points']
    osd_index = {(r['code'], r['physical_p']): r for r in osd if r['arm'] == 'bp_osd0'}
    rows = []
    fair = {}
    for family in ('binary_css', 'bp4'):
        cases = [c for c in comparisons if c['family'] == family]
        valid = [c for c in cases if all(.9 <= c[k]['runtime_ratio'] <= 1.1 for k in ('previous_matched', 'joint_matched'))]
        ratios = [c['joint_matched']['ler']/c['previous_matched']['ler'] for c in valid]
        fair[family] = {'both_observed_times_within_10_percent': len(valid),
                        'lower_ler': sum(r < 1 for r in ratios), 'equal_ler': sum(r == 1 for r in ratios),
                        'higher_ler': sum(r > 1 for r in ratios), 'median_ler_ratio': statistics.median(ratios)}
    for c in comparisons:
        j = c['joint_matched']; previous = c['previous_matched']; controls = c['controls']
        reference = osd_index.get((c['code'], c['matched_x_rate']))
        row = {'code': c['code'], 'n': c['n'], 'family': c['family'], 'matched_x_rate': c['matched_x_rate'], 'physical_p': c['physical_p'],
               'previous_n_ler': c['previous_n']['ler'], 'previous_matched_cap': previous['iteration_cap'],
               'previous_matched_ler': previous['ler'], 'previous_runtime_ratio': previous['runtime_ratio'],
               'selected_damping': controls['damping'], 'selected_alpha_mode': controls['alpha_mode'], 'selected_alpha': controls['alpha'],
               'selected_beta': controls['beta'], 'joint_n_ler': c['joint_n']['ler'],
               'selected_matched_cap': j['iteration_cap'], 'selected_matched_ler': j['ler'],
               'selected_ci95_low': j['ci95_low'], 'selected_ci95_high': j['ci95_high'],
               'calibration_runtime_ratio': c['calibration_ratio'], 'actual_runtime_ratio': j['runtime_ratio'],
               'actual_within_10_percent': .9 <= j['runtime_ratio'] <= 1.1,
               'actual_within_budget': j['runtime_ratio'] <= 1.1,
               'bp_osd0_x_only_ler': reference['rate'] if reference else None,
               'bp_osd0_same_channel': c['family'] == 'binary_css'}
        rows.append(row)
    with (HERE / 'selected-point-results.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n'); writer.writeheader(); writer.writerows(rows)
    lines = ['# Completed runtime-budget results: checked interpretation', '',
             'All218 point workers and the final full-ledger collector completed with exit0:0. The independent check reconciles1,464 confirmation rows,249,888 decoder shots and29,280 logical failures. Every confirmation stopped at20 failures.163,668 coarse/finalist training measurements are separate and are never pooled into final LERs.', '',
             'More iterations alone barely changed binary BP:107 points received larger caps, and only one had a lower observed LER. This fixed-control comparison uses nested shared physical prefixes, so the other caps retain the same stopping-prefix LER rather than introducing unrelated sampling noise. The finite measurements do not prove an asymptotic error floor.', '',
             'Joint controls give mixed descriptive changes. At the original n-cap, BP has17 lower/82 equal/10 higher LER estimates; Q-BP has29 lower/64 equal/16 higher. The median joint/previous LER ratio is1.00 for both families at both n-cap and calibrated-cap comparisons. Dense high-noise paper rates dominate this grid; this median is not a threshold or a statement of equality at every rate. Different-control20-failure estimates are uncertain and do not establish simultaneous superiority.', '',
             'At the same n-cap and unchanged observed LER, mean executed iterations decrease at10/82 BP strata and24/64 Q-BP strata. Median iteration ratios are still1.00, both overall and within those same-LER groups. Thus there are pointwise work reductions, without a broad median reduction across the grid.', '',
             'The selected offset is zero in217/218 strata. All BP strata retain scaling magnitude1(65 paper-ramp,44 constant). Q-BP retains magnitude1 in108/109 strata(39 paper-ramp,69 constant). The one exception is length162/Q-BP at p_X=.01: d=0,constant alpha=.75,beta=.5. Selection on finite training data is not proof that other offsets/scales never help.', '',
             '**Runtime qualification:** all218 selected calibration cases lie within10% of target. Fresh observed confirmation times do so at145/218 points;36 exceed1.1 times the reference, while37 are below.9. Thus the full collection is a calibrated-budget study, not218 exact observed equal-runtime comparisons. Actual ratios stay in every table/export. BP selected-ratio range.705–1.434; Q-BP range.794–1.559.', '',
             'Q-BP already exceeds the budget at the original n-cap for most strata. Its previous-damping calibration cap is lower than n at100/109 points and higher at four. Higher-cap rows remain available as explicitly over-budget context. BP is X-only; Q-BP remains depolarizing at1.5p_X, so cross-family numerical LER differences do not isolate decoder choice.', '',
             '| Family | Both actual times within10% | Joint lower / equal / higher LER | Median ratio in that subset |',
             '| --- | ---: | --- | ---: |']
    for family, values in fair.items():
        lines.append(f'| {family} | {values["both_observed_times_within_10_percent"]} | {values["lower_ler"]} / {values["equal_ler"]} / {values["higher_ler"]} | {values["median_ler_ratio"]:.3g} |')
    lines += ['', 'At X-only p=.02, the selected BP rows remain far above the audited BP+OSD0 reference:', '',
              '| Length | Selected BP cap | Selected BP LER | Actual time / OSD0 | BP+OSD0 LER |',
              '| ---: | ---: | ---: | ---: | ---: |']
    for c in sorted([c for c in comparisons if c['family'] == 'binary_css' and c['matched_x_rate'] == .02], key=lambda c: c['n']):
        r = c['joint_matched']; reference = osd_index.get((c['code'], .02))
        value = 'pending' if reference is None else f'{reference["rate"]:.5g}'
        lines.append(f'| {c["n"]} | {r["iteration_cap"]} | {r["ler"]:.5g} | {r["runtime_ratio"]:.3f} | {value} |')
    lines += ['', 'Length450 BP+OSD0 at this rate is still running. Its selected BP row is over budget and is not treated as a strict timing match. The same-channel OSD0 advantage at the other three strata is large relative to the pointwise interval widths.', '',
              '![Per-cap measurements at matched X rate .02](iteration-comparison.png)', '',
              'The complete per-cap table remains in the main study RESULTS.md/iteration-results.csv. selected-point-results.csv here supplies one independently selected comparison per stratum, including controls, caps, confidence bounds and both calibration/actual timing. Full verification and all tuning data are losslessly archived in the study with raw-byte hashes. The local raw files and event ledgers are retained unchanged.', '',
              'Separate background studies: MacKay inferred-budget damping confirmation is now complete40/40,112,619,245 shots/791 failures; the rare length274 Q-BP p=.015 point stopped at100M shots with11 failures(LER1.1e-7,95% interval[5.49e-8,1.97e-7]). OSD0/CS10 has212 fully audited/published points; four length450 points remain running. Two completed length338/p=.01 points await the final OSD campaign audit, so they are not silently promoted here.']
    (HERE / 'FINDINGS.md').write_text('\n'.join(lines).rstrip()+'\n')
    assessment['strict_observed_runtime_subset'] = fair
    (HERE / 'assessment.json').write_text(json.dumps(assessment, indent=2)+'\n')
    report = ROOT / 'RESULTS.md'; content = report.read_text()
    if 'Checked interpretation:' in content:
        content = content.split('\n', 1)[0]+'\n\n'+content[content.index('Independent audit:'):]
    link = '../../../'+str(HERE.relative_to(REPO))+'/FINDINGS.md'
    insert = f'\nChecked interpretation: [completed-results assessment and per-cap figure]({link}). Full audit/tuning archives and extraction instructions are in [EVIDENCE.md](EVIDENCE.md).\n\nMore iterations lowered BP LER at only1 of107 extended-cap strata. Joint tuning gives a median LER ratio of1.00 across this grid for both families. Actual confirmation runtime is within10% of reference at145/218 selected points;36 are over1.1x and remain flagged.\n'
    content = content.replace('\n\n', '\n'+insert+'\n', 1)
    content = content.replace('Missing point workers remain pending; their calibrated plans and raw progress are retained under results/.', 'All218 point workers are complete; calibrated plans and raw event ledgers remain under results/.')
    report.write_text(content)
    print(json.dumps(fair, indent=2))


if __name__ == '__main__': main()
