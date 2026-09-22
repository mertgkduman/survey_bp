"""Native BP is a reference; syndrome fit is independently checked."""


def test_native_bp_fits_tiny_syndrome():
    import numpy as np
    from bp_registry.reference import decode

    h = np.eye(2, dtype=np.uint8)
    syndrome = np.array([1, 0], dtype=np.uint8)
    result = decode(h, syndrome, error_rate=0.1, max_iter=10)
    assert np.array_equal((h @ result.candidate) % 2, syndrome)
    assert result.converged is True
    assert result.iterations >= 1

