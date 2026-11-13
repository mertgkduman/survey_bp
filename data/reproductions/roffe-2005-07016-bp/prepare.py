"""Extract measured Figure 3 BP coordinates and construct its exact ring-HGP codes."""
import json
from hashlib import sha256
from pathlib import Path
import re
import tarfile
import numpy as np
from bp_registry.code_constructions import derive_css_logicals,write_css_npz
from bp_registry.css import CssCode,semantic_sha256,gf2_rank
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[2]
COLORS={'1.000000,0.000000,0.000000':9,'0.000000,0.000000,1.000000':11,
        '0.000000,0.501961,0.000000':13,'0.501961,0.000000,0.501961':15}


def toric(distance):
    r=np.eye(distance,dtype=np.uint8)^np.roll(np.eye(distance,dtype=np.uint8),1,axis=1)
    identity=np.eye(distance,dtype=np.uint8)
    hx=np.hstack((np.kron(r,identity),np.kron(identity,r.T)))
    hz=np.hstack((np.kron(identity,r),np.kron(r.T,identity)))
    lx,lz=derive_css_logicals(hx,hz)
    return CssCode(hx,hz,lx,lz).validate()


def extract(archive):
    with tarfile.open(archive) as tar:
        figure=tar.extractfile('toric_threshold.pgf').read()
    text=figure.decode();curves={};bars={}
    for block in text.split('\\begin{pgfscope}'):
        ends=re.findall(r'\\pgfpath(?:move|line)to\{\\pgfqpoint\{([\d.-]+)in\}\{([\d.-]+)in\}\}',block)
        color=re.search(r'\\definecolor\{currentstroke\}\{rgb\}\{([^}]+)\}',block)
        if len(ends)==2 and color and color.group(1) in COLORS and ends[0][0]==ends[1][0]:
            bars.setdefault(COLORS[color.group(1)],[]).append(tuple(map(float,(ends[0][0],ends[0][1],ends[1][1]))))
    for block in text.split('\\begin{pgfscope}'):
        vertices=re.findall(r'\\pgfpath(?:move|line)to\{\\pgfqpoint\{([\d.-]+)in\}\{([\d.-]+)in\}\}',block)
        if len(vertices)<20 or '\\pgfsetdash{{3.700000pt}{1.600000pt}}' not in block:continue
        color=re.search(r'\\definecolor\{currentstroke\}\{rgb\}\{([^}]+)\}',block).group(1)
        d=COLORS[color];points=[]
        for xs,ys in vertices:
            x,y=float(xs),float(ys)
            if not any(abs(x-bx)<1e-7 and min(lo,hi)-1e-6<=y<=max(lo,hi)+1e-6 for bx,lo,hi in bars[d]):
                raise ValueError('dashed vertex has no corresponding measured error bar')
            raw=10**(-2+(x-.869111)/(3.046496-.869111));p=round(raw,6)
            if abs(raw-p)>1e-7:raise ValueError('plot rate does not map to the displayed decimal grid')
            points.append({'p':p,'block_ler_approx':10**((y-2.716649)/(.458176/2)),
                           'x_inches':x,'y_inches':y})
        if d in curves:raise ValueError('duplicate dashed source curve')
        curves[d]=points
    if {d:len(p) for d,p in curves.items()}!={9:25,11:28,13:28,15:28}:raise ValueError('source figure differs from inspected revision')
    return {'schema':'roffe-figure3-source-points-v1','paper':'https://arxiv.org/abs/2005.07016v2',
            'source_url':'https://arxiv.org/src/2005.07016v2','source_archive_sha256':sha256(Path(archive).read_bytes()).hexdigest(),
            'figure_member':'toric_threshold.pgf','figure_sha256':sha256(figure).hexdigest(),
            'x_log10_calibration':{'p_001_x':.869111,'p_01_x':3.046496},
            'y_log10_calibration':{'rate_1_y':2.716649,'inches_per_two_decades':.458176},
            'coordinate_status':'approximate ordinates from original vector figure; author sample counts unavailable',
            'curves':{str(d):p for d,p in sorted(curves.items())}}


def prepare(archive):
    points=extract(archive);(ROOT/'source_points.json').write_text(json.dumps(points,indent=2,sort_keys=True)+'\n')
    codes={}
    for d in (9,11,13,15):
        code=toric(d);path=ROOT/f'codes/toric{d}.npz';write_css_npz(code,path)
        codes[f'toric{d}']={'artifact':str(path.relative_to(REPO)),'semantic_sha256':semantic_sha256(code),
            'raw_sha256':sha256(path.read_bytes()).hexdigest(),'n':code.n,'k':code.k,'d':d,
            'rank_per_component':gf2_rank(code.hx),'edges_per_component':int(code.hz.sum()),
            'ordering_status':'source Eq. (4): ring R=I+cyclic-shift, row-major symmetric HGP; redundant checks retained',
            'logical_basis':'project free-column quotient basis, paired XZ',
            'label':f'Roffe toric [[{code.n},2,{d}]]'}
    (ROOT/'codes.json').write_text(json.dumps(codes,indent=2,sort_keys=True)+'\n')
    return codes

if __name__=='__main__':
    import sys
    print(json.dumps(prepare(Path(sys.argv[1])),indent=2))
