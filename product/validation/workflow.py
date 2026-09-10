from __future__ import annotations

import json
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "product" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gve.authority import Authority
from gve.engine import Engine
from gve.product_registry import product_registry


def _run(args: list[str], cwd: Path) -> str:
    cp = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if cp.returncode != 0:
        raise AssertionError(
            f"command failed {args!r}: exit={cp.returncode} stderr={cp.stderr!r}"
        )
    return cp.stdout.rstrip("\r\n")


def _write_validation_script(path: Path) -> None:
    path.write_text(
        "#!/bin/sh\n"
        "set -eu\n"
        "test -f generated.txt\n"
        "printf 'validation-pass'\n",
        encoding="utf-8",
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def validate_workflow() -> bool:
    expected_tasks = {
        "filesystem.list",
        "filesystem.file-read",
        "filesystem.file-stat",
        "filesystem.file-hash",
        "filesystem.file-create",
        "filesystem.file-modify",
        "filesystem.file-delete",
        "git.repository",
        "git.branch",
        "git.head",
        "git.status",
        "git.diff",
        "git.diff-check",
        "git.branch-create",
        "git.branch-switch",
        "git.add",
        "git.commit",
        "git.fetch",
        "git.remote-head",
        "git.push",
        "execute.script",
        "github.issue-read",
        "github.issue-create",
        "github.issue-modify",
        "github.pull-request-read",
        "github.pull-request-create",
        "github.pull-request-modify",
    }
    observed_tasks = set(product_registry().identities())
    if observed_tasks != expected_tasks:
        raise AssertionError(
            f"complete task vocabulary mismatch missing={sorted(expected_tasks-observed_tasks)} "
            f"extra={sorted(observed_tasks-expected_tasks)}"
        )

    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        repo = base / "repo"
        remote = base / "remote.git"
        repo.mkdir()

        _run(["git", "init", "-b", "main"], repo)
        _run(["git", "config", "user.email", "validator@example.invalid"], repo)
        _run(["git", "config", "user.name", "GVE Workflow Validator"], repo)

        scripts = repo / "scripts"
        scripts.mkdir()
        _write_validation_script(scripts / "validate")
        (repo / "README.md").write_text("reference workflow\n", encoding="utf-8")

        _run(["git", "add", "README.md", "scripts/validate"], repo)
        _run(["git", "commit", "-m", "baseline"], repo)
        baseline = _run(["git", "rev-parse", "HEAD"], repo)

        _run(["git", "init", "--bare", str(remote)], base)
        _run(["git", "remote", "add", "origin", str(remote)], repo)

        authority = Authority(
            repository=repo.resolve(),
            git_remotes=frozenset({"origin"}),
            execute_limits=(
                ("wall_seconds", 10),
                ("max_concurrent", 8),
                ("max_total_spawned", 32),
                ("max_spawns_per_second", 16),
            ),
        )

        payload = {
            "schema_version": 1,
            "workflow_id": "repository-change-publication",
            "tasks": [
                {
                    "id": "repository",
                    "task": "git.repository",
                    "parameters": {
                        "expected_root": str(repo.resolve()),
                        "expected_remotes": {"origin": str(remote)},
                    },
                },
                {
                    "id": "branch",
                    "task": "git.branch",
                    "parameters": {"expected": "main"},
                },
                {
                    "id": "head",
                    "task": "git.head",
                    "parameters": {"expected": baseline},
                },
                {
                    "id": "status",
                    "task": "git.status",
                    "parameters": {"expected_clean": True},
                },
                {
                    "id": "remote_before",
                    "task": "git.remote-head",
                    "parameters": {
                        "remote": "origin",
                        "branch": "main",
                        "expected": None,
                    },
                },
                {
                    "id": "create",
                    "task": "filesystem.file-create",
                    "parameters": {
                        "path": "generated.txt",
                        "content": "generated\n",
                    },
                },
                {
                    "id": "validate",
                    "task": "execute.script",
                    "parameters": {
                        "script": "scripts/validate",
                        "args": [],
                        "working_directory": ".",
                        "limits": {
                            "wall_seconds": 5,
                            "max_concurrent": 4,
                            "max_total_spawned": 16,
                            "max_spawns_per_second": 8,
                        },
                    },
                },
                {
                    "id": "diff_check",
                    "task": "git.diff-check",
                    "parameters": {},
                },
                {
                    "id": "add",
                    "task": "git.add",
                    "parameters": {"paths": ["generated.txt"]},
                },
                {
                    "id": "commit",
                    "task": "git.commit",
                    "parameters": {"message": "generated change"},
                },
                {
                    "id": "push",
                    "task": "git.push",
                    "parameters": {
                        "remote": "origin",
                        "local_branch": "main",
                        "remote_branch": "main",
                        "expected_remote_head": None,
                    },
                },
                {
                    "id": "verify",
                    "task": "git.remote-head",
                    "parameters": {
                        "remote": "origin",
                        "branch": "main",
                        "expected": {"$ref": "commit.result.commit"},
                    },
                },
            ],
        }

        result = Engine(product_registry()).execute(payload, authority)
        if result["status"] != "success":
            raise AssertionError(json.dumps(result, indent=2, sort_keys=True))

        ids = [item["id"] for item in result["tasks"]]
        expected_ids = [item["id"] for item in payload["tasks"]]
        if ids != expected_ids:
            raise AssertionError(f"workflow order mismatch: {ids!r}")

        records = {item["id"]: item for item in result["tasks"]}
        commit = records["commit"]["result"]["commit"]
        if records["verify"]["result"]["commit"] != commit:
            raise AssertionError("remote verification did not resolve to committed result")
        if records["validate"]["result"]["stdout"] != "validation-pass":
            raise AssertionError("repository-owned validation script did not execute")
        if records["push"]["effects"].get("push_attempted") is not True:
            raise AssertionError("normal push attempt was not represented as GVE effect")

        remote_head = _run(
            ["git", "--git-dir", str(remote), "rev-parse", "refs/heads/main"],
            base,
        )
        if remote_head != commit:
            raise AssertionError(
                f"published remote mismatch expected={commit} observed={remote_head}"
            )

    return True
