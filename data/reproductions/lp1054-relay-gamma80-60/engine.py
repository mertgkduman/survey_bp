"""Gamma-control traversal; every BP update uses unchanged canonical sweeps."""
from dataclasses import asdict, dataclass
from hashlib import sha256
import importlib.util
from pathlib import Path
import sys
import time

import numpy as np
from numba import njit

ROOT = Path(__file__).resolve().parent


def module(name,path):
    if name in sys.modules:return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name,path)
    value = importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value)
    return value


base = module('_lp1054_engine',ROOT.with_name('panteleev-2012-04068-lifted-product')/'engine.py')
sample,multiply,outcome = base.sample,base.multiply,base.outcome
search = base.search
VERSION = 'lp1054-relay-gamma80-60-v1'


@dataclass(frozen=True)
class GammaControls:
    method: str = 'relay'
    initial: int = 80
    per_unit: int = 60
    units: int = 1
    damping: float = .3
    alpha: float = .8
    paper_scale: bool = False
    beta: float = 0.
    width: int = 1
    rounds: int = 1
    solutions: int = 1
    first_gamma: float = .125
    gamma_low: float = -.24
    gamma_high: float = .66

    def __post_init__(self):
        # Reuse the qualified control validator. Degenerate intervals are
        # intentional fixed-gamma ablations; the actual traversal receives
        # exactly equal endpoints, with no epsilon perturbation.
        values = asdict(self)
        if not np.isfinite([self.gamma_low,self.gamma_high]).all() or not -.75<=self.gamma_low<=self.gamma_high<=1.:
            raise ValueError('invalid ordered gamma interval')
        if self.gamma_low==self.gamma_high:
            values['gamma_low'],values['gamma_high'] = -.24,.66
        search.Controls(**values)
        if (self.method!='relay' or self.initial!=80 or self.per_unit!=60 or self.solutions!=1
                or self.units!=1 or self.rounds!=1 or self.width!=1 or self.paper_scale):
            raise ValueError('this study requires RelayBP-1 with80/60 iteration caps')


@njit(cache=True)
def _gamma_vector(first,low,high,seed,shot,leg,n):
    result = np.empty(n,dtype=np.float64)
    for v in range(n):result[v] = first if leg==0 else low+(high-low)*search.uniform(seed,shot,leg,v)
    return result


def gamma_vector(c,seed,shot,leg,n):
    return _gamma_vector(c.first_gamma,c.gamma_low,c.gamma_high,seed,shot,leg,n)


class Prepared:
    def __init__(self,code,p,c,seed):
        if c['family']!='bp' or c.get('osd'):raise ValueError('binary CSS BP-internal study only')
        self.code,self.c,self.seed = code,c,seed
        self.controls = GammaControls(**c['search']) if c.get('search') else None
        if self.controls and c['cap']!=80+60*self.controls.units:raise ValueError('incorrect cumulative cap')
        if not self.controls and c['cap']!=140:raise ValueError('matched continuous BP requires140 sweeps')
        prepared = base.Prepared(code,p,{k:v for k,v in c.items() if k!='search'},seed)
        self.graphs,self.initial,self.priors,self.coefficients = prepared.graphs,prepared.initial,prepared.priors,prepared.coefficients

    def decode(self,syndromes,shot):
        if type(shot) is not int or shot<0:raise ValueError('nonnegative public shot counter required')
        raw = [];c = self.controls
        start = time.perf_counter_ns()
        for i,(g,s) in enumerate(zip(self.graphs,syndromes)):
            if c:
                value = search.search(g.row_ptr,g.variables,self.code.n,s,self.initial,self.priors[i],1,
                    c.initial,c.per_unit,c.units,c.damping,c.alpha,c.paper_scale,c.beta,c.width,c.rounds,
                    c.solutions,c.first_gamma,c.gamma_low,c.gamma_high,self.seed+i,shot)
            else:
                value = base.loops.binary_loop(g.row_ptr,g.variables,self.code.n,s,self.initial,
                                              self.priors[i],self.c['cap'],self.coefficients)
            raw.append(value)
        elapsed = time.perf_counter_ns()-start
        candidates = [];details = [];iterations = edges = 0
        # All provenance extraction/hashing is OUTSIDE the decoder timer.
        for component,(g,value) in enumerate(zip(self.graphs,raw)):
            if c:
                candidate,post,valid,selected,trace,scores,posts,messages = value
                it = int(trace[:,3].sum());work = int(2*np.dot(trace[:,3],trace[:,4]))
                detail = {'units':trace.tolist(),'scores':scores.tolist(),'selected':int(selected),
                    'all_posterior_sha256':sha256(posts.tobytes()).hexdigest(),
                    'all_message_sha256':sha256(messages.tobytes()).hexdigest(),
                    'gamma_sha256':[sha256(gamma_vector(c,self.seed+component,shot,leg,self.code.n).tobytes()).hexdigest()
                                    for leg in range(len(trace))]}
            else:
                candidate,post,valid,it = value;it = int(it);work = int(2*it*len(g.variables));detail = {}
            detail.update(iterations=it,edges=len(g.variables),valid=bool(valid),
                          posterior_sha256=sha256(post.tobytes()).hexdigest())
            candidates.append(candidate);details.append(detail);iterations += it;edges += work
        bias_updates=self.code.n*iterations if c else 0
        draws=self.code.n*sum(len(d['units'])-1 for d in details) if c else 0
        clips=sum(sum(u[7] for u in d['units']) for d in details) if c else 0
        return candidates,{'iterations':iterations,'directed_edge_updates':edges,'decode_ns':elapsed,
            'gamma_bias_updates':bias_updates,'disorder_draws':draws,'memory_clips':clips,'components':details}
