"""Source-unicycle controller on an isolated existing study runtime.

No message update is implemented here; the source's two hypotheses call the
existing canonical SP kernel and the qualified exact branch certificate.
"""
import importlib.util
import sys
from pathlib import Path
from dataclasses import replace
from hashlib import sha256
import time
import numpy as np
from bp_registry.artifacts import load_artifact
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.canonical.numerics import BINARY_SPA_F64_V2

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('_inferred_unicycle_rt',HERE/'bp_study_runtime.py')
rt=importlib.util.module_from_spec(s);s.loader.exec_module(rt)
sys.modules[s.name]=rt
s=importlib.util.spec_from_file_location('_inferred_certificate',HERE/'mackay-0304161-paper-rates/run.py')
source=importlib.util.module_from_spec(s);s.loader.exec_module(source)
original_state,original_event=rt.state,rt.event
rt.BATCH=1024


def state(job):
    if job['arm']!='unicycle_sp':return original_state(job)
    code=load_artifact(rt.REPO,job['code_artifact'],expected_semantic_sha256=job['code_semantic_sha256']).code
    graph=CompiledBinaryFlooding.from_check_matrix(code.hz[:,:-1],
           profile=replace(BINARY_SPA_F64_V2,v2c_damping=0.,check_cap=None))
    packed=tuple(np.packbits(x,axis=1,bitorder='little') for x in (code.hx,code.hz,code.lx,code.lz))
    return job,code.n,packed,[graph]


def event(value,shot):
    job,n,packed,graphs=value
    if job['arm']!='unicycle_sp':return original_event(value,shot)
    truth=rt.parent.base._sample(job['seed'],round(job['physical_p']*100000),shot,n,depolarizing=False)
    syndrome=rt.parent.base._syndrome(packed[1],truth)
    start=time.perf_counter_ns()
    candidate,valid,branches=source.certified_split(graphs[0],syndrome,p=job['physical_p'],
                                      limit=job['decoder']['iterations_per_branch'])
    elapsed=time.perf_counter_ns()-start
    outcome,_=rt.parent.outcome(*packed,truth,candidate,joint=False)
    if valid!=(outcome!='type_i'):raise ValueError('source controller validity mismatch')
    iterations=sum(branches)
    return {'shot':shot,'outcome':outcome,'iterations':iterations,'branch_iterations':branches,
            'certified_branch_pruned':0 in branches,
            'directed_edge_updates':2*job['graph_edges']*iterations,'decode_ns':elapsed,
            'error_sha256':sha256(truth.tobytes()).hexdigest(),'syndrome_sha256':sha256(syndrome.tobytes()).hexdigest(),
            'candidate_sha256':sha256(candidate.tobytes()).hexdigest()}

rt.state,rt.event=state,event


class Ledger(rt.Ledger):
    def __init__(self,directory,job):
        self.pruned=0
        super().__init__(directory,job)

    def add(self,row,line):
        if self.job['arm']=='unicycle_sp':
            skipped=0 in row['branch_iterations']
            if type(row.get('certified_branch_pruned')) is not bool or row['certified_branch_pruned']!=skipped or skipped and row['outcome']=='type_i':
                raise ValueError('invalid certified branch pruning record')
            self.pruned+=skipped
        super().add(row,line)

    def summary(self):
        return {**super().summary(),'certified_branches_pruned':self.pruned}

rt.Ledger=Ledger
