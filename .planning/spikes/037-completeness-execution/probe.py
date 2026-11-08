from pathlib import Path
from dataclasses import replace
from tempfile import TemporaryDirectory
from itertools import product
import sys,json
import numpy as np
import stim
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from audit_support import Audit
from bp_registry.circuit.dem import DemBinaryModel
from bp_registry.circuit.sinter_adapter import CanonicalBpSinterDecoder
from bp_registry.canonical.problems import OriginalProblem
from bp_registry.quaternary.problems import PauliCode
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.resolution import STABLE_SPA_F64
HERE=Path(__file__).parent


def dem_semantics():
    model=DemBinaryModel.from_dem(stim.DetectorErrorModel('error(1) D0 L0\nerror(0) D1\nerror(0.1) D0 ^ D1 L0\nerror(0.2) D1 L1\nerror(0.3) L0'))
    h=np.zeros((2,3),dtype=np.uint8)
    for c,v in model.table.edges:h[c,v]=1
    np.testing.assert_array_equal(h,[[1,0,0],[1,1,0]])
    np.testing.assert_array_equal(model.observable_matrix,[[1,0,1],[0,1,0]])
    np.testing.assert_array_equal(model.syndrome_bias,[1,0]);np.testing.assert_array_equal(model.observable_bias,[1,0])
    np.testing.assert_allclose(1/(1+np.exp(model.prior_llrs)),[.1,.2,.3],atol=1e-15,rtol=0)
    for x,y,z in product((0,1),repeat=3):
        v=np.array([x,y,z],dtype=np.uint8)
        np.testing.assert_array_equal((h@v%2)^model.syndrome_bias,[1^x,x^y])
        np.testing.assert_array_equal((model.observable_matrix@v%2)^model.observable_bias,[1^x^z,y])
    return dict(assignments=8,source_error_count=model.source_error_count,independent_variables=3,separator_does_not_split_mechanism=True,unobserved_fault_retained=True)


def circuit_admission(a):
    decoder=CanonicalBpSinterDecoder().compile_decoder_for_dem(dem=stim.DetectorErrorModel('error(.1) D0 L0'))
    for name,kwargs in [('negative_limit',{'max_iterations':-1}),('unknown_rule',{'rule':'unknown'}),('unknown_tie',{'tie_break':'unknown'})]:
        try:replace(decoder,**kwargs)
        except (ValueError,TypeError):rejected=True
        else:rejected=False
        a.record('D03_circuit_compiled_'+name,rejected,accepted_invalid=not rejected)
    for name,kwargs in [('nonfinite_prior',{'prior_llrs':np.array([np.nan])}),('bad_CSR',{'row_ptr':np.array([0,999])})]:
        try:replace(decoder.model,**kwargs)
        except (ValueError,TypeError):rejected=True
        else:rejected=False
        a.record('D03_DEM_model_'+name,rejected,accepted_invalid=not rejected,unsafe_compiled_execution_not_attempted=True)


def ownership(a):
    original=OriginalProblem('audit-original',np.ones((1,2),dtype=np.uint8),np.ones((1,2),dtype=np.uint8),np.array([0],dtype=np.uint8))
    code=PauliCode(checks=np.array([[1,1]],dtype=np.uint8))
    for name,arr in [('binary_original',original.hz),('Pauli_code',code.checks)]:
        try:arr.setflags(write=True);arr.flat[0]=0
        except ValueError:changed=False
        else:changed=True
        a.record('D04_immutable_'+name,not changed,write_flag_reenabled=changed)
    decoder=CanonicalBpSinterDecoder().compile_decoder_for_dem(dem=stim.DetectorErrorModel('error(.1) L0'))
    events=np.empty((1,0),dtype=np.uint8);before=decoder.decode_detailed(events)[0];identity=decoder.model.dem_sha256
    try:decoder.model.prior_llrs.setflags(write=True);decoder.model.prior_llrs[:]*=-1
    except ValueError:changed=False
    else:changed=True
    after=decoder.decode_detailed(events)[0]
    a.record('D04_DEM_identity_binds_execution',not changed,before=before,after=after,identity_unchanged=identity==decoder.model.dem_sha256)


def batch_evidence(a):
    graph=CompiledBinaryFlooding.from_check_matrix(np.array([[1,0]],dtype=np.uint8),policy=STABLE_SPA_F64)
    result=graph.run_batch(np.array([[1]],dtype=np.uint8),error_rate=.2,max_iterations=2)
    try:result.candidates.setflags(write=True);result.candidates[0,0]^=1
    except ValueError:changed=False
    else:changed=True
    with TemporaryDirectory() as d:
        p=Path(d)/'events.jsonl'
        try:result.write_ledger(p)
        except (ValueError,TypeError):rejected=True;row=None
        else:rejected=False;row=json.loads(p.read_text())
    if row is not None:(HERE/'mutated-batch-event.json').write_text(json.dumps(row,indent=2)+'\n')
    a.record('D05_batch_evidence_matches_returned_candidate',not changed or rejected,changed=changed,export_rejected=rejected,event=row)

def valid_boundary_controls():
    rejected=0
    for kwargs in ({'max_iterations':-1},{'rule':'unknown'},{'tie_break':'unknown'}):
        try:CanonicalBpSinterDecoder(**kwargs)
        except ValueError:rejected+=1
    assert rejected==3
    return dict(factory_rejections=rejected,classification='factory guards work; alternate construction bypass is D03')


def compiled_ownership_control():
    graph=CompiledBinaryFlooding.from_check_matrix(np.array([[1,0]],dtype=np.uint8),policy=STABLE_SPA_F64)
    for value in (graph.row_ptr,graph.variables):
        try:value.setflags(write=True)
        except ValueError:pass
        else:raise AssertionError('compiled graph storage became writable')
    return dict(immutable_buffers=2)


def ledger_control():
    graph=CompiledBinaryFlooding.from_check_matrix(np.array([[1,0]],dtype=np.uint8),policy=STABLE_SPA_F64)
    result=graph.run_batch(np.array([[1]],dtype=np.uint8),error_rate=.2,max_iterations=2)
    path=HERE/'valid-batch-event.jsonl';result.write_ledger(path);row=json.loads(path.read_text())
    assert row['candidate_valid'] and row['candidate'][0]==row['syndrome'][0]
    return dict(rows=1,valid=True)


if __name__=='__main__':
    a=Audit(HERE);a.probe('DEM_affine_parity_projection',dem_semantics);a.probe('circuit_factory_validation_control',valid_boundary_controls);a.probe('compiled_graph_ownership_control',compiled_ownership_control);a.probe('unmodified_batch_ledger_control',ledger_control);circuit_admission(a);ownership(a);batch_evidence(a);a.finish()
