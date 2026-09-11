#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Callable

from core_engine import validate_core_engine, validate_planning_binding
from filesystem import validate_filesystem_plugin
from git import validate_git_plugin
from execute import validate_execute
from github import validate_github
from cli import validate_cli
from registry import validate_registry
from workflow import validate_workflow
from macro_discover import validate_macro_discover
from macro_issue import validate_macro_issue
from macro_pr import validate_macro_pr

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "product" / "validation" / "requirement-evaluation.json"
TASKS: dict[str, Callable[[], bool | None]] = {
    "planning-binding": validate_planning_binding,
    "core-engine": validate_core_engine,
    "filesystem": validate_filesystem_plugin,
    "git": validate_git_plugin,
    "execute": validate_execute,
    "github": validate_github,
    "cli": validate_cli,
    "registry": validate_registry,
    "workflow": validate_workflow,
    "macro-discover": validate_macro_discover,
    "macro-issue": validate_macro_issue,
    "macro-pr": validate_macro_pr,
}


def fail(message: str) -> int:
    print(f"FAIL product-validation: {message}", file=sys.stderr)
    return 1


def load_manifest() -> dict:
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load product Requirement Evaluation Manifest: {exc}") from exc
    if data.get("version") != 1 or not isinstance(data.get("bindings"), list):
        raise ValueError("invalid product Requirement Evaluation Manifest structure")
    return data


def manifest_tasks() -> list[str]:
    data = load_manifest()
    ordered: list[str] = []
    for binding in data["bindings"]:
        if not isinstance(binding, dict):
            raise ValueError("product manifest binding must be an object")
        tasks = binding.get("tasks")
        if not isinstance(tasks, list) or not tasks:
            raise ValueError("product manifest binding requires a non-empty tasks list")
        for task in tasks:
            if not isinstance(task, str) or not task:
                raise ValueError("product validation task identity must be a non-empty string")
            if task not in TASKS:
                raise ValueError(f"product manifest references unknown task: {task}")
            if task not in ordered:
                ordered.append(task)
    return ordered


def execute(task: str) -> int:
    fn = TASKS.get(task)
    if fn is None:
        return fail(f"unknown product Validation task: {task}")
    try:
        result = fn()
    except Exception as exc:
        return fail(f"{task}: {exc}")
    if result is False:
        return fail(f"{task}: returned failure")
    print(f"PASS {task}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list-tasks", action="store_true")
    parser.add_argument("--task")
    args = parser.parse_args(argv)

    if args.list_tasks and args.task:
        return fail("--list-tasks and --task are mutually exclusive")
    if args.list_tasks:
        for task in sorted(TASKS):
            print(task)
        return 0
    if args.task:
        return execute(args.task)

    try:
        tasks = manifest_tasks()
    except ValueError as exc:
        return fail(str(exc))
    for task in tasks:
        result = execute(task)
        if result:
            return result
    print("Product Validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
