"""Deterministic canonical-adaptation CSS aSCED splitter construction.

The pinned author implementation supplies the rank-growth and same-component
co-neighbor-removal ideas, but generates supports through unseeded ``rand()``.
This module therefore records those source components while making its
lexicographic search and its detectability gate explicit project conventions.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations
import json
from math import comb
from typing import Literal, Mapping

import numpy as np

from ..canonical.budgets import WorkVector
from ..css import CssCode, gf2_rank, semantic_sha256
from .algebra import Pauli, to_symplectic
from .kernel import QbpSweep, ScalarLlrBp4Kernel
from .mbp4 import FixedAlphaMbp4Kernel
from .problems import PauliCode, QuaternaryOriginalProblem
from ..canonical.lineage import LineageEdge, LineageId, stable_lineage_id


SplitterRole = Literal["x", "z"]
RunFidelity = Literal["canonical_adaptation"]

_SOURCE_COMPONENT_IDS = (
    "kit-cel/quantum_asced@816772071486615dfc7d71d1e15df597edc58a26:"
    "src/Graph_Optimization/Graph_Optimization_GF4.cpp:add_splitters:rank_growth",
    "kit-cel/quantum_asced@816772071486615dfc7d71d1e15df597edc58a26:"
    "src/Graph_Optimization/Graph_Optimization.cpp:remove_infeasible_indices:co_neighbor_removal",
)
_GB46_COMMIT = "816772071486615dfc7d71d1e15df597edc58a26"
_GB46_PATH = "Codes/GB_46_2/GB_46_2_H_44.alist"
_GB46_RAW_SHA256 = "4bd60bc22ccda388780ad2ad2a29b63143b3f024e599e57ef5bcb983f51cb9b2"


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _identity(prefix: str, value: object) -> str:
    return f"{prefix}-{sha256(_canonical_bytes(value)).hexdigest()}"


def _readonly_binary(value: object, *, name: str, ndim: int) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim != ndim or not np.issubdtype(array.dtype, np.integer) or np.any((array != 0) & (array != 1)):
        raise ValueError(f"{name} must be a {ndim}D binary integer array")
    result = np.array(array, dtype=np.uint8, copy=True)
    result.setflags(write=False)
    return result


def _readonly_pauli(value: object, *, name: str) -> np.ndarray:
    array = np.asarray(value)
    if array.ndim != 2 or not np.issubdtype(array.dtype, np.integer) or np.any((array < 0) | (array > 3)):
        raise ValueError(f"{name} must be a two-dimensional I/X/Y/Z array")
    result = np.array(array, dtype=np.uint8, copy=True)
    result.setflags(write=False)
    return result


def _pauli_row(role: SplitterRole, support: tuple[int, ...], n: int) -> np.ndarray:
    row = np.zeros(n, dtype=np.uint8)
    row[list(support)] = Pauli.X if role == "x" else Pauli.Z
    return row


def _css_pauli_rows(code: CssCode) -> tuple[np.ndarray, tuple[SplitterRole, ...]]:
    validated = code.validate()
    x = np.where(validated.hx == 1, Pauli.X, Pauli.I).astype(np.uint8)
    z = np.where(validated.hz == 1, Pauli.Z, Pauli.I).astype(np.uint8)
    return np.vstack((x, z)), ("x",) * len(x) + ("z",) * len(z)


def _artifact_sha256(code: CssCode) -> str:
    """Identify a validated CSS artifact even when no logical basis is supplied."""
    if code.lx is not None and code.lz is not None:
        return semantic_sha256(code)
    return sha256(_canonical_bytes({"hx": code.hx.tolist(), "hz": code.hz.tolist(), "logical_basis": None})).hexdigest()


def parse_pinned_gb46_css(raw: bytes) -> CssCode:
    """Parse the one admitted GB46 aList input after binding its raw source bytes."""
    if sha256(raw).hexdigest() != _GB46_RAW_SHA256:
        raise ValueError("GB46 input must match the pinned raw SHA-256")
    try:
        lines = [line.split() for line in raw.decode("utf-8").splitlines()]
        n, m = (int(value) for value in lines[0])
        row_weights = [int(value) for value in lines[3]]
    except (UnicodeDecodeError, IndexError, ValueError) as error:
        raise ValueError("GB46 input is not a readable quaternary aList") from error
    if (n, m) != (46, 44) or len(row_weights) != m:
        raise ValueError("GB46 input must describe exactly 44 checks on 46 qubits")
    indices_start = 4 + n
    values_start = indices_start + m
    if len(lines) < values_start + m:
        raise ValueError("GB46 input must retain quaternary aList row values")
    matrix = np.zeros((m, n), dtype=np.uint8)
    for row, weight in enumerate(row_weights):
        if weight < 1 or len(lines[indices_start + row]) < weight or len(lines[values_start + row]) < weight:
            raise ValueError("GB46 input has a truncated check row")
        for column_text, value_text in zip(lines[indices_start + row][:weight], lines[values_start + row][:weight]):
            column, value = int(column_text) - 1, int(value_text)
            if not 0 <= column < n or value not in {1, 2} or matrix[row, column] != 0:
                raise ValueError("GB46 input has invalid or mixed Pauli entries")
            matrix[row, column] = value
    if np.any(matrix[:22] == 2) or np.any(matrix[22:] == 1) or int(np.count_nonzero(matrix == 1)) != 176 or int(np.count_nonzero(matrix == 2)) != 176:
        raise ValueError("GB46 input must retain 22 ordered X-only rows followed by 22 Z-only rows")
    return CssCode((matrix[:22] == 1).astype(np.uint8), (matrix[22:] == 2).astype(np.uint8)).validate()


def gb46_canonical_fixture_payload(raw: bytes) -> dict[str, object]:
    """Construct the immutable, project-owned GB46 fixture from exact input bytes."""
    code = parse_pinned_gb46_css(raw)
    result = construct_splitter_batch(code, delta=2, row_weight=4, attempt_cap=10_000)
    if isinstance(result, SplitterSearchExhausted):
        raise ValueError("the pinned GB46 canonical construction unexpectedly exhausted")
    return {
        "schema": "asced-gb46-canonical-fixture-v1",
        "run_fidelity": "canonical_adaptation",
        "source_input": {"commit": _GB46_COMMIT, "path": _GB46_PATH, "raw_sha256": _GB46_RAW_SHA256, "rows": 44, "qubits": 46},
        "construction_profile": {"delta": 2, "batches": 1, "row_weight": 4, "attempt_cap_per_role": 10_000, "order": "x_then_z", "search": "lexicographic_first_support"},
        "splitter": result.splitter.tolist(),
        "h_ext": result.h_ext.tolist(),
        "h_ext_row_map": [list(item) for item in result.h_ext_row_map],
        "receipt": {
            "run_fidelity": result.receipt.run_fidelity,
            "constructor_identity": result.receipt.constructor_identity,
            "source_component_ids": list(result.receipt.source_component_ids),
            "artifact_sha256": result.receipt.artifact_sha256,
            "profile_sha256": result.receipt.profile_sha256,
            "splitter_sha256": result.receipt.splitter_sha256,
            "h_ext_sha256": result.receipt.h_ext_sha256,
            "terminal_status": result.receipt.terminal_status,
            "search_receipts": [_search_receipt_payload(item) for item in result.receipt.search_receipts],
            "constructed_receipt_sha256": result.receipt.receipt_sha256,
        },
        "qualification": {
            "rank_before": result.qualification.rank_before, "rank_after": result.qualification.rank_after,
            "rank_growth": result.qualification.rank_growth, "detectable_rank": result.qualification.detectable_rank,
            "row_weights": list(result.qualification.row_weights), "max_same_role_overlap": result.qualification.max_same_role_overlap,
            "virtual_path_count": result.qualification.virtual_path_count, "qualification_sha256": result.qualification.qualification_sha256,
        },
    }


def _symplectic_rank(rows: np.ndarray) -> int:
    bits = to_symplectic(rows)
    return gf2_rank(np.concatenate((bits[..., 0], bits[..., 1]), axis=1))


def _commutation(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    left_bits, right_bits = to_symplectic(left), to_symplectic(right)
    return np.asarray(
        (left_bits[:, None, :, 0].astype(np.int64) * right_bits[None, :, :, 1].astype(np.int64)
         + left_bits[:, None, :, 1].astype(np.int64) * right_bits[None, :, :, 0].astype(np.int64)).sum(axis=2) % 2,
        dtype=np.uint8,
    )


def _same_role_cycle_free(candidate: np.ndarray, existing: np.ndarray, roles: tuple[SplitterRole, ...], role: SplitterRole) -> bool:
    support = candidate != Pauli.I
    return all(int(np.count_nonzero(support & (row != Pauli.I))) <= 1 for row, row_role in zip(existing, roles) if row_role == role)


@dataclass(frozen=True, slots=True)
class AscedSplitterRow:
    """One accepted splitter with its deterministic support-search ordinal."""

    role: SplitterRole
    support: tuple[int, ...]
    candidate_ordinal: int

    def __post_init__(self) -> None:
        if self.role not in {"x", "z"} or not self.support or tuple(sorted(set(self.support))) != self.support:
            raise ValueError("splitter rows require a role and a strictly ordered nonempty support")
        if type(self.candidate_ordinal) is not int or self.candidate_ordinal < 0:
            raise ValueError("splitter candidate ordinal must be nonnegative")


@dataclass(frozen=True, slots=True)
class SplitterSearchReceipt:
    """Audit trail for the bounded canonical lexicographic support search."""

    role: SplitterRole
    attempt_cap: int
    candidates_examined: int
    accepted_ordinal: int | None
    rejected_cycle: int
    rejected_rank: int
    rejected_detectability: int


@dataclass(frozen=True, slots=True)
class SplitterSearchExhausted:
    """Typed terminal proving that no partial splitter batch was emitted."""

    role: SplitterRole
    attempt_cap: int
    receipts: tuple[SplitterSearchReceipt, ...]
    terminal_status: Literal["exhausted"] = "exhausted"


@dataclass(frozen=True, slots=True)
class SplitterQualification:
    """Independent project qualification for a complete ordered CSS splitter matrix."""

    rank_before: int
    rank_after: int
    rank_growth: int
    detectable_rank: int
    row_weights: tuple[int, ...]
    max_same_role_overlap: int
    virtual_path_count: int
    qualification_sha256: str


@dataclass(frozen=True, slots=True)
class ConstructedSplitterReceipt:
    """Content-addressed receipt for project-generated, never author-generated rows."""

    run_fidelity: RunFidelity
    constructor_identity: str
    source_component_ids: tuple[str, str]
    artifact_sha256: str
    profile_sha256: str
    splitter_sha256: str
    h_ext_sha256: str
    terminal_status: Literal["completed"]
    search_receipts: tuple[SplitterSearchReceipt, ...]
    receipt_sha256: str


def _construction_profile(*, delta: int, row_weight: int, attempt_cap: int) -> dict[str, object]:
    """Return the complete deterministic construction profile bound by a receipt."""
    return {
        "delta": delta,
        "row_weight": row_weight,
        "attempt_cap": attempt_cap,
        "order": "x_then_z",
        "search": "lexicographic_first_support",
    }


def _search_receipt_payload(receipt: SplitterSearchReceipt) -> dict[str, object]:
    """Serialize a search witness without relying on slots implementation details."""
    return {
        "role": receipt.role,
        "attempt_cap": receipt.attempt_cap,
        "candidates_examined": receipt.candidates_examined,
        "accepted_ordinal": receipt.accepted_ordinal,
        "rejected_cycle": receipt.rejected_cycle,
        "rejected_rank": receipt.rejected_rank,
        "rejected_detectability": receipt.rejected_detectability,
    }


def _constructed_receipt_payload(
    *,
    artifact_sha256: str,
    profile: dict[str, object],
    splitter_sha256: str,
    h_ext_sha256: str,
    qualification_sha256: str,
    search_receipts: tuple[SplitterSearchReceipt, ...],
) -> dict[str, object]:
    """Return the bytes covered by a completed project-construction receipt."""
    return {
        "run_fidelity": "canonical_adaptation",
        "source_component_ids": _SOURCE_COMPONENT_IDS,
        "artifact_sha256": artifact_sha256,
        "profile": profile,
        "splitter_sha256": splitter_sha256,
        "h_ext_sha256": h_ext_sha256,
        "qualification_sha256": qualification_sha256,
        "search": [_search_receipt_payload(receipt) for receipt in search_receipts],
    }


@dataclass(frozen=True, slots=True)
class QualifiedAscedBatch:
    """Immutable CSS splitter rows, graph bytes, receipt, and qualification witnesses."""

    code: CssCode
    rows: tuple[AscedSplitterRow, ...]
    splitter: np.ndarray
    h_ext: np.ndarray
    h_ext_row_map: tuple[tuple[str, str, int], ...]
    receipt: ConstructedSplitterReceipt
    qualification: SplitterQualification

    def __post_init__(self) -> None:
        splitter = _readonly_pauli(self.splitter, name="splitter")
        h_ext = _readonly_pauli(self.h_ext, name="extended check matrix")
        if splitter.shape[0] != len(self.rows) or h_ext.shape[1] != self.code.n:
            raise ValueError("splitter and extended graph dimensions must match the CSS code")
        if h_ext.shape[0] != self.code.hx.shape[0] + len(self.rows) + self.code.hz.shape[0]:
            raise ValueError("extended graph must contain original and splitter rows")
        object.__setattr__(self, "splitter", splitter)
        object.__setattr__(self, "h_ext", h_ext)


@dataclass(frozen=True, slots=True)
class AscedWorkingGraph:
    """A transformed factor graph whose splitter checks need not mutually commute.

    It intentionally is not ``QuaternaryWorkingProblem``: the latter models a
    stabilizer code and rejects the nonzero ``T Lambda H^T`` required by the
    aSCED affine partition.  It retains the same immutable-original and typed
    transform/lift lineage contract for the decoder-visible working graph.
    """

    lineage_id: str
    original: QuaternaryOriginalProblem
    parent_edge: LineageEdge
    checks: np.ndarray
    syndrome: np.ndarray
    row_map: tuple[tuple[str, str, int], ...]
    transform_identity: str
    lift_identity: str

    def __post_init__(self) -> None:
        checks = _readonly_pauli(self.checks, name="aSCED working checks")
        syndrome = _readonly_binary(self.syndrome, name="aSCED working syndrome", ndim=1)
        if not self.lineage_id.startswith("working-") or checks.shape[0] != syndrome.size or checks.shape[1] != self.original.code.n:
            raise ValueError("aSCED working graph dimensions or lineage are invalid")
        if len(self.row_map) != checks.shape[0] or self.parent_edge != LineageEdge(
            "transform", LineageId("original", self.original.lineage_id), LineageId("working", self.lineage_id),
        ):
            raise ValueError("aSCED working graph requires a certified transform from its immutable original")
        if not self.transform_identity or not self.lift_identity:
            raise ValueError("aSCED working graph requires explicit transform and lift identities")
        object.__setattr__(self, "checks", checks)
        object.__setattr__(self, "syndrome", syndrome)


@dataclass(frozen=True, slots=True)
class AscedBatch:
    """One closed, receipt-bound augmented graph and its preflight path count."""

    batch_id: str
    local_order: int
    qualified: QualifiedAscedBatch
    working: AscedWorkingGraph
    graph_identity: str
    path_count: int

    def __post_init__(self) -> None:
        if not self.batch_id or self.local_order < 0 or self.path_count != 2 ** len(self.qualified.rows):
            raise ValueError("aSCED batch identity, order, and path count must be receipt-derived")
        if self.working.parent_edge.relation != "transform" or not self.working.transform_identity or not self.working.lift_identity:
            raise ValueError("aSCED materialization requires an explicit certified transform and lift")


@dataclass(frozen=True, slots=True)
class AscedSpec:
    """Closed controller limits for one CSS aSCED ensemble."""

    max_iterations: int
    path_cap: int
    max_total_bp_calls: int

    def __post_init__(self) -> None:
        if type(self.max_iterations) is not int or self.max_iterations < 0:
            raise ValueError("aSCED max_iterations must be a nonnegative integer")
        if type(self.path_cap) is not int or self.path_cap < 1:
            raise ValueError("aSCED path_cap must be a positive integer")
        if type(self.max_total_bp_calls) is not int or self.max_total_bp_calls < 0:
            raise ValueError("aSCED max_total_bp_calls must be a nonnegative integer")


@dataclass(frozen=True, slots=True)
class AscedPathResult:
    """Complete immutable evidence for one declared virtual syndrome path."""

    batch_index: int
    path_index: int
    batch_id: str
    graph_identity: str
    virtual_bits: tuple[int, ...]
    extended_syndrome: tuple[int, ...]
    candidate: tuple[int, ...]
    extended_valid: bool
    original_valid: bool
    pauli_weight: int
    terminal: str
    work: WorkVector
    kernel_profile: str
    overcomplete_map_receipt: str | None = None


@dataclass(frozen=True, slots=True)
class AscedResult:
    """All retained path terminals and the paper-rule original-space choice."""

    spec: AscedSpec
    paths: tuple[AscedPathResult, ...]
    selected_candidate: tuple[int, ...] | None
    selected_origin: tuple[int, int] | None
    original_valid_pool: tuple[tuple[int, int], ...]
    termination: Literal["selected", "type_i_failure"]
    work: WorkVector
    component_ids: dict[str, str]
    interpretation_ids: dict[str, str]
    run_fidelity: RunFidelity = "canonical_adaptation"

    def as_evidence(self) -> dict[str, object]:
        return {
            "spec": {"max_iterations": self.spec.max_iterations, "path_cap": self.spec.path_cap},
            "paths": [
                {
                    "batch_index": path.batch_index, "path_index": path.path_index,
                    "batch_id": path.batch_id, "graph_identity": path.graph_identity,
                    "virtual_bits": list(path.virtual_bits), "extended_syndrome": list(path.extended_syndrome),
                    "candidate": list(path.candidate), "extended_valid": path.extended_valid,
                    "original_valid": path.original_valid, "pauli_weight": path.pauli_weight,
                    "terminal": path.terminal, "work": path.work.as_evidence(structural_event_version=4),
                    "kernel_profile": path.kernel_profile, "overcomplete_map_receipt": path.overcomplete_map_receipt,
                }
                for path in self.paths
            ],
            "selected_candidate": None if self.selected_candidate is None else list(self.selected_candidate),
            "selected_origin": None if self.selected_origin is None else list(self.selected_origin),
            "original_valid_pool": [list(item) for item in self.original_valid_pool],
            "termination": self.termination, "work": self.work.as_evidence(structural_event_version=4),
            "component_ids": dict(self.component_ids), "interpretation_ids": dict(self.interpretation_ids),
            "run_fidelity": self.run_fidelity,
        }


@dataclass(frozen=True, slots=True)
class _AscedSessionCode:
    """Decoder-only immutable check view; it intentionally has no stabilizer claim."""

    checks: np.ndarray

    def __post_init__(self) -> None:
        checked = _readonly_pauli(self.checks, name="aSCED session checks")
        object.__setattr__(self, "checks", checked)

    @property
    def n(self) -> int:
        return int(self.checks.shape[1])

    def syndrome(self, candidate: object) -> np.ndarray:
        from .algebra import syndrome
        return syndrome(self.checks, candidate)


@dataclass(frozen=True, slots=True)
class _AscedSessionProblem:
    code: _AscedSessionCode
    syndrome: np.ndarray
    lineage_id: str

    def __post_init__(self) -> None:
        observed = _readonly_binary(self.syndrome, name="aSCED session syndrome", ndim=1)
        if observed.shape != (self.code.checks.shape[0],) or not self.lineage_id:
            raise ValueError("aSCED session syndrome must match decoder checks")
        object.__setattr__(self, "syndrome", observed)


def _virtual_bits(path_index: int, delta: int) -> tuple[int, ...]:
    return tuple((path_index >> offset) & 1 for offset in range(delta))


def _path_syndrome(original: QuaternaryOriginalProblem, batch: AscedBatch, bits: tuple[int, ...]) -> np.ndarray:
    x_rows = batch.qualified.code.hx.shape[0]
    z_rows = batch.qualified.code.hz.shape[0]
    x_splitters = sum(row.role == "x" for row in batch.qualified.rows)
    g_x = np.asarray(bits[:x_splitters], dtype=np.uint8)
    g_z = np.asarray(bits[x_splitters:], dtype=np.uint8)
    result = np.concatenate((original.syndrome[:x_rows], g_x, original.syndrome[x_rows:x_rows + z_rows], g_z))
    result.setflags(write=False)
    return result


class AscedController:
    """Run every receipt-bound CSS aSCED virtual path before selection."""

    def __init__(self, spec: AscedSpec) -> None:
        if not isinstance(spec, AscedSpec):
            raise ValueError("aSCED controller requires AscedSpec")
        self.spec = spec

    def run(
        self,
        original: QuaternaryOriginalProblem,
        batches: tuple[AscedBatch, ...] | list[AscedBatch],
        priors: object,
        *,
        kernel: ScalarLlrBp4Kernel | FixedAlphaMbp4Kernel,
        overcomplete: Mapping[str, tuple[object, object, tuple[object, ...]]] | None = None,
    ) -> AscedResult:
        if not isinstance(original, QuaternaryOriginalProblem):
            raise ValueError("aSCED execution requires a CSS-derived immutable original problem")
        declared = tuple(batches)
        if not declared:
            raise ValueError("aSCED execution requires preflighted materialized batches")
        if not isinstance(kernel, (ScalarLlrBp4Kernel, FixedAlphaMbp4Kernel)):
            raise ValueError("aSCED supports only scalar BP4 or fixed-alpha MBP4 kernels")
        if isinstance(kernel, FixedAlphaMbp4Kernel) and kernel.spec.max_iterations != self.spec.max_iterations:
            raise ValueError("aSCED MBP4 iteration cap must equal the controller BP-work cap")
        total = sum(batch.path_count for batch in declared)
        if total > self.spec.path_cap:
            raise ValueError("aSCED path cardinality exceeds the declared preflight cap")
        if total * self.spec.max_iterations > self.spec.max_total_bp_calls:
            raise ValueError("aSCED declared all-path BP work exceeds the controller cap before paths start")
        if tuple((batch.local_order, batch.batch_id) for batch in declared) != tuple(sorted((batch.local_order, batch.batch_id) for batch in declared)):
            raise ValueError("aSCED batches must retain their stable materialized order")
        for batch in declared:
            _verify_qualified_batch(batch.qualified)
            if batch.working.original.semantic_sha256 != original.semantic_sha256:
                raise ValueError("aSCED batch must retain the immutable original problem observation")
        if overcomplete is not None and set(overcomplete) != {batch.batch_id for batch in declared}:
            raise ValueError("aSCED overcomplete execution requires one exact constructed map per batch")
        path_results: list[AscedPathResult] = []
        for batch_index, batch in enumerate(declared):
            for path_index in range(batch.path_count):
                bits = _virtual_bits(path_index, len(batch.qualified.rows))
                z_ext = _path_syndrome(original, batch, bits)
                checks, observed, graph_identity, map_receipt = batch.working.checks, z_ext, batch.graph_identity, None
                if overcomplete is not None:
                    checks, observed, graph_identity, map_receipt = _overcomplete_path_inputs(batch, z_ext, overcomplete[batch.batch_id])
                problem = _AscedSessionProblem(_AscedSessionCode(checks), observed, f"asced-path-{batch.batch_id}-{path_index}")
                session = kernel.new_session(
                    problem, priors, budget_scope="attempt",
                )
                if isinstance(kernel, ScalarLlrBp4Kernel):
                    sweep: QbpSweep = session.run(max_iterations=self.spec.max_iterations)
                    candidate, terminal, work = sweep.candidate, sweep.terminal, sweep.work
                else:
                    decoded = session.run()
                    if len(decoded.sweeps) > self.spec.max_iterations:
                        raise RuntimeError("MBP4 exceeded the aSCED preflight BP-work cap")
                    candidate, terminal, work = decoded.candidate, decoded.termination, decoded.work
                extended_valid = bool(np.array_equal(problem.code.syndrome(candidate), observed))
                original_valid = bool(np.array_equal(original.code.syndrome(candidate), original.syndrome))
                path_results.append(AscedPathResult(
                    batch_index, path_index, batch.batch_id, graph_identity, bits,
                    tuple(int(value) for value in z_ext), tuple(int(value) for value in candidate),
                    extended_valid, original_valid, int(np.count_nonzero(candidate)), terminal, work,
                    kernel.profile.profile_id, map_receipt,
                ))
        pool = tuple((path.batch_index, path.path_index) for path in path_results if path.original_valid)
        selected = min((path for path in path_results if path.original_valid), key=lambda path: (path.pauli_weight, path.batch_index, path.path_index), default=None)
        return AscedResult(
            self.spec, tuple(path_results), None if selected is None else selected.candidate,
            None if selected is None else (selected.batch_index, selected.path_index), pool,
            "type_i_failure" if selected is None else "selected", WorkVector.sum(path.work for path in path_results),
            {"css_batching": "wursthorn-et-al-asced-css-batching", "virtual_lsb": "kit-cel-quantum-asced-pinned-lsb"},
            {"virtual_bit_order": "least_significant_bit_first", "stable_tie": "batch_index_then_path_index"},
        )


def reconstruct_asced(
    spec: AscedSpec, original: QuaternaryOriginalProblem, batches: tuple[AscedBatch, ...] | list[AscedBatch], priors: object,
    expected: AscedResult, *, kernel: ScalarLlrBp4Kernel | FixedAlphaMbp4Kernel,
    overcomplete: Mapping[str, tuple[object, object, tuple[object, ...]]] | None = None,
) -> AscedResult:
    """Independently re-run decoder-visible paths and reject altered evidence."""
    if not isinstance(expected, AscedResult):
        raise ValueError("aSCED replay requires an AscedResult")
    rebuilt = AscedController(spec).run(original, batches, priors, kernel=kernel, overcomplete=overcomplete)
    if rebuilt.as_evidence() != expected.as_evidence():
        raise ValueError("aSCED replay evidence differs from declared all-path execution")
    return rebuilt


def _overcomplete_path_inputs(
    batch: AscedBatch, z_ext: np.ndarray, value: tuple[object, object, tuple[object, ...]],
) -> tuple[np.ndarray, np.ndarray, str, str]:
    """Bind one path to the full verified splitter/map receipt pair."""
    from .asced_overcomplete import (
        AscedOvercompleteMap, ConstructedOvercompleteReceipt, OvercompleteSearchExhausted,
        OvercompleteSearchReceipt, construct_overcomplete_map, map_overcomplete_syndrome,
    )

    map_, receipt, searches = value
    if (
        not isinstance(map_, AscedOvercompleteMap) or not isinstance(receipt, ConstructedOvercompleteReceipt)
        or not isinstance(searches, tuple) or len(searches) != 2
        or any(not isinstance(search, OvercompleteSearchReceipt) for search in searches)
    ):
        raise ValueError("aSCED execution requires typed constructed overcomplete receipts")
    if map_.comparison_only or map_.fidelity != "canonical_adaptation":
        raise ValueError("source comparison maps cannot enter canonical aSCED execution")
    pair_cap = searches[0].pair_cap
    if pair_cap != searches[1].pair_cap:
        raise ValueError("aSCED overcomplete search receipts disagree on pair cap")
    rebuilt = construct_overcomplete_map(batch.qualified, pair_cap=pair_cap)
    if isinstance(rebuilt, OvercompleteSearchExhausted):
        raise ValueError("aSCED overcomplete reconstruction unexpectedly exhausted")
    expected_map, expected_receipt, expected_searches = rebuilt
    if (
        receipt != expected_receipt or searches != expected_searches
        or map_.row_order != expected_map.row_order or map_.row_origin_map != expected_map.row_origin_map
        or map_.fidelity != expected_map.fidelity or map_.comparison_only != expected_map.comparison_only
        or map_.h_ext_sha256 != expected_map.h_ext_sha256 or map_.row_origin_sha256 != expected_map.row_origin_sha256
        or map_.mapping_sha256 != expected_map.mapping_sha256 or map_.h_oc_sha256 != expected_map.h_oc_sha256
        or map_.qualification_sha256 != expected_map.qualification_sha256
        or not np.array_equal(map_.h_ext, expected_map.h_ext) or not np.array_equal(map_.mapping, expected_map.mapping)
        or not np.array_equal(map_.h_oc, expected_map.h_oc)
    ):
        raise ValueError("aSCED overcomplete receipt pair does not match deterministic batch construction")
    raw = np.array(batch.qualified.h_ext, dtype=np.uint8, copy=True)
    extras: list[np.ndarray] = []
    for search in searches:
        pair = getattr(search, "accepted_pair", None)
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise ValueError("aSCED overcomplete search receipt is incomplete")
        support = map_.h_oc[len(raw) + len(extras)]
        extras.append(np.where(support, Pauli.X if search.role == "x" else Pauli.Z, Pauli.I).astype(np.uint8))
    checks = np.vstack((raw, *extras))
    if not np.array_equal((checks != 0).astype(np.uint8), map_.h_oc):
        raise ValueError("aSCED overcomplete checks do not equal the certified H_oc")
    graph_identity = _identity("asced-overcomplete-graph", {
        "batch_graph": batch.graph_identity, "map_receipt": receipt.receipt_sha256,
        "h_oc_sha256": map_.h_oc_sha256,
    })
    return checks, map_overcomplete_syndrome(map_, z_ext), graph_identity, receipt.receipt_sha256


def augment_css(code: CssCode, rows: tuple[AscedSplitterRow, ...]) -> tuple[np.ndarray, tuple[tuple[str, str, int], ...]]:
    """Build the fixed Phase-10 order ``[H_X, T_X, H_Z, T_Z]``."""
    validated = code.validate()
    x_rows = tuple(row for row in rows if row.role == "x")
    z_rows = tuple(row for row in rows if row.role == "z")
    tx = np.vstack([_pauli_row("x", row.support, validated.n) for row in x_rows]) if x_rows else np.empty((0, validated.n), dtype=np.uint8)
    tz = np.vstack([_pauli_row("z", row.support, validated.n) for row in z_rows]) if z_rows else np.empty((0, validated.n), dtype=np.uint8)
    hx = np.where(validated.hx == 1, Pauli.X, Pauli.I).astype(np.uint8)
    hz = np.where(validated.hz == 1, Pauli.Z, Pauli.I).astype(np.uint8)
    row_map = (
        tuple(("x", "original", index) for index in range(len(hx)))
        + tuple(("x", "splitter", index) for index in range(len(tx)))
        + tuple(("z", "original", index) for index in range(len(hz)))
        + tuple(("z", "splitter", index) for index in range(len(tz)))
    )
    return np.vstack((hx, tx, hz, tz)), row_map


def qualify_splitter_batch(code: CssCode, rows: tuple[AscedSplitterRow, ...], *, row_weight: int) -> tuple[np.ndarray, np.ndarray, tuple[tuple[str, str, int], ...], SplitterQualification]:
    """Independently prove the rank, detectability, type, weight, and cycle gates."""
    validated = code.validate()
    if len(rows) == 0 or len(rows) % 2:
        raise ValueError("splitter delta must be a positive even number")
    if tuple(row.role for row in rows) != ("x",) * (len(rows) // 2) + ("z",) * (len(rows) // 2):
        raise ValueError("splitter rows must be ordered X then Z with equal counts")
    if any(len(row.support) != row_weight or any(index < 0 or index >= validated.n for index in row.support) for row in rows):
        raise ValueError("splitter rows must have the declared bounded weight")
    h, h_roles = _css_pauli_rows(validated)
    splitter = np.vstack([_pauli_row(row.role, row.support, validated.n) for row in rows])
    rank_before = _symplectic_rank(h)
    rank_after = _symplectic_rank(np.vstack((h, splitter)))
    detectable_rank = gf2_rank(_commutation(splitter, h))
    combined = np.vstack((h, splitter))
    roles = h_roles + tuple(row.role for row in rows)
    max_overlap = max(
        (int(np.count_nonzero((left != Pauli.I) & (right != Pauli.I)))
         for index, left in enumerate(combined)
         for other_index, right in enumerate(combined[:index])
         if roles[index] == roles[other_index] and index >= len(h)),
        default=0,
    )
    if rank_after != rank_before + len(rows):
        raise ValueError("splitter rows do not achieve the required rank growth")
    if detectable_rank != len(rows):
        raise ValueError("splitter rows do not achieve project detectable rank")
    if max_overlap > 1:
        raise ValueError("splitter rows introduce a same-role 4-cycle")
    h_ext, row_map = augment_css(validated, rows)
    payload = {
        "rank_before": rank_before, "rank_after": rank_after, "detectable_rank": detectable_rank,
        "rows": [(row.role, list(row.support), row.candidate_ordinal) for row in rows],
        "h_ext": h_ext.tolist(), "row_map": [list(item) for item in row_map],
        "row_weight": row_weight, "max_same_role_overlap": max_overlap,
    }
    qualification = SplitterQualification(
        rank_before, rank_after, rank_after - rank_before, detectable_rank,
        tuple(len(row.support) for row in rows), max_overlap, 2 ** len(rows),
        sha256(_canonical_bytes(payload)).hexdigest(),
    )
    return splitter, h_ext, row_map, qualification


def construct_splitter_batch(code: CssCode | PauliCode, *, delta: int, row_weight: int, attempt_cap: int) -> QualifiedAscedBatch | SplitterSearchExhausted:
    """Construct one bounded, deterministic CSS splitter batch before any shot exists."""
    if not isinstance(code, CssCode):
        raise ValueError("aSCED splitter construction requires a CSS artifact; general Pauli inputs are rejected")
    validated = code.validate()
    if type(delta) is not int or delta <= 0 or delta % 2:
        raise ValueError("splitter delta must be a positive even integer")
    if type(row_weight) is not int or not 1 <= row_weight <= validated.n:
        raise ValueError("splitter row weight must be bounded by the CSS block length")
    if type(attempt_cap) is not int or attempt_cap < 1:
        raise ValueError("splitter attempt cap must be positive")
    h, h_roles = _css_pauli_rows(validated)
    searchable_candidates = min(attempt_cap, comb(validated.n, row_weight))
    rows: list[AscedSplitterRow] = []
    search_receipts: list[SplitterSearchReceipt] = []
    for role in ("x",) * (delta // 2) + ("z",) * (delta // 2):
        cycle_rejections = rank_rejections = detectability_rejections = 0
        candidates_examined = 0
        accepted: AscedSplitterRow | None = None
        for ordinal, support in enumerate(combinations(range(validated.n), row_weight)):
            if ordinal >= searchable_candidates:
                break
            candidates_examined += 1
            candidate = _pauli_row(role, support, validated.n)
            existing = np.vstack((h, *[_pauli_row(item.role, item.support, validated.n) for item in rows])) if rows else h
            existing_roles = h_roles + tuple(item.role for item in rows)
            if not _same_role_cycle_free(candidate, existing, existing_roles, role):
                cycle_rejections += 1
                continue
            trial = np.vstack((existing, candidate))
            trial_splitters = np.vstack([_pauli_row(item.role, item.support, validated.n) for item in (*rows, AscedSplitterRow(role, support, ordinal))])
            if _symplectic_rank(trial) != _symplectic_rank(h) + len(rows) + 1:
                rank_rejections += 1
                continue
            if gf2_rank(_commutation(trial_splitters, h)) != len(rows) + 1:
                detectability_rejections += 1
                continue
            trial_rows = tuple(rows + [AscedSplitterRow(role, support, ordinal)])
            accepted = trial_rows[-1]
            rows.append(accepted)
            break
        search_receipts.append(SplitterSearchReceipt(
            role, attempt_cap, candidates_examined,
            None if accepted is None else accepted.candidate_ordinal,
            cycle_rejections, rank_rejections, detectability_rejections,
        ))
        if accepted is None:
            return SplitterSearchExhausted(role, attempt_cap, tuple(search_receipts))
    complete_rows = tuple(rows)
    splitter, h_ext, row_map, qualification = qualify_splitter_batch(validated, complete_rows, row_weight=row_weight)
    profile = _construction_profile(delta=delta, row_weight=row_weight, attempt_cap=attempt_cap)
    artifact_sha = _artifact_sha256(validated)
    splitter_sha = sha256(_canonical_bytes(splitter.tolist())).hexdigest()
    h_ext_sha = sha256(_canonical_bytes({"rows": h_ext.tolist(), "row_map": [list(item) for item in row_map]})).hexdigest()
    receipt_payload = _constructed_receipt_payload(
        artifact_sha256=artifact_sha,
        profile=profile,
        splitter_sha256=splitter_sha,
        h_ext_sha256=h_ext_sha,
        qualification_sha256=qualification.qualification_sha256,
        search_receipts=tuple(search_receipts),
    )
    receipt = ConstructedSplitterReceipt(
        "canonical_adaptation", "asced-css-lexicographic-v1", _SOURCE_COMPONENT_IDS, artifact_sha,
        sha256(_canonical_bytes(profile)).hexdigest(), splitter_sha, h_ext_sha, "completed",
        tuple(search_receipts), sha256(_canonical_bytes(receipt_payload)).hexdigest(),
    )
    return QualifiedAscedBatch(validated, complete_rows, splitter, h_ext, row_map, receipt, qualification)


def _verify_qualified_batch(batch: QualifiedAscedBatch) -> None:
    """Fail closed when any graph, witness, or receipt byte no longer agrees."""
    if not isinstance(batch, QualifiedAscedBatch):
        raise ValueError("materialization accepts only a complete QualifiedAscedBatch")
    if batch.receipt.run_fidelity != "canonical_adaptation" or batch.receipt.terminal_status != "completed":
        raise ValueError("materialization requires a completed canonical-adaptation construction receipt")
    receipt = batch.receipt
    if receipt.constructor_identity != "asced-css-lexicographic-v1" or receipt.source_component_ids != _SOURCE_COMPONENT_IDS:
        raise ValueError("materialization rejected an unrecognized construction receipt")
    if receipt.artifact_sha256 != _artifact_sha256(batch.code):
        raise ValueError("materialization rejected a receipt/source artifact mismatch")
    if not batch.rows or len(receipt.search_receipts) != len(batch.rows):
        raise ValueError("materialization rejected an incomplete construction search receipt")
    if len(batch.qualification.row_weights) != len(batch.rows):
        raise ValueError("materialization rejected a malformed qualification witness")
    row_weight = batch.qualification.row_weights[0]
    if any(weight != row_weight for weight in batch.qualification.row_weights):
        raise ValueError("materialization rejected a nonuniform construction profile")
    attempt_cap = receipt.search_receipts[0].attempt_cap
    if attempt_cap < 1 or any(search.attempt_cap != attempt_cap for search in receipt.search_receipts):
        raise ValueError("materialization rejected inconsistent search attempt caps")
    profile = _construction_profile(delta=len(batch.rows), row_weight=row_weight, attempt_cap=attempt_cap)
    if receipt.profile_sha256 != sha256(_canonical_bytes(profile)).hexdigest():
        raise ValueError("materialization rejected a receipt/profile mismatch")
    for row, search in zip(batch.rows, receipt.search_receipts):
        rejected = search.rejected_cycle + search.rejected_rank + search.rejected_detectability
        if (
            search.role != row.role
            or search.accepted_ordinal != row.candidate_ordinal
            or search.candidates_examined != row.candidate_ordinal + 1
            or search.candidates_examined > min(search.attempt_cap, comb(batch.code.n, row_weight))
            or rejected != search.candidates_examined - 1
        ):
            raise ValueError("materialization rejected an inconsistent construction search receipt")
    expected_splitter, expected_h_ext, expected_map, expected_qualification = qualify_splitter_batch(
        batch.code, batch.rows, row_weight=row_weight,
    )
    if (
        not np.array_equal(expected_splitter, batch.splitter)
        or not np.array_equal(expected_h_ext, batch.h_ext)
        or expected_map != batch.h_ext_row_map
        or expected_qualification != batch.qualification
    ):
        raise ValueError("materialization rejected a mismatched splitter graph or qualification witness")
    splitter_sha = sha256(_canonical_bytes(batch.splitter.tolist())).hexdigest()
    h_ext_sha = sha256(_canonical_bytes({"rows": batch.h_ext.tolist(), "row_map": [list(item) for item in batch.h_ext_row_map]})).hexdigest()
    if batch.receipt.splitter_sha256 != splitter_sha or batch.receipt.h_ext_sha256 != h_ext_sha:
        raise ValueError("materialization rejected a receipt/content digest mismatch")
    receipt_payload = _constructed_receipt_payload(
        artifact_sha256=receipt.artifact_sha256,
        profile=profile,
        splitter_sha256=splitter_sha,
        h_ext_sha256=h_ext_sha,
        qualification_sha256=batch.qualification.qualification_sha256,
        search_receipts=receipt.search_receipts,
    )
    if receipt.receipt_sha256 != sha256(_canonical_bytes(receipt_payload)).hexdigest():
        raise ValueError("materialization rejected a constructed receipt digest mismatch")
    reconstructed = construct_splitter_batch(
        batch.code, delta=len(batch.rows), row_weight=row_weight, attempt_cap=attempt_cap,
    )
    if (
        isinstance(reconstructed, SplitterSearchExhausted)
        or reconstructed.rows != batch.rows
        or reconstructed.receipt != receipt
    ):
        raise ValueError("materialization rejected a noncanonical construction search receipt")


def materialize_asced_batches(
    original: QuaternaryOriginalProblem,
    batches: tuple[QualifiedAscedBatch, ...] | list[QualifiedAscedBatch],
    *, path_cap: int,
) -> tuple[AscedBatch, ...]:
    """Freeze all validated aSCED graphs and their closed virtual path cardinality."""
    if not isinstance(original, QuaternaryOriginalProblem):
        raise ValueError("aSCED materialization requires an immutable quaternary original problem")
    declared = tuple(batches)
    if not declared or type(path_cap) is not int or path_cap < 1:
        raise ValueError("aSCED materialization requires nonempty batches and a positive path cap")
    total_paths = sum(2 ** len(batch.rows) for batch in declared if isinstance(batch, QualifiedAscedBatch))
    if len(declared) != len([batch for batch in declared if isinstance(batch, QualifiedAscedBatch)]):
        raise ValueError("materialization rejects raw rows, partial searches, and exhausted terminals")
    if total_paths > path_cap:
        raise ValueError("aSCED path cardinality exceeds the declared preflight cap")
    materialized: list[AscedBatch] = []
    identities: set[str] = set()
    for local_order, qualified in enumerate(declared):
        _verify_qualified_batch(qualified)
        h, roles = _css_pauli_rows(qualified.code)
        if not np.array_equal(original.code.checks, h) or tuple(original.code.row_roles) != roles:
            raise ValueError("materialization requires a splitter batch matching the immutable original CSS graph")
        x_count = qualified.code.hx.shape[0]
        z_count = qualified.code.hz.shape[0]
        x_splitters = sum(row.role == "x" for row in qualified.rows)
        z_splitters = sum(row.role == "z" for row in qualified.rows)
        extended_syndrome = np.concatenate((
            original.syndrome[:x_count], np.zeros(x_splitters, dtype=np.uint8),
            original.syndrome[x_count:x_count + z_count], np.zeros(z_splitters, dtype=np.uint8),
        ))
        graph_payload = {
            "original": original.semantic_sha256,
            "receipt": qualified.receipt.receipt_sha256,
            "qualification": qualified.qualification.qualification_sha256,
            "row_map": [list(item) for item in qualified.h_ext_row_map],
            "local_order": local_order,
        }
        graph_identity = _identity("asced-graph", graph_payload)
        if graph_identity in identities:
            raise ValueError("materialization requires distinct declared batch graph identities")
        identities.add(graph_identity)
        transform_identity = _identity("asced-transform", graph_payload)
        lift_identity = _identity("asced-lift", {"original": original.semantic_sha256, "graph": graph_identity})
        working_id = stable_lineage_id("working", {"original": original.lineage_id, "graph": graph_identity}).value
        working = AscedWorkingGraph(
            working_id, original,
            LineageEdge("transform", LineageId("original", original.lineage_id), LineageId("working", working_id)),
            checks=qualified.h_ext, syndrome=extended_syndrome, row_map=qualified.h_ext_row_map,
            transform_identity=transform_identity, lift_identity=lift_identity,
        )
        materialized.append(AscedBatch(
            f"asced-batch-{local_order}-{qualified.receipt.receipt_sha256[:16]}", local_order,
            qualified, working, graph_identity, 2 ** len(qualified.rows),
        ))
    return tuple(materialized)


__all__ = [
    "AscedBatch", "AscedController", "AscedPathResult", "AscedResult", "AscedSpec", "AscedSplitterRow", "AscedWorkingGraph", "ConstructedSplitterReceipt", "QualifiedAscedBatch", "SplitterQualification",
    "SplitterSearchExhausted", "SplitterSearchReceipt", "augment_css", "construct_splitter_batch", "gb46_canonical_fixture_payload",
    "materialize_asced_batches", "parse_pinned_gb46_css", "qualify_splitter_batch", "reconstruct_asced",
]
