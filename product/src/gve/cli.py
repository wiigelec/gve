from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .authority import Authority
from .engine import Engine
from .plugins.execute import HARD_LIMITS
from .product_registry import product_registry


def _positive_limit(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a positive integer") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gve")
    sub = parser.add_subparsers(dest="command", required=True)

    execute = sub.add_parser("execute")
    execute.add_argument("--repository", required=True)
    execute.add_argument("--git-remote", action="append", default=[])
    execute.add_argument("--github-repository")
    execute.add_argument("--execute-max-wall-seconds", type=_positive_limit)
    execute.add_argument("--execute-max-concurrent", type=_positive_limit)
    execute.add_argument("--execute-max-total-spawned", type=_positive_limit)
    execute.add_argument("--execute-max-spawns-per-second", type=_positive_limit)
    execute.add_argument("payload")
    return parser


def _limit_tuple(args: argparse.Namespace) -> tuple[tuple[str, int], ...]:
    mapping = {
        "wall_seconds": args.execute_max_wall_seconds,
        "max_concurrent": args.execute_max_concurrent,
        "max_total_spawned": args.execute_max_total_spawned,
        "max_spawns_per_second": args.execute_max_spawns_per_second,
    }
    result = []
    for key, value in mapping.items():
        if value is None:
            continue
        ceiling = HARD_LIMITS[key]
        if value > ceiling:
            raise ValueError(f"{key} exceeds product hard ceiling {ceiling}")
        result.append((key, value))
    return tuple(result)


def execute_command(args: argparse.Namespace) -> int:
    try:
        repository = Path(args.repository).resolve()
        payload_path = Path(args.payload)
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        authority = Authority(
            repository=repository,
            git_remotes=frozenset(args.git_remote),
            github_repository=args.github_repository,
            execute_limits=_limit_tuple(args),
        )
        result = Engine(product_registry()).execute(payload, authority)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        result = {
            "schema_version": 1,
            "workflow_id": None,
            "status": "failure",
            "tasks": [],
            "error": {
                "code": "cli-failure",
                "message": str(exc),
                "details": {},
            },
        }
        print(json.dumps(result, sort_keys=True))
        return 2

    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "success" else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)
    if args.command == "execute":
        return execute_command(args)
    return 2
