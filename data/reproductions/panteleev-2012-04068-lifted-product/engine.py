"""Detached study traversal: unchanged canonical BP equations and OSD algebra."""
from dataclasses import replace
from hashlib import sha256
import importlib.util
import math
from pathlib import Path
import sys
import time

from numba import njit
import numpy as np
from bp_registry.canonical.compiled import CompiledBinaryFlooding
from bp_registry.canonical.numerics import BINARY_SPA_F64_V2
from bp_registry.quaternary.compiled import CompiledBp4Graph
from bp_registry.resolution import BpFloodingPolicy, ResolutionPolicy
from bp_registry.postprocessing.osd import UniformOsd

ROOT = Path(__file__).resolve().parent


def module(name,path):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name,path)
    value = importlib.util.module_from_spec(spec); sys.modules[name] = value; spec.loader.exec_module(value)
    return value


loops = module('_runtime_budget_engine',ROOT.with_name('roffe-2005-07016-runtime-budget')/'engine.py')
search = module('_roffe_search_engine',ROOT.with_name('roffe-2005-07016-search')/'engine.py')
VERSION = 'lp1054-canonical-stack-v1'


@njit(cache=True)
def sample(seed,point,shot,n,p):
    x,z = np.zeros(n,dtype=np.uint8),np.zeros(n,dtype=np.uint8)
    for v in range(n):
        u = search.uniform(seed,shot,point,v)
        if u < p/3:
            x[v] = 1
        elif u < 2*p/3:
            x[v] = z[v] = 1
        elif u < p:
            z[v] = 1
    return x,z


@njit(cache=True)
def multiply(h,v):
    out = np.zeros(h.shape[0],dtype=np.uint8)
    for i in range(h.shape[0]):
        for j in range(h.shape[1]):
            out[i] ^= h[i,j] & v[j]
    return out


class Prepared:
    def __init__(self,code,p,c,seed):
        self.code,self.p,self.c,self.seed = code,p,c,seed
        self.joint = c['family']=='qbp'
        policy = BpFloodingPolicy(check_rule='min_sum',resolution=ResolutionPolicy('float64'),
            damping=c['damping'],alpha=c['alpha'],beta=c['beta'],
            hard_decision='map_pauli' if self.joint else 'min_llr',zero_syndrome_shortcut=False,
            version='bp-flooding-policy-v2',check_stabilization='exact_unity',product_epsilon=1e-10)
        if self.joint:
            self.graphs = [CompiledBp4Graph.from_css(code,p,rule='min_sum',policy=policy)]
        else:
            self.graphs = [CompiledBinaryFlooding.from_check_matrix(h,rule='min_sum',
                profile=BINARY_SPA_F64_V2,policy=policy) for h in (code.hz,code.hx)]
        self.coefficients = np.array([policy.coefficients])
        self.initial = math.log((1-2*p/3)/(2*p/3))
        self.priors = [] if self.joint else [np.full(code.n,g.bind_error_rate(2*p/3).prior) for g in self.graphs]
        self.osd = [UniformOsd(h,method=c['osd'],order=0 if c['osd']=='OSD_0' else 10)
                    for h in (code.hz,code.hx)] if c.get('osd') else []
        self.search_controls = search.Controls(**c['search']) if c.get('search') else None

    def decode(self,syndromes,shot):
        c = self.c; details = []; candidates = []; total_it = total_edges = 0
        start = time.perf_counter_ns()
        if self.joint:
            g = self.graphs[0]
            candidate,post,valid,it = loops.pauli_loop(g.row_ptr,g.variable_ptr,g.variable_edges,
                g.variables,g.labels,g.prior_llrs,np.concatenate((syndromes[1],syndromes[0])),c['cap'],self.coefficients)
            candidates = [((candidate==1)|(candidate==2)).astype(np.uint8),
                          ((candidate==2)|(candidate==3)).astype(np.uint8)]
            total_it = int(it); total_edges = int(2*it*len(g.variables))
            detail = {'iterations':int(it),'edges':len(g.variables),'valid':bool(valid),
                      'posterior_sha256':sha256(post.tobytes()).hexdigest()}
            if self.osd and not valid:
                marginals = (np.logaddexp(0.,-post[:,2])-np.logaddexp(-post[:,0],-post[:,1]),
                             np.logaddexp(0.,-post[:,0])-np.logaddexp(-post[:,1],-post[:,2]))
                detail['osd'] = []
                for i,(syndrome,llr) in enumerate(zip(syndromes,marginals)):
                    result = self.osd[i].decode(syndrome,llr,error_rate=2*self.p/3)
                    candidates[i] = result.candidate
                    detail['osd'].append({'work':result.work,'candidate_set_sha256':result.candidate_set_sha256})
            details = [detail]
        else:
            for component,(g,syndrome) in enumerate(zip(self.graphs,syndromes)):
                q = 2*self.p/3
                priors = self.priors[component]
                if self.search_controls:
                    sc = self.search_controls
                    result = search.search(g.row_ptr,g.variables,self.code.n,syndrome,self.initial,priors,
                        int(sc.method=='relay'),sc.initial,sc.per_unit,sc.units,sc.damping,sc.alpha,sc.paper_scale,
                        sc.beta,sc.width,sc.rounds,sc.solutions,sc.first_gamma,sc.gamma_low,sc.gamma_high,
                        self.seed+component,shot)
                    candidate,post,valid,selected,trace,scores,posts,messages = result
                    it = int(trace[:,3].sum()); edges = int(2*np.dot(trace[:,3],trace[:,4]))
                    detail = {'units':trace.tolist(),'scores':scores.tolist(),'selected':int(selected),
                        'all_posterior_sha256':sha256(posts.tobytes()).hexdigest(),
                        'all_message_sha256':sha256(messages.tobytes()).hexdigest()}
                else:
                    candidate,post,valid,it = loops.binary_loop(g.row_ptr,g.variables,self.code.n,syndrome,
                        self.initial,priors,c['cap'],self.coefficients)
                    edges = int(2*it*len(g.variables)); detail = {}
                detail.update(iterations=int(it),edges=len(g.variables),valid=bool(valid),
                    posterior_sha256=sha256(post.tobytes()).hexdigest())
                if self.osd and not valid:
                    result = self.osd[component].decode(syndrome,post,error_rate=q)
                    candidate = result.candidate
                    detail['osd'] = {'work':result.work,'candidate_set_sha256':result.candidate_set_sha256}
                candidates.append(candidate); details.append(detail)
                total_it += int(it); total_edges += edges
        elapsed = time.perf_counter_ns()-start
        return candidates,{'iterations':total_it,'directed_edge_updates':total_edges,
                           'decode_ns':elapsed,'components':details}


def outcome(code,truth,candidates):
    residual = [e^r for e,r in zip(truth,candidates)]
    if multiply(code.hz,residual[0]).any() or multiply(code.hx,residual[1]).any():
        return 'type_i'
    if multiply(code.lz,residual[0]).any() or multiply(code.lx,residual[1]).any():
        return 'type_ii'
    return 'success'
