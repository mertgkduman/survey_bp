"""Inspectable capabilities; constructors remain the combination admission gate."""
from typing import get_args


def capability_inventory():
    """Return a fresh, JSON-safe inventory of implemented policy counterparts.

    A family name means that its stated counterpart exists. It does not assert
    interchangeable equations, arbitrary policy compositions or paper fidelity.
    """
    from bp_registry.canonical.policy_decoder import BinaryPolicy
    shared = lambda field: list(get_args(BinaryPolicy.model_fields[field].annotation))
    return {
        "version": "policy-capabilities-v1",
        "scope": "existing_or_source_defined_counterparts_only",
        "admission": "BinaryPolicy plus BinaryPolicyDecoder graph admission; existing Pauli and GPU constructors",
        "shared_binary_and_circuit": {
            "entry_points": ["canonical.policy_decoder.BinaryPolicyDecoder", "circuit.SharedPolicySinterDecoder"],
            "updates": shared("rule"), "schedules": shared("schedule"), "controllers": shared("controller"),
            "assignment_shapes": ["scalar", "source_iteration", "check", "edge"],
            "generated_assignment_refresh": ["configuration", "attempt", "source_iteration"],
            "randomized_traversal": ["layered", "check_node_serial", "variable_node_serial"],
            "memory": ["affine_prior", "v2c_damping", "pdbp_field_mix", "pdprime_delta_mix", "posterior_momentum"],
            "damped_interventions": ["guided_decimation", "impulse_exact_shortening", "freezing", "syndrome_flip", "sign_flip", "restart_belief"],
            "ensemble_selection": ["mbbp_frequency_over_weight", "mbbp_coordinate_majority_declared_tie"],
            "compiled": ["ordinary_scalar_parameter_flooding", "explicit_bp_flooding_policy_v2_v3"],
            "message_formats": ["float16", "float32", "float64", "int8", "int16", "int32"],
            "precision_note": "message rounding with float64 arithmetic; no native low-bit speed claim",
            "qualification": "shared existing binary equations; source controller qualifications are retained; no circuit curve reproduction claim",
        },
        "pauli": {
            "entry_points": ["quaternary.kernel", "quaternary.schedules", "quaternary.compiled", "quaternary.mbp4", "quaternary.qbpgd", "quaternary.asced"],
            "existing_counterparts": ["scalar_llr_bp4", "compiled_flooding_spa_ms_nms_oms",
                "six_message_formats", "flooding", "variable_serial", "c2v_normalization", "c2v_offset",
                "fixed_alpha_mbp4", "qbpgd", "css_asced", "css_asced_overcomplete"],
            "binary_ports": "excluded unless a separately defined Pauli recurrence already exists; no new adaptations",
            "circuit_boundary": "a DEM exposes binary fault mechanisms, not joint Pauli variables or CSS splitter operands",
        },
        "gpu": {
            "entry_point": "gpu.CudaFlooding",
            "existing": ["binary_flooding", "pauli_flooding", "float64_spa_v3", "ms_nms_oms", "damping", "shot_batching"],
            "excluded": ["serial_and_residual_schedules", "branching_controllers", "general_memory_histories",
                         "generated_or_indexed_assignments", "non_float64_message_formats", "shared_sinter_transport"],
            "reason": "retain the hardware-qualified subset; no new GPU implementation or implicit host fallback",
        },
        "required_operands_and_exclusions": {
            "layered": "explicit conflict-free partition covering all original checks",
            "residual": "nonempty edge pool, undamped SPA, existing residual lifecycle",
            "group_shuffled": "at least two checks, source size-two overlap-one groups and SPA",
            "restart_belief": "explicit source exact-distance declaration or existing B1-only mechanism; no inferred circuit distance",
            "mbbp": "declared original-row transforms; member evidence retains canonical-adaptation qualification",
            "si": "existing CSS-only optional adaptation requires opposite stabilizer support; no defined DEM counterpart",
            "otf": "existing CSS optional adaptation remains available; source circuit procedure is explicitly blocked in postprocessing/otf.py",
            "cluster_learned": "artifact admission exists, but no trained scheduling executor is implemented; not advertised as runnable",
            "adaptive_mbp4": "no complete source contract in the implemented registry",
            "osd_lsd": "optional separate postprocessors/native references, not BP kernel policies",
        },
    }
