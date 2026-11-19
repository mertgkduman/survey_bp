"""Bounded checks for controller equivalence, training and confirmation."""
import json
from pathlib import Path
import tempfile

import numpy as np

import run
import confirm
import report
import screen
import tune


def same(a, b):
    for field in ("candidate", "posterior", "trace"):
        np.testing.assert_array_equal(getattr(a, field), getattr(b, field))
    for field in ("converged", "iterations", "directed_edge_updates", "random_draws", "biased_node_updates", "lineage"):
        assert getattr(a, field) == getattr(b, field), field


def reduced(job):
    p = dict(job["policy"])
    method = job["method"]
    if method == "priortilt":
        p.update(initial=2, round_len=1, rounds=3, ends=(), phases=(((.1,.5,.8,2.),)))
    else:
        p.update(initial=2, per_leg=2)
        if method == "beam":
            p.update(rounds=2, width=2)
        elif method == "relay5":
            p.update(additional=2, results=2)
        else:
            p.update(additional=2)
    return {**job, "policy": p}


def original_decoder(job, basis, model):
    from bp_registry.canonical.prior_tilt import PriorTiltDecoder
    from bp_registry.circuit.paper_decoders import CircuitPaperDecoder
    from bp_registry.circuit.relay_list import CircuitRelayListDecoder
    spec = run.spec_for(job)
    seed = job["seed_by_basis"][basis]
    if job["method"] == "priortilt":
        return PriorTiltDecoder(model.table, model.prior_llrs, spec, seed)
    cls = CircuitRelayListDecoder if job["method"] == "relay5" else CircuitPaperDecoder
    return cls(model, spec, seed)


def controller_checks(plan):
    selected = {j["method"]: j for j in plan["jobs"] if j["code"] == "BB144" and
                (j["mode"] == "xz" or j["method"] == "relay5")}
    tests, altered = 0, set()
    for method, full in selected.items():
        circuit, model = run.case_model(full, "x")
        raw = circuit.compile_detector_sampler(seed=501).sample(16, separate_observables=True, bit_packed=True)
        masks = run.source_masks(circuit.detector_error_model())
        for job, n in ((full, 2), (reduced(full), 16)):
            base = original_decoder(job, "x", model)
            neutral = run.prepared(plan, {**job, "controls": run.NEUTRAL}, "x", model)
            active = run.prepared(plan, {**job, "controls": {"damping":.25,"alpha":.9,"beta":.5}}, "x", model)
            det, obs = (v[:n] for v in raw)
            for i, syndrome in enumerate(np.unpackbits(det, axis=1, bitorder="little", count=model.table.check_count)):
                same(base.decode(syndrome, shot=i), neutral.decode(syndrome, shot=i))
                tests += 1
                if not np.array_equal(active.decode(syndrome, shot=i).posterior, neutral.decode(syndrome, shot=i).posterior):
                    altered.add(method)
            events = screen.events(active, model, det, np.arange(n))
            run.chunk_summary(events, det, obs, model, *masks, method, run.spec_for(job))
        print("Qualified",method,flush=True)
    assert altered == set(selected)
    print(tests,"bitwise neutral controller comparisons and non-neutral original-DEM audits",flush=True)


def end_to_end(plan):
    job = json.loads(json.dumps(reduced(plan["jobs"][0])))
    mini = {**plan, "jobs": [job], "groups": {job["group"]: plan["groups"][job["group"]]}}
    mini["tuning"] = {**plan["tuning"], "screen_iterations": 1, "screen_limit": 512,
                      "screen_seed": 801, "policy_seed": 802,
                      "screen_block": {"xz": 16}, "shots_per_stage": {"xz": [2,2,2]},
                      "damping": [0., .25], "scaling": [.9,1.], "offset": [0.]}
    mini["protocol"] = {**plan["protocol"], "max_shots": 32, "target_errors": 1,
                        "minimum_free_bytes": 0, "evaluation_batch": {"xz": 16}}
    with tempfile.TemporaryDirectory(prefix="advanced-bp-qualification-") as tmp:
        run.ROOT = Path(tmp)
        run.write_json(run.ROOT/"plan.json", mini)
        screen.prepare(mini, job["group"], 2)
        tune.tune(mini, 0, 2)
        resolved = run.resolve_job(mini, 0)
        assert report.result(mini, 0) is None
        confirm.run_point(mini, resolved, False, 2)
        confirm.run_point(mini, resolved, True, 2)
        assert report.result(mini, 0) is not None
        report.collect(mini)
    print("PASS screening, tuning, unfiltered confirmation, full ledger audit and publication",flush=True)


if __name__ == "__main__":
    plan = run.load()
    controller_checks(plan)
    end_to_end(plan)
