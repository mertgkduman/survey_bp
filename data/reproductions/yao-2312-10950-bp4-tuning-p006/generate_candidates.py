"""Create the frozen, data-only first-stage BP4 tuning registry."""

from __future__ import annotations

import json
from pathlib import Path

from bp_registry.resolution import BpFloodingPolicy, ResolutionPolicy


ROOT = Path(__file__).resolve().parent


def candidates() -> dict[str, object]:
    items: list[dict[str, object]] = []

    def profile(name: str, *, p0: float = .06, damping: float = 0.0,
                cap: float | None = None, epsilon: float = 1e-10,
                iterations: int = 100) -> None:
        items.append({"id": name, "kernel": "profile_v2", "p0": p0,
                      "damping": damping, "check_cap": cap,
                      "product_epsilon": epsilon, "max_iterations": iterations})

    def policy(name: str, *, check_rule: str = "sum_product",
               fmt: str = "float64", scale: int | None = None,
               scope: str = "all_messages", damping: float = 0.0,
               alpha: float = 1.0, beta: float = 0.0) -> None:
        resolution = ResolutionPolicy(format=fmt, scale=scale, scope=scope,
                                      coefficients="same" if scale is not None else "float64")
        bp = BpFloodingPolicy(check_rule=check_rule, resolution=resolution,
                              damping=damping, alpha=alpha, beta=beta,
                              hard_decision="strict_pauli", zero_syndrome_shortcut=False)
        items.append({"id": name, "kernel": "policy_flooding", "p0": .06,
                      "max_iterations": 100, "policy": bp.as_spec()})

    baseline = "sp_f64_v2_d0_p006_t100"
    profile(baseline)
    for d, label in ((.05, "005"), (.1, "01"), (.2, "02"), (.3, "03"), (.5, "05")):
        profile(f"sp_f64_v2_d{label}_p006_t100", damping=d)
    for p0, label in ((.03, "003"), (.045, "0045"), (.075, "0075"),
                      (.09, "009"), (.12, "012")):
        profile(f"sp_f64_v2_d01_p{label}_t100", p0=p0, damping=.1)
    for t in (30, 300, 1000):
        profile(f"sp_f64_v2_d01_p006_t{t}", damping=.1, iterations=t)
    for cap in (8., 12., 20., 25.):
        profile(f"sp_f64_v2_d01_p006_cap{int(cap)}", damping=.1, cap=cap)
    for epsilon, label in ((1e-8, "1e8"), (1e-12, "1e12")):
        profile(f"sp_f64_v2_d01_p006_eps{label}", damping=.1, epsilon=epsilon)

    for d, label in ((0., "0"), (.1, "01"), (.2, "02")):
        policy(f"sp_policy_f64_d{label}", damping=d)
    policy("sp_policy_f32_d01", fmt="float32", damping=.1)
    policy("sp_policy_f16_d01", fmt="float16", damping=.1)
    for scale in (4, 8, 16):
        for scope, short in (("all_messages", "all"), ("scalar_edges", "edge")):
            for d, label in ((0., "0"), (.2, "02")):
                policy(f"sp_q8_s{scale}_{short}_d{label}", fmt="int8", scale=scale,
                       scope=scope, damping=d)
    for scale in (4, 8, 16):
        for d, label in ((0., "0"), (.2, "02")):
            policy(f"ms_q8_s{scale}_a1_b0_d{label}", check_rule="min_sum",
                   fmt="int8", scale=scale, damping=d)
    for scale in (4, 8):
        policy(f"ms_q8_s{scale}_a08_b0_d02", check_rule="min_sum",
               fmt="int8", scale=scale, damping=.2, alpha=.8)
        policy(f"ms_q8_s{scale}_a1_b025_d02", check_rule="min_sum",
               fmt="int8", scale=scale, damping=.2, beta=.25)

    ids = [item["id"] for item in items]
    if len(ids) != len(set(ids)) or baseline not in ids:
        raise AssertionError("candidate identity collision")
    return {"schema": "yao-bp4-tuning-candidates-v1", "physical_p": .06,
            "baseline_id": baseline, "selection_status": "exploratory_screen",
            "candidates": items}


def main() -> None:
    path = ROOT / "decoders" / "screen_candidates.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f"candidate registry already exists: {path}")
    value = candidates()
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")
    print(f"wrote {len(value['candidates'])} candidate decoder policies")


if __name__ == "__main__":
    main()
