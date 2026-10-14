#!/usr/bin/env python3
"""Prepare a read-only, unapplied matched-input proposal for native aSCED.

This utility deliberately never invokes a compiler, imports the native extension,
or writes below the pinned author checkout.  Its patch is review evidence only.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / "data" / "native"
DEFAULT_SPEC = NATIVE / "phase10-asced-source-spec.json"
DEFAULT_BUILD = NATIVE / "phase10-asced-build-receipt.json"
DEFAULT_RUN = NATIVE / "phase10-asced-run-receipt.json"
DEFAULT_SOURCE = Path("/tmp/phase10-asced-native/source/quantum_asced")
COMMIT = "816772071486615dfc7d71d1e15df597edc58a26"
SCHEMA = "phase11-asced-injected-input-proposal-v1"
TOUCHED_FILES = (
    "include/Simulation_Env.h",
    "src/Simulation_Env.cpp",
    "src/Pybind11_Module.cpp",
)


class QualificationError(RuntimeError):
    """Evidence is incomplete, drifted, or no longer safe to describe."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise QualificationError(f"cannot load JSON evidence {path}: {error}") from error
    if not isinstance(data, dict):
        raise QualificationError(f"JSON evidence {path} must be an object")
    return data


def _source_head(source_dir: Path) -> str:
    try:
        return subprocess.run(
            ["git", "-C", str(source_dir), "rev-parse", "HEAD"],
            text=True,
            capture_output=True,
            check=False,
        ).stdout.strip()
    except OSError:
        return ""


def _require_text(path: Path, needle: str, *, label: str) -> str:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise QualificationError(f"missing pinned source file {path}") from error
    if needle not in text:
        raise QualificationError(f"pinned source no longer contains {label}")
    return text


def _verify_inputs(
    *, spec_path: Path, build_path: Path, run_path: Path, source_dir: Path
) -> dict[str, Any]:
    spec = _load_json(spec_path)
    source = spec.get("source")
    if spec.get("schema") != "phase10-asced-source-spec-v1" or not isinstance(source, dict):
        raise QualificationError("unsupported Phase 10 source specification")
    if source.get("commit") != COMMIT or source.get("repository") != "https://github.com/kit-cel/quantum_asced.git":
        raise QualificationError("source specification no longer names the exact pinned native identity")
    expected = source.get("source_digests")
    if not isinstance(expected, dict) or not expected:
        raise QualificationError("source specification lacks exact source digests")
    observed: dict[str, str] = {}
    for relative, digest in expected.items():
        if not isinstance(relative, str) or not isinstance(digest, str):
            raise QualificationError("source specification has an invalid digest entry")
        path = source_dir / relative
        if not path.is_file():
            raise QualificationError(f"source digest mismatch for {relative}: file is absent")
        actual = _sha256_file(path)
        if actual != digest:
            raise QualificationError(f"source digest mismatch for {relative}")
        observed[relative] = actual
    if _source_head(source_dir) != COMMIT:
        raise QualificationError("pinned source checkout HEAD does not match the audited commit")

    build = _load_json(build_path)
    run = _load_json(run_path)
    spec_sha256 = _sha256_file(spec_path)
    if build.get("schema") != "phase10-asced-build-receipt-v1" or build.get("terminal") != "build_success":
        raise QualificationError("Phase 10 build receipt is not the retained successful build")
    if run.get("schema") != "phase10-asced-run-receipt-v1" or run.get("terminal") != "native_success":
        raise QualificationError("Phase 10 run receipt is not the retained aggregate observation")
    if build.get("source_spec_sha256") != spec_sha256 or run.get("source_spec_sha256") != spec_sha256:
        raise QualificationError("retained receipts are not bound to the exact source specification")
    aggregate = run.get("aggregate")
    if not isinstance(aggregate, dict) or any(key in aggregate for key in ("injected_error", "shot_identity", "paired_outcome", "random_seed")):
        raise QualificationError("aggregate receipt cannot contain matched-shot fields")
    unavailable = spec.get("discrepancies", {}).get("instrumentation", {}).get("unavailable", [])
    required_unavailable = {"shot_error_injection", "random_seed", "per_shot_identity"}
    if not isinstance(unavailable, list) or not required_unavailable.issubset(unavailable):
        raise QualificationError("source specification no longer records matched-input instrumentation as unavailable")

    simulation = _require_text(
        source_dir / "src/Simulation_Env.cpp",
        "if (channel.simulate_error(error))",
        label="internal channel sampling",
    )
    for symbol in ("channel.simulate_syndrome_extraction", "decoder.decode", "channel.check_logical_equivalence", "channel.check_physical_equivalence"):
        if symbol not in simulation:
            raise QualificationError(f"pinned downstream path no longer contains {symbol}")
    pybind = _require_text(source_dir / "src/Pybind11_Module.cpp", 'pybind11::class_<Simulation_Env>', label="Simulation_Env pybind surface")
    if "run_injected_error" in pybind or "injected_error" in pybind:
        raise QualificationError("pinned pybind surface unexpectedly exposes injected input")
    return {
        "spec": spec,
        "build": build,
        "run": run,
        "spec_sha256": spec_sha256,
        "source_digests": observed,
        "additional_source_digests": {
            relative: _sha256_file(source_dir / relative)
            for relative in TOUCHED_FILES
        },
    }


