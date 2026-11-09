"""Reproducible qualification of F01/F02; preserves all earlier evidence."""
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys

import stim

from bp_registry.batch_records import read_records
from bp_registry.canonical.policy_decoder import BinaryPolicy
from bp_registry.circuit import SharedPolicySinterDecoder
from bp_registry.policy_capabilities import capability_inventory

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRIOR = ROOT / ".planning/quick/261108-qcu-expand-existing-compatible-policies-acro"
AUDIT = ROOT / ".planning/spikes/053-shared-evidence"
CHANGED = {
    "src/bp_registry/canonical/compatibility.py",
    "src/bp_registry/canonical/memory_execution.py",
    "src/bp_registry/circuit/shared_policies.py",
    "src/bp_registry/policy_capabilities.py",
}


def digest(path):
    value = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def save(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def replay_shared_history():
    smoke = PRIOR / "sinter-smoke"
    dem = stim.Circuit((smoke / "circuit.stim").read_text()).detector_error_model(decompose_errors=True)
    cases = [(path, dem) for path in sorted(smoke.glob("*/*.jsonl"))]
    fixture = json.loads((AUDIT / "chunking-counterexample.json").read_text())
    cases += [(path, stim.DetectorErrorModel(fixture["dem"])) for path in sorted(AUDIT.glob("chunking-*.jsonl"))]
    cases.append((AUDIT / "affine-ledger.jsonl", stim.DetectorErrorModel(
        "error(1) D0 L8\nerror(0) D8\nerror(0.2) D0 ^ D8 L9\nerror(0.8) L0")))
    records = []
    for path, model in cases:
        before = digest(path)
        header = json.loads(path.read_text().splitlines()[0])
        assert header["schema"] == "circuit-shared-policy-ledger-v1"
        decoder = SharedPolicySinterDecoder(BinaryPolicy.model_validate_json(json.dumps(header["policy"]))).compile_decoder_for_dem(dem=model)
        result = decoder.verify_ledger(path)
        assert before == digest(path)
        records.append(dict(path=str(path.relative_to(ROOT)), sha256=before, **result))
    save("shared-v1-replay.json", records)
    return dict(ledgers=len(records), shots=sum(r["shots"] for r in records), exact_replay=True)


def carry_unchanged_evidence():
    source = json.loads((ROOT / ".planning/spikes/050-shared-mathematics/results.json").read_text())["source_hashes"]
    actual_changes = {name for name, old in source.items() if digest(ROOT / name) != old}
    assert actual_changes == CHANGED, actual_changes
    prior = json.loads((PRIOR / "qualification.json").read_text())
    for name, expected in prior["evidence_sha256"].items():
        assert digest(PRIOR / name) == expected, name
    carried = json.loads((AUDIT / "carried-qualification.json").read_text())
    hardware = ROOT / ".planning/quick/261108-meg-implement-compatible-circuit-policies-an/gpu-final"
    for name, expected in json.loads((hardware / "source-sha256.json").read_text()).items():
        assert digest(ROOT / name) == expected, name
    for ledger in carried["gpu_ledgers"]:
        path = ROOT / ledger["path"]
        assert digest(path) == ledger["sha256"], path
        assert len(read_records(path, "gpu-flooding-ledger-v1")) - 1 == ledger["shots"]
    result = dict(unchanged_source_files=len(source) - len(CHANGED), changed_source_files=sorted(CHANGED),
        prior_evidence_files=len(prior["evidence_sha256"]),
        independent_mathematics_cases_carried=2880, aligned_upstream_cases_carried=1188,
        gpu_hardware_shots_carried=sum(r["shots"] for r in carried["gpu_ledgers"]),
        new_gpu_execution=False, pauli_and_gpu_source_unchanged=True,
        interpretation="Existing mathematical/native/hardware evidence carried after source and evidence hash checks; not fresh hardware execution")
    save("carried-evidence.json", result)
    return result


def result_impact():
    roots = ["data", "manifests", "experiments", "from_dr_pfister_presentetations"]
    names = subprocess.check_output(["git", "ls-files", "-z", "--", *roots], cwd=ROOT).decode().split("\0")
    # Reject a claim of preservation if any tracked result differs from the task baseline.
    subprocess.run(["git", "diff", "--exit-code", "82311bd", "--", *roots], cwd=ROOT, check=True,
                   stdout=subprocess.DEVNULL)
    needles = [b"circuit-shared-policy-ledger", b"SharedPolicySinterDecoder", b"pdprime_delta_mix"]
    matches = {n.decode(): [] for n in needles}
    hashes = {}
    for name in filter(None, names):
        path = ROOT / name
        if not path.is_file():
            continue
        value = sha256()
        found, tail = set(), b""
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                value.update(chunk)
                window = tail + chunk
                found.update(n for n in needles if n in window)
                tail = window[-128:]
        hashes[name] = value.hexdigest()
        for needle in found:
            matches[needle.decode()].append(name)
    save("tracked-result-hashes.json", hashes)
    prior = json.loads((AUDIT / "result-impact.json").read_text())
    assert not matches[needles[0].decode()] and not matches[needles[1].decode()]
    assert set(matches[needles[2].decode()]) == set(prior["pdprime_files"])
    for name, expected in prior["matched_file_sha256"].items():
        assert hashes[name] == expected
    result = dict(scope="git-tracked files in declared roots", roots=roots, tracked_files=len(hashes),
        matches=matches, unchanged_since_baseline="82311bd", affected_campaigns_found=0,
        selective_rerun="none identified in tracked campaigns; old audit counterexamples remain historical evidence",
        identity_migration="New randomized shared Sinter results use observation-v2; do not append to a v1 experiment identity",
        limitation="Untracked/private campaigns are not exhaustively scanned or scientifically revalidated; publication gates are unchanged")
    save("result-impact.json", result)
    return result


def main():
    subprocess.run([sys.executable, str(PRIOR / "legacy_probe.py"), str(HERE / "legacy-current.json")], check=True, cwd=ROOT)
    assert (HERE / "legacy-current.json").read_bytes() == (PRIOR / "legacy-baseline.json").read_bytes()
    legacy = dict(receipts=len(json.loads((HERE / "legacy-current.json").read_text())), byte_identical=True,
                  baseline="872f7e1", sha256=digest(HERE / "legacy-current.json"))
    save("legacy-parity.json", legacy)
    shared = replay_shared_history()
    carried = carry_unchanged_evidence()
    impact = result_impact()
    save("capabilities.json", capability_inventory())
    tests = {}
    for name in ["f01-admission-final.log", "kernel-regression.log", "f02-final.log"]:
        log = (HERE / name).read_text()
        passed = re.search(r"(\d+) passed", log)
        assert passed and " failed" not in log, name
        skipped = re.search(r"(\d+) skipped", log)
        tests[name] = dict(passed=int(passed[1]), skipped=int(skipped[1]) if skipped else 0)
    smoke = json.loads((HERE / "sinter-smoke/verification.json").read_text())
    source = {str(p.relative_to(ROOT)): digest(p) for p in sorted((ROOT / "src/bp_registry").rglob("*.py"))}
    evidence = {str(p.relative_to(HERE)): digest(p) for p in sorted(HERE.rglob("*"))
                if p.is_file() and p.name not in {"qualification.json", "qualification.log", "PLAN.md", "SUMMARY.md", "VERIFICATION.md"}}
    save("qualification.json", dict(schema="shared-policy-fixes-qualification-v1", status="passed",
        baseline="82311bd", fix_commits=["fd5c3d0", "78f1c1c"],
        implementation_commit=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
        findings_closed=["F01", "F02"], tests=tests, tests_overlap=True, legacy=legacy,
        shared_v1_history=shared, sinter_v2=smoke, carried_evidence=carried, result_impact=impact,
        source_sha256=source, evidence_sha256=evidence))
    print(json.dumps(dict(legacy=legacy, shared_v1=shared, tests=tests, affected_campaigns=0)))


if __name__ == "__main__":
    main()
