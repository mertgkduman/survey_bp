"""Independent sparse author/canonical matrix and released Table4 metadata checks."""
import csv
from hashlib import sha256
import json
from pathlib import Path
import sys
import numpy as np
import stim
from bp_registry.circuit.dem import DemBinaryModel
ROOT=Path(__file__).resolve().parent
REFERENCE=ROOT/'results/reference/prior'


def check():
    manifest=json.loads((ROOT/'reference-manifest.json').read_text())
    assert sha256((ROOT/'reference-qualification.tar.gz').read_bytes()).hexdigest()==manifest['archive_sha256']
    ref=ROOT/'results/reference'
    if not ref.exists():
        import tarfile
        with tarfile.open(ROOT/'reference-qualification.tar.gz') as archive:archive.extractall(ref,filter='data')
    for name,digest in manifest['files'].items():assert sha256((ref/name).read_bytes()).hexdigest()==digest
    sys.path.insert(0,str(REFERENCE))
    from priortilt.dem import dem_to_matrices
    from priortilt.params import xyz_schedule
    source=json.loads((ROOT/'source.json').read_text());schedule=xyz_schedule('BB144',.003)
    assert source['prior_schedule']['ends']==schedule['ends'] and source['prior_schedule']['phases']==schedule['phases']
    rows=[]
    for case in source['circuits']:
        path=ROOT/'circuits'/case['file'];assert sha256(path.read_bytes()).hexdigest()==case['sha256']
        circuit=stim.Circuit.from_file(str(path));dem=circuit.detector_error_model();model=DemBinaryModel.from_dem(dem)
        author=dem_to_matrices(dem);h=author.check_matrix.tocsr()
        assert np.array_equal(h.indptr,model.row_ptr) and np.array_equal(h.indices,model.variables) and np.all(h.data==1)
        np.testing.assert_array_equal(author.observables_matrix.toarray(),model.observable_matrix)
        expected=np.array([i.args_copy()[0] for i in dem.flattened() if i.type=='error'])
        np.testing.assert_array_equal(author.priors,expected)
        assert model.table.variable_count==len(expected)==author.check_matrix.shape[1]
        assert model.table.check_count==1728 and model.table.variable_count>67000
        rows.append({'file':case['file'],'checks':model.table.check_count,'mechanisms':model.table.variable_count,'edges':model.table.edge_count,
                     'detector_merge_collisions':0,'execution_sha256':model.execution_sha256,'author_sparse_H_A_priors_exact':True})
    path=ROOT/'source-data/BB144_XYZ_p0.003.csv';assert sha256(path.read_bytes()).hexdigest()==source['source_csv_sha256']
    raw=list(csv.DictReader(path.open()));assert len(raw)==4
    for r in raw:
        meta=json.loads(r['json_metadata']);params=json.loads(r['decoder_params'])
        assert meta['experiment']=='xyz' and meta['code']=='BB144' and meta['p_CNOT']==.003 and meta['syndrome_rounds']==12
        if r['decoder']=='PriorTilt_3phase':
            assert params['schedule']=={k:schedule[k] for k in ('ends','phases')}
            assert (params['initial_iters'],params['round_len'],params['max_rounds'],params['num_results'])==(60,6,6000,1)
        else:
            assert r['decoder']=='RelayBP-5' and params=={'num_sets':601,'pre_iter':80,'set_max_iter':60,'gamma0':.125,'gamma_dist_interval':[-.24,.66],'num_results':5}
    table=list(csv.DictReader((ROOT/'source-table4.csv').open()))
    for r in table:
        matches=[v for v in raw if v['decoder']==r['method']]
        assert float(r['ler_per_cycle'])==sum(int(v['errors'])/int(v['shots']) for v in matches)/12
    evidence={'source_commit':source['commit'],'circuits':rows,'source_basis_rows':4,'source_table_points':2,
              'source_csv_sha256':source['source_csv_sha256'],'prior_schedule_exact':True,
              'relay_budget_interpretation':source['relay_budget_interpretation'],
              'scope':'Exact sparse author/canonical H and A and priors; no dense H, no dropped/split/merged mechanisms; paper total-leg budget explicit.'}
    (ROOT/'source-contract.json').write_text(json.dumps(evidence,indent=2)+'\n');return evidence


if __name__=='__main__':print(json.dumps(check(),indent=2))