def inspect(*, spec_path: Path, build_path: Path, run_path: Path, source_dir: Path) -> dict[str, Any]:
    """Return deterministic evidence that the current binding cannot pair shots."""
    inputs = _verify_inputs(spec_path=spec_path, build_path=build_path, run_path=run_path, source_dir=source_dir)
    return {
        "schema": "phase11-asced-current-boundary-v1",
        "mode": "read_only",
        "source_commit": COMMIT,
        "source_spec_sha256": inputs["spec_sha256"],
        "source_digests": inputs["source_digests"],
        "matched_input_status": "unavailable",
        "execution_authorized": False,
        "build_authorized": False,
        "aggregate_receipt_limits": [
            "no_injected_error",
            "no_per_shot_identity",
            "no_paired_outcomes",
            "no_random_seed",
        ],
        "observed_source_symbols": {
            "internal_sampling": "Simulation_Env::simulate_trial -> channel.simulate_error",
            "unchanged_downstream": "simulate_syndrome_extraction -> decode -> logical/physical evaluation",
            "missing_pybind_entrypoint": "Simulation_Env has no injected-error binding",
        },
    }


def _patched_sources(source_dir: Path) -> dict[str, str]:
    """Return proposed source text without writing anywhere outside the proposal."""
    header = (source_dir / "include/Simulation_Env.h").read_text(encoding="utf-8")
    cpp = (source_dir / "src/Simulation_Env.cpp").read_text(encoding="utf-8")
    pybind = (source_dir / "src/Pybind11_Module.cpp").read_text(encoding="utf-8")
    header_anchor = "    void init(const std::shared_ptr<Channel_Config> channel_config, const std::shared_ptr<Decoder_Config> decoder_config);\n"
    cpp_anchor = "\n\nbool Simulation_Env::check_lower_bound_error"
    pybind_anchor = "\n        .def_readwrite(\"num_threads\", &Simulation_Env::num_threads)"
    injection_header = "\n    // Proposal-only entry point: bypasses channel sampling.\n    std::string run_injected_error(const vector& injected_error);\n"
    injection_cpp = r'''

std::string Simulation_Env::run_injected_error(const vector& injected_error)
{
    if (injected_error.size() != n)
        throw std::invalid_argument("Injected Pauli vector has wrong length");
    if (channel_set.size() != 1 || decoder_set.size() != 1)
        throw std::invalid_argument("Injected-error proposal requires exactly one initialized worker");

    vector error = injected_error;
    Channel& channel = *channel_set.front();
    Decoder& decoder = *decoder_set.front();
    channel.simulate_syndrome_extraction(decoder, error);
    decoder.decode();
    if (!decoder.syndromes_match) return "failure_I";
    if (!channel.check_logical_equivalence(error, decoder.error_estimate)) return "failure_II";
    return channel.check_physical_equivalence(error, decoder.error_estimate) ? "success_I" : "success_II";
}
'''
    injection_pybind = '\n        .def("run_injected_error", &Simulation_Env::run_injected_error, pybind11::arg("injected_error"))\n'
    if header.count(header_anchor) != 1 or cpp.count(cpp_anchor) != 1 or pybind.count(pybind_anchor) != 1:
        raise QualificationError("pinned source no longer matches the narrow proposal anchors")
    return {
        "include/Simulation_Env.h": header.replace(header_anchor, header_anchor + injection_header),
        "src/Simulation_Env.cpp": cpp.replace(cpp_anchor, injection_cpp + cpp_anchor),
        "src/Pybind11_Module.cpp": pybind.replace(pybind_anchor, injection_pybind + pybind_anchor),
    }


