#!/usr/bin/env python3
"""Public entry point for the bounded Phase 11 GB46 controlled calibration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from bp_registry.campaigns.controlled_execution import (
    assess_phase11_controlled,
    preflight_phase11_controlled_design,
    replay_phase11_controlled,
    run_phase11_controlled,
    verify_phase11_controlled,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DESIGN = ROOT / "data/studies/phase11-gb46-joint-separate.json"
DEFAULT_AUTHORIZATION_PACKAGE = ROOT / "data/results/phase11-production-authorization.json"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    authorization = commands.add_parser(
        "verify-authorization",
        help="read and validate the default-deny Phase 11 production package without dispatching work",
    )
    authorization.add_argument("--package", type=Path, default=DEFAULT_AUTHORIZATION_PACKAGE)
    record_authorization = commands.add_parser(
        "record-authorization",
        help="seal an explicit human review decision without dispatching campaign work",
    )
    record_authorization.add_argument("--package", type=Path, default=DEFAULT_AUTHORIZATION_PACKAGE)
    record_authorization.add_argument(
        "--decision", required=True, choices=("authorize_exact_manifests", "preserve_deny"),
    )
    record_authorization.add_argument("--reviewer")
    record_authorization.add_argument("--reason")
    record_authorization.add_argument("--reviewed-package-sha256")
    record_authorization.add_argument("--confirmed-ceilings-sha256")
    record_authorization.add_argument("--account")
    record_authorization.add_argument("--partition")
    record_authorization.add_argument("--approved-manifest-sha256", action="append", default=[])
    for name in ("preflight", "run", "resume", "merge", "replay", "verify", "assess"):
        command = commands.add_parser(name)
        command.add_argument("--design", type=Path, default=DEFAULT_DESIGN)
        command.add_argument("--output-root", type=Path, default=ROOT / "data/results/phase11-gb46-controlled-calibration")
        command.add_argument("--shard", metavar="POINT:START:END", help="one declared inclusive range; inverted bounds are an empty shard")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    try:
        if args.command == "verify-authorization":
            from bp_registry.campaigns.profiling_gate import validate_phase11_dispatch_package

            package_path = args.package if args.package.is_absolute() else ROOT / args.package
            if package_path.is_symlink() or not package_path.is_file():
                raise ValueError("authorization package must be a regular file")
            package = json.loads(package_path.read_bytes())
            validate_phase11_dispatch_package(ROOT, package)
            receipt = package
        elif args.command == "record-authorization":
            from bp_registry.campaigns.profiling_gate import materialize_phase11_authorization_receipt

            package_path = args.package if args.package.is_absolute() else ROOT / args.package
            receipt = materialize_phase11_authorization_receipt(
                ROOT, package_path, decision=args.decision, reviewer=args.reviewer, reason=args.reason,
                reviewed_package_sha256=args.reviewed_package_sha256,
                confirmed_ceilings_sha256=args.confirmed_ceilings_sha256,
                account=args.account, partition=args.partition,
                approved_manifest_sha256s=tuple(args.approved_manifest_sha256),
            )
        else:
            receipt = preflight_phase11_controlled_design(root=ROOT, design_path=args.design)
            shard = None
            if args.shard is not None:
                point, start, end = args.shard.split(":", 2)
                shard = (point, int(start), int(end))
            if args.command == "run":
                receipt = run_phase11_controlled(root=ROOT, design_path=args.design, output_root=args.output_root, shard=shard)
            elif args.command == "resume":
                receipt = run_phase11_controlled(root=ROOT, design_path=args.design, output_root=args.output_root, resume=True, shard=shard)
            elif args.command == "merge":
                receipt = verify_phase11_controlled(root=ROOT, design_path=args.design, output_root=args.output_root)
            elif args.command == "replay":
                receipt = replay_phase11_controlled(root=ROOT, design_path=args.design, output_root=args.output_root)
            elif args.command == "verify":
                receipt = verify_phase11_controlled(root=ROOT, design_path=args.design, output_root=args.output_root)
            elif args.command == "assess":
                receipt = assess_phase11_controlled(root=ROOT, design_path=args.design, output_root=args.output_root)
    except (OSError, ValueError) as error:
        print(json.dumps({"schema": "phase11_controlled_cli_v1", "status": "error", "error": str(error)}, sort_keys=True))
        raise SystemExit(2) from error
    print(json.dumps({"schema": "phase11_controlled_cli_v1", "status": "ok", "phase": args.command, **receipt}, sort_keys=True))


if __name__ == "__main__":
    main()
