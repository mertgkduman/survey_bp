"""Source-derived MacKay--Mitchison--McFadden Construction U inputs.

quant-ph/0304161v3, Section 4.6 (Construction U), fixes the extra all-one
column and gives the length-73 difference set. The length-273 ordering is
project generated and frozen, not claimed to be the authors' matrix bytes.
"""

from __future__ import annotations

import numpy as np

from .code_constructions import _circulant, derive_css_logicals
from .css import CssCode


DIFFERENCE_SETS = {
    73: (2, 8, 15, 19, 20, 34, 42, 44, 72),
}


def singer_273() -> tuple[int, ...]:
    """Trace-zero Singer set in GF(2^12), with explicit field coordinates.

    x^12 + x^6 + x^4 + x + 1 is checked to make x primitive at runtime.
    Representatives x^i, 0<=i<273, cover GF(4096)^*/GF(16)^*.
    The relative trace is a + a^16 + a^256.
    """
    modulus = (1 << 12) | (1 << 6) | (1 << 4) | (1 << 1) | 1

    def multiply(a: int, b: int) -> int:
        result = 0
        while b:
            if b & 1:
                result ^= a
            b >>= 1
            a <<= 1
            if a & (1 << 12):
                a ^= modulus
        return result

    def power(a: int, exponent: int) -> int:
        result = 1
        while exponent:
            if exponent & 1:
                result = multiply(result, a)
            a = multiply(a, a)
            exponent >>= 1
        return result

    if power(2, 4095) != 1 or any(power(2, 4095 // prime) == 1 for prime in (3, 5, 7, 13)):
        raise ValueError("Singer generator is not primitive")
    return tuple(i for i in range(273)
                 if (a := power(2, i)) ^ power(a, 16) ^ power(a, 256) == 0)


def unicycle_checks(length: int) -> np.ndarray:
    """Keep all redundant cyclic checks and append the all-one column."""
    modulus = length - 1
    if modulus == 273:
        exponents = singer_273()
    elif modulus in DIFFERENCE_SETS:
        exponents = DIFFERENCE_SETS[modulus]
    else:
        raise ValueError("registered unicycle lengths are 74 and 274")
    differences = [(a - b) % modulus for a in exponents for b in exponents if a != b]
    if sorted(differences) != list(range(1, modulus)):
        raise ValueError("not a perfect cyclic difference set")
    cyclic = _circulant(modulus, exponents)
    return np.hstack((cyclic, np.ones((modulus, 1), dtype=np.uint8)))


def build_unicycle(length: int) -> CssCode:
    checks = unicycle_checks(length)
    lx, lz = derive_css_logicals(checks, checks)
    return CssCode(hx=checks, hz=checks, lx=lx, lz=lz).validate()
