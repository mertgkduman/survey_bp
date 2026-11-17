"""Independent packed original-DEM evaluation for memory-benchmark ledgers."""
import numpy as np
from numba import njit


def source_masks(dem):
    """Parse original Stim targets directly, independently of DemBinaryModel.

    This source-grid contract requires independent mechanisms in (0,1/2).
    It rejects projections that would require bias folding or column dropping.
    """
    instructions=[i for i in dem.flattened() if i.type=='error']
    d=np.zeros((len(instructions),(dem.num_detectors+7)//8),np.uint8)
    o=np.zeros((len(instructions),(dem.num_observables+7)//8),np.uint8)
    for j,i in enumerate(instructions):
        if not 0<i.args_copy()[0]<.5:raise ValueError('source-grid evaluation requires unfurled positive DEM probabilities below one half')
        for t in i.targets_copy():
            if t.is_relative_detector_id():d[j,t.val//8]^=np.uint8(1<<(t.val%8))
            elif t.is_logical_observable_id():o[j,t.val//8]^=np.uint8(1<<(t.val%8))
    return d,o


@njit(cache=True)
def audit_candidates(candidates,detectors,observables,predictions,stats,dmasks,omasks):
    # stats columns: iterations, directed edges, converged, draws, bias, lineage.
    n=len(dmasks);counts=np.zeros(6,np.int64)
    for shot in range(len(candidates)):
        residual=detectors[shot].copy();pred=np.zeros(observables.shape[1],np.uint8)
        for byte in range(candidates.shape[1]):
            bits=candidates[shot,byte]
            if not bits:continue
            for bit in range(8):
                v=byte*8+bit
                if bits&(1<<bit):
                    if v>=n:raise ValueError('nonzero candidate padding')
                    for k in range(len(residual)):residual[k]^=dmasks[v,k]
                    for k in range(len(pred)):pred[k]^=omasks[v,k]
        valid=True;bad=False
        for k in range(len(residual)):
            if residual[k]:valid=False
        for k in range(len(pred)):
            if pred[k]!=predictions[shot,k]:raise ValueError('recorded observable prediction disagrees with original DEM')
            if pred[k]!=observables[shot,k]:bad=True
        if int(valid)!=stats[shot,2]:raise ValueError('convergence disagrees with original detector equation')
        counts[0]+=1;counts[1]+=int(bad)
        counts[2+int(not valid)*2+int(bad)]+=1
    return counts


def validate_trace(method,trace,stat,model,spec):
    """Reconcile every path's work; no hidden-truth decoder selection."""
    it,edge,valid,draws,bias,lineage=map(int,stat)
    e=len(model.variables);n=model.table.variable_count
    if method not in ('priortilt','relay','beam') or trace.ndim!=2 or trace.shape[1]!=8 or trace.dtype.kind not in 'iu' or valid not in (0,1):raise ValueError('invalid trace types')
    if it<1 or np.any(trace[:,2 if method=='priortilt' else 3]<1):raise ValueError('invalid iteration count')
    if method=='priortilt':
        if len(trace):
            if it!=spec.initial+int(trace[:,2].sum()) or not np.array_equal(trace[:,0],np.arange(1,len(trace)+1)):
                raise ValueError('tilt iteration trace changed')
            if not np.array_equal(trace[:,1],[sum(r>b for b in spec.ends) for r in trace[:,0]]):raise ValueError('phase assignment changed')
            if any(not 1<=v<=spec.round_len for v in trace[:,2]) or len(trace)>spec.rounds:raise ValueError('tilt budget exceeded')
            if draws!=int(trace[:,3].sum()) or bias!=int((trace[:,2]*trace[:,5]).sum()):raise ValueError('tilt typed work changed')
            if trace[-1,6]!=it or trace[-1,7]!=valid or np.any(trace[:-1,7]) or np.any(trace[:-1,2]!=spec.round_len):raise ValueError('tilt stopping trace changed')
            if np.any(trace[:,4]>trace[:,3]) or np.any(trace[:,5]>trace[:,3]) or np.any(trace[:,3]>n):raise ValueError('tilt node counts changed')
        elif not 1<=it<=spec.initial or draws or bias:raise ValueError('invalid initial-only tilt record')
        if edge!=2*e*it or it>spec.initial+spec.round_len*spec.rounds:raise ValueError('tilt BP work changed')
    elif method=='relay':
        if not 1<=len(trace)<=spec.additional+1 or it!=int(trace[:,3].sum()) or edge!=2*e*it:raise ValueError('relay path work changed')
        if int(trace[0,3])>spec.initial or np.any(trace[1:,3]>spec.per_leg):raise ValueError('relay budget exceeded')
        if draws!=n*(len(trace)-1) or bias!=int(trace[:,7].sum()):raise ValueError('relay typed work changed')
        if trace[-1,5]!=valid or np.any(trace[:-1,5]) or np.any(trace[:,4]!=e):raise ValueError('relay stopping trace changed')
    else:
        if not len(trace) or it!=int(trace[:,3].sum()) or edge!=int((2*trace[:,3]*trace[:,4]).sum()):raise ValueError('beam all-path work changed')
        degree=np.bincount(model.variables,minlength=n);fixed=[frozenset()]
        if trace[0,3]>spec.initial or trace[0,4]!=e:raise ValueError('beam root changed')
        for i,row in enumerate(trace[1:],1):
            parent,v,bit=map(int,row[:3])
            if not 0<=parent<i or not 0<=v<n or bit not in (0,1):raise ValueError('invalid beam lineage')
            mask=fixed[parent]|{v};fixed.append(mask)
            if v in fixed[parent]:raise ValueError('beam fixed a node twice')
            if len(mask)>spec.rounds or row[3]>spec.per_leg or row[4]!=e-sum(degree[j] for j in mask):raise ValueError('beam masked work changed')
        maximum=1+sum(2*min(spec.width,2**d) for d in range(spec.rounds))
        if len(trace)>maximum or draws or bias:raise ValueError('beam budget or typed work changed')
        if trace[-1,5]!=valid or np.any(trace[:-1,5]):raise ValueError('beam stopping trace changed')
