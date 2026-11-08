"""Versioned source-iteration dispatch at formerly implicit entry points."""
import numbers

SOURCE_ITERATION_V2 = "source-iteration-v2"
LEGACY_ZERO_V1 = "legacy-zero-v1"


def validate_context_version(version: str) -> str:
    if type(version) is not str or version not in (SOURCE_ITERATION_V2, LEGACY_ZERO_V1):
        raise ValueError("unknown update context version")
    return version


def context_version(kernel) -> str:
    return validate_context_version(getattr(kernel, "update_context_version", SOURCE_ITERATION_V2))


def source_iteration(kernel, iteration: int) -> int:
    """Resolve standalone/local dispatch; explicit flooding context is unchanged.

    Legacy replay reproduces the implicit zero used before the D01 correction.
    The index denotes completed source traversals, never local work or order.
    """
    if isinstance(iteration, (bool,)) or not isinstance(iteration, numbers.Integral) or iteration < 0:
        raise ValueError("source iteration must be a nonnegative integer")
    return 0 if context_version(kernel) == LEGACY_ZERO_V1 else int(iteration)
