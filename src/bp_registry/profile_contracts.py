"""Construction-time validation for executable numerical profile evidence."""
from dataclasses import fields
import math
import numbers


def validate_fixed_fields(profile, contract, *, parameters=(), overrides=None) -> None:
    """Keep descriptive fields fixed; only implemented parameters may vary.

    Use the implementation's contract class, not instance-class defaults: a
    subclass changing a field default must not silently relabel the arithmetic.
    This runs at construction, never in message-update loops.
    """
    overrides = {} if overrides is None else overrides
    for field in fields(contract):
        if field.name in parameters:
            continue
        expected = overrides.get(field.name, field.default)
        actual = getattr(profile, field.name)
        if type(actual) is not type(expected) or actual != expected:
            raise ValueError(f"{contract.__name__}.{field.name} is fixed by its executable contract")


def finite_real(value) -> bool:
    """Reject booleans/non-numeric values before validating numeric bounds."""
    return not isinstance(value, bool) and isinstance(value, numbers.Real) and math.isfinite(value)
