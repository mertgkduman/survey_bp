"""Construction-time buffer validation for bounds-unchecked compiled kernels."""
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
    array = np.asarray(value, dtype=dtype, order='C')
    return np.frombuffer(array.tobytes(), dtype=dtype).reshape(array.shape)
