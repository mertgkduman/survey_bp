"""Aligned installed ldpc and pinned Relay execution through shared policies."""
from pathlib import Path
from itertools import product
from dataclasses import replace
from hashlib import sha256
import importlib.metadata
import json
import sys
import subprocess
import numpy as np
from scipy.sparse import csr_matrix
import ldpc

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(HERE.parent))
from audit_support import Audit
from bp_registry.canonical.policy_decoder import BinaryPolicy,BinaryPolicyDecoder
from bp_registry.canonical.contracts import MemoryCompositionSpec
from bp_registry.canonical.updates import ParameterAssignment
from bp_registry.resolution import STABLE_SPA_F64

H=np.array([[1,1,1,0,0],[0,0,1,1,1]],np.uint8)


def native_ldpc():
    rng=np.random.default_rng(5101)
    records=[];worst=0.
    for sample in range(12):
        rates=rng.uniform(.08,.45,5)
        prior=np.log1p(-rates)-np.log(rates)
        for rule,alpha,cap,bits in product(['spa','min_sum','normalized_min_sum'],[.55,.8,1.],[1,3,6],[(0,1),(1,0),(1,1)]):
            if rule!='normalized_min_sum' and alpha!=1.: continue
            native=ldpc.BpDecoder(H,error_channel=rates,max_iter=cap,
                bp_method='product_sum' if rule=='spa' else 'minimum_sum',ms_scaling_factor=alpha,
                schedule='parallel',input_vector_type='syndrome')
            syndrome=np.array(bits,np.uint8)
            expected=native.decode(syndrome)
            kwargs=(dict(flooding_policy=replace(STABLE_SPA_F64,damping=0.,hard_decision="min_llr")) if rule=='spa' else
                    dict(rule=rule,parameter=ParameterAssignment(shape='scalar',value=alpha)))
            for backend in (['compiled'] if rule=='spa' else ['scalar','compiled']):
                decoder=BinaryPolicyDecoder(H,BinaryPolicy(**kwargs,backend=backend,max_iterations=cap))
                result=decoder.decode(syndrome,prior_llrs=prior)
                posterior=np.array(result.ledger['execution']['posterior'])
                error=float(np.max(abs(posterior-native.log_prob_ratios)));worst=max(worst,error)
                np.testing.assert_allclose(posterior,native.log_prob_ratios,atol=2e-12,rtol=2e-12)
                np.testing.assert_array_equal(result.candidate,expected)
                assert (result.iterations,result.converged)==(native.iter,bool(native.converge))
                records.append(dict(sample=sample,rates=rates.tolist(),syndrome=list(bits),rule=rule,alpha=alpha,
                    cap=cap,backend=backend,candidate=expected.tolist(),iterations=int(native.iter),posterior_error=error))
    (HERE/'ldpc-cases.json').write_text(json.dumps(records,indent=2)+'\n')
    binary=next(Path(ldpc.__file__).parent.glob('bp_decoder/_bp_decoder*.so'))
    return dict(cases=len(records),max_error=worst,seed=5101,tolerance=2e-12,
        version=importlib.metadata.version('ldpc'),binary_sha256=sha256(binary.read_bytes()).hexdigest(),
        build_commit='not established',alignment='heterogeneous positive LLRs; nonzero syndrome; parallel; undamped SPA; explicit alpha; no active cap or exact tie')


def native_relay_memory():
    source=Path('/tmp/survey-bp-relay-v022-source')
    package=Path('/tmp/survey-bp-relay-v022-package')
    commit='14cb31a18f9b9d7d099791b793e35b8a2951f8f3'
    assert subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()==commit
    files=['crates/relay_bp/src/bp/min_sum.rs','crates/relay_bp/src/bp/relay.rs']
    for name in files:
        assert (source/name).read_bytes()==subprocess.check_output(['git','-C',str(source),'show',f'{commit}:{name}'])
    sys.path.insert(0,str(package))
    import relay_bp
    assert Path(relay_bp.__file__).is_relative_to(package)
    rng=np.random.default_rng(5102)
    records=[];worst=0.
    for sample in range(8):
        rates=rng.uniform(.1,.45,5);prior=np.log1p(-rates)-np.log(rates)
        for gamma,cap,bits in product([0.,.2,.6],[1,3,6],[(0,1),(1,0),(1,1)]):
            native=relay_bp.MinSumBPDecoderF64(check_matrix=csr_matrix(H),error_priors=rates,
                max_iter=cap,alpha=1.,gamma0=gamma,max_data_value=25.).decode_detailed(np.array(bits,np.uint8))
            memory=MemoryCompositionSpec.model_validate(dict(bindings=[dict(binding_id='affine',kind='affine_prior',
                target='prior',parameters=dict(alpha=gamma),order=0,history_owner='affine-state',state_lifetime='attempt',
                advance_boundary='source_iteration',refresh_boundary='attempt_start',source_status='canonical_adaptation')]))
            decoder=BinaryPolicyDecoder(H,BinaryPolicy(rule='min_sum',memory=memory,max_iterations=cap))
            result=decoder.decode(bits,prior_llrs=prior)
            posterior=np.array(result.ledger['execution']['posterior'])
            error=float(np.max(abs(posterior-native.posterior_ratios)));worst=max(worst,error)
            np.testing.assert_allclose(posterior,native.posterior_ratios,atol=2e-12,rtol=2e-12)
            np.testing.assert_array_equal(result.candidate,native.decoding)
            assert result.iterations==int(native.iterations)
            records.append(dict(sample=sample,rates=rates.tolist(),syndrome=list(bits),gamma=gamma,cap=cap,
                candidate=result.candidate.tolist(),iterations=result.iterations,posterior_error=error))
    (HERE/'relay-cases.json').write_text(json.dumps(records,indent=2)+'\n')
    return dict(cases=len(records),max_error=worst,seed=5102,commit=commit,
        source_sha256={f:sha256((source/f).read_bytes()).hexdigest() for f in files},
        binary_sha256={str(p):sha256(p.read_bytes()).hexdigest() for p in package.rglob('*.so')},
        scope='inner min-sum plus affine prior memory; not full Relay controller/published-curve equivalence')


if __name__=='__main__':
    audit=Audit(HERE)
    audit.probe('shared_native_ldpc',native_ldpc)
    audit.probe('shared_pinned_Relay_inner_memory',native_relay_memory)
    audit.finish()
