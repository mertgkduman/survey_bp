"""Pinned native correspondences and deliberately classified source differences."""
from importlib.util import spec_from_file_location,module_from_spec
from pathlib import Path
from itertools import product
from hashlib import sha256
import subprocess,tempfile
import numpy as np
from audit_support import Audit
from bp_registry.canonical.numerics import BINARY_SPA_F64_V3,check_to_variable
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.quaternary.numerics import QBP4_F64_V2,QBP4_F64_V3,pauli_hard_decision
from bp_registry.resolution import BpFloodingPolicy,ResolutionPolicy
HERE=Path(__file__).parent
spec=spec_from_file_location('native_reference',HERE.parent/'009-open-source-cross-check/probe.py')
native=module_from_spec(spec);spec.loader.exec_module(native)
# Reuse the pinned harness, with its SPA comparison explicitly migrated to v3.
native.BINARY_SPA_F64_V2=BINARY_SPA_F64_V3


def ldpc_v3():
    result=native.ldpc_crosscheck()
    result['alignment']=result['alignment'].replace('SPA v2','SPA v3')
    return result


def normalized_min_sum():
    import ldpc
    h=np.array([[1,1,1,0,0],[0,1,0,1,1],[1,0,1,1,0]],dtype=np.uint8)
    count=0;worst=0.;ties=0
    for alpha,p,bits,cap in product((.75,1.),(.071,.283),list(product((0,1),repeat=3))[1:],(1,3,6)):
        s=np.array(bits,dtype=np.uint8)
        reference=ldpc.BpDecoder(h,error_rate=p,max_iter=cap,bp_method='minimum_sum',ms_scaling_factor=alpha,schedule='parallel',input_vector_type='syndrome')
        candidate=reference.decode(s)
        policy=BpFloodingPolicy(check_rule='min_sum',resolution=ResolutionPolicy(),alpha=alpha,
            zero_syndrome_shortcut=False,version='bp-flooding-policy-v2',check_stabilization='exact_unity',product_epsilon=1e-10)
        graph=CompiledBinaryFlooding.from_check_matrix(h,rule='min_sum',policy=policy)
        prior=np.log1p(-p)-np.log(p);old=np.full(len(graph.variables),prior)
        for _ in range(reference.iter):
            actual=graph.sweep(old,s,error_rate=p);old=actual.new_v2c
        expected=np.array(reference.log_prob_ratios);error=float(np.max(abs(actual.beliefs-expected)));worst=max(worst,error)
        assert error<2e-11,(alpha,p,bits,cap,error)
        different=np.flatnonzero(candidate!=actual.candidate)
        assert all(abs(expected[i])<2e-11 and abs(actual.beliefs[i])<2e-11 for i in different)
        ties+=len(different);count+=1
    return dict(cases=count,max_posterior_error=worst,tie_coordinates=ties,normalizations=[.75,1.],alignment='new policy v2, float64, damping=0, compare actual native terminal iteration')


def source_decisions():
    proof=native.asced_microprobe()
    differences=[]
    for values in product((-2.,0.,2.),repeat=3):
        source=int(pauli_hard_decision(values,profile=QBP4_F64_V2));generic=int(pauli_hard_decision(values,profile=QBP4_F64_V3))
        scores=np.array([0.,*values]);assert scores[generic]==scores.min()
        if source!=generic:
            differences.append(dict(llrs=values,source=source,generic=generic,source_is_MAP=bool(scores[source]==scores.min())))
    return dict(native_proof=proof,v3_differences=differences,interpretation='generic v3 differs intentionally at source ties/nonmaximal fallthroughs')


def source_zero_checks():
    root=native.ASCED_SOURCE;files=['src/Decoder/BP/BP_CN_Processing/BP_SPA.cpp','include/Utility.h']
    identity=native.source_identity(root,'816772071486615dfc7d71d1e15df597edc58a26',files)
    function=native.extract_function((root/files[0]).read_text(),'void BP_SPA::check_node_update')
    safe=native.extract_function((root/files[1]).read_text(),'namespace safe')
    host='''#include <cmath>
#include <vector>
#include <iostream>
#include <iomanip>
using std::size_t;
'''+safe+'''
struct State {std::vector<std::vector<size_t>> M_sets,N_sets_indices; std::vector<std::vector<double>> LLR_v2c,LLR_c2v;std::vector<int> syndrome;double norm_factor=1.;};
class BP_SPA {public: State bp;void check_node_update(size_t j);};
'''+function+'''
int main(){double x,y,z;while(std::cin>>x>>y>>z){BP_SPA decoder;decoder.bp.M_sets={{0,1,2}};decoder.bp.N_sets_indices={{0},{0},{0}};decoder.bp.LLR_v2c={{x},{y},{z}};decoder.bp.LLR_c2v={{0.,0.,0.}};decoder.bp.syndrome={0};decoder.check_node_update(0);for(auto x:decoder.bp.LLR_c2v[0])std::cout<<std::setprecision(17)<<x<<" ";std::cout<<"\\n";}}
'''
    cases=[(0.,1.,2.),(0.,0.,2.),(1.,-2.,3.),(40.,40.,40.),(-40.,-40.,0.)]
    with tempfile.TemporaryDirectory(prefix='bp-native-zero-') as temporary:
        cpp=Path(temporary)/'probe.cpp';exe=Path(temporary)/'probe';cpp.write_text(host)
        subprocess.run(['c++','-std=c++17','-O0',str(cpp),'-o',str(exe)],check=True,capture_output=True)
        output=subprocess.run([str(exe)],input=''.join(' '.join(map(str,x))+'\n' for x in cases),text=True,capture_output=True,check=True).stdout
    rows=[]
    for values,line in zip(cases,output.splitlines(),strict=True):
        source=np.array([float(x) for x in line.split()]);canonical=np.array([check_to_variable(np.delete(values,i)) for i in range(3)])
        assert np.all(np.isfinite(canonical))
        if not any(x==0 for x in values):np.testing.assert_allclose(source,canonical,rtol=0,atol=2e-11)
        rows.append(dict(input=values,native=[str(x) if not np.isfinite(x) else float(x) for x in source],canonical=canonical,native_nonfinite=int(np.count_nonzero(~np.isfinite(source)))))
    assert any(row['native_nonfinite'] for row in rows)
    return dict(identity=identity,function_sha256=sha256(function.encode()).hexdigest(),rows=rows,scope='unchanged extracted check-update function, not complete aSCED execution',interpretation='upstream total-product division has zero/zero cases; canonical explicit exclusion remains finite')


if __name__=='__main__':
    a=Audit(HERE)
    a.probe('native_ldpc_with_v3_SPA_and_explicit_alignment',ldpc_v3)
    a.probe('native_ldpc_new_policy_v2_normalized_min_sum',normalized_min_sum)
    a.probe('pinned_Relay_affine_memory_correspondence',native.relay_crosscheck)
    a.probe('pinned_aSCED_and_corrected_v3_decision_classification',source_decisions)
    a.probe('pinned_aSCED_zero_check_counterexamples',source_zero_checks)
    a.finish()