def _unified_patch(source_dir: Path, patched: dict[str, str]) -> str:
    chunks: list[str] = []
    for relative in TOUCHED_FILES:
        original = (source_dir / relative).read_text(encoding="utf-8")
        diff = difflib.unified_diff(
            original.splitlines(keepends=True),
            patched[relative].splitlines(keepends=True),
            fromfile=f"a/{relative}",
            tofile=f"b/{relative}",
        )
        chunks.extend(diff)
    patch = "".join(chunks)
    if not patch or "channel.simulate_error" in patch:
        raise QualificationError("proposal diff must only add the bypass route and never alter channel sampling")
    return patch


def proposal(*, spec_path: Path, build_path: Path, run_path: Path, source_dir: Path) -> tuple[dict[str, Any], str]:
    """Build a canonical review receipt and unapplied source patch in memory."""
    inputs = _verify_inputs(spec_path=spec_path, build_path=build_path, run_path=run_path, source_dir=source_dir)
    patched = _patched_sources(source_dir)
    patch = _unified_patch(source_dir, patched)
    before = inputs["additional_source_digests"]
    after = {relative: _sha256_bytes(text.encode("utf-8")) for relative, text in patched.items()}
    source = inputs["spec"]["source"]
    driver = inputs["spec"]["build_proposal"]["driver"]
    receipt: dict[str, Any] = {
        "schema": SCHEMA,
        "purpose": "Unapplied review-only source proposal; it grants no apply, build, execution, fidelity, or rights authorization.",
        "current_matched_input_status": "unavailable",
        "authorization_required": True,
        "derivative_execution_authorized": False,
        "apply_authorized": False,
        "build_authorized": False,
        "fidelity_claim": "none",
        "source": {"repository": source["repository"], "commit": COMMIT, "tree": source["tree"]},
        "source_spec_sha256": inputs["spec_sha256"],
        "build_receipt_sha256": _sha256_file(build_path),
        "run_receipt_sha256": _sha256_file(run_path),
        "aggregate_receipt_limits": ["no_injected_error", "no_per_shot_identity", "no_paired_outcomes", "no_random_seed"],
        "prior_authorization_scope": driver["scope"],
        "forbidden_changes": driver["forbidden_changes"],
        "touched_files": list(TOUCHED_FILES),
        "touched_symbols": {
            "include/Simulation_Env.h": ["Simulation_Env::run_injected_error declaration"],
            "src/Simulation_Env.cpp": ["Simulation_Env::run_injected_error"],
            "src/Pybind11_Module.cpp": ["Simulation_Env.run_injected_error binding"],
        },
        "before_source_digests": before,
        "after_source_digests": after,
        "diff_sha256": _sha256_bytes(patch.encode("utf-8")),
        "native_order": ["I", "X", "Z", "Y"],
        "canonical_order": ["I", "X", "Y", "Z"],
        "translation_round_trips": [
            {"canonical": ["I", "X", "Y", "Z"], "native": ["I", "X", "Z", "Y"], "round_trip": ["I", "X", "Y", "Z"]},
            {"canonical": ["Y", "Z", "Y", "X"], "native": ["Z", "Y", "Z", "X"], "round_trip": ["Y", "Z", "Y", "X"]},
        ],
        "injected_vector_digest": {
            "algorithm": "sha256",
            "encoding": "canonical compact JSON array of native-order Pauli labels",
            "required_before_execution": True,
            "value": None,
        },
        "unchanged_downstream_symbols": [
            "channel.simulate_syndrome_extraction",
            "decoder.decode",
            "decoder.syndromes_match",
            "channel.check_logical_equivalence",
            "channel.check_physical_equivalence",
            "Simulation_Env::get_error_rates",
        ],
        "build_isolation": {"workers": 1, "separate_derivative_source_identity_required": True, "separate_derivative_build_identity_required": True, "separate_derivative_run_identity_required": True},
        "proposed_source_identity": None,
        "proposed_build_identity": None,
        "proposed_run_identity": None,
        "splitter_randomness_limit": "The native randomized splitter selection has no public seed in the audited binding; matched samples do not make internal splitter paths reproducible.",
        "selection_discrepancy": "Native path-local syndromes_match filtering differs from the paper's original-syndrome-valid selection rule and remains unresolved.",
        "approval_questions": [
            "Do the authors or rights holder approve this exact source modification and resulting derivative identity?",
            "Does review agree that bypassing only channel sampling preserves the intended source algorithm semantics?",
            "Will the derivative receive separately approved source, build, run, and matched-shot receipt identities before any execution?",
        ],
    }
    return receipt, patch


