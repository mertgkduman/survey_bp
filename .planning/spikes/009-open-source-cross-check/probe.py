"""Matched upstream decoder checks; does not install or mutate native packages."""
from dataclasses import replace
from hashlib import sha256
from itertools import product
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import numpy as np
from scipy.sparse import csr_matrix
from audit_support import Audit, ROOT
from bp_registry.canonical.kernel import BinarySpaKernel
from bp_registry.canonical.numerics import BINARY_SPA_F64_V2, MIN_SUM_CPU_F64
from bp_registry.canonical.schedules import EdgeTable, FloodingSchedule
from bp_registry.canonical.updates import MinSumUpdate
from bp_registry.quaternary.numerics import commutation_llr, pauli_hard_decision, QBP4_F64_V2

HERE=Path(__file__).parent
RELAY_SOURCE=Path('/tmp/survey-bp-relay-v022-source')
RELAY_PACKAGE=Path('/tmp/survey-bp-relay-v022-package')
ASCED_SOURCE=Path('/tmp/phase10-asced-native/source/quantum_asced')

def source_identity(root,commit,files):
    actual=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
    assert actual==commit,(actual,commit)
    for file in files:
        assert (root/file).read_bytes()==subprocess.check_output(['git','-C',str(root),'show',f'{commit}:{file}'])
    return dict(commit=commit,root=str(root),sha256={f:sha256((root/f).read_bytes()).hexdigest() for f in files})

def ldpc_crosscheck():
    import ldpc
    import importlib.metadata
    assert importlib.metadata.version('ldpc')=='2.4.1'
    package=Path(ldpc.__file__).parent
    hashes={str(p.relative_to(package)):sha256(p.read_bytes()).hexdigest() for p in package.glob('bp_decoder/*.so')}
    matrices=[np.array([[1,1,1,0,0],[0,1,0,1,1],[1,0,1,1,0]],dtype=np.uint8),
              np.array([[1,1,0],[0,1,1]],dtype=np.uint8)]
    cases=0; max_error=0.; ties=[]; mismatches=[]
    for rule in ('product_sum','minimum_sum'):
        profile=replace(BINARY_SPA_F64_V2,v2c_damping=0.) if rule=='product_sum' else MIN_SUM_CPU_F64
        kernel=BinarySpaKernel(profile=profile,update_rule=None if rule=='product_sum' else MinSumUpdate())
        for h in matrices:
            schedule=FloodingSchedule(EdgeTable.from_check_matrix(h),kernel=kernel,profile=profile)
            for bits in product(range(2),repeat=len(h)):
                if not any(bits): continue # Native Python wrapper short-circuits all-zero syndrome.
                s=np.array(bits,dtype=np.uint8)
                for p in (.071,.137,.283):
                    for cap in (1,2,5):
                        native=ldpc.BpDecoder(h,error_rate=p,max_iter=cap,bp_method=rule,
                                             ms_scaling_factor=1.,schedule='parallel',input_vector_type='syndrome')
                        candidate=native.decode(s).copy()
                        old=schedule.initialize(p)
                        for step in range(1,int(native.iter)+1):
                            sweep=schedule.sweep(old,s,error_rate=p); old=sweep.new_v2c
                        native_llr=np.array(native.log_prob_ratios)
                        delta=float(np.max(abs(sweep.beliefs-native_llr)))
                        max_error=max(max_error,delta)
                        assert delta<2e-11,(rule,p,cap,bits,delta)
                        if not np.array_equal(candidate,sweep.candidate):
                            differing=np.flatnonzero(candidate!=sweep.candidate)
                            entry=dict(rule=rule,p=p,cap=cap,syndrome=bits,indices=differing.tolist(),
                                       canonical_llr=sweep.beliefs[differing].tolist(),native_llr=native_llr[differing].tolist())
                            if all(abs(native_llr[j])<2e-11 and abs(sweep.beliefs[j])<2e-11 for j in differing): ties.append(entry)
                            else: mismatches.append(entry)
                        cases+=1
    assert not mismatches,mismatches
    return dict(version='2.4.1',module=str(package),binary_sha256=hashes,cases=cases,
                max_posterior_error=max_error,tie_discrepancies=ties,unexplained=mismatches,
                alignment='parallel; explicit syndrome input; min-sum alpha=1; SPA v2 damping=0; no saturation reached')

