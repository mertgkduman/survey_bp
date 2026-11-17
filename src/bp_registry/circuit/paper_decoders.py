"""Source-configured circuit Relay/Beam traversals over canonical min-sum.

PriorTilt shares the very same sweep through canonical.prior_tilt. These
controllers receive no true faults or logical observations. Historical CSS
traversals remain unchanged. Beam340 denotes a per-path cap, not total work.
"""
from dataclasses import dataclass
import math
import numpy as np
from numba import njit
from bp_registry.compiled_contracts import immutable_array
from .dem import DemBinaryModel
from bp_registry.canonical.compiled import _candidate_matches
from bp_registry.canonical.prior_tilt import (PriorTiltDecoder,PriorTiltSpec,PriorResult,
                                             indexed_uniform,sweep,VERSION)


@njit(cache=True)
def segment(rows,variables,prior,syndrome,fixed,inherited,start,gamma,cap,memory):
    n=len(prior);rp=np.zeros(len(rows),np.int64);vv=np.empty(len(variables),np.int64)
    mapping=np.empty(len(variables),np.int64);target=syndrome.copy();edge_count=0
    for check in range(len(rows)-1):
        for e in range(rows[check],rows[check+1]):
            v=variables[e]
            if fixed[v]<0:vv[edge_count]=v;mapping[edge_count]=e;edge_count+=1
            elif fixed[v]==1:target[check]^=np.uint8(1)
        rp[check+1]=edge_count
    vv=vv[:edge_count];mapping=mapping[:edge_count]
    old=inherited[mapping].copy();new=np.empty(edge_count);c2v=np.empty(edge_count)
    post=start.copy();candidate=np.zeros(n,np.uint8);sums=np.zeros(n);effective=prior.copy()
    bias_updates=0;valid=False;done=0
    for it in range(cap):
        if memory:
            for v in range(n):
                effective[v]=(1.-gamma[v])*prior[v]+gamma[v]*post[v]
                bias_updates+=int(effective[v]!=prior[v])
        sweep(rp,vv,n,old,target,effective,c2v,post,candidate,new)
        old,new=new,old
        for v in range(n):
            if fixed[v]>=0:candidate[v]=fixed[v]
            else:sums[v]+=post[v]
        done+=1
        valid=_candidate_matches(rows,variables,candidate,syndrome)
        if valid:break
    messages=inherited.copy()
    for e in range(edge_count):messages[mapping[e]]=old[e]
    return candidate,post,sums,messages,valid,done,edge_count,bias_updates


@njit(cache=True)
def relay(rows,variables,prior,syndrome,initial,per_leg,additional,g0,low,high,seed,shot):
    n=len(prior);fixed=np.full(n,-1,np.int8);inherited=prior[variables].copy();post=prior.copy()
    gamma=np.full(n,g0);trace=np.zeros((additional+1,8),np.int64)
    steps=0;directed=0;bias=0;draws=0;lineage=np.uint64(1469598103934665603)
    candidate=np.zeros(n,np.uint8);used=0;valid=False
    fallback=np.zeros(n,np.uint8);fallback_post=prior.copy()
    for leg in range(additional+1):
        if leg:
            for v in range(n):gamma[v]=low+(high-low)*indexed_uniform(seed,shot,leg,v)
            draws+=n
        for bits in gamma.view(np.uint64):lineage=(lineage^bits)*np.uint64(1099511628211)
        value=segment(rows,variables,prior,syndrome,fixed,inherited,post,gamma,
                      initial if leg==0 else per_leg,True)
        candidate,post=value[0],value[1];valid=value[4];steps+=value[5]
        if leg==0:fallback=candidate.copy();fallback_post=post.copy()
        directed+=2*value[5]*value[6];bias+=value[7]
        trace[used]=np.array([leg-1,-1,-1,value[5],value[6],int(valid),0,value[7]])
        used+=1
        if valid:break
    if not valid:candidate=fallback;post=fallback_post
    return candidate,post,valid,steps,directed,trace[:used],draws,bias,lineage


