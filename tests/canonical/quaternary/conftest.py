"""Independent small Pauli fixtures for quaternary canonical tests.

These helpers intentionally do not import the production algebra.  They make
the encoding and commutation convention visible at the test boundary.
"""

from __future__ import annotations

import numpy as np


PAULI_BITS = ((0, 0), (1, 0), (1, 1), (0, 1))
PAULI_PRODUCTS = (
    (0, 1, 2, 3),
    (1, 0, 3, 2),
    (2, 3, 0, 1),
    (3, 2, 1, 0),
)
COMMUTES = tuple(
    tuple(((left_x * right_z + left_z * right_x) % 2) == 0 for right_x, right_z in PAULI_BITS)
    for left_x, left_z in PAULI_BITS
)


def hand_syndrome(checks: object, error: object) -> np.ndarray:
    """Return check parities using only the fixture commutation table."""
    check_rows = np.asarray(checks, dtype=np.uint8)
    candidate = np.asarray(error, dtype=np.uint8)
    answer = np.zeros(check_rows.shape[0], dtype=np.uint8)
    for row, check in enumerate(check_rows):
        parity = 0
        for label, value in zip(check, candidate, strict=True):
            parity ^= int(not COMMUTES[int(label)][int(value)])
        answer[row] = parity
    return answer
