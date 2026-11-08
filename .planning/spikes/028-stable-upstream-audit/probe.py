"""Explicit native alignment and source-derived numerical envelope comparison."""
from dataclasses import replace
from pathlib import Path
from hashlib import sha256
from importlib.util import spec_from_file_location,module_from_spec,find_spec
from itertools import product
import json,math
import numpy as np
import ldpc
from audit_support import Audit
from bp_registry.resolution import STABLE_SPA_F64
from bp_registry.canonical.compiled import CompiledBinaryFlooding
HERE=Path(__file__).parent

def load(name,folder):
    spec=spec_from_file_location(name,HERE.parent/folder/'probe.py');m=module_from_spec(spec);spec.loader.exec_module(m);return m
oracle=load('parity_oracle','019-numerical-envelope');native=load('native_scope','013-v3-upstream-audit')
POLICY=replace(STABLE_SPA_F64,damping=0.,zero_syndrome_shortcut=False)


def aligned_native():
    h=np.array([[1,1,1,0,0],[0,1,0,1,1],[1,0,1,1,0]],dtype=np.uint8)
    graph=CompiledBinaryFlooding.from_check_matrix(h,policy=POLICY);worst=0.;cases=0;ties=0
    for rate,bits,cap in product((.071,.283,.6),list(product((0,1),repeat=3))[1:],(1,3,6)):
        s=np.array(bits,dtype=np.uint8)
        decoder=ldpc.BpDecoder(h,error_rate=rate,max_iter=cap,bp_method='product_sum',schedule='parallel',input_vector_type='syndrome')
        candidate=decoder.decode(s);old=np.full(len(graph.variables),math.log1p(-rate)-math.log(rate))
        for _ in range(decoder.iter):
            result=graph.sweep(old,s,error_rate=rate);old=result.new_v2c
        expected=np.asarray(decoder.log_prob_ratios);error=float(np.max(abs(result.beliefs-expected)));worst=max(worst,error)
        assert error<2e-11
        different=np.flatnonzero(candidate!=result.candidate)
        assert all(abs(expected[i])<2e-11 and abs(result.beliefs[i])<2e-11 for i in different)
        ties+=len(different);cases+=1
    binary=next(Path(ldpc.__file__).parent.glob('bp_decoder/_bp_decoder*.so'))
    return dict(cases=cases,tolerance=2e-11,max_posterior_error=worst,tie_coordinates=ties,
        alignment='float64 parallel sum-product, zero damping, nonzero syndromes, actual native terminal iteration',
        binary_sha256=sha256(binary.read_bytes()).hexdigest(),native_build_commit='not established; installed binary identity retained')


def high_confidence():
    h=np.ones((1,3),dtype=np.uint8);s=np.array([1],dtype=np.uint8);rows=[]
    graph=CompiledBinaryFlooding.from_check_matrix(h,policy=POLICY)
    for magnitude in (1.,10.,20.,30.,38.,40.,100.,500.):
        rate=math.exp(-magnitude)/(1+math.exp(-magnitude));decoder=ldpc.BpDecoder(h,error_rate=rate,max_iter=1,bp_method='product_sum',schedule='parallel',input_vector_type='syndrome')
        decoder.decode(s);actual=graph.sweep(np.full(3,magnitude),s,error_rate=rate).beliefs
        exact=magnitude-oracle.parity_llr([magnitude,magnitude]);assert np.max(abs(actual-exact))<2e-11
        rows.append(dict(prior_llr=magnitude,exact_posterior=exact,stable_posterior=actual,native_posterior=[float(x) if np.isfinite(x) else str(x) for x in decoder.log_prob_ratios]))
    return dict(rows=rows,interpretation='native high-confidence divergence is classified; exact inference defines acceptance, not matching native defects')


def source_phi():
    # Deliberate NumPy transcription of pinned source operations, NOT Sionna execution.
    # Source always bounds phi arguments, even with optional output clipping None.
    def phi(x):
        x=np.clip(x,1e-12,28.324079);return np.log(np.exp(x)+1)-np.log(np.exp(x)-1)
    rows=[]
    for magnitude in (.1,1.,10.,20.,40.,100.):
        values=np.full(3,magnitude);mapped=phi(abs(values));out=phi(mapped.sum()-mapped)
        expected=oracle.parity_llr([magnitude,magnitude])
        rows.append(dict(input=magnitude,source_transcription=float(out[0]),exact=expected,absolute_error=abs(float(out[0])-expected)))
    assert rows[-1]['absolute_error']>50
    return dict(source=json.loads((HERE/'sionna-source.json').read_text()),
        execution='NumPy operation transcription only; torch/Sionna not executed',torch_available=find_spec('torch') is not None,
        rows=rows,design_correspondence='extrinsic check update; pluggable CN/VN updates, ordered callbacks, schedule/state interfaces',
        adaptation='different stable arithmetic, explicit finite unary convention, no inherited phi bounds')

if __name__=='__main__':
    a=Audit(HERE);a.probe('stable_SPA_aligned_native_ldpc',aligned_native);a.probe('stable_SPA_high_confidence_oracle',high_confidence)
    a.probe('source_phi_bound_classification',source_phi);a.probe('native_NMS_controls',native.normalized_min_sum)
    a.probe('native_Relay_inner_memory_controls',native.native.relay_crosscheck);a.probe('native_aSCED_zero_classification',native.source_zero_checks);a.finish()
