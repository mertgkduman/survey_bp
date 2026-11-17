"""Public native/wrapper proof: observable correct need not imply H-consistency."""
from hashlib import sha256
import importlib
import json
from pathlib import Path
import subprocess
import sys
import numpy as np
import stim

ROOT=Path(__file__).resolve().parents[3]
SOURCE=Path('/tmp/survey-bp-priortilt-source-261113373')
sys.path[:0]=[str(SOURCE),'/tmp/survey-bp-priortilt-native-261113373']
from priortilt import PriorTilt
from priortilt.sinter_priortilt import SinterCompiledDecoder_PriorTilt


def main():
    dem=stim.DetectorErrorModel('error(0.1) D0 L0\nerror(0.1) D1\nerror(0.1) D2\nerror(0.1) D0 D1 D2')
    decoder=PriorTilt(dem,schedule={'ends':[],'phases':[[0.,0.,0.,2.]]},initial_iters=1,round_len=1,max_rounds=1,seed=2)
    h=decoder._matrices.check_matrix.toarray().astype(np.uint8)
    a=decoder._matrices.observables_matrix.toarray().astype(np.uint8)
    truth=np.array([1,1,0,0],np.uint8);s=h@truth%2;obs=a@truth%2
    estimated=decoder.decode_errors(s);converged=decoder.converged
    predicted=decoder.decode(s)
    adapter=SinterCompiledDecoder_PriorTilt(decoder)
    packed=adapter.decode_shots_bit_packed(bit_packed_detection_event_data=np.packbits(s[None,:],axis=1,bitorder='little'))
    predicted_batch=np.unpackbits(packed,axis=1,count=dem.num_observables,bitorder='little')[0]
    assert not decoder.converged
    valid=bool(np.array_equal(h@estimated%2,s));logical=bool(np.array_equal(a@estimated%2,obs))
    assert not converged and not valid and logical
    np.testing.assert_array_equal(predicted,obs);np.testing.assert_array_equal(predicted_batch,obs)
    remote_blobs={'priortilt/__init__.py':'2a0c45b758e9a2e17237d51b319767c96d9ba01b',
                  'priortilt/sinter_priortilt.py':'e536d89f3b95e7a430fc65797784bdb93b31eec3',
                  'decoder/src/lib.rs':'040da491b6c56f1a75018efaac228f6c2a3aeb36',
                  'simulation_functions.py':'1864a65e30571e713e97a3f5898a931ff286723a'}
    for p,blob in remote_blobs.items():
        assert subprocess.check_output(['git','-C',str(SOURCE),'hash-object',p],text=True).strip()==blob
    examples=[]
    for p in sorted((ROOT/'data/reproductions/priortilt-2611-13373/results').glob('*priortilt/audit.json')):
        result=json.loads(p.read_text())
        for basis,row in result['bases'].items():
            n00,n01,n10,n11=row['joint_counts']
            assert n01+n11==row['errors'] and n10+n11==row['nonconvergence']
            if n10:examples.append({'canonical_point':p.parent.name,'basis':basis,'shots':row['shots'],
                'observable_errors':n01+n11,'nonconverged_observable_correct':n10,'joint_criterion_failures':n01+n10+n11,
                'scope':'canonical adaptation data; not an estimate of the authors historical convergence statistics'})
    so=Path(importlib.import_module('priortilt_rs').__file__)
    output={'author_commit':subprocess.check_output(['git','-C',str(SOURCE),'rev-parse','HEAD'],text=True).strip(),
            'current_github_blobs_matching_pinned_source':remote_blobs,'native_binary_sha256':sha256(so.read_bytes()).hexdigest(),
            'dem':str(dem),'H':h.tolist(),'A':a.tolist(),'true_error':truth.tolist(),'syndrome':s.tolist(),
            'estimated_error':estimated.tolist(),'estimated_syndrome':(h@estimated%2).tolist(),'true_observables':obs.tolist(),
            'predicted_observables':predicted.tolist(),'sinter_adapter_predictions':predicted_batch.tolist(),
            'converged':converged,'H_consistent':valid,'observable_correct':logical,'observable_only_success':logical,
            'joint_definition_success':valid and logical,'iterations':decoder.iterations,
            'scope':'two-sweep zero-offset toy proof through unmodified author code; not the paper configuration or a performance measurement',
            'canonical_examples':examples}
    (Path(__file__).parent/'probe.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output,indent=2))


if __name__=='__main__':main()
