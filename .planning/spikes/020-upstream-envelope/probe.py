"""Native boundary behavior is classified rather than copied as an oracle."""
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec
from dataclasses import replace
from hashlib import sha256
import math
import numpy as np
import ldpc
from audit_support import Audit
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.canonical.numerics import BINARY_SPA_F64_V3
from bp_registry.resolution import BpFloodingPolicy,ResolutionPolicy

HERE=Path(__file__).parent
def load(name,path):
    spec=spec_from_file_location(name,HERE.parent/path/'probe.py');module=module_from_spec(spec);spec.loader.exec_module(module);return module
oracle=load('envelope_oracle','019-numerical-envelope')
native=load('pinned_comparisons','013-v3-upstream-audit')


def ldpc_envelope():
    rows=[];h=np.ones((1,3),dtype=np.uint8);syndrome=np.array([1],dtype=np.uint8)
    for magnitude in (.1,1.,10.,20.,30.,38.,40.,100.,500.):
        p=math.exp(-magnitude)/(1+math.exp(-magnitude))
        reference=ldpc.BpDecoder(h,error_rate=p,max_iter=1,bp_method='product_sum',schedule='parallel',input_vector_type='syndrome')
        reference.decode(syndrome)
        actual=np.array(reference.log_prob_ratios)
        graph=CompiledBinaryFlooding.from_check_matrix(h,profile=replace(BINARY_SPA_F64_V3,v2c_damping=0.))
        canonical=graph.sweep(np.full(3,magnitude),syndrome,error_rate=p).beliefs
        exact=magnitude-oracle.parity_llr([magnitude,magnitude])
        assert reference.iter==1 and np.all(np.isfinite(canonical))
        rows.append(dict(prior_llr=magnitude,exact_posterior=exact,
                         ldpc_posterior=[float(x) if np.isfinite(x) else str(x) for x in actual],
                         canonical_posterior=canonical,ldpc_finite=bool(np.all(np.isfinite(actual)))))
    binary=next(Path(ldpc.__file__).parent.glob('bp_decoder/_bp_decoder*.so'))
    return dict(rows=rows,binary_sha256=sha256(binary.read_bytes()).hexdigest(),
                interpretation='native nonfinite messages and canonical finite approximation are both distinct from exact SPA; no universal upstream oracle')


def high_confidence_minsum():
    h=np.ones((1,3),dtype=np.uint8);s=np.array([1],dtype=np.uint8);cases=0;worst=0.
    for magnitude in (1.,10.,40.,100.,500.):
        p=math.exp(-magnitude)/(1+math.exp(-magnitude))
        for alpha in (.75,1.):
            native_decoder=ldpc.BpDecoder(h,error_rate=p,max_iter=1,bp_method='minimum_sum',ms_scaling_factor=alpha,schedule='parallel',input_vector_type='syndrome')
            native_decoder.decode(s)
            policy=BpFloodingPolicy(check_rule='min_sum',resolution=ResolutionPolicy(),alpha=alpha,
                version='bp-flooding-policy-v2',check_stabilization='exact_unity',product_epsilon=1e-10,zero_syndrome_shortcut=False)
            graph=CompiledBinaryFlooding.from_check_matrix(h,rule='min_sum',policy=policy)
            actual=graph.sweep(np.full(3,magnitude),s,error_rate=p).beliefs
            error=float(np.max(abs(actual-np.asarray(native_decoder.log_prob_ratios))));worst=max(worst,error)
            assert error<2e-11
            assert np.max(abs(actual-(1-alpha)*magnitude))<2e-11
            cases+=1
    return dict(cases=cases,max_posterior_error=worst,scope='unbounded explicit policy-v2 min-sum and normalized min-sum, one sweep')


if __name__=='__main__':
    a=Audit(HERE)
    a.probe('native_ldpc_high_confidence_classification',ldpc_envelope)
    a.probe('high_confidence_native_minsum_correspondence',high_confidence_minsum)
    a.probe('pinned_aSCED_zero_division_classification',native.source_zero_checks)
    a.probe('pinned_Relay_inner_memory_correspondence',native.native.relay_crosscheck)
    a.finish()
