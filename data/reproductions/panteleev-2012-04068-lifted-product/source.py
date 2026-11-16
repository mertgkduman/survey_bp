"""Exact Example4 of Panteleev/Kalachev arXiv:2012.04068v2."""
from hashlib import sha256
import json
from pathlib import Path
import urllib.request
import numpy as np
from bp_registry.css import CssCode,gf2_rank,semantic_sha256
from bp_registry.code_constructions import derive_css_logicals,write_css_npz

ROOT = Path(__file__).resolve().parent
EXPONENTS = [[1,2,4,8,16],[5,10,20,9,18],[25,19,7,14,28]]


def construct():
    """Eq12/Example3 ring products followed by binary expansion, lift31."""
    a = np.asarray(EXPONENTS);m,n = a.shape;lift = 31
    hx = np.zeros((m*n*lift,(n*n+m*m)*lift),dtype=np.uint8)
    hz = np.zeros_like(hx)
    for i in range(m):
        for j in range(n):
            circ = np.roll(np.eye(lift,dtype=np.uint8),int(a[i,j]),axis=1)
            for k in range(n):
                hx[(i*n+k)*lift:(i*n+k+1)*lift,(j*n+k)*lift:(j*n+k+1)*lift] = circ
                hz[(k*m+i)*lift:(k*m+i+1)*lift,(k*n+j)*lift:(k*n+j+1)*lift] = circ
            for k in range(m):
                hx[(k*n+j)*lift:(k*n+j+1)*lift,(n*n+k*m+i)*lift:(n*n+k*m+i+1)*lift] = circ.T
                hz[(j*m+k)*lift:(j*m+k+1)*lift,(n*n+i*m+k)*lift:(n*n+i*m+k+1)*lift] = circ.T
    lx,lz = derive_css_logicals(hx,hz)
    return CssCode(hx,hz,lx,lz).validate()


def build():
    code = construct();assert (code.n,code.k)==(1054,140)
    write_css_npz(code,ROOT/'code.npz')
    hashes = {}
    for paper in ('2012.04068v2','1904.02703v3'):
        with urllib.request.urlopen('https://export.arxiv.org/e-print/'+paper,timeout=120) as r:raw=r.read()
        hashes[paper] = sha256(raw).hexdigest()
    receipt = {'paper':'arXiv:2012.04068v2','title':'Quantum LDPC Codes with Almost Linear Minimum Distance',
        'example':'Example4, Eq12 and Example3 LP(A,A*)','exponents':EXPONENTS,'lift':31,
        'semantic_sha256':semantic_sha256(code),'n':code.n,'k':code.k,
        'ranks':[gf2_rank(code.hx),gf2_rank(code.hz)],'source_archive_sha256':hashes,
        'distance':'unknown; BP-OSD search found no nondegenerate word of weight<20; not a lower-bound certificate',
        'rates':[.02,.04,.06,.08,.10,.12],
        'source_settings':{'check_rule':'min_sum','alpha':.625,'max_iterations':32,
            'budget_source':'cited arXiv:1904.02703v3, Section3; not stated for1054 in original LP paper'},
        'settings_limit':'Original LP paper provides no LER plot/rate grid/numeric iteration cap for1054. Controlled prospective depolarizing grid0.02,0.04,0.06,0.08,0.10,0.12. Budget32 and scale0.625 borrowed from cited BP-OSD paper, whose schedule is layered; this study uses canonical flooding. No original LP paper curve ordinates exist to compare.',
        'checks':'CSS commutation; n/k/ranks; paired logical quotient basis; independent explicit polynomial-index construction in tests',
        'circulant_convention':'row0 has1 at exponent; inverse convention is an equivalent within-lift permutation'}
    (ROOT/'source.json').write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':build()
