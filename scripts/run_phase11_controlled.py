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


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("preflight", "run", "resume", "merge", "replay", "verify", "assess"):
        command = commands.add_parser(name)
        command.add_argument("--design", type=Path, default=DEFAULT_DESIGN)
        command.add_argument("--output-root", type=Path, default=ROOT / "data/results/phase11-gb46-controlled-calibration")
        command.add_argument("--shard", metavar="POINT:START:END", help="one declared inclusive range; inverted bounds are an empty shard")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = _parser().parse_args(argv)
    try:
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
