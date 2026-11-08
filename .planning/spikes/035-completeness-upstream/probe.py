from pathlib import Path
from itertools import product
from hashlib import sha256
import sys,gzip,json
import numpy as np
import ldpc,stim
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from audit_support import Audit
from bp_registry.circuit.sinter_adapter import CanonicalBpSinterDecoder
HERE=Path(__file__).parent

def heterogeneous_native():
    rng=np.random.default_rng(3501);h=np.array([[1,1,1,0,0],[0,0,1,1,1]],dtype=np.uint8);cases=0;events=[]
    for sample in range(12):
        rates=rng.uniform(.03,.35,5)
        dem=stim.DetectorErrorModel('\n'.join(f'error({p}) '+' '.join(f'D{c}' for c in np.flatnonzero(h[:,v]))+f' L{v}' for v,p in enumerate(rates)))
        for rule,bp in [('spa','product_sum'),('min_sum','minimum_sum')]:
            for cap,bits in product((1,3,6),((0,1),(1,0),(1,1))):
                s=np.array(bits,dtype=np.uint8)
                native=ldpc.BpDecoder(h,error_channel=rates,max_iter=cap,bp_method=bp,schedule='parallel',input_vector_type='syndrome')
                expected=native.decode(s)
                decoder=CanonicalBpSinterDecoder(max_iterations=cap,rule=rule).compile_decoder_for_dem(dem=dem)
                actual,ok,it=decoder.decode_detailed(s[None,:])
                np.testing.assert_array_equal(actual[0],expected)
                assert bool(ok[0])==bool(native.converge) and int(it[0])==int(native.iter)
                events.append(dict(event='native_canonical_fixture',assessment_status='not_assessed',case=cases,rates=rates.tolist(),syndrome=s.tolist(),rule=rule,max_iterations=cap,native_candidate=expected.tolist(),canonical_candidate=actual[0].tolist(),native_converged=bool(native.converge),canonical_converged=bool(ok[0]),native_iterations=int(native.iter),canonical_iterations=int(it[0])))
                cases+=1
    with gzip.open(HERE/'events.jsonl.gz','wt') as handle:
        for event in events:handle.write(json.dumps(event,sort_keys=True)+'\n')
    binary=next(Path(ldpc.__file__).parent.glob('bp_decoder/_bp_decoder*.so'))
    return dict(cases=cases,seed=3501,alignment='heterogeneous positive priors below 0.5, nonzero syndrome, parallel SPA/MS, no active saturation, original stopping',native_binary_sha256=sha256(binary.read_bytes()).hexdigest(),native_build_commit='not established')

if __name__=='__main__':
    a=Audit(HERE);a.probe('heterogeneous_DEM_native_BP_alignment',heterogeneous_native);a.finish()
