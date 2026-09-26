#!/usr/bin/env python3
"""Independently check finite GF(2) intervention design fixtures, not a decoder."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "docs/evidence/intervention-design-validation-20260926.json"


def bits(width: int):
    return itertools.product((0, 1), repeat=width)


def product(matrix, vector):
    return tuple(sum(a * b for a, b in zip(row, vector, strict=True)) % 2 for row in matrix)


def validate():
    cases = 0
    zero_column_cases = 0
    valid_cases = 0
    evidence_hash = hashlib.sha256()
    for flat in bits(6):
        matrix = (flat[:3], flat[3:])
        for syndrome in bits(2):
            for mask in bits(3):
                fixed = tuple(i for i, selected in enumerate(mask) if selected)
                free = tuple(i for i in range(3) if i not in fixed)
                for assignment in bits(len(fixed)):
                    contribution = product(tuple(tuple(row[i] for i in fixed) for row in matrix), assignment)
                    residual = tuple(a ^ b for a, b in zip(syndrome, contribution, strict=True))
                    shortened = tuple(tuple(row[i] for i in free) for row in matrix)
                    seen = set()
                    for candidate in bits(len(free)):
                        lifted = [None] * 3
                        for i, value in zip(fixed, assignment, strict=True):
                            lifted[i] = value
                        for i, value in zip(free, candidate, strict=True):
                            lifted[i] = value
                        lifted = tuple(lifted)
                        if lifted in seen:
                            raise AssertionError("lift is not injective")
                        seen.add(lifted)
                        working_valid = product(shortened, candidate) == residual
                        original_valid = product(matrix, lifted) == syndrome
                        if working_valid != original_valid:
                            raise AssertionError("shortening equivalence failed")
                        cases += 1
                        valid_cases += original_valid
                        zero_column_cases += not free
                        evidence_hash.update(json.dumps([flat, syndrome, mask, assignment, candidate, lifted, original_valid], separators=(",", ":")).encode())
                    expected = {v for v in bits(3) if all(v[i] == a for i, a in zip(fixed, assignment, strict=True))}
                    if seen != expected:
                        raise AssertionError("lift does not cover all compatible original vectors")
    if cases != 16384 or zero_column_cases != 2048:
        raise AssertionError("enumeration coverage drifted")

    # A working solution to a flipped syndrome is not automatically original-valid.
    matrix, syndrome, delta = ((1, 1),), (1,), (1,)
    candidate, correction = (0, 0), (1, 0)
    flipped = tuple(a ^ b for a, b in zip(syndrome, delta, strict=True))
    assert product(matrix, candidate) == flipped
    assert product(matrix, candidate) != syndrome
    assert product(matrix, correction) == delta
    lifted = tuple(a ^ b for a, b in zip(candidate, correction, strict=True))
    assert product(matrix, lifted) == syndrome
    # All-fixed cases: incompatible value leaves an empty check with residual 1.
    assert product(((),), ()) != (1,)
    assert product(((1,),), (0,)) != (1,)
    assert product(((),), ()) == (0,)
    assert product(((1,),), (1,)) == (1,)
    # Finite bias is a local field, not an exact algebraic fixed-bit constraint.
    prior, incoming = 25, (-25, -25)
    posterior = prior + sum(incoming)
    assert posterior < 0
    return {
        "schema_version": 1,
        "status": "passed",
        "claim_limit": "Finite algebra design fixtures only; no BP implementation, source trajectory equivalence or simulation performance claim.",
        "shortening": {
            "matrix_shape": [2, 3], "binary_matrices": 64,
            "syndromes_per_matrix": 4, "fixed_subsets_per_syndrome": 8,
            "candidate_cases": cases, "original_valid_cases": valid_cases,
            "all_fixed_candidate_cases": zero_column_cases,
            "checks": ["working_original_equivalence", "lift_injective", "lift_covers_fixed_compatible_vectors"],
            "ordered_case_digest_sha256": evidence_hash.hexdigest(),
        },
        "constructed_cases": {
            "syndrome_flip": {"H": [[1, 1]], "original_s": [1], "delta": [1], "working_candidate": [0, 0], "working_valid": True, "original_valid_without_certificate": False, "certificate_t": [1, 0], "certified_lift": [1, 0], "certified_original_valid": True},
            "all_fixed_contradiction": {"H": [[1]], "s": [1], "fixed_value": 0, "residual_empty_check": 1, "satisfiable": False},
            "all_fixed_valid": {"H": [[1]], "s": [1], "fixed_value": 1, "residual_empty_check": 0, "satisfiable": True},
            "finite_prior_counterexample": {"prior": prior, "incoming_messages": list(incoming), "posterior": posterior, "finite_prior_sign_can_change": True, "claim_scope": "Local-field counterexample; does not simulate a complete decoder."},
        },
        "validator_byte_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    payload = (json.dumps(validate(), indent=2, sort_keys=True) + "\n").encode()
    target = args.output
    if target.is_symlink() or target.resolve() == Path(__file__).resolve():
        parser.error("output must not alias the validator or a symlink")
    if args.check:
        if not target.is_file() or target.read_bytes() != payload:
            parser.exit(1, "retained design evidence does not match\n")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(payload)
    print(f"16384 shortening cases and 4 constructed cases passed; {'matches' if args.check else 'wrote'} {target}")


if __name__ == "__main__":
    main()
