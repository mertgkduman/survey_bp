"""Independent algebra and outcome contracts for small CSS codes."""

import pytest


def test_css_rejects_noncommuting_checks():
    import numpy as np
    from bp_registry.css import CssCode

    hx = np.array([[1, 0]], dtype=np.uint8)
    hz = np.array([[1, 0]], dtype=np.uint8)
    with pytest.raises(ValueError):
        CssCode(hx=hx, hz=hz).validate()


def test_css_rejects_nonbinary_entry():
    import numpy as np
    from bp_registry.css import CssCode

    with pytest.raises(ValueError):
        CssCode(hx=np.array([[2, 0]]), hz=np.array([[0, 1]])).validate()


def test_evaluator_separates_exact_from_degenerate(small_css_checks):
    import numpy as np
    from bp_registry.css import CssCode
    from bp_registry.evaluator import evaluate_candidate

    hx, hz = small_css_checks
    code = CssCode(hx=hx, hz=hz)
    zero = np.zeros(3, dtype=np.uint8)
    stabilizer = hx[0]
    assert evaluate_candidate(code, true_error=zero, candidate=zero).outcome == "exact"
    assert evaluate_candidate(code, true_error=zero, candidate=stabilizer).outcome == "degenerate"

