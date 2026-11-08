"""Construction-time buffer validation for bounds-unchecked compiled kernels."""
import math
import numbers
import numpy as np


def integer_vector(value, name):
    array = np.asarray(value)
    if array.ndim != 1 or not np.issubdtype(array.dtype, np.integer):
        raise ValueError(f'{name} must be an integer vector')
    return array


def csr_pointer(value, count, name):
    array = integer_vector(value, name)
    if (len(array) == 0 or array[0] != 0 or array[-1] != count
            or np.any(array[1:] < array[:-1]) or np.any(array < 0)):
        raise ValueError(f'{name} must be monotone CSR offsets spanning all edges')
    return array


def immutable_array(value, dtype):
    """Own bytes, with no writable alias even through setflags()."""
    with np.errstate(over='ignore', invalid='ignore'):
        array = np.asarray(value, dtype=dtype, order='C')
    if np.issubdtype(array.dtype, np.inexact) and not np.all(np.isfinite(array)):
        raise ValueError('stored compiled buffer must be finite in its execution dtype')
    return np.frombuffer(array.tobytes(), dtype=dtype).reshape(array.shape)


def finite_float64_scalar(value, name):
    """Normalize once, then validate the value actually used by native code."""
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, numbers.Real):
        raise ValueError(f'{name} must be a finite real float64 scalar')
    try:
        normalized = float(value)
    except (ValueError, OverflowError) as error:
        raise ValueError(f'{name} must be representable as finite float64') from error
    if not math.isfinite(normalized):
        raise ValueError(f'{name} must be representable as finite float64')
    return normalized
