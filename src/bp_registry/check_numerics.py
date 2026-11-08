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


@register_jitable
def stable_boxplus(left: float, right: float) -> float:
    """Log-domain binary parity reduction; +inf is the internal empty fold."""
    if left == math.inf:
        return right
    if right == math.inf:
        return left
    if left == 0.0 or right == 0.0:
        return 0.0
    small, large = min(abs(left), abs(right)), max(abs(left), abs(right))
    # Avoid cancellation of the two log corrections for very small LLRs.
    # Here the product is bounded by tanh(0.5), far from the unity singularity.
    if small < 1.0:
        product = math.tanh(small / 2.0) * math.tanh(large / 2.0)
        magnitude = math.log1p(product) - math.log1p(-product)
        return -magnitude if (left < 0.0) != (right < 0.0) else magnitude
    magnitude = max(0.0, small + math.log1p(math.exp(-(small + large)))
                    - math.log1p(math.exp(-(large - small))))
    return -magnitude if (left < 0.0) != (right < 0.0) else magnitude


@register_jitable
def stable_check_extrinsics(values, row_ptr, syndrome, epsilon, output):
    """Linear-time prefix/suffix SPA; no excluded-product divisions or quadratic loops.

    Finite input is required. Degree-one checks use the declared finite unary
    convention; +inf is solely an internal fold identity, never a message.
    """
    prefix = np.empty(len(values), dtype=np.float64)
    unary = math.log1p(1.0 - epsilon) - math.log(epsilon)
    for check in range(len(row_ptr) - 1):
        start, stop = row_ptr[check], row_ptr[check + 1]
        accumulated = math.inf
        for edge in range(start, stop):
            if not math.isfinite(values[edge]):
                raise ValueError("nonfinite log-domain SPA input")
            prefix[edge] = accumulated
            accumulated = stable_boxplus(accumulated, values[edge])
        suffix = math.inf
        for edge in range(stop - 1, start - 1, -1):
            message = unary if stop - start == 1 else stable_boxplus(prefix[edge], suffix)
            output[edge] = -message if syndrome[check] else message
            suffix = stable_boxplus(values[edge], suffix)
