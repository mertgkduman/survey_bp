"""Independent structural and semantic checks for the presentation pilot."""

from __future__ import annotations

import csv
import hashlib
from itertools import product
import json
import math
from pathlib import Path

import numpy as np

from bp_registry.code_constructions import build_b1_ghp
from bp_registry.css import in_row_space
from bp_registry.quaternary.compiled import CompiledBp4Graph, _boxplus_pair, _candidate_matches, _commutation_llr
from bp_registry.quaternary.problems import compile_css_artifact

from run_reproduction import BITS, LABELS, bp4_graph_from_css, css_syndrome, double_gross, logical_failure
from policy_kernel import _q


ROOT = Path(__file__).resolve().parent
ORACLE_ANTICOMMUTES = {1: (0, 0, 1, 1), 3: (0, 1, 1, 0)}


def check_bp4_check_updates() -> None:
    """Compare compiled X/Z check LLRs with direct four-state parity sums."""
    rng = np.random.Generator(np.random.PCG64(981))
    cases = 0
    for degree in (2, 3, 4):
        for labels in product((1, 3), repeat=degree):
            for observed in (0, 1):
                priors = rng.dirichlet(np.ones(4), size=degree)
                llrs = np.log(priors[:, 0, None] / priors[:, 1:])
                for target in range(degree):
                    neighbors = tuple(index for index in range(degree) if index != target)
                    incoming = [_commutation_llr(llrs[index], labels[index], 100.0)
                                for index in neighbors]
                    message = incoming[0]
                    for value in incoming[1:]:
                        message = _boxplus_pair(message, value, 100.0)
                    if observed:
                        message = -message
                    masses = []
                    for target_state in range(4):
                        mass = 0.0
                        for states in product(range(4), repeat=degree - 1):
                            parity = ORACLE_ANTICOMMUTES[labels[target]][target_state]
                            weight = 1.0
                            for index, state in zip(neighbors, states, strict=True):
                                parity ^= ORACLE_ANTICOMMUTES[labels[index]][state]
                                weight *= priors[index, state]
                            if parity == observed:
                                mass += weight
                        masses.append(mass)
                    anti_state = 2 if labels[target] == 1 else 1
                    assert math.isclose(message, math.log(masses[0] / masses[anti_state]),
                                        rel_tol=0.0, abs_tol=1e-12)
                    cases += 1
    assert cases == 192


def check_code(code, n: int, k: int) -> None:
    assert code.n == n and code.k == k
    assert np.array_equal((code.hx.astype(np.int64) @ code.hz.astype(np.int64).T) % 2,
                          np.zeros((code.hx.shape[0], code.hz.shape[0]), dtype=np.int64))
    assert np.all(code.hx.sum(axis=1) > 0) and np.all(code.hz.sum(axis=1) > 0)
    zero = np.zeros(n, dtype=np.uint8)
    assert not logical_failure(code, zero, zero)
    # Independent row-space test: stabilizer generators are success, logical
    # generators are failure, despite all having zero syndrome.
    for xbits, zbits, expect in ((code.hx[0], zero, False), (zero, code.hz[0], False),
                                  (code.lx[0], zero, True), (zero, code.lz[0], True)):
        label = LABELS[xbits, zbits]
        assert not np.any(css_syndrome(code, label))
        assert logical_failure(code, zero, label) is expect
        assert (in_row_space(code.hx, xbits) and in_row_space(code.hz, zbits)) is (not expect)


def main() -> None:
    check_bp4_check_updates()
    b1, gross = build_b1_ghp(), double_gross()
    check_code(b1, 882, 24)
    check_code(gross, 288, 12)
    # On the smaller code, compare the direct low-memory graph to the existing
    # validated PauliCode path edge for edge and prior for prior.
    standard_code = compile_css_artifact(gross)
    standard = CompiledBp4Graph.from_code(
        standard_code,
        np.tile(np.asarray((0.92, 0.08 / 3, 0.08 / 3, 0.08 / 3)), (gross.n, 1)),
    )
    direct = bp4_graph_from_css(gross, 0.08)
    for name in ("row_ptr", "variable_ptr", "variable_edges", "variables", "labels"):
        assert np.array_equal(getattr(standard, name), getattr(direct, name)), name
    assert np.allclose(standard.prior_llrs, direct.prior_llrs, atol=1e-14, rtol=0)
    assert _q(0.125, 4) == 0.0 and _q(0.375, 4) == 0.5
    assert _q(100.0, 4) == 31.75 and _q(-100.0, 16) == -7.9375
    rng = np.random.Generator(np.random.PCG64(91))
    for _ in range(20):
        labels = rng.integers(0, 4, gross.n, dtype=np.uint8)
        assert np.array_equal(css_syndrome(gross, labels), standard_code.syndrome(labels))
        assert np.array_equal(BITS[labels], BITS[labels.astype(int)])
    for _ in range(100):
        labels = rng.integers(0, 4, gross.n, dtype=np.uint8)
        assert _candidate_matches(direct.row_ptr, direct.variables, direct.labels,
                                  labels, css_syndrome(gross, labels))
    with (ROOT / "results/source_curves.csv").open(newline="", encoding="utf-8") as handle:
        source = list(csv.DictReader(handle))
    assert len(source) == 41
    upper = [row for row in source if row["point_type"] == "upper_95_one_sided"]
    assert len(upper) == 1
    assert abs(float(upper[0]["reported_ler"]) - (1 - 0.05 ** (1 / int(upper[0]["reported_trials"])))) < 1e-15
    for path in (ROOT / "results").glob("pilot_*.json"):
        result = json.loads(path.read_text())
        ledger = (ROOT / "results" / result["event_ledger"]).read_bytes()
        assert hashlib.sha256(ledger).hexdigest() == result["event_ledger_sha256"]
        assert len(ledger.splitlines()) == result["shots"]
    print("presentation spike checks passed")


if __name__ == "__main__":
    main()
