"""Immutable-source standalone native reference; does not replace ldpc or run BP."""
import ctypes
from hashlib import sha256
from pathlib import Path
import subprocess

import numpy as np

REPO = Path(__file__).resolve().parents[3]
SOURCE = REPO / '.git/osd-upstream'
LIBRARY = REPO / '.git/osd-reference.so'
COMMIT = 'd3429964cd4ffe1abfc041c6ec8b8425cb174f40'


def build():
    actual = subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip()
    if actual != COMMIT:
        raise ValueError('native OSD source commit differs')
    if subprocess.check_output(['git', '-C', str(SOURCE), 'status', '--porcelain'], text=True).strip():
        raise ValueError('native OSD source has local edits')
    command = ['g++', '-std=c++17', '-O3', '-shared', '-fPIC', '-I'+str(SOURCE / 'src_cpp'),
               str(Path(__file__).with_name('reference.cpp')), '-o', str(LIBRARY)]
    subprocess.run(command, check=True)
    return {'commit': actual, 'command': command,
            'library_sha256': sha256(LIBRARY.read_bytes()).hexdigest(),
            'compiler': subprocess.check_output(['g++', '--version'], text=True).splitlines()[0],
            'source_sha256': {p: sha256((SOURCE / p).read_bytes()).hexdigest() for p in
                              ('src_cpp/osd.hpp', 'src_cpp/sort.hpp', 'src_cpp/gf2sparse_linalg.hpp', 'LICENSE')}}


class Native:
    def __init__(self, matrix, order, p=.1):
        self.matrix = np.ascontiguousarray(matrix, dtype=np.uint8)
        self.library = ctypes.CDLL(str(LIBRARY))
        self.library.osd_create.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p, ctypes.c_int, ctypes.c_double]
        self.library.osd_create.restype = ctypes.c_void_p
        self.library.osd_decode.argtypes = [ctypes.c_void_p]*5
        self.library.osd_decode.restype = ctypes.c_int
        self.library.osd_destroy.argtypes = [ctypes.c_void_p]
        self.library.osd_error.restype = ctypes.c_char_p
        self.handle = self.library.osd_create(*self.matrix.shape, self.matrix.ctypes.data, order, p)
        if not self.handle:
            raise ValueError(self.library.osd_error().decode())
        self.order = order

    def close(self):
        if self.handle:
            self.library.osd_destroy(self.handle); self.handle = None

    def decode(self, syndrome, posterior, trace=True, control_ties=True):
        s = np.ascontiguousarray(syndrome, dtype=np.uint8)
        # Upstream qsort has unspecified equal-value ordering. Feed equivalent
        # signed-order ranks to control ties by original column ID explicitly.
        if control_ties:
            order = np.argsort(posterior, kind='stable')
            ranks = np.empty(len(posterior), dtype=np.float64); ranks[order] = np.arange(len(order))
        else:
            ranks = np.ascontiguousarray(posterior, dtype=np.float64)
        selected = np.empty(len(posterior), dtype=np.uint8)
        capacity = 1+len(posterior)+self.order*(self.order-1)//2
        candidates = np.empty((capacity, len(posterior)), dtype=np.uint8) if trace else None
        count = self.library.osd_decode(self.handle, s.ctypes.data, ranks.ctypes.data,
                                       selected.ctypes.data, candidates.ctypes.data if trace else None)
        if count < 0:
            raise ValueError(self.library.osd_error().decode())
        return selected, candidates[:count] if trace else None