@njit(cache=True)
def beam(rows,variables,prior,syndrome,initial,per_round,width,rounds,degree):
    n=len(prior)
    maximum=1
    for d in range(rounds):maximum+=2*min(width,2**d)
    fixed=np.full(n,-1,np.int8);gamma=np.zeros(n)
    root=segment(rows,variables,prior,syndrome,fixed,prior[variables],prior,gamma,initial,False)
    trace_root=np.array([[-1,-1,-1,root[5],root[6],int(root[4]),0,0]],np.int64)
    steps=root[5];directed=2*root[5]*root[6];used=1
    if root[4]:return root[0],root[1],True,steps,directed,trace_root,0,0,np.uint64(0)
    posts=np.empty((maximum,n));messages=np.empty((maximum,len(variables)))
    sums=np.empty((maximum,n));masks=np.full((maximum,n),-1,np.int8)
    trace=np.zeros((maximum,8),np.int64);scores=np.zeros(maximum)
    fallback=root[0].copy();posts[0]=root[1];sums[0]=root[2];messages[0]=root[3]
    trace[0]=trace_root[0]
    frontier=np.zeros(width,np.int64);frontier_count=1
    for depth in range(rounds):
        children=np.empty(2*width,np.int64);child_count=0
        for f in range(frontier_count):
            parent=frontier[f]
            # Match the pinned native root initialization, including node0
            # seeding before the source's degree>2 scan. Later scans start inf.
            variable=0 if depth==0 else -1
            reliability=abs(sums[parent,0]) if depth==0 else math.inf
            for v in range(n):
                if masks[parent,v]<0 and degree[v]>2 and abs(sums[parent,v])<reliability:
                    variable=v;reliability=abs(sums[parent,v])
            if variable<0:continue
            for bit in range(2):
                index=used;masks[index]=masks[parent];masks[index,variable]=bit
                value=segment(rows,variables,prior,syndrome,masks[index],messages[parent],posts[parent],gamma,per_round,False)
                posts[index]=value[1];sums[index]=value[2];messages[index]=value[3]
                trace[index]=np.array([parent,variable,bit,value[5],value[6],int(value[4]),0,0])
                steps+=value[5];directed+=2*value[5]*value[6];used+=1
                if value[4]:return value[0],value[1],True,steps,directed,trace[:used],0,0,np.uint64(0)
                for v in range(n):
                    if masks[index,v]<0:scores[index]+=abs(value[2][v])
                scores[index]/=value[5]
                children[child_count]=index;child_count+=1
        # Pinned native priority queue: larger encounter IDs win exact ties.
        for a in range(child_count):
            for b in range(a+1,child_count):
                x,y=children[a],children[b]
                if scores[y]>scores[x] or scores[y]==scores[x] and y>x:
                    children[a],children[b]=y,x
        frontier_count=min(width,child_count)
        frontier[:frontier_count]=children[:frontier_count]
        for i in range(frontier_count,child_count):trace[children[i],6]=1
        if not frontier_count:break
    # Source returns the initial failed BP candidate, not the last child.
    return fallback,posts[0],False,steps,directed,trace[:used],0,0,np.uint64(0)


@dataclass(frozen=True,slots=True)
class PaperDecoderSpec:
    method:str
    initial:int=80
    per_leg:int=60
    additional:int=300
    first_gamma:float=.125
    gamma_low:float=-.24
    gamma_high:float=.66
    width:int=32
    rounds:int=10

    def __post_init__(self):
        if self.method not in ('relay','beam'):raise ValueError('paper relay or beam required')
        if any(type(x) is not int or not 1<=x<=4096 for x in (self.initial,self.per_leg,self.width,self.rounds)) or type(self.additional) is not int or not 0<=self.additional<=4096:
            raise ValueError('bounded integer budgets required')
        if not all(math.isfinite(x) for x in (self.first_gamma,self.gamma_low,self.gamma_high)) or not self.gamma_low<self.gamma_high:
            raise ValueError('finite ordered memory controls required')
        if self.method=='beam' and (self.additional!=300 or self.first_gamma!=.125 or self.gamma_low!=-.24 or self.gamma_high!=.66):
            raise ValueError('relay-only controls cannot configure beam')
        if self.method=='relay' and (self.width!=32 or self.rounds!=10):raise ValueError('beam-only controls cannot configure relay')


class CircuitPaperDecoder:
    def __init__(self,model,spec,seed=0):
        if not isinstance(model,DemBinaryModel) or model.table.variable_count==0:raise ValueError("nonempty validated DEM model required")
        self.model=model;self.spec=spec
        self.degree=immutable_array(np.bincount(model.variables,minlength=model.table.variable_count),np.int64)
        # Reuse validated graph/prior ownership and canonical construction.
        self.base=PriorTiltDecoder(model.table,model.prior_llrs,PriorTiltSpec(),seed)
        if not isinstance(spec,PaperDecoderSpec):raise ValueError('explicit paper decoder spec required')

    def decode(self,syndrome,*,shot:int):
        s=np.asarray(syndrome);m=self.model
        if s.shape!=(m.table.check_count,) or s.dtype.kind not in 'biu' or np.any((s!=0)&(s!=1)) or type(shot) is not int or not 0<=shot<2**63-1:
            raise ValueError('binary detector row and global shot index required')
        c=self.spec;args=(m.row_ptr,m.variables,m.prior_llrs,np.asarray(s^m.syndrome_bias,dtype=np.uint8))
        if c.method=='relay':value=relay(*args,c.initial,c.per_leg,c.additional,c.first_gamma,c.gamma_low,c.gamma_high,self.base.seed,shot)
        else:value=beam(*args,c.initial,c.per_leg,c.width,c.rounds,self.degree)
        return PriorResult(*value[:-1],int(value[-1]))
