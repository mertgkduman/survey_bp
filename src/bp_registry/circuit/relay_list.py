"""Versioned multi-solution Relay-BP over the unchanged canonical min-sum sweep.

Paper: Ye/Delfosse arXiv:2611.13373v1, Table 4. Selection follows IBM
relay-bp v0.2.2 (14cb31a): count converged legs including duplicates, minimize
sum(original prior LLRs on candidate support), retain the first exact minimum.
Canonical arithmetic and indexed randomness remain distinct from native Rust.
"""
from dataclasses import dataclass
import math
import numpy as np
from numba import njit
from bp_registry.canonical.prior_tilt import PriorResult, indexed_uniform
from .paper_decoders import segment
from .dem import DemBinaryModel

VERSION='canonical-circuit-relay-list-v1'


@dataclass(frozen=True,slots=True)
class RelayListSpec:
    initial:int=80
    per_leg:int=60
    additional:int=600
    results:int=5
    first_gamma:float=.125
    gamma_low:float=-.24
    gamma_high:float=.66

    def __post_init__(self):
        if any(type(v) is not int or not 1<=v<=100000 for v in (self.initial,self.per_leg,self.results)) or type(self.additional) is not int or not 0<=self.additional<=10000:
            raise ValueError('bounded integer relay budgets required')
        if not all(math.isfinite(v) for v in (self.first_gamma,self.gamma_low,self.gamma_high)) or self.gamma_low>=self.gamma_high:
            raise ValueError('finite ordered relay controls required')


@njit(cache=True)
def candidate_quality(candidate,prior):
    score=0.
    for v in range(len(prior)):
        if candidate[v] and math.isfinite(prior[v]):score+=prior[v]
    return score


@njit(cache=True)
def candidate_hash(candidate):
    h=np.uint64(1469598103934665603)
    for bit in candidate:h=(h^np.uint64(bit))*np.uint64(1099511628211)
    return np.int64(h)


@njit(cache=True)
def relay_list(rows,variables,prior,syndrome,initial,per_leg,additional,results,g0,low,high,seed,shot):
    n=len(prior);fixed=np.full(n,-1,np.int8);inherited=prior[variables].copy();post=prior.copy()
    gamma=np.full(n,g0);trace=np.zeros((additional+1,8),np.int64)
    steps=0;directed=0;bias=0;draws=0;lineage=np.uint64(1469598103934665603)
    best=np.zeros(n,np.uint8);best_post=prior.copy();best_score=math.inf;converged=0;used=0
    for leg in range(additional+1):
        if leg:
            for v in range(n):gamma[v]=low+(high-low)*indexed_uniform(seed,shot,leg,v)
            draws+=n
        for bits in gamma.view(np.uint64):lineage=(lineage^bits)*np.uint64(1099511628211)
        value=segment(rows,variables,prior,syndrome,fixed,inherited,post,gamma,initial if leg==0 else per_leg,True)
        candidate,post=value[0],value[1];valid=value[4]
        steps+=value[5];directed+=2*value[5]*value[6];bias+=value[7]
        if leg==0:best=candidate.copy();best_post=post.copy()
        score=math.inf;improved=False;digest=np.int64(0)
        if valid:
            converged+=1;score=candidate_quality(candidate,prior);digest=candidate_hash(candidate)
            if score<best_score:
                best_score=score;best=candidate.copy();best_post=post.copy();improved=True
        bits=np.array([score],np.float64).view(np.int64)[0]
        # leg, strict improvement, score float64 bits, iterations, edges,
        # leg convergence, candidate digest (signed uint64 bits), biased updates.
        trace[used]=np.array([leg,int(improved),bits,value[5],value[6],int(valid),digest,value[7]],np.int64);used+=1
        if converged>=results:break
    return best,best_post,converged>0,steps,directed,trace[:used],draws,bias,lineage


class CircuitRelayListDecoder:
    def __init__(self,model,spec=RelayListSpec(),seed=0):
        if not isinstance(model,DemBinaryModel) or not model.table.variable_count or not isinstance(spec,RelayListSpec):
            raise ValueError('validated nonempty DEM and relay-list spec required')
        if type(seed) is not int or not 0<=seed<2**63:raise ValueError('nonnegative integer seed required')
        self.model=model;self.spec=spec;self.seed=seed

    def decode(self,syndrome,*,shot:int):
        s=np.asarray(syndrome);m=self.model;c=self.spec
        if s.shape!=(m.table.check_count,) or s.dtype.kind not in 'biu' or np.any((s!=0)&(s!=1)) or type(shot) is not int or not 0<=shot<2**63-1:
            raise ValueError('binary syndrome and global shot index required')
        result=relay_list(m.row_ptr,m.variables,m.prior_llrs,np.asarray(s^m.syndrome_bias,np.uint8),c.initial,c.per_leg,c.additional,c.results,c.first_gamma,c.gamma_low,c.gamma_high,self.seed,shot)
        return PriorResult(*result[:-1],int(result[-1]))


def validate_relay_list_trace(trace,stat,model,spec,candidate=None):
    it,edges,valid,draws,bias,lineage=map(int,stat);e=model.table.edge_count;n=model.table.variable_count
    if trace.ndim!=2 or trace.shape[1]!=8 or trace.dtype.kind not in 'iu' or not 1<=len(trace)<=spec.additional+1:
        raise ValueError('invalid relay-list trace')
    if not np.array_equal(trace[:,0],np.arange(len(trace))) or np.any(trace[:,3]<1) or trace[0,3]>spec.initial or np.any(trace[1:,3]>spec.per_leg):
        raise ValueError('relay-list leg budgets changed')
    if it!=int(trace[:,3].sum()) or edges!=2*e*it or np.any(trace[:,4]!=e) or draws!=n*(len(trace)-1) or bias!=int(trace[:,7].sum()):
        raise ValueError('relay-list work changed')
    flags=trace[:,5]
    if np.any((flags!=0)&(flags!=1)) or valid!=int(np.any(flags)) or int(flags.sum())>spec.results:
        raise ValueError('relay-list convergence changed')
    if np.any(np.cumsum(flags)[:-1]>=spec.results) or (flags.sum()<spec.results and len(trace)!=spec.additional+1):
        raise ValueError('relay-list stopping changed')
    best=math.inf
    for i,row in enumerate(trace):
        score=np.array([row[2]],np.int64).view(np.float64)[0]
        cap=spec.initial if i==0 else spec.per_leg
        if not row[5]:
            if row[3]!=cap or row[1] or row[6] or score!=math.inf:raise ValueError('failed relay leg changed')
        else:
            if not math.isfinite(score) or row[1]!=int(score<best):raise ValueError('relay first-minimum selection changed')
            if score<best:best=score
    if candidate is not None and np.any(flags):
        winner=trace[np.flatnonzero(trace[:,1])[-1]]
        if candidate_hash(candidate)!=winner[6] or candidate_quality(candidate,model.prior_llrs)!=np.array([winner[2]],np.int64).view(np.float64)[0]:
            raise ValueError('returned relay candidate is not the first minimum recorded winner')
