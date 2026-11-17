"""Transient prior-offset policy over the existing canonical min-sum sweep.

Equations 3–7 of arXiv:2611.13373v1. Graph/prior/syndrome are the only
scientific inputs. Historical kernels and policy versions remain unchanged.
"""
from dataclasses import dataclass
import math
import numpy as np
from numba import njit
from bp_registry.compiled_contracts import immutable_array
from .compiled import _policy_sweep_into, _candidate_matches
from .schedules import EdgeTable

VERSION = 'canonical-prior-policies-v1'


@dataclass(frozen=True, slots=True)
class PriorTiltSpec:
    initial: int = 60
    round_len: int = 6
    rounds: int = 3000
    ends: tuple[int, ...] = ()
    # Explicit source-code order: (pi, c1, c2, theta), not paper table order.
    phases: tuple[tuple[float, float, float, float], ...] = ((.1, .5, .8, 2.),)

    def __post_init__(self):
        if any(type(v) is not int for v in (self.initial,self.round_len,self.rounds)):
            raise ValueError('iteration controls must be integers')
        if not 1 <= self.round_len <= self.initial <= 100_000 or not 0 <= self.rounds <= 100_000:
            raise ValueError('invalid initial/round iteration controls')
        ends=tuple(self.ends);phases=tuple(tuple(p) for p in self.phases)
        if len(phases)!=len(ends)+1 or any(type(e) is not int or not 0<e<self.rounds for e in ends) or any(a>=b for a,b in zip(ends,ends[1:])):
            raise ValueError('phase boundaries must be strictly increasing within the round budget')
        for p in phases:
            if len(p)!=4 or any(isinstance(v,(bool,np.bool_)) or not math.isfinite(v) for v in p):
                raise ValueError('finite (pi,c1,c2,theta) phase tuples required')
            if not 0<=p[0]<=1 or min(p[1:])<0 or p[3]==0:
                raise ValueError('invalid phase probability, coefficients or threshold')
        object.__setattr__(self,'ends',ends);object.__setattr__(self,'phases',phases)


@njit(cache=True)
def indexed_uniform(seed, shot, stage, node):
    x=(np.uint64(seed) ^ np.uint64(shot+1)*np.uint64(0x9e3779b97f4a7c15)
       ^np.uint64(stage+1)*np.uint64(0xd1b54a32d192ed03)
       ^np.uint64(node+1)*np.uint64(0x94d049bb133111eb))
    x=(x^(x>>np.uint64(30)))*np.uint64(0xbf58476d1ce4e5b9)
    x=(x^(x>>np.uint64(27)))*np.uint64(0x94d049bb133111eb)
    x^=x>>np.uint64(31)
    return float(x>>np.uint64(11))/9007199254740992.


@njit(cache=True)
def sweep(rows,variables,n,old,syndrome,prior,c2v,post,candidate,new):
    """Paper hard-decision ties; all message equations use the canonical sweep.

    Its total-minus-excluded-message float64 order is retained explicitly;
    author prefix/suffix arithmetic is a separate numerical reference.
    """
    _policy_sweep_into(rows,variables,n,old,syndrome,prior,2,1,False,1,
                       0.,1.,1.,0.,c2v,post,candidate,new,False,1e-10)
    for v in range(n):
        if not math.isfinite(post[v]):raise ValueError('nonfinite BP posterior')
        candidate[v]=int(post[v]<=0.)
    for e in range(len(new)):
        if not math.isfinite(new[e]):raise ValueError('nonfinite BP edge state')


