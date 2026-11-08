from pathlib import Path
from itertools import product
from hashlib import sha256
import importlib.metadata
import json
import sys
import numpy as np
import ldpc
import stim
import sinter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from audit_support import Audit
from bp_registry.circuit import CircuitPolicy, PolicyBpSinterDecoder, DemBinaryModel

HERE = Path(__file__).resolve().parent
H = np.array([[1, 1, 1, 0, 0], [0, 0, 1, 1, 1]], np.uint8)


def aligned_native():
    rng = np.random.default_rng(4401)
    rows, worst = [], 0.
    for sample in range(12):
        rates = rng.uniform(.03, .45, 5)
        dem = stim.DetectorErrorModel("\n".join(f"error({p}) " +
            " ".join(f"D{c}" for c in np.flatnonzero(H[:, v])) + f" L{v}" for v, p in enumerate(rates)))
        settings = [("spa", 1., 1)] + [(rule, alpha, cap)
            for rule, alpha in (("min_sum", 1.), ("normalized_min_sum", .8), ("normalized_min_sum", .55))
            for cap in (1, 3, 6)]
        for (rule, alpha, cap), bits in product(settings, ((0, 1), (1, 0), (1, 1))):
            s = np.array(bits, np.uint8)
            native = ldpc.BpDecoder(H, error_channel=rates, max_iter=cap,
                bp_method="product_sum" if rule == "spa" else "minimum_sum",
                ms_scaling_factor=alpha, schedule="parallel", input_vector_type="syndrome")
            expected = native.decode(s)
            decoder = PolicyBpSinterDecoder(CircuitPolicy(rule=rule, parameter=alpha,
                max_iterations=cap)).compile_decoder_for_dem(dem=dem)
            actual = decoder.decode_detailed(s[None])
            posterior = np.asarray(actual.ledger[1]["attempts"][0]["posterior"])
            error = float(abs(posterior - native.log_prob_ratios).max())
            worst = max(worst, error)
            np.testing.assert_array_equal(actual.faults[0], expected)
            np.testing.assert_allclose(posterior, native.log_prob_ratios, atol=2e-12, rtol=2e-12)
            assert (actual.iterations[0], actual.converged[0]) == (native.iter, native.converge)
            rows.append(dict(sample=sample, rates=rates.tolist(), syndrome=s.tolist(), rule=rule,
                alpha=alpha, cap=cap, candidate=expected.tolist(), iterations=int(native.iter),
                converged=bool(native.converge), max_posterior_error=error))
    (HERE / "native-cases.json").write_text(json.dumps(rows, indent=2) + "\n")
    binary = next(Path(ldpc.__file__).parent.glob("bp_decoder/_bp_decoder*.so"))
    return dict(cases=len(rows), max_error=worst, tolerance=2e-12,
                native_version=importlib.metadata.version("ldpc"),
                native_binary=str(binary), native_sha256=sha256(binary.read_bytes()).hexdigest(),
                native_build_commit="not established; no v2.4.1 tag at queried source URL")


def affine_and_packed():
    # Include >8 detector/observable bits to exercise byte boundaries and padding.
    dem = stim.DetectorErrorModel(
        "error(1) D0 L8\nerror(0) D8\nerror(0.2) D0 ^ D8 L9\nerror(0.8) L0")
    model = DemBinaryModel.from_dem(dem)
    decoder = PolicyBpSinterDecoder().compile_decoder_for_dem(dem=dem)
    cases = []
    for a, b in product((0, 1), repeat=2):
        faults = np.array([a, b], np.uint8)
        detector = np.zeros(9, np.uint8)
        detector[0], detector[8] = 1 ^ a, a
        observable = np.zeros(10, np.uint8)
        observable[8], observable[9], observable[0] = 1, a, b
        projected = model.syndrome_bias.copy()
        for c, v in model.table.edges:
            projected[c] ^= faults[v]
        np.testing.assert_array_equal(projected, detector)
        np.testing.assert_array_equal((model.observable_matrix @ faults) % 2 ^ model.observable_bias, observable)
        actual = decoder.decode_shots_bit_packed(
            bit_packed_detection_event_data=np.packbits(detector[None], axis=1, bitorder="little"))
        expected = observable.copy()
        expected[0] = 1  # MAP of the unobserved p=.8 mechanism, not sampled truth b.
        np.testing.assert_array_equal(np.unpackbits(actual, axis=1, bitorder="little", count=10)[0], expected)
        assert actual.shape == (1, 2) and int(actual[0, 1]) < 4
        cases.append(dict(faults=faults.tolist(), observed=detector.tolist(), predicted=expected.tolist()))
    return dict(cases=cases, stim_version=stim.__version__, sinter_version=sinter.__version__,
                semantics="unobserved logical effect is inferred from its prior, never supplied as truth")


if __name__ == "__main__":
    a = Audit(HERE)
    a.probe("new_circuit_native_BP_alignment", aligned_native)
    a.probe("Stim_affine_and_multibyte_Sinter_contract", affine_and_packed)
    a.finish()
