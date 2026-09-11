from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "product" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gve.authority import Authority
from gve.product_registry import product_registry


def sh(args, cwd):
    cp = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if cp.returncode:
        raise AssertionError(f"command failed {args}: {cp.stderr}")
    return cp.stdout.rstrip("\r\n")


def call(name, params, auth):
    task = product_registry().resolve(name)
    return task.execute(task.validate(params, auth), auth)


def validate_git_plugin() -> bool:
    expected = {
        "git.repository", "git.branch", "git.head", "git.status", "git.status-scope", "git.staged-scope", "git.pending-diff-check", "git.diff",
        "git.diff-check", "git.branch-create", "git.branch-switch", "git.add",
        "git.commit", "git.fetch", "git.remote-head", "git.push",
    }
    identities = set(product_registry().identities())
    if not expected.issubset(identities):
        raise AssertionError(f"Git registry incomplete: {sorted(expected-identities)}")

    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        repo = base / "repo"
        remote = base / "remote.git"
        repo.mkdir()
        sh(["git", "init", "-b", "main"], repo)
        sh(["git", "config", "user.email", "validator@example.invalid"], repo)
        sh(["git", "config", "user.name", "GVE Validator"], repo)
        (repo / "a.txt").write_text("one\n", encoding="utf-8")
        sh(["git", "add", "a.txt"], repo)
        sh(["git", "commit", "-m", "initial"], repo)
        first = sh(["git", "rev-parse", "HEAD"], repo)
        sh(["git", "init", "--bare", str(remote)], base)
        sh(["git", "remote", "add", "origin", str(remote)], repo)

        auth = Authority(repository=repo.resolve(), git_remotes=frozenset({"origin"}))

        r = call("git.repository", {"expected_root": str(repo.resolve()), "expected_remotes": {"origin": str(remote)}}, auth)
        assert r["result"]["root"] == str(repo.resolve())
        assert r["result"]["remotes"]["origin"] == str(remote)

        assert call("git.branch", {"expected": "main"}, auth)["result"]["branch"] == "main"
        assert call("git.head", {"expected": first}, auth)["result"]["commit"] == first
        assert call("git.status", {"expected_clean": True}, auth)["result"]["clean"] is True

        (repo / " space.txt").write_text("x\n", encoding="utf-8")
        status = call("git.status", {}, auth)["result"]
        item = next(x for x in status["entries"] if x["path"] == " space.txt")
        assert item["status"] == "??"

        scoped = call(
            "git.status-scope",
            {"allowed_paths": [" space.txt"], "include_untracked": True},
            auth,
        )["result"]
        assert scoped["clean"] is False
        assert scoped["allowed_paths"] == [" space.txt"]

        try:
            call(
                "git.status-scope",
                {"allowed_paths": ["a.txt"], "include_untracked": True},
                auth,
            )
        except Exception as exc:
            assert getattr(exc, "code", None) == "state-precondition"
        else:
            raise AssertionError("out-of-scope dirty path was accepted")

        try:
            call(
                "git.status-scope",
                {"allowed_paths": [" space.txt", " space.txt"]},
                auth,
            )
        except Exception as exc:
            assert getattr(exc, "code", None) == "git"
        else:
            raise AssertionError("duplicate scoped dirty path was accepted")

        sh(["git", "add", " space.txt"], repo)
        staged = call("git.staged-scope", {"allowed_paths": [" space.txt"]}, auth)["result"]
        assert staged["entries"]
        try:
            call("git.staged-scope", {"allowed_paths": ["a.txt"]}, auth)
        except Exception as exc:
            assert getattr(exc, "code", None) == "state-precondition"
        else:
            raise AssertionError("out-of-scope staged path was accepted")
        sh(["git", "reset", "HEAD", "--", " space.txt"], repo)

        (repo / "pending-good.txt").write_text("good\n", encoding="utf-8")
        assert call("git.pending-diff-check", {"paths": ["pending-good.txt"]}, auth)["result"]["clean"] is True
        assert call("git.staged-scope", {"allowed_paths": []}, auth)["result"]["entries"] == []
        (repo / "pending-good.txt").unlink()
        (repo / "pending-bad.txt").write_text("bad trailing space \n", encoding="utf-8")
        try:
            call("git.pending-diff-check", {"paths": ["pending-bad.txt"]}, auth)
        except Exception as exc:
            assert getattr(exc, "code", None) == "state-precondition"
        else:
            raise AssertionError("pending whitespace error was accepted")
        assert call("git.staged-scope", {"allowed_paths": []}, auth)["result"]["entries"] == []
        (repo / "pending-bad.txt").unlink()

        diff = call("git.diff", {"paths": ["a.txt"]}, auth)["result"]["diff"]
        assert diff == ""
        assert call("git.diff-check", {}, auth)["result"]["clean"] is True

        created = call("git.branch-create", {"name": "work", "start": first}, auth)
        assert created["result"]["branch"] == "work"
        call("git.branch-switch", {"name": "work"}, auth)

        (repo / "b.txt").write_text("two\n", encoding="utf-8")
        call("git.add", {"paths": ["b.txt"]}, auth)
        committed = call("git.commit", {"message": "second"}, auth)
        second = committed["result"]["commit"]
        assert committed["result"]["parent"] == first

        missing = call("git.remote-head", {"remote": "origin", "branch": "work", "expected": None}, auth)
        assert missing["result"]["commit"] is None
        pushed = call(
            "git.push",
            {"remote": "origin", "local_branch": "work", "remote_branch": "work", "expected_remote_head": None},
            auth,
        )
        assert pushed["result"]["local_commit"] == second
        verified = call("git.remote-head", {"remote": "origin", "branch": "work", "expected": second}, auth)
        assert verified["result"]["commit"] == second

        call("git.fetch", {"remote": "origin", "branches": ["work"]}, auth)

        try:
            call("git.push", {"remote": "other", "local_branch": "work", "remote_branch": "work"}, auth)
        except Exception as exc:
            assert getattr(exc, "code", None) == "authority"
        else:
            raise AssertionError("unauthorized Git remote was accepted")

        try:
            call("git.diff", {"raw_args": ["--no-index"]}, auth)
        except Exception as exc:
            assert getattr(exc, "code", None) == "git"
        else:
            raise AssertionError("raw Git argument escape hatch was accepted")

        try:
            call(
                "git.push",
                {"remote": "origin", "local_branch": "work", "remote_branch": "work", "force": True},
                auth,
            )
        except Exception as exc:
            assert getattr(exc, "code", None) == "git"
        else:
            raise AssertionError("force-push parameter was accepted")

        try:
            call(
                "git.push",
                {"remote": "origin", "local_branch": "work", "remote_branch": "work", "expected_remote_head": first},
                auth,
            )
        except Exception as exc:
            assert getattr(exc, "code", None) == "state-precondition"
        else:
            raise AssertionError("remote race mismatch was accepted")

    return True