@njit(cache=True)
def tilt(rows,variables,prior,syndrome,initial,round_len,rounds,ends,phases,seed,shot):
    n=len(prior);edges=len(variables)
    old=prior[variables].copy();new=np.empty(edges);c2v=np.empty(edges)
    post=prior.copy();candidate=np.zeros(n,np.uint8)
    sums=np.zeros(n);low=np.zeros(n);high=np.zeros(n);offset=np.zeros(n);effective=prior.copy()
    valid=False;steps=0;draws=0;bias_updates=0;lineage=np.uint64(1469598103934665603)
    for t in range(initial):
        sweep(rows,variables,n,old,syndrome,prior,c2v,post,candidate,new)
        old,new=new,old;steps+=1
        if t>=initial-round_len:
            for v in range(n):sums[v]+=post[v];low[v]=min(low[v],post[v]);high[v]=max(high[v],post[v])
            for e in range(edges):
                v=variables[e];low[v]=min(low[v],old[e]);high[v]=max(high[v],old[e])
        valid=_candidate_matches(rows,variables,candidate,syndrome)
        if valid:return candidate,post,valid,steps,2*edges*steps,np.empty((0,8),np.int64),draws,bias_updates,lineage
    trace=np.zeros((rounds,8),np.int64)
    phase=0;used=0
    for r in range(1,rounds+1):
        while phase<len(ends) and r>ends[phase]:phase+=1
        pi,c1,c2,theta=phases[phase]
        eligible=0;positive=0;nonzero=0
        for v in range(n):
            offset[v]=0.
            if sums[v]<theta*prior[v]:
                eligible+=1;draws+=1
                if indexed_uniform(seed,shot,r,v)<pi:offset[v]=-c1*low[v];positive+=1
                else:offset[v]=-c2*high[v]
            effective[v]=prior[v]+offset[v];nonzero+=int(offset[v]!=0.)
            sums[v]=0.;low[v]=0.;high[v]=0.
        for bits in offset.view(np.uint64):
            lineage=(lineage^bits)*np.uint64(1099511628211)
        done=0
        for k in range(round_len):
            sweep(rows,variables,n,old,syndrome,effective,c2v,post,candidate,new)
            old,new=new,old;steps+=1;done+=1;bias_updates+=nonzero
            for v in range(n):sums[v]+=post[v];low[v]=min(low[v],post[v]);high[v]=max(high[v],post[v])
            for e in range(edges):
                v=variables[e];low[v]=min(low[v],old[e]);high[v]=max(high[v],old[e])
            valid=_candidate_matches(rows,variables,candidate,syndrome)
            if valid:break
        trace[used]=np.array([r,phase,done,eligible,positive,nonzero,steps,int(valid)])
        used+=1
        if valid:break
    return candidate,post,valid,steps,2*edges*steps,trace[:used],draws,bias_updates,lineage


@dataclass(frozen=True)
class PriorResult:
    candidate: np.ndarray
    posterior: np.ndarray
    converged: bool
    iterations: int
    directed_edge_updates: int
    trace: np.ndarray
    random_draws: int
    biased_node_updates: int
    lineage: int


class PriorTiltDecoder:
    def __init__(self,table:EdgeTable,prior,spec:PriorTiltSpec,seed:int=0):
        if not isinstance(table,EdgeTable) or EdgeTable.from_edges(table.check_count,table.variable_count,table.edges)!=table:
            raise ValueError('validated canonical graph required')
        if not isinstance(spec,PriorTiltSpec) or type(seed) is not int or not 0<=seed<2**63:
            raise ValueError('explicit policy and nonnegative integer seed required')
        p=np.asarray(prior)
        if p.shape!=(table.variable_count,) or p.dtype.kind not in 'fiu':raise ValueError('one real LLR per variable required')
        self.prior=immutable_array(p,np.float64);self.spec=spec;self.seed=seed
        ptr=np.zeros(table.check_count+1,np.int64)
        for check,v in table.edges:ptr[check+1]+=1
        self.rows=immutable_array(np.cumsum(ptr),np.int64)
        self.variables=immutable_array([v for c,v in table.edges],np.int64)
        self.table=table

    def decode(self,syndrome,*,shot:int):
        s=np.asarray(syndrome)
        if s.shape!=(self.table.check_count,) or s.dtype.kind not in 'biu' or np.any((s!=0)&(s!=1)):
            raise ValueError('binary syndrome with graph check count required')
        if type(shot) is not int or not 0<=shot<2**63-1:raise ValueError('nonnegative global shot index required')
        p=self.spec
        result=tilt(self.rows,self.variables,self.prior,np.asarray(s,dtype=np.uint8),p.initial,p.round_len,p.rounds,
                    np.asarray(p.ends,dtype=np.int64),np.asarray(p.phases,dtype=np.float64),self.seed,shot)
        return PriorResult(*result[:-1],int(result[-1]))
