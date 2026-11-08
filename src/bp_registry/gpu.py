"""Explicit optional CUDA backend for the canonical float64 flooding subset."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import platform
import time

import numpy as np

from .compiled_contracts import immutable_array
from .batch_records import encode_records, write_records, read_records


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(*arrays):
    result = sha256()
    for array in arrays:
        value = np.ascontiguousarray(array)
        result.update(str((value.shape, value.dtype.str)).encode())
        result.update(value.tobytes())
    return result.hexdigest()


@dataclass(frozen=True)
class GpuBatchResult:
    candidates: np.ndarray
    converged: np.ndarray
    iterations: np.ndarray
    syndromes: np.ndarray
    evidence_json: str

    def __post_init__(self):
        header = json.loads(self.evidence_json)
        arrays = tuple(np.asarray(getattr(self, name)) for name in ("candidates", "converged", "iterations", "syndromes"))
        c, v, k, s = arrays
        if (c.ndim != 2 or s.ndim != 2 or v.shape != (len(c),) or k.shape != (len(c),) or len(s) != len(c)
                or c.dtype != np.uint8 or s.dtype != np.uint8 or v.dtype != np.bool_ or k.dtype != np.int64
                or np.any(c > (1 if header.get("family") == "binary" else 3)) or np.any(s > 1)
                or np.any(k < 0) or np.any(k > header.get("max_iterations", -1))
                or header.get("shape") != list(s.shape) or header.get("variable_count") != c.shape[1]
                or header.get("schema") != "gpu-flooding-ledger-v1"):
            raise ValueError("invalid CUDA batch dimensions, values, or metadata")
        declared = header.pop("result_sha256", None)
        if declared != sha256((_json(header) + _digest(*arrays)).encode()).hexdigest():
            raise ValueError("CUDA result arrays disagree with bound evidence")
        for name, value in zip(("candidates", "converged", "iterations", "syndromes"), arrays):
            object.__setattr__(self, name, immutable_array(value, value.dtype))

    @property
    def metadata(self):
        return json.loads(self.evidence_json)

    @property
    def ledger_json(self):
        # Large per-shot JSON is an export cost, not a decoding hot-loop cost.
        # The arrays and small metadata were already bound and made immutable.
        header = self.metadata
        edges, n, states = header["edge_count"], header["variable_count"], header["state_coordinates"]
        rows = [header]
        for i in range(len(self.syndromes)):
            k = int(self.iterations[i])
            rows.append({"shot": i, "syndrome": self.syndromes[i].tolist(), "candidate": self.candidates[i].tolist(),
                         "converged": bool(self.converged[i]), "iterations": k,
                         "work": {"c2v": k * edges, "v2c": k * edges * states,
                                  "belief_elements": k * n * states, "candidate_checks": k + 1}})
        return encode_records(rows)

    @property
    def ledger(self):
        return json.loads(self.ledger_json)

    def write_ledger(self, path):
        write_records(path, self.ledger_json, "gpu-flooding-ledger-v1")


class CudaFlooding:
    """Reusable device graph; bounded workspace and no implicit CPU fallback.

    Construct with from_binary(graph, error_rate=...) or from_pauli(graph).
    Graphs must carry an explicit v2 min-sum or v3 stable-SPA float64 policy.
    """
    @classmethod
    def from_binary(cls, graph, *, error_rate, allow_simulator=False):
        from .canonical.compiled import CompiledBinaryFlooding
        if not isinstance(graph, CompiledBinaryFlooding):
            raise ValueError("expected a validated CompiledBinaryFlooding")
        _, prior = graph._inputs(np.zeros(graph.table.check_count, np.uint8), error_rate)
        return cls(graph, np.full((graph.table.variable_count, 1), prior), error_rate, allow_simulator)

    @classmethod
    def from_pauli(cls, graph, *, allow_simulator=False):
        from .quaternary.compiled import CompiledBp4Graph
        if not isinstance(graph, CompiledBp4Graph):
            raise ValueError("expected a validated CompiledBp4Graph")
        return cls(graph, graph.prior_llrs, None, allow_simulator)

    def __init__(self, graph, priors, error_rate, allow_simulator):
        from .canonical.compiled import CompiledBinaryFlooding
        from .quaternary.compiled import CompiledBp4Graph
        from numba import cuda, config
        import numba
        from .cuda_kernels import flooding
        if type(allow_simulator) is not bool:
            raise ValueError("allow_simulator must be a boolean")
        if isinstance(graph, CompiledBinaryFlooding):
            _, prior = graph._inputs(np.zeros(graph.table.check_count, np.uint8), error_rate)
            expected_prior = np.full((graph.table.variable_count, 1), prior)
        elif isinstance(graph, CompiledBp4Graph) and error_rate is None:
            expected_prior = graph.prior_llrs
        else:
            raise ValueError("CUDA requires a validated binary or Pauli graph")
        if not np.array_equal(priors, expected_prior):
            raise ValueError("CUDA priors must match the bound canonical graph")
        policy = graph.policy
        if (policy is None or policy.resolution.format != "float64" or
                policy.version == "bp-flooding-policy-v1" or
                (policy.check_rule == "sum_product" and policy.check_stabilization != "log_domain")):
            raise ValueError("CUDA requires explicit float64 stable SPA v3 or min-sum v2/v3 policy")
        simulated = bool(config.ENABLE_CUDASIM)
        if simulated and not allow_simulator:
            raise RuntimeError("CUDA simulator is active; explicit allow_simulator=True is required")
        if not cuda.is_available():
            raise RuntimeError("CUDA device unavailable; request a GPU allocation and load its CUDA toolkit")
        self._cuda, self._kernel, self._graph = cuda, flooding, graph
        self._error_rate, self._policy = error_rate, policy
        self._family = "binary" if error_rate is not None else "pauli"
        self._prior = immutable_array(priors, np.float64)
        variables, rows = graph.variables, graph.row_ptr
        n, states = self._prior.shape
        if states == 1:
            var_edges = np.argsort(variables, kind="stable").astype(np.int64)
            var_ptr = np.concatenate(([0], np.cumsum(np.bincount(variables, minlength=n)))).astype(np.int64)
            labels = np.ones(len(variables), np.uint8)
        else:
            var_edges, var_ptr, labels = graph.variable_edges, graph.variable_ptr, graph.labels
        self._host = tuple(immutable_array(a, a.dtype) for a in (rows, var_ptr, var_edges, variables, labels, self._prior))
        self._identity = _digest(*self._host)
        self._device = tuple(cuda.to_device(a) for a in self._host)
        self._runtime = {"backend": "cuda-simulator" if simulated else "numba-cuda-f64-v1",
                         "numba": numba.__version__, "numpy": np.__version__, "python": platform.python_version(),
                         "kernel_sha256": sha256(Path(__file__).with_name("cuda_kernels.py").read_bytes()).hexdigest()}
        if not simulated:
            device = cuda.get_current_device()
            name = device.name.decode() if isinstance(device.name, bytes) else str(device.name)
            self._runtime.update(device=name, compute_capability=list(device.compute_capability),
                                 cuda_runtime=list(cuda.runtime.get_version()))

    def run_batch(self, syndromes, *, max_iterations, stop_on_convergence=True, workspace_bytes=256 * 1024**2):
        if (type(max_iterations) is not int or not 0 <= max_iterations < np.iinfo(np.int64).max or
                type(stop_on_convergence) is not bool or type(workspace_bytes) is not int or workspace_bytes < 1):
            raise ValueError("invalid CUDA iteration, stopping, or workspace request")
        if self._family == "binary" and not stop_on_convergence:
            raise ValueError("binary CPU contract requires stop_on_convergence=True")
        s = np.asarray(syndromes)
        m, n, states, edges = len(self._host[0]) - 1, *self._prior.shape, len(self._host[3])
        if (s.ndim != 2 or s.shape[1] != m or not np.issubdtype(s.dtype, np.integer) or
                np.any((s != 0) & (s != 1))):
            raise ValueError("syndromes must be a binary integer shot-by-check matrix")
        s = np.array(s, dtype=np.uint8, order="C", copy=True)
        per_shot = 8 * (edges * (states + 3) + n * states) + n + m + 10
        if workspace_bytes < per_shot and len(s):
            raise ValueError("workspace budget cannot hold one shot")
        chunk_size = max(1, min(65535, workspace_bytes // max(1, per_shot)))
        candidates = np.empty((len(s), n), np.uint8)
        valid, iterations = np.empty(len(s), bool), np.empty(len(s), np.int64)
        cuda, policy = self._cuda, self._policy
        started = time.perf_counter()
        capacity = min(len(s), chunk_size)
        if capacity:
            old = cuda.device_array((capacity, edges, states), np.float64)
            comm, prefix, c2v = (cuda.device_array((capacity, edges), np.float64) for _ in range(3))
            beliefs = cuda.device_array((capacity, n, states), np.float64)
            dc = cuda.device_array((capacity, n), np.uint8)
            di = cuda.device_array(capacity, np.int64)
            dv, df = (cuda.device_array(capacity, np.uint8) for _ in range(2))
        for begin in range(0, len(s), chunk_size):
            end = min(len(s), begin + chunk_size)
            count = end - begin
            ds = cuda.to_device(s[begin:end])
            self._kernel[count, 128](*self._device, ds, max_iterations, policy.check_rule == "min_sum",
                                    *policy.coefficients, policy.product_epsilon, policy.decision_code,
                                    policy.zero_syndrome_shortcut, stop_on_convergence,
                                    old, comm, prefix, c2v, beliefs, dc, di, dv, df)
            if np.any(df[:count].copy_to_host()):
                raise FloatingPointError("nonfinite CUDA BP state; entire batch rejected")
            candidates[begin:end], iterations[begin:end], valid[begin:end] = (
                dc[:count].copy_to_host(), di[:count].copy_to_host(), dv[:count].copy_to_host())
        seconds = time.perf_counter() - started
        header = {"schema": "gpu-flooding-ledger-v1", "runtime": self._runtime, "family": self._family,
                  "graph_prior_sha256": self._identity, "policy": policy.as_spec(),
                  "syndromes_sha256": _digest(s), "shape": list(s.shape),
                  "max_iterations": max_iterations, "stop_on_convergence": stop_on_convergence,
                  "variable_count": n, "edge_count": edges, "state_coordinates": states,
                  "elapsed_seconds_including_transfers_and_any_jit": seconds}
        header["result_sha256"] = sha256((_json(header) + _digest(candidates, valid, iterations, s)).encode()).hexdigest()
        return GpuBatchResult(candidates, valid, iterations, s, _json(header))

    def verify_ledger(self, path):
        """Independently replay stored shots on the canonical compiled CPU."""
        rows = read_records(path, "gpu-flooding-ledger-v1")
        if not rows:
            raise ValueError("empty CUDA ledger")
        header = rows[0]
        if (header.get("schema") != "gpu-flooding-ledger-v1" or header.get("family") != self._family or
                header.get("graph_prior_sha256") != self._identity or header.get("policy") != self._policy.as_spec() or
                header.get("variable_count") != self._prior.shape[0] or
                header.get("state_coordinates") != self._prior.shape[1] or
                header.get("edge_count") != len(self._host[3]) or
                header.get("shape") != [len(rows) - 1, len(self._host[0]) - 1]):
            raise ValueError("CUDA ledger configuration mismatch")
        syndromes = np.asarray([row["syndrome"] for row in rows[1:]], dtype=np.uint8).reshape(header["shape"])
        if _digest(syndromes) != header.get("syndromes_sha256"):
            raise ValueError("CUDA ledger syndrome identity mismatch")
        metadata = {key: value for key, value in header.items() if key != "ledger_sha256"}
        GpuBatchResult(
            np.asarray([row["candidate"] for row in rows[1:]], np.uint8).reshape((len(rows)-1, self._prior.shape[0])),
            np.asarray([row["converged"] for row in rows[1:]], bool),
            np.asarray([row["iterations"] for row in rows[1:]], np.int64), syndromes, _json(metadata))
        edges, n, states = len(self._host[3]), *self._prior.shape
        for i, (s, row) in enumerate(zip(syndromes, rows[1:])):
            kwargs = ({"error_rate": self._error_rate} if self._family == "binary" else
                      {"stop_on_convergence": header["stop_on_convergence"]})
            cpu = self._graph.run(s, max_iterations=header["max_iterations"], **kwargs)
            k = cpu.iterations
            expected = {"shot": i, "syndrome": s.tolist(), "candidate": cpu.candidate.tolist(),
                        "converged": cpu.converged, "iterations": k,
                        "work": {"c2v": k * edges, "v2c": k * edges * states,
                                 "belief_elements": k * n * states, "candidate_checks": k + 1}}
            if row != expected:
                raise ValueError(f"CUDA ledger disagrees with CPU replay at shot {i}")
        return {"verified": True, "shots": len(syndromes), "reference": "canonical-compiled-cpu"}
