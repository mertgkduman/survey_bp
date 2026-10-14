#!/usr/bin/env python3
"""Consume Phase 11 controlled authorization through terminal receipts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from bp_registry.campaigns.controlled_evaluation import (
    execute_authorized_controlled_manifest,
    preflight_controlled_manifest,
    verify_controlled_evaluation_receipt,
    write_controlled_evaluation_verification,
)


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "data/results/phase11-production-authorization.json"
DESIGNS = {
    "gb46": ROOT / "data/studies/phase11-gb46-joint-separate.json",
    "bb72": ROOT / "data/studies/phase11-bb72-joint-separate.json",
}
RESULTS = ROOT / "data/results/phase11-controlled-evaluation"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, default=PACKAGE)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("preflight", "execute-or-close", "resume", "verify"):
        command = commands.add_parser(name)
        command.add_argument("--code", choices=tuple(DESIGNS), required=True)
        command.add_argument("--design", type=Path)
        command.add_argument("--receipt", type=Path)
    verify_all = commands.add_parser("verify-all")
    verify_all.add_argument("--verification", type=Path, default=RESULTS / "verification.json")
    return parser


def _design(args: argparse.Namespace) -> Path:
    return args.design if args.design is not None else DESIGNS[args.code]


def _receipt(args: argparse.Namespace) -> Path:
    return args.receipt if args.receipt is not None else RESULTS / args.code / "evaluation-receipt.json"


def main(argv: list[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    package = args.package if args.package.is_absolute() else ROOT / args.package
    try:
        if args.command == "preflight":
            receipt = preflight_controlled_manifest(root=ROOT, package_path=package, design_path=_design(args))
        elif args.command in {"execute-or-close", "resume"}:
            receipt = execute_authorized_controlled_manifest(
                root=ROOT, package_path=package, design_path=_design(args), receipt_path=_receipt(args),
            )
        elif args.command == "verify":
            receipt = verify_controlled_evaluation_receipt(
                root=ROOT, package_path=package, design_path=_design(args), receipt_path=_receipt(args),
            )
        else:
            receipt = write_controlled_evaluation_verification(
                root=ROOT, package_path=package,
                receipt_paths={
                    "GB46": RESULTS / "gb46" / "evaluation-receipt.json",
                    "BB72": RESULTS / "bb72" / "evaluation-receipt.json",
                },
                verification_path=args.verification,
            )
    except (OSError, ValueError) as error:
        print(json.dumps({"schema": "phase11_controlled_evaluation_cli_v1", "status": "error", "error": str(error)}, sort_keys=True))
        raise SystemExit(2) from error
    print(json.dumps({"schema": "phase11_controlled_evaluation_cli_v1", "status": "ok", "command": args.command, **receipt}, sort_keys=True))


if __name__ == "__main__":
    main()
