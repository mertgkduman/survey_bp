"""Shared scalar/Numba check stabilization; reduction order belongs to callers."""
import math
import numpy as np
try:
    from numba.extending import register_jitable
except ImportError:  # The inspectable scalar kernels do not require the CPU extra.
    def register_jitable(function):
        return function


@register_jitable
def stabilized_log_ratio(product: float, epsilon: float, clamp_band: bool = False) -> float:
    """Exact-unity safeguard or whole epsilon-band clamp, explicitly selected."""
    if clamp_band:
        product = min(1.0 - epsilon, max(-1.0 + epsilon, product))
    elif product >= 1.0:
        product = 1.0 - epsilon
    elif product <= -1.0:
        product = -1.0 + epsilon
    return math.log1p(product) - math.log1p(-product)


@register_jitable
def minsum_summary(values, start, stop):
    """Two minima and sign parity in one scan, including repeated minima."""
    first, second, first_index, negatives = math.inf, math.inf, -1, 0
    for edge in range(start, stop):
        value = values[edge]
        magnitude = abs(value)
        negatives += int(value < 0.0)
        if magnitude < first:
            second, first, first_index = first, magnitude, edge
        elif magnitude < second:
            second = magnitude
    return first, second, first_index, negatives


@register_jitable
def tanh_factors(values):
    """Compute each expensive transcendental once; preserve product fold order."""
    result = np.empty(len(values), dtype=np.float64)
    for edge in range(len(values)):
        value = values[edge]
        if not math.isfinite(value):
            raise ValueError("nonfinite check input")
        result[edge] = 1.0 if value > 40.0 else -1.0 if value < -40.0 else math.tanh(value / 2.0)
    return result