def verify_proposal(*, proposal_path: Path, patch_path: Path) -> dict[str, Any]:
    receipt = _load_json(proposal_path)
    if receipt.get("schema") != SCHEMA:
        raise QualificationError("unsupported proposal schema")
    if receipt.get("authorization_required") is not True or receipt.get("derivative_execution_authorized") is not False:
        raise QualificationError("proposal must require authorization and prohibit derivative execution")
    if receipt.get("touched_files") != list(TOUCHED_FILES):
        raise QualificationError("proposal declares an unexpected diff scope")
    patch = patch_path.read_bytes()
    if receipt.get("diff_sha256") != _sha256_bytes(patch):
        raise QualificationError("proposal diff digest mismatch")
    changed_lines = b"\n".join(
        line
        for line in patch.splitlines()
        if line.startswith((b"+", b"-")) and not line.startswith((b"+++", b"---"))
    )
    forbidden = (b"simulate_errors(double epsilon)", b"get_error_rates", b"Minimum_Weight_Selection", b"Pauli_Channel.cpp")
    if any(item in changed_lines for item in forbidden):
        raise QualificationError("proposal patch reaches aggregate, selection, or channel implementation scope")
    return {"schema": "phase11-asced-proposal-verification-v1", "status": "review_only_valid", "execution_authorized": False}


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "proposal"):
        command = subparsers.add_parser(name)
        command.add_argument("--spec-path", type=Path, default=DEFAULT_SPEC)
        command.add_argument("--build-receipt-path", type=Path, default=DEFAULT_BUILD)
        command.add_argument("--run-receipt-path", type=Path, default=DEFAULT_RUN)
        command.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    proposal_parser = subparsers.choices["proposal"]
    proposal_parser.add_argument("--proposal-path", type=Path, required=True)
    proposal_parser.add_argument("--patch-path", type=Path, required=True)
    verify = subparsers.add_parser("verify-proposal")
    verify.add_argument("--proposal-path", type=Path, required=True)
    verify.add_argument("--patch-path", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "inspect":
            result = inspect(spec_path=args.spec_path, build_path=args.build_receipt_path, run_path=args.run_receipt_path, source_dir=args.source_dir)
            print(json.dumps(result, sort_keys=True))
        elif args.command == "proposal":
            receipt, patch = proposal(spec_path=args.spec_path, build_path=args.build_receipt_path, run_path=args.run_receipt_path, source_dir=args.source_dir)
            _write_json(args.proposal_path, receipt)
            args.patch_path.parent.mkdir(parents=True, exist_ok=True)
            args.patch_path.write_text(patch, encoding="utf-8")
            print(json.dumps({"proposal": str(args.proposal_path), "patch": str(args.patch_path), "status": "review_only"}, sort_keys=True))
        else:
            print(json.dumps(verify_proposal(proposal_path=args.proposal_path, patch_path=args.patch_path), sort_keys=True))
    except (OSError, QualificationError, ValueError) as error:
        print(f"qualification failed: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
