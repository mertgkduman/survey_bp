from pathlib import Path
from dataclasses import replace
from hashlib import sha256
import json
import subprocess
import sys
import tempfile
import numpy as np
import stim

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from audit_support import Audit, ROOT
from bp_registry.batch_records import canonical_json, encode_records, read_records
from bp_registry.circuit import CircuitPolicy, PolicyBpSinterDecoder
from bp_registry.gpu import GpuBatchResult

HERE = Path(__file__).resolve().parent
PRIOR = ROOT / ".planning/quick/261108-meg-implement-compatible-circuit-policies-an"


def circuit():
    return PolicyBpSinterDecoder(CircuitPolicy(max_iterations=3)).compile_decoder_for_dem(
        dem=stim.DetectorErrorModel("error(0.1) D0 L0"))


def ordinary_binding():
    decoder = circuit()
    result = decoder.decode_detailed(np.array([[0], [1]], np.uint8))
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "ledger.jsonl"
        result.write_ledger(path)
        replay = decoder.verify_ledger(path)
        original = path.read_bytes()
        try:
            result.write_ledger(path)
        except FileExistsError:
            pass
        else:
            raise AssertionError("existing ledger overwritten")
        assert path.read_bytes() == original
    for name in ("predictions", "faults", "converged", "iterations"):
        try:
            getattr(result, name).setflags(write=True)
        except ValueError:
            pass
        else:
            raise AssertionError(f"mutable result {name}")
    try:
        replace(result, predictions=result.predictions ^ 1)
    except ValueError:
        pass
    else:
        raise AssertionError("stale ledger accepted")
    return dict(replay=replay, immutable_columns=4, exclusive_publication=True, stale_binding_rejected=True)


def execution_dtype_binding():
    decoder = circuit()
    original = decoder.decode_detailed(np.array([[0]], np.uint8))
    examples = [("faults", "faults", [[256]]), ("predictions", "prediction", [[256]]),
                ("converged", "converged", [2]), ("iterations", "iterations", [1.5]),
                ("iterations", "iterations", [-1])]
    accepted = []
    for field, key, values in examples:
        value = np.asarray(values)
        rows = original.ledger
        rows[1][key] = values[0]
        try:
            changed = replace(original, **{field: value, "ledger_json": encode_records(rows)})
        except ValueError:
            continue
        bound = [row[key] for row in changed.ledger[1:]]
        actual = getattr(changed, field).tolist()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.jsonl"
            changed.write_ledger(path)
            try:
                decoder.verify_ledger(path)
            except ValueError:
                replay_rejected = True
            else:
                replay_rejected = False
        accepted.append(dict(field=field, input=values, stored_array=actual, bound_ledger=bound,
                             array_ledger_agree=actual == bound, independent_replay_rejected=replay_rejected))
    (HERE / "conversion-counterexamples.json").write_text(json.dumps(accepted, indent=2) + "\n")
    assert not accepted, f"{len(accepted)} invalid result values admitted; {sum(not r['array_ledger_agree'] for r in accepted)} diverge after casting"


def carried_hardware_evidence():
    hashes = json.loads((PRIOR / "gpu-final/source-sha256.json").read_text())
    for name, digest in hashes.items():
        assert sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
    # Baseline source equality also covers shared canonical CPU dependencies.
    changed = subprocess.check_output(["git", "diff", "b598ad1", "--", "src", "pyproject.toml"], cwd=ROOT, text=True)
    assert not changed, "production source changed since the carried qualification"
    qualification = json.loads((PRIOR / "gpu-final/gpu-qualification.json").read_text())
    bundle = []
    for case in qualification:
        path = PRIOR / f"gpu-final/gpu-{case['family']}-{case['policy']}.jsonl"
        rows = read_records(path, "gpu-flooding-ledger-v1")
        header = {k: v for k, v in rows[0].items() if k != "ledger_sha256"}
        result = GpuBatchResult(np.asarray([r["candidate"] for r in rows[1:]], np.uint8),
            np.asarray([r["converged"] for r in rows[1:]], bool),
            np.asarray([r["iterations"] for r in rows[1:]], np.int64),
            np.asarray([r["syndrome"] for r in rows[1:]], np.uint8), canonical_json(header))
        assert result.ledger == rows
        assert len(rows)-1 == case["shots"] == case["stored_cpu_replay"]["shots"]
        assert case["stored_cpu_replay"]["verified"]
        assert case["parity"] == "all_candidates_iterations_convergence_exact"
        for field, value in (("candidates", result.candidates.astype(np.int64)),
                             ("iterations", result.iterations.astype(float))):
            try:
                replace(result, **{field: value})
            except ValueError:
                pass
            else:
                raise AssertionError("GPU execution dtype admission bypass")
        bundle.append(dict(path=str(path.relative_to(ROOT)), sha256=sha256(path.read_bytes()).hexdigest(),
            shots=len(rows)-1, runtime=case["gpu_runtime"], warm_speedup_vs_two_cpu_workers=case["speedup_vs_two_cpu_workers"],
            median_decode_seconds=float(np.median(case["gpu_warm_seconds"])), export_seconds=case["ledger_export_seconds"],
            validation="fresh content/result binding; CPU replay and H200 execution carried from original qualification"))
    for name in ("full-suite.log", "gpu-hardware-final.log", "circuit-final.log"):
        path = PRIOR / name
        bundle.append(dict(path=str(path.relative_to(ROOT)), sha256=sha256(path.read_bytes()).hexdigest(),
                           summary=path.read_text().splitlines()[-1]))
    (HERE / "carried-qualification.json").write_text(json.dumps(bundle, indent=2) + "\n")
    return dict(source_hashes_verified=len(hashes), hardware_shots=sum(x['shots'] for x in qualification),
                stored_ledgers_freshly_validated=4, new_hardware_execution=False,
                timing_scope="warm decode includes transfer/result binding; JIT and JSON export excluded")


if __name__ == "__main__":
    audit = Audit(HERE)
    audit.probe("normal_circuit_evidence_binding", ordinary_binding)
    audit.probe("circuit_execution_dtype_admission", execution_dtype_binding)
    audit.probe("source_bound_hardware_qualification", carried_hardware_evidence)
    audit.finish()
