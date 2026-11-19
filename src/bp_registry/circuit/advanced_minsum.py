"""Advanced BP control loops with a configurable canonical min-sum sweep.

The loops retain the traversal, controller state and budget of the frozen
PriorTilt, Relay and Beam implementations. The final argument binds kernel
controls and records range-protection interventions for the current shot.
"""
import math

import numpy as np
from numba import njit

from bp_registry.canonical.compiled import _candidate_matches, _policy_sweep_into
from bp_registry.canonical.prior_tilt import indexed_uniform
from bp_registry.circuit.relay_list import candidate_hash, candidate_quality


@njit(cache=True)
def sweep(rows, variables, n, old, syndrome, prior, c2v, post, candidate, new, kernel):
    damping, alpha, beta = kernel[:3]
    _policy_sweep_into(rows, variables, n, old, syndrome, prior, 2, 1, False, 1,
                       damping, 1.0-damping, alpha, beta,
                       c2v, post, candidate, new, False, 1e-10)
    # Limit only extreme outgoing messages, preserving fixed units for the
    # PriorTilt thresholds, Relay memory and Beam scores across branches.
    bound = 2.0 ** 480
    for v in range(n):
        if not math.isfinite(post[v]):
            raise ValueError("nonfinite posterior")
        candidate[v] = int(post[v] <= 0.)
    for e in range(len(new)):
        value = new[e]
        if not math.isfinite(value):
            raise ValueError("nonfinite outgoing message")
        if abs(value) > bound:
            new[e] = math.copysign(bound, value)
            kernel[3] += 1


@njit(cache=True)
def tilt(rows,variables,prior,syndrome,initial,round_len,rounds,ends,phases,seed,shot,kernel):
    n=len(prior);edges=len(variables)
    old=prior[variables].copy();new=np.empty(edges);c2v=np.empty(edges)
    post=prior.copy();candidate=np.zeros(n,np.uint8)
    sums=np.zeros(n);low=np.zeros(n);high=np.zeros(n);offset=np.zeros(n);effective=prior.copy()
    valid=False;steps=0;draws=0;bias_updates=0;lineage=np.uint64(1469598103934665603)
    for t in range(initial):
        sweep(rows,variables,n,old,syndrome,prior,c2v,post,candidate,new,kernel)
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
            sweep(rows,variables,n,old,syndrome,effective,c2v,post,candidate,new,kernel)
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


@njit(cache=True)
def segment(rows,variables,prior,syndrome,fixed,inherited,start,gamma,cap,memory,kernel):
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
        sweep(rp,vv,n,old,target,effective,c2v,post,candidate,new,kernel)
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
def relay(rows,variables,prior,syndrome,initial,per_leg,additional,g0,low,high,seed,shot,kernel):
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
                      initial if leg==0 else per_leg,True,kernel)
        candidate,post=value[0],value[1];valid=value[4];steps+=value[5]
        if leg==0:fallback=candidate.copy();fallback_post=post.copy()
        directed+=2*value[5]*value[6];bias+=value[7]
        trace[used]=np.array([leg-1,-1,-1,value[5],value[6],int(valid),0,value[7]])
        used+=1
        if valid:break
    if not valid:candidate=fallback;post=fallback_post
    return candidate,post,valid,steps,directed,trace[:used],draws,bias,lineage


@njit(cache=True)
def beam(rows,variables,prior,syndrome,initial,per_round,width,rounds,degree,kernel):
    n=len(prior)
    maximum=1
    for d in range(rounds):maximum+=2*min(width,2**d)
    fixed=np.full(n,-1,np.int8);gamma=np.zeros(n)
    root=segment(rows,variables,prior,syndrome,fixed,prior[variables],prior,gamma,initial,False,kernel)
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
                value=segment(rows,variables,prior,syndrome,masks[index],messages[parent],posts[parent],gamma,per_round,False,kernel)
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


@njit(cache=True)
def relay_list(rows,variables,prior,syndrome,initial,per_leg,additional,results,g0,low,high,seed,shot,kernel):
    n=len(prior);fixed=np.full(n,-1,np.int8);inherited=prior[variables].copy();post=prior.copy()
    gamma=np.full(n,g0);trace=np.zeros((additional+1,8),np.int64)
    steps=0;directed=0;bias=0;draws=0;lineage=np.uint64(1469598103934665603)
    best=np.zeros(n,np.uint8);best_post=prior.copy();best_score=math.inf;converged=0;used=0
    for leg in range(additional+1):
        if leg:
            for v in range(n):gamma[v]=low+(high-low)*indexed_uniform(seed,shot,leg,v)
            draws+=n
        for bits in gamma.view(np.uint64):lineage=(lineage^bits)*np.uint64(1099511628211)
        value=segment(rows,variables,prior,syndrome,fixed,inherited,post,gamma,initial if leg==0 else per_leg,True,kernel)
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


class AdvancedMinSum:
    """Existing paper controller with the selected sweep parameters."""
    def __init__(self, model, method, policy, controls, seed):
        from .tuned_minsum import MinSumSpec
        self.model = model
        self.method = method
        self.policy = policy
        self.controls = MinSumSpec(**controls)
        self.seed = seed
        self.degree = np.bincount(model.variables, minlength=model.table.variable_count)
        if method == "priortilt":
            self.ends = np.asarray(policy.ends, dtype=np.int64)
            self.phases = np.asarray(policy.phases, dtype=np.float64)

    def decode(self, syndrome, *, shot):
        from bp_registry.canonical.prior_tilt import PriorResult
        model, policy, controls = self.model, self.policy, self.controls
        kernel = np.asarray([controls.damping, controls.alpha, controls.beta, 0.], np.float64)
        args = (model.row_ptr, model.variables, model.prior_llrs,
                syndrome if self.method == "priortilt" else syndrome ^ model.syndrome_bias)
        if self.method == "priortilt":
            result = tilt(*args, policy.initial, policy.round_len, policy.rounds,
                          self.ends, self.phases, self.seed, shot, kernel)
        elif self.method == "beam":
            result = beam(*args, policy.initial, policy.per_leg, policy.width, policy.rounds,
                          self.degree, kernel)
        else:
            common = (policy.initial, policy.per_leg, policy.additional)
            gamma = (policy.first_gamma, policy.gamma_low, policy.gamma_high)
            if self.method == "relay5":
                result = relay_list(*args, *common, policy.results, *gamma, self.seed, shot, kernel)
            else:
                result = relay(*args, *common, *gamma, self.seed, shot, kernel)
        event = PriorResult(*result[:-1], int(result[-1]))
        if kernel[3]:
            from dataclasses import replace
            # This reserved trailer is stripped before the inherited trace validator.
            trailer = np.array([[-2, int(kernel[3]), 0, 0, 0, 0, 0, 0]], np.int64)
            event = replace(event, trace=np.concatenate((event.trace, trailer)))
        return event
