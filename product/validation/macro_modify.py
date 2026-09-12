from __future__ import annotations

import json
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
from gve.errors import PayloadError
from gve.macro_request import parse_macro_request
from gve.macro_runner import MacroRunner, RepositoryContext
from gve.product_macro_registry import product_macro_registry
from gve.product_registry import product_registry


def _sh(args, cwd):
    cp = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if cp.returncode:
        raise AssertionError(f"command failed {args!r}: {cp.stderr}")
    return cp.stdout.rstrip("\r\n")


def _request(parameters):
    return parse_macro_request(
        {
            "schema_version": 1,
            "header": {"repository": {}},
            "macro": {"name": "modify", "parameters": parameters},
        }
    )


def validate_macro_modify() -> bool:
    macros = product_macro_registry()
    if "modify" not in macros.identities():
        raise AssertionError("modify is not registered")
    definition = macros.resolve("modify")
    assert definition.stages == (
        "PRECHECK", "BRANCH", "MUTATE", "VALIDATE", "COMMIT", "PUBLISH", "VERIFY"
    )

    digest = "a" * 64
    plan = definition.build(
        {
            "changes": [
                {"operation": "create", "path": "new.txt", "content": "new\n"},
                {
                    "operation": "modify",
                    "path": "old.txt",
                    "content": "updated\n",
                    "expected_sha256": digest,
                },
            ],
            "commit_message": "change files",
            "expected_head": "1" * 40,
            "allowed_dirty_paths": ["notes.txt"],
        }
    )
    tasks = [dict(task) for stage in plan.stages for task in stage.tasks]
    assert [stage.label for stage in plan.stages] == list(definition.stages)
    ids = [task["id"] for task in tasks]
    assert len(ids) == len(set(ids))
    names = [task["task"] for task in tasks]
    assert names[:6] == [
        "git.repository", "git.branch", "git.head", "git.status",
        "git.staged-scope", "git.remote-head",
    ]
    assert "filesystem.file-create" in names
    assert "filesystem.file-modify" in names
    assert names.count("execute.script") == 1
    assert names.count("git.commit") == 1
    assert names.count("git.push") == 1
    assert names[-1] == "git.remote-head"

    by_id = {task["id"]: task for task in tasks}
    assert by_id["modify-remote-before"]["parameters"]["branch"] == {
        "$ref": "modify-branch.result.branch"
    }
    assert by_id["modify-head"]["parameters"]["expected"] == "1" * 40
    assert by_id["modify-validate"]["parameters"]["script"] == "scripts/validate"
    assert by_id["modify-staged-before"]["parameters"]["allowed_paths"] == ["new.txt", "old.txt"]
    assert by_id["modify-pending-diff-check"]["task"] == "git.pending-diff-check"
    assert by_id["modify-pending-diff-check"]["parameters"]["paths"] == ["new.txt", "old.txt"]
    assert ids.index("modify-pending-diff-check") < ids.index("modify-add")
    assert by_id["modify-add"]["parameters"]["paths"] == ["new.txt", "old.txt"]
    assert by_id["modify-staged-scope"]["parameters"]["allowed_paths"] == [
        "new.txt", "old.txt"
    ]
    assert by_id["modify-push"]["parameters"]["remote"] == "origin"
    assert by_id["modify-push"]["parameters"]["expected_remote_head"] == {
        "$ref": "modify-remote-before.result.commit"
    }
    assert by_id["modify-verify"]["parameters"]["expected"] == {
        "$ref": "modify-commit.result.commit"
    }

    no_validate = definition.build(
        {
            "changes": [{"operation": "create", "path": "x.txt", "content": "x"}],
            "commit_message": "x",
            "expected_head": "2" * 40,
            "validate": False,
            "allow_dirty": True,
            "allowed_dirty_paths": ["preexisting.txt"],
            "remote_branch": "release",
        }
    )
    assert no_validate.stages[3].tasks == ()
    assert no_validate.stages[0].tasks[3]["task"] == "git.status-scope"
    assert no_validate.stages[0].tasks[-1]["parameters"]["branch"] == "release"

    with_branch = definition.build(
        {
            "changes": [{"operation": "create", "path": "b.txt", "content": "b"}],
            "commit_message": "b",
            "expected_head": "3" * 40,
            "branch": {"create": True, "name": "dev/fs003"},
            "validate": False,
        }
    )
    branch_tasks = [dict(x) for x in with_branch.stages[1].tasks]
    assert [x["task"] for x in branch_tasks] == [
        "git.branch-create", "git.branch-switch", "git.branch", "git.head"
    ]
    assert branch_tasks[0]["parameters"] == {"name": "dev/fs003", "start": "3" * 40}
    all_branch_tasks = [dict(task) for stage in with_branch.stages for task in stage.tasks]
    branch_by_id = {task["id"]: task for task in all_branch_tasks}
    assert branch_by_id["modify-push"]["parameters"]["local_branch"] == "dev/fs003"
    assert branch_by_id["modify-push"]["parameters"]["remote_branch"] == "dev/fs003"

    invalid = [
        {},
        {"changes": [], "commit_message": "x"},
        {"changes": [{"operation": "create", "path": "x", "content": "x", "expected_sha256": digest}], "commit_message": "x"},
        {"changes": [{"operation": "modify", "path": "x", "content": "x"}], "commit_message": "x"},
        {"changes": [{"operation": "modify", "path": "x", "content": "x", "expected_sha256": "bad"}], "commit_message": "x"},
        {"changes": [{"operation": "create", "path": "../x", "content": "x"}], "commit_message": "x"},
        {"changes": [{"operation": "create", "path": "x", "content": "x"}, {"operation": "create", "path": "./x", "content": "y"}], "commit_message": "x"},
        {"changes": [{"operation": "create", "path": "x", "content": "x"}], "commit_message": ""},
        {"changes": [{"operation": "create", "path": "x", "content": "x"}], "commit_message": "x", "validate": 1},
        {"changes": [{"operation": "create", "path": "x", "content": "x"}], "commit_message": "x", "extra": True},
    ]
    for params in invalid:
        try:
            definition.build(params)
        except PayloadError:
            pass
        else:
            raise AssertionError(f"invalid modify parameters accepted: {params!r}")

    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        repo = base / "repo"
        remote = base / "remote.git"
        repo.mkdir()
        _sh(["git", "init", "-b", "main"], repo)
        _sh(["git", "config", "user.name", "GVE Validator"], repo)
        _sh(["git", "config", "user.email", "validator@example.invalid"], repo)
        (repo / "base.txt").write_text("base\n", encoding="utf-8")
        _sh(["git", "add", "base.txt"], repo)
        _sh(["git", "commit", "-m", "baseline"], repo)
        baseline = _sh(["git", "rev-parse", "HEAD"], repo)
        _sh(["git", "init", "--bare", str(remote)], base)
        _sh(["git", "remote", "add", "origin", str(remote)], repo)
        (repo / "notes.txt").write_text("preexisting\n", encoding="utf-8")
        _sh(["git", "add", "notes.txt"], repo)
        authority = Authority(repository=repo.resolve(), git_remotes=frozenset({"origin"}), execute_limits=(("wall_seconds",600),("max_concurrent",32),("max_total_spawned",1024),("max_spawns_per_second",64)))
        result = MacroRunner(Engine(product_registry()), macros).execute(
            _request({"changes":[{"operation":"create","path":"generated.txt","content":"generated\n"}],"commit_message":"generated","expected_head":baseline,"validate":False,"allow_dirty":True,"allowed_dirty_paths":["notes.txt"]}),
            authority,
            RepositoryContext(repo.resolve(), None, "main", baseline),
        )
        assert result["status"] == "failure"
        failed = next(x for x in result["tasks"] if x["status"] == "failure")
        assert failed["id"] == "modify-staged-before"
        assert not (repo / "generated.txt").exists()

    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        repo = base / "repo"
        remote = base / "remote.git"
        repo.mkdir()
        _sh(["git", "init", "-b", "main"], repo)
        _sh(["git", "config", "user.name", "GVE Validator"], repo)
        _sh(["git", "config", "user.email", "validator@example.invalid"], repo)
        (repo / "base.txt").write_text("base\n", encoding="utf-8")
        _sh(["git", "add", "base.txt"], repo)
        _sh(["git", "commit", "-m", "baseline"], repo)
        baseline = _sh(["git", "rev-parse", "HEAD"], repo)
        _sh(["git", "init", "--bare", str(remote)], base)
        _sh(["git", "remote", "add", "origin", str(remote)], repo)

        authority = Authority(
            repository=repo.resolve(),
            git_remotes=frozenset({"origin"}),
            execute_limits=(
                ("wall_seconds", 600),
                ("max_concurrent", 32),
                ("max_total_spawned", 1024),
                ("max_spawns_per_second", 64),
            ),
        )
        result = MacroRunner(Engine(product_registry()), macros).execute(
            _request(
                {
                    "changes": [
                        {"operation": "create", "path": "generated.txt", "content": "generated\n"}
                    ],
                    "commit_message": "generated",
                    "expected_head": baseline,
                    "validate": False,
                }
            ),
            authority,
            RepositoryContext(repo.resolve(), None, "main", baseline),
        )
        if result["status"] != "success":
            raise AssertionError(json.dumps(result, indent=2, sort_keys=True))
        assert [stage["label"] for stage in result["stages"]] == list(definition.stages)
        projected = result["result"]
        assert set(projected) == {
            "repository", "branch", "publication_branch", "expected_head",
            "observed_head", "branch_created", "files_changed", "validation",
            "diff", "commit", "commit_count", "push_mode", "remote_head",
            "history_rewrite_or_force_push_occurred", "merge_occurred",
        }
        assert projected["repository"]["root"] == str(repo.resolve())
        assert projected["expected_head"] == baseline
        assert projected["observed_head"] == baseline
        assert projected["branch"] == "main"
        assert projected["publication_branch"] == "main"
        assert projected["branch_created"] is False
        assert projected["files_changed"] == ["generated.txt"]
        assert projected["validation"] == {"requested": False, "status": "not-requested"}
        assert projected["diff"] is not None
        assert projected["commit_count"] == 1
        assert projected["push_mode"] == "normal"
        assert projected["history_rewrite_or_force_push_occurred"] is False
        assert projected["merge_occurred"] is False
        commit = next(x for x in result["tasks"] if x["id"] == "modify-commit")["result"]["commit"]
        assert projected["commit"] == commit
        assert projected["remote_head"] == commit
        assert next(x for x in result["tasks"] if x["id"] == "modify-verify")["result"]["commit"] == commit
        assert _sh(
            ["git", "--git-dir", str(remote), "rev-parse", "refs/heads/main"], base
        ) == commit

    return True