def relay_crosscheck():
    identity=source_identity(RELAY_SOURCE,'14cb31a18f9b9d7d099791b793e35b8a2951f8f3',
                             ['crates/relay_bp/src/bp/min_sum.rs','crates/relay_bp/src/bp/relay.rs'])
    sys.path.insert(0,str(RELAY_PACKAGE))
    import relay_bp
    assert Path(relay_bp.__file__).is_relative_to(RELAY_PACKAGE)
    identity['binary_sha256']={str(p):sha256(p.read_bytes()).hexdigest() for p in RELAY_PACKAGE.rglob('*.so')}
    h=np.array([[1,1,1,0,0],[0,1,0,1,1],[1,0,1,1,0]],dtype=np.uint8)
    kernel=BinarySpaKernel(profile=MIN_SUM_CPU_F64,update_rule=MinSumUpdate())
    schedule=FloodingSchedule(EdgeTable.from_check_matrix(h),kernel=kernel,profile=MIN_SUM_CPU_F64)
    comparisons=[]
    for bits in product(range(2),repeat=len(h)):
        if not any(bits): continue
        s=np.array(bits,dtype=np.uint8)
        for p in (.071,.137,.283):
            for gamma in (None,.2,.6):
                for cap in (1,3,7):
                    result=relay_bp.MinSumBPDecoderF64(check_matrix=csr_matrix(h),error_priors=np.full(h.shape[1],p),
                                                     max_iter=cap,alpha=1.,gamma0=gamma,max_data_value=25.).decode_detailed(s)
                    old=schedule.initialize(p); channel=np.full(h.shape[1],kernel.prior(p)); posterior=channel.copy()
                    for _ in range(int(result.iterations)):
                        effective=channel if gamma is None else (1-gamma)*channel+gamma*posterior
                        expected=schedule.sweep(old,s,error_rate=p,prior_llrs=effective)
                        old=expected.new_v2c; posterior=expected.beliefs
                    np.testing.assert_allclose(posterior,result.posterior_ratios,atol=2e-11,rtol=0)
                    actual=np.array(result.decoding)
                    diff=np.flatnonzero(actual!=expected.candidate)
                    assert all(abs(expected.beliefs[j])<1e-12 for j in diff),(bits,p,actual,expected.candidate)
                    comparisons.append(dict(syndrome=bits,p=p,gamma=gamma,cap=cap,tie_differences=diff.tolist(),iterations=int(result.iterations)))
    return dict(identity=identity,cases=len(comparisons),comparisons=comparisons,
                scope='Native F64 min-sum inner BP with affine prior memory, caps 1/3/7, clip 25; not a full Relay restart equivalence claim')

def extract_function(source,signature):
    start=source.index(signature); brace=source.index('{',start); depth=1; end=brace+1
    while depth:
        depth += (source[end]=='{')-(source[end]=='}'); end+=1
    return source[start:end]

def asced_microprobe():
    file='src/Decoder/BP/BP4_Decoder.cpp'
    identity=source_identity(ASCED_SOURCE,'816772071486615dfc7d71d1e15df597edc58a26',[file])
    expected=json.loads((ROOT/'data/native/phase10-asced-source-spec.json').read_text())['source']['source_digests'][file]
    assert identity['sha256'][file]==expected
    text=(ASCED_SOURCE/file).read_text()
    functions=[extract_function(text,s) for s in ('double BP4_Decoder::quantize_belief','void BP4_Decoder::hard_decision')]
    # Original function bodies are compiled unchanged in an ephemeral minimal host.
    # No downloaded source is copied into the repository or relabelled as a full native run.
    host='''#include <algorithm>
#include <cmath>
#include <vector>
#include <iostream>
#include <iomanip>
using std::log1p; using std::exp;
class BP4_Decoder { public:
std::vector<double> LLR_total_X, LLR_total_Z, LLR_total_Y;
std::vector<int> error_estimate;
double quantize_belief(double,double,double); void hard_decision();
};
'''+ '\n'.join(functions)+'''
int main(){ double x,y,z; while(std::cin>>x>>y>>z){ BP4_Decoder b;
b.LLR_total_X={x}; b.LLR_total_Y={y}; b.LLR_total_Z={z}; b.error_estimate={0}; b.hard_decision();
std::cout << std::setprecision(17) << b.error_estimate[0] << " " << b.quantize_belief(x,y,z) << "\\n";
}}
'''
    values=list(product((-2.,0.,2.),repeat=3))+[(100.,-70.,30.),(-100.,30.,70.)]
    with tempfile.TemporaryDirectory(prefix='bp-audit-asced-') as tmp:
        source=Path(tmp)/'probe.cpp'; binary=Path(tmp)/'probe'; source.write_text(host)
        subprocess.run(['c++','-std=c++17','-O0',str(source),'-o',str(binary)],check=True,capture_output=True)
        output=subprocess.run([str(binary)],input=''.join(' '.join(map(str,v))+'\n' for v in values),
                              text=True,capture_output=True,check=True).stdout
    failing_map=[]
    for values,row in zip(values,output.splitlines(),strict=True):
        native,projection=row.split(); translated=(0,1,3,2)[int(native)]
        assert translated==int(pauli_hard_decision(values,profile=QBP4_F64_V2))
        assert abs(float(projection)-commutation_llr(values,1,profile=QBP4_F64_V2))<2e-12
        masses=np.array([0.,*[-v for v in values]])
        if masses[translated]<max(masses): failing_map.append(dict(llrs=values,selected=translated))
    return dict(identity=identity,source_functions_sha256=[sha256(f.encode()).hexdigest() for f in functions],
                cases=len(output.splitlines()),nonmaximal_decisions=failing_map,
                scope='unchanged extracted native C++ functions; not full aSCED simulation or matched-shot reproduction')

if __name__=='__main__':
    a=Audit(HERE)
    a.probe('ldpc_2_4_1_matched_posteriors_and_decisions',ldpc_crosscheck)
    a.probe('relay_v022_native_min_sum',relay_crosscheck)
    a.probe('asced_pinned_cpp_projection_and_decision',asced_microprobe)
    a.finish()
