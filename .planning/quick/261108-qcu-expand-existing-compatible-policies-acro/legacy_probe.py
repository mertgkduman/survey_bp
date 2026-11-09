"""Same uniform-channel receipts on the frozen baseline and expanded tree."""
from dataclasses import asdict, is_dataclass
import json
from pathlib import Path
import sys
import numpy as np
import stim

from bp_registry.canonical.budgets import BudgetTree
from bp_registry.canonical.problems import OriginalProblem
from bp_registry.canonical.schedules import EdgeTable
from bp_registry.canonical.intervention_session import BpSession
from bp_registry.canonical.guided_decimation import GuidedDecimationController
from bp_registry.canonical.impulse import ImpulseController
from bp_registry.canonical.interventions import FreezingController, SyndromeFlipController, SignFlipController
from bp_registry.canonical.restarting import RestartController
from bp_registry.canonical.mbbp import MbbpController, MbbpSpec, MbbpBasis
from bp_registry.canonical.fair_legs import FairLegController, FairLegConfig
from bp_registry.circuit import CircuitPolicy, PolicyBpSinterDecoder


def encode(value):
    if hasattr(value, "as_evidence"):
        return encode(value.as_evidence())
    if is_dataclass(value):
        return encode(asdict(value))
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, dict):
        return {k: encode(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [encode(v) for v in value]
    return value


records = []
for h, s in [([[1, 1], [1, 1]], [0, 1]), ([[1, 1], [0, 1]], [1, 0]),
             ([[1, 1, 0], [0, 1, 1]], [1, 1])]:
    h, s = np.array(h, dtype=np.uint8), np.array(s, dtype=np.uint8)
    original = OriginalProblem("original-legacy-parity", np.zeros((1, h.shape[1]), dtype=np.uint8), h, s)
    for p in [.1, .3]:
        def run(control):
            return control.run(original, error_rate=p, budgets=BudgetTree(limits=(), parents={}))
        for mode in ["exact_shortening", "semantic_forced_zero", "semantic_forced_one"]:
            records.append(encode(run(ImpulseController(dict(realization=mode, selection="minimum_original_weight",
                baseline_sweeps=1, attempt_sweeps=1, attempt_cap=2)))))
        records.append(encode(run(FreezingController(dict(period_sweeps=1, lifetime_sweeps=1, retry_cap=2, root_seed="freeze")))))
        records.append(encode(run(SyndromeFlipController(dict(baseline_sweeps=2, attempt_sweeps=1, top_k=2,
            max_weight=1, test_cap=2, root_seed="sf")))))
        records.append(encode(run(SignFlipController(dict(alpha=.875, trunk_sweeps=1, continuation_sweeps=1)))))
        records.append(encode(run(RestartController(dict(preset="source_exact_distance", code_id="declared-test-code",
            eta=1, t_cap=1, root_sweeps=1, residual_sweeps=1, exact_distance=3)))))
        gd = GuidedDecimationController(dict(kind="guided_decimation", variant="algorithm1_v2_interpretation",
            source_revision="arxiv:2312.10950v2", finite_bias_magnitude=25.,
            zero_rule="positive_prior_for_zero_posterior", final_round_rule="return_after_last_fixation",
            round_limit=2, sweeps_per_round=1))
        records.append(encode(gd.run(BpSession(EdgeTable.from_check_matrix(h), s, error_rate=p),
            check_matrix=h, budgets=BudgetTree(limits=(), parents={}))))
        mbbp = MbbpController(MbbpSpec((MbbpBasis("base", 0, "explicit", "identity", ((1, 1),)),), 2))
        records.append(encode(mbbp.run(original, error_rate=p)))
        fair = FairLegController(h, s, error_rate=p, config=FairLegConfig(initial_iterations=1,
            extra_iterations_per_unit=1, max_extra_units=2))
        records.extend(encode(fair.run_pair(sample_seed_identity="legacy-parity")))

dem = stim.DetectorErrorModel("error(0.1) D0 D1 L0\nerror(0.7) D0 D1\nerror(1) L1")
for rule in ["spa", "min_sum", "normalized_min_sum", "offset_min_sum"]:
    for controller in ["single", "relay", "guided", "beam"]:
        decoder = PolicyBpSinterDecoder(CircuitPolicy(rule=rule, controller=controller,
            max_attempts=1 if controller == "single" else 2, max_iterations=2)).compile_decoder_for_dem(dem=dem)
        result = decoder.decode_detailed(np.array([[0, 0], [1, 1], [0, 1], [1, 0]], dtype=np.uint8))
        records.append(result.ledger)

Path(sys.argv[1]).write_text(json.dumps(records, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")
print(f"{len(records)} complete legacy receipts")
