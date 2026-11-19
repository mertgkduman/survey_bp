"""Exercise the canonical decoder and worker paths on a bounded pilot."""
from copy import deepcopy
from dataclasses import asdict
from pathlib import Path
import tempfile

import numpy as np
import stim

from bp_registry.canonical.prior_tilt import PriorTiltDecoder, PriorTiltSpec
from bp_registry.circuit.dem import DemBinaryModel
from bp_registry.circuit.tuned_minsum import MinSumSpec, TunableMinSum
import evaluate
import report
import run
import tune


def range_stress():
    # Four mutually reinforcing parity checks and one impossible detector.
    # The exact all-positive messages diverge in magnitude without changing sign.
    dem = stim.DetectorErrorModel("\n".join(["error(.2) D0 D1 D2 D3"] * 4 + ["detector D4"]))
    model = DemBinaryModel.from_dem(dem)
    syndrome = np.array([0, 0, 0, 0, 1], np.uint8)
    native_range = PriorTiltDecoder(model.table, model.prior_llrs,
                                    PriorTiltSpec(initial=18080, round_len=1, rounds=0))
    try:
        native_range.decode(syndrome, shot=0)
    except ValueError as exc:
        assert "nonfinite" in str(exc)
    else:
        raise AssertionError("overflow fixture failed to reproduce the original error")
    for spec in (MinSumSpec(), MinSumSpec(damping=.25, alpha=.8, beta=.5)):
        result = TunableMinSum(model, spec).decode(syndrome, shot=0)
        assert result.lineage > 0 and np.isfinite(result.posterior).all()
        assert not result.converged and result.iterations == 18080
        assert result.directed_edge_updates == 18080 * 2 * model.table.edge_count
        assert np.array_equal(result.candidate, np.zeros(model.table.variable_count, np.uint8))
    print("PASS full-cap float64 overflow fixture for ordinary and tuned min-sum")


def main():
    range_stress()
    original = run.ROOT
    plan = run.load()
    assert len(plan["jobs"]) == 28
    assert len(plan["training_points"]) == 4
    assert {p["p"] for p in plan["training_points"].values()} == {.003}
    probes = []
    for group, point in plan["training_points"].items():
        for basis in run.BASES:
            circuit, model = run.case_model(point, basis)
            source = PriorTiltDecoder(model.table, model.prior_llrs, PriorTiltSpec(initial=32, round_len=1, rounds=0))
            bp = TunableMinSum(model, MinSumSpec(iterations=32))
            for i, syndrome in enumerate(circuit.compile_detector_sampler(seed=721).sample(3).astype(np.uint8)):
                a, b = (decoder.decode(syndrome, shot=i) for decoder in (source, bp))
                np.testing.assert_array_equal(a.candidate, b.candidate)
                np.testing.assert_array_equal(a.posterior, b.posterior)
                assert (a.converged, a.iterations, a.directed_edge_updates) == (
                    b.converged, b.iterations, b.directed_edge_updates)
                probes.append((group, basis, i))
    (original / "results").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="qualification-", dir=original / "results") as root:
        run.ROOT = Path(root)
        small = deepcopy(plan)
        small["jobs"] = [next(j for j in plan["jobs"] if j["group"] == "xz-bb144"
                              and j["method"] == method and j["p"] == .003) for method in ("bp", "tuned-bp")]
        small["protocol"].update({"iterations": 12, "max_shots": 32, "target_errors": 1, "minimum_free_bytes": 0})
        small["protocol"]["evaluation_batch"]["xz"] = 16
        small["tuning"].update({"seed": 20261119072, "shots_per_basis": [8, 12, 16], "advance": [3, 2]})
        small["tuning"]["candidates"] = [tune.NEUTRAL, {"damping": .25, "alpha": .8, "beta": .5},
                                        {"damping": .5, "alpha": .65, "beta": 0.0}]
        run.write_json(run.ROOT / "plan.json", small)
        assert report.checked_row(small, 1) is None
        tune.tune(small, "xz-bb144", 2)
        assert run.read_json(run.selection_path("xz-bb144"))["controls"] in small["tuning"]["candidates"]
        for index in range(2):
            job = run.resolve_job(small, index)
            evaluate.run_point(small, job, False, 2)
            assert report.checked_row(small, index) is None
            evaluate.run_point(small, job, True, 2)
            row = report.checked_row(small, index)
            assert all(row[f"{b}_errors"] == 1 or row[f"{b}_shots"] == 32 for b in run.BASES)
            assert row["iterations"] == 12 and 0 <= row["ci95_low"] <= row["ler_per_cycle"] <= row["ci95_high"]
            evaluate.run_point(small, job, False, 2)
            assert report.checked_row(small, index) == row
        report.collect(small)
    print(f"PASS {len(probes)} canonical neutral checks, training selection and two spawned-process end-to-end audits")


if __name__ == "__main__":
    main()
