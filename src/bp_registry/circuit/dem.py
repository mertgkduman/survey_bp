"""Lossless independent-mechanism projection of a Stim detector error model."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import math

import numpy as np
import stim

from bp_registry.canonical.schedules import EdgeTable


@dataclass(frozen=True, slots=True)
class DemBinaryModel:
    """One binary variable per independent DEM error instruction.

    A `^` separator suggests a decomposition; it does not split the Bernoulli
    mechanism. Keeping the whole instruction preserves its detector and
    observable parity under the declared DEM semantics.
    """

    dem_sha256: str
    table: EdgeTable
    row_ptr: np.ndarray
    variables: np.ndarray
    observable_matrix: np.ndarray
    prior_llrs: np.ndarray
    syndrome_bias: np.ndarray
    observable_bias: np.ndarray
    source_error_count: int

    @classmethod
    def from_dem(cls, dem: stim.DetectorErrorModel) -> "DemBinaryModel":
        if not isinstance(dem, stim.DetectorErrorModel):
            raise TypeError("dem must be a Stim DetectorErrorModel")
        n_det, n_obs = dem.num_detectors, dem.num_observables
        rows: list[list[int]] = [[] for _ in range(n_det)]
        obs_columns: list[set[int]] = []
        priors: list[float] = []
        syndrome_bias = np.zeros(n_det, dtype=np.uint8)
        observable_bias = np.zeros(n_obs, dtype=np.uint8)
        source_error_count = 0
        for instruction in dem.flattened():
            if instruction.type in {"detector", "logical_observable", "shift_detectors"}:
                continue
            if instruction.type != "error":
                raise ValueError(f"unsupported DEM instruction: {instruction.type}")
            source_error_count += 1
            args = instruction.args_copy()
            if len(args) != 1 or not math.isfinite(args[0]) or not 0 <= args[0] <= 1:
                raise ValueError("DEM error probability must be in [0,1]")
            probability = float(args[0])
            detectors: set[int] = set()
            observables: set[int] = set()
            for target in instruction.targets_copy():
                if target.is_separator():
                    continue
                if target.is_relative_detector_id():
                    index = target.val
                    if index in detectors:
                        detectors.remove(index)
                    else:
                        detectors.add(index)
                elif target.is_logical_observable_id():
                    index = target.val
                    if index in observables:
                        observables.remove(index)
                    else:
                        observables.add(index)
                else:
                    raise ValueError(f"unsupported DEM error target: {target}")
            if probability == 0:
                continue
            if probability == 1:
                for index in detectors:
                    syndrome_bias[index] ^= 1
                for index in observables:
                    observable_bias[index] ^= 1
                continue
            variable = len(priors)
            priors.append(math.log1p(-probability) - math.log(probability))
            obs_columns.append(observables)
            for index in detectors:
                rows[index].append(variable)
        edges = [(check, variable) for check, row in enumerate(rows) for variable in sorted(row)]
        table = EdgeTable.from_edges(n_det, len(priors), edges)
        row_ptr = np.zeros(n_det + 1, dtype=np.int64)
        variables = np.empty(table.edge_count, dtype=np.int64)
        for edge, (check, variable) in enumerate(table.edges):
            row_ptr[check + 1] += 1
            variables[edge] = variable
        np.cumsum(row_ptr, out=row_ptr)
        observable_matrix = np.zeros((n_obs, len(priors)), dtype=np.uint8)
        for variable, observable_ids in enumerate(obs_columns):
            for observable in observable_ids:
                observable_matrix[observable, variable] = 1
        arrays = (row_ptr, variables, observable_matrix, syndrome_bias, observable_bias)
        for array in arrays:
            array.setflags(write=False)
        prior_llrs = np.asarray(priors, dtype=np.float64)
        prior_llrs.setflags(write=False)
        return cls(
            sha256(str(dem).encode("utf-8")).hexdigest(), table, row_ptr, variables,
            observable_matrix, prior_llrs, syndrome_bias, observable_bias, source_error_count,
        )
