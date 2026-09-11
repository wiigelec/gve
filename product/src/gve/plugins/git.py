from __future__ import annotations

import re
import subprocess
from pathlib import Path
from typing import Any

from ..authority import Authority
from ..errors import GVEError
from ..registry import TaskDefinition

OID_RE = re.compile(r"^[0-9a-f]{40}$")


class GitError(GVEError):
    code = "git"


class GitAuthorityError(GVEError):
    code = "authority"


class GitPreconditionError(GVEError):
    code = "state-precondition"


def _fields(p: dict[str, Any], allowed: set[str], required: set[str]) -> None:
    unknown = set(p) - allowed
    missing = required - set(p)
    if unknown or missing:
        raise GitError(
            "invalid Git task parameters",
            details={"unknown": sorted(unknown), "missing": sorted(missing)},
        )


def _repo(a: Authority) -> Path:
    root = a.repository.resolve()
    cp = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if cp.returncode != 0:
        raise GitPreconditionError("active repository is not a Git repository")
    observed = Path(cp.stdout.rstrip("\r\n")).resolve()
    if observed != root:
        raise GitAuthorityError(
            "active repository is not the Git top-level",
            details={"authorized": str(root), "observed": str(observed)},
        )
    return root


def _run(a: Authority, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    root = _repo(a)
    cp = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if check and cp.returncode != 0:
        raise GitError(
            "Git operation failed",
            details={"exit_code": cp.returncode, "stderr": cp.stderr.rstrip("\r\n")},
        )
    return cp


def _s(v: Any, field: str) -> str:
    if not isinstance(v, str) or not v:
        raise GitError(f"{field} must be a non-empty string")
    return v


def _b(v: Any, field: str) -> bool:
    if not isinstance(v, bool):
        raise GitError(f"{field} must be boolean")
    return v


def _oid(v: Any, field: str, *, nullable: bool = False) -> str | None:
    if nullable and v is None:
        return None
    if not isinstance(v, str) or not OID_RE.fullmatch(v):
        raise GitError(f"{field} must be a lowercase 40-character Git object ID")
    return v


def _branch(a: Authority, value: Any, field: str) -> str:
    name = _s(value, field)
    cp = _run(a, ["check-ref-format", "--branch", name], check=False)
    if cp.returncode != 0:
        raise GitError(f"{field} is not a valid branch name")
    return name


def _remote(a: Authority, value: Any) -> str:
    name = _s(value, "remote")
    if name not in a.git_remotes:
        raise GitAuthorityError("Git remote is not authorized", details={"remote": name})
    existing = set(_run(a, ["remote"]).stdout.splitlines())
    if name not in existing:
        raise GitPreconditionError("authorized Git remote is not configured", details={"remote": name})
    return name


def _path(a: Authority, value: Any) -> str:
    p = _s(value, "path").replace("\\", "/")
    raw = Path(p)
    if raw.is_absolute():
        raise GitAuthorityError("Git path must be repository-relative")
    root = _repo(a)
    resolved = (root / p).resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError:
        raise GitAuthorityError("Git path escapes repository", details={"path": p})
    return p


def _paths(a: Authority, value: Any, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list) or (nonempty and not value):
        raise GitError("paths must be an array" + (" and non-empty" if nonempty else ""))
    return [_path(a, v) for v in value]


def _remotes(a: Authority) -> dict[str, str]:
    result = {}
    for name in _run(a, ["remote"]).stdout.splitlines():
        result[name] = _run(a, ["remote", "get-url", name]).stdout.rstrip("\r\n")
    return result


def repository_v(p, a):
    _fields(p, {"expected_root", "expected_remotes"}, set())
    expected_root = p.get("expected_root")
    if expected_root is not None:
        expected_root = _s(expected_root, "expected_root")
    expected_remotes = p.get("expected_remotes")
    if expected_remotes is not None:
        if not isinstance(expected_remotes, dict):
            raise GitError("expected_remotes must be an object")
        for k, v in expected_remotes.items():
            _s(k, "remote name"); _s(v, "remote URL")
    _repo(a)
    return {"expected_root": expected_root, "expected_remotes": expected_remotes}


def repository_x(p, a):
    root = _repo(a); remotes = _remotes(a)
    result = {"root": str(root), "remotes": remotes}
    if p["expected_root"] is not None and p["expected_root"] != str(root):
        raise GitPreconditionError("repository root expectation mismatch", details={"observed": str(root)})
    if p["expected_remotes"] is not None:
        mismatches = {}
        for name, expected in p["expected_remotes"].items():
            observed = remotes.get(name)
            if observed != expected:
                mismatches[name] = {"expected": expected, "observed": observed}
        if mismatches:
            raise GitPreconditionError("repository remote expectation mismatch", details={"mismatches": mismatches})
    return {"observations": result, "result": result}


def branch_v(p, a):
    _fields(p, {"expected"}, set())
    expected = p.get("expected")
    if expected is not None: expected = _s(expected, "expected")
    _repo(a)
    return {"expected": expected}


def branch_x(p, a):
    cp = _run(a, ["symbolic-ref", "--quiet", "--short", "HEAD"], check=False)
    observed = cp.stdout.rstrip("\r\n") if cp.returncode == 0 else None
    if p["expected"] is not None and observed != p["expected"]:
        raise GitPreconditionError("branch expectation mismatch", details={"expected": p["expected"], "observed": observed})
    return {"observations": {"branch": observed}, "result": {"branch": observed}}


def head_v(p, a):
    _fields(p, {"expected"}, set())
    expected = p.get("expected")
    if expected is not None: expected = _oid(expected, "expected")
    _repo(a)
    return {"expected": expected}


def head_x(p, a):
    cp = _run(a, ["rev-parse", "--verify", "HEAD"], check=False)
    observed = cp.stdout.rstrip("\r\n") if cp.returncode == 0 else None
    if p["expected"] is not None and observed != p["expected"]:
        raise GitPreconditionError("HEAD expectation mismatch", details={"expected": p["expected"], "observed": observed})
    return {"observations": {"commit": observed}, "result": {"commit": observed}}


def status_v(p, a):
    _fields(p, {"expected_clean", "include_untracked"}, set())
    expected = p.get("expected_clean")
    if expected is not None: expected = _b(expected, "expected_clean")
    include = p.get("include_untracked", True)
    include = _b(include, "include_untracked")
    _repo(a)
    return {"expected_clean": expected, "include_untracked": include}


def status_x(p, a):
    untracked = "all" if p["include_untracked"] else "no"
    raw = _run(a, ["status", "--porcelain=v1", "-z", f"--untracked-files={untracked}"]).stdout
    chunks = raw.split("\0")
    entries = []
    i = 0
    while i < len(chunks):
        record = chunks[i]
        if not record:
            i += 1
            continue
        if len(record) < 3:
            raise GitError("malformed Git porcelain status record")
        code = record[:2]
        path = record[3:]
        entry = {"status": code, "path": path}
        if code[0] in "RC" or code[1] in "RC":
            i += 1
            if i >= len(chunks) or not chunks[i]:
                raise GitError("malformed Git rename/copy status record")
            entry["original_path"] = chunks[i]
        entries.append(entry)
        i += 1
    clean = not entries
    if p["expected_clean"] is not None and clean != p["expected_clean"]:
        raise GitPreconditionError("Git cleanliness expectation mismatch", details={"expected": p["expected_clean"], "observed": clean})
    result = {"clean": clean, "entries": entries}
    return {"observations": result, "result": result}


def status_scope_v(p, a):
    _fields(p, {"allowed_paths", "include_untracked"}, {"allowed_paths"})
    allowed_paths = _paths(a, p["allowed_paths"])
    if len(set(allowed_paths)) != len(allowed_paths):
        raise GitError("allowed_paths must contain unique repository-relative paths")
    include = p.get("include_untracked", True)
    include = _b(include, "include_untracked")
    return {"allowed_paths": allowed_paths, "include_untracked": include}


def status_scope_x(p, a):
    base = status_x(
        {"expected_clean": None, "include_untracked": p["include_untracked"]},
        a,
    )
    result = base["result"]
    allowed = set(p["allowed_paths"])
    outside = []
    for entry in result["entries"]:
        candidates = [entry["path"]]
        if "original_path" in entry:
            candidates.append(entry["original_path"])
        for candidate in candidates:
            if candidate not in allowed:
                outside.append(candidate)
    if outside:
        raise GitPreconditionError(
            "Git dirty path scope mismatch",
            details={
                "allowed_paths": p["allowed_paths"],
                "outside_paths": sorted(set(outside)),
                "entries": result["entries"],
            },
        )
    scoped = dict(result)
    scoped["allowed_paths"] = list(p["allowed_paths"])
    return {"observations": scoped, "result": scoped}


def staged_scope_v(p, a):
    _fields(p, {"allowed_paths"}, {"allowed_paths"})
    allowed_paths = _paths(a, p["allowed_paths"])
    if len(set(allowed_paths)) != len(allowed_paths):
        raise GitError("allowed_paths must contain unique repository-relative paths")
    return {"allowed_paths": allowed_paths}


def staged_scope_x(p, a):
    result = status_x({"expected_clean": None, "include_untracked": True}, a)["result"]
    allowed = set(p["allowed_paths"])
    staged = []
    outside = []
    for entry in result["entries"]:
        code = entry["status"]
        if not code or code[0] in {" ", "?"}:
            continue
        candidates = [entry["path"]]
        if "original_path" in entry:
            candidates.append(entry["original_path"])
        staged.append(entry)
        for candidate in candidates:
            if candidate not in allowed:
                outside.append(candidate)
    if outside:
        raise GitPreconditionError(
            "Git staged path scope mismatch",
            details={
                "allowed_paths": p["allowed_paths"],
                "outside_paths": sorted(set(outside)),
                "entries": staged,
            },
        )
    result = {"allowed_paths": list(p["allowed_paths"]), "entries": staged}
    return {"observations": result, "result": result}


def diff_v(p, a):
    _fields(p, {"cached", "paths"}, set())
    cached = _b(p.get("cached", False), "cached")
    paths = _paths(a, p.get("paths", []))
    return {"cached": cached, "paths": paths}


def _diff_args(p, check=False):
    args = ["diff"]
    if p["cached"]: args.append("--cached")
    if check: args.append("--check")
    if p["paths"]: args.extend(["--", *p["paths"]])
    return args


def diff_x(p, a):
    text = _run(a, _diff_args(p)).stdout
    return {"observations": {"cached": p["cached"], "paths": p["paths"]}, "result": {"diff": text}}


def diff_check_x(p, a):
    cp = _run(a, _diff_args(p, check=True), check=False)
    clean = cp.returncode == 0
    result = {"clean": clean, "diagnostics": (cp.stdout + cp.stderr)}
    if not clean:
        raise GitPreconditionError("git diff --check failed", details=result)
    return {"observations": result, "result": result}


def branch_create_v(p, a):
    _fields(p, {"name", "start"}, {"name"})
    name = _branch(a, p["name"], "name")
    start = p.get("start")
    if start is not None: start = _oid(start, "start")
    if _run(a, ["show-ref", "--verify", "--quiet", f"refs/heads/{name}"], check=False).returncode == 0:
        raise GitPreconditionError("branch already exists")
    return {"name": name, "start": start}


def branch_create_x(p, a):
    start = p["start"] or _run(a, ["rev-parse", "HEAD"]).stdout.rstrip("\r\n")
    _run(a, ["branch", p["name"], start])
    commit = _run(a, ["rev-parse", f"refs/heads/{p['name']}"]).stdout.rstrip("\r\n")
    return {"effects": {"created_branch": p["name"]}, "result": {"branch": p["name"], "commit": commit}}


def branch_switch_v(p, a):
    _fields(p, {"name"}, {"name"})
    name = _branch(a, p["name"], "name")
    if _run(a, ["show-ref", "--verify", "--quiet", f"refs/heads/{name}"], check=False).returncode != 0:
        raise GitPreconditionError("branch does not exist")
    return {"name": name}


def branch_switch_x(p, a):
    _run(a, ["switch", p["name"]])
    commit = _run(a, ["rev-parse", "HEAD"]).stdout.rstrip("\r\n")
    return {"effects": {"current_branch": p["name"]}, "result": {"branch": p["name"], "commit": commit}}


def add_v(p, a):
    _fields(p, {"paths"}, {"paths"})
    return {"paths": _paths(a, p["paths"], nonempty=True)}


def add_x(p, a):
    _run(a, ["add", "--", *p["paths"]])
    return {"effects": {"staged_paths": p["paths"]}, "result": {"paths": p["paths"]}}


def commit_v(p, a):
    _fields(p, {"message"}, {"message"})
    return {"message": _s(p["message"], "message")}


def commit_x(p, a):
    if _run(a, ["diff", "--cached", "--quiet"], check=False).returncode == 0:
        raise GitPreconditionError("no staged changes to commit")
    parent_cp = _run(a, ["rev-parse", "--verify", "HEAD"], check=False)
    parent = parent_cp.stdout.rstrip("\r\n") if parent_cp.returncode == 0 else None
    _run(a, ["commit", "-m", p["message"]])
    commit = _run(a, ["rev-parse", "HEAD"]).stdout.rstrip("\r\n")
    return {"effects": {"commit_created": commit}, "result": {"commit": commit, "parent": parent}}


def fetch_v(p, a):
    _fields(p, {"remote", "branches"}, {"remote"})
    remote = _remote(a, p["remote"])
    branches = p.get("branches")
    if branches is not None:
        if not isinstance(branches, list):
            raise GitError("branches must be an array")
        branches = [_branch(a, x, "branch") for x in branches]
    return {"remote": remote, "branches": branches}


def fetch_x(p, a):
    args = ["fetch", p["remote"]]
    if p["branches"] is not None: args.extend(p["branches"])
    cp = _run(a, args)
    return {"observations": {"remote": p["remote"], "stderr": cp.stderr}, "result": {"remote": p["remote"], "branches": p["branches"]}}


def remote_head_v(p, a):
    _fields(p, {"remote", "branch", "expected"}, {"remote", "branch"})
    remote = _remote(a, p["remote"])
    branch = _branch(a, p["branch"], "branch")
    expected = p.get("expected", "__absent__")
    if expected != "__absent__": expected = _oid(expected, "expected", nullable=True)
    return {"remote": remote, "branch": branch, "expected": expected}


def _observe_remote_head(p, a):
    cp = _run(a, ["ls-remote", "--heads", p["remote"], f"refs/heads/{p['branch']}"])
    line = cp.stdout.strip()
    return line.split()[0] if line else None


def remote_head_x(p, a):
    observed = _observe_remote_head(p, a)
    if p["expected"] != "__absent__" and observed != p["expected"]:
        raise GitPreconditionError("remote head expectation mismatch", details={"expected": p["expected"], "observed": observed})
    result = {"remote": p["remote"], "branch": p["branch"], "commit": observed}
    return {"observations": result, "result": result}


def push_v(p, a):
    _fields(p, {"remote", "local_branch", "remote_branch", "expected_remote_head"}, {"remote", "local_branch", "remote_branch"})
    remote = _remote(a, p["remote"])
    local_branch = _branch(a, p["local_branch"], "local_branch")
    remote_branch = _branch(a, p["remote_branch"], "remote_branch")
    if _run(a, ["show-ref", "--verify", "--quiet", f"refs/heads/{local_branch}"], check=False).returncode != 0:
        raise GitPreconditionError("local branch does not exist")
    expected = p.get("expected_remote_head", "__absent__")
    if expected != "__absent__": expected = _oid(expected, "expected_remote_head", nullable=True)
    return {"remote": remote, "local_branch": local_branch, "remote_branch": remote_branch, "expected_remote_head": expected}


def push_x(p, a):
    before = _observe_remote_head({"remote": p["remote"], "branch": p["remote_branch"]}, a)
    if p["expected_remote_head"] != "__absent__" and before != p["expected_remote_head"]:
        raise GitPreconditionError("push remote race guard mismatch", details={"expected": p["expected_remote_head"], "observed": before})
    local_commit = _run(a, ["rev-parse", f"refs/heads/{p['local_branch']}"]).stdout.rstrip("\r\n")
    cp = _run(a, ["push", p["remote"], f"{p['local_branch']}:refs/heads/{p['remote_branch']}"])
    return {
        "observations": {"remote_head_before": before},
        "effects": {"push_attempted": True, "transport_exit_code": cp.returncode},
        "result": {"remote": p["remote"], "remote_branch": p["remote_branch"], "local_commit": local_commit, "transport_stderr": cp.stderr},
    }


def tasks() -> tuple[TaskDefinition, ...]:
    return (
        TaskDefinition("git.repository", repository_v, repository_x),
        TaskDefinition("git.branch", branch_v, branch_x),
        TaskDefinition("git.head", head_v, head_x),
        TaskDefinition("git.status", status_v, status_x),
        TaskDefinition("git.status-scope", status_scope_v, status_scope_x),
        TaskDefinition("git.staged-scope", staged_scope_v, staged_scope_x),
        TaskDefinition("git.diff", diff_v, diff_x),
        TaskDefinition("git.diff-check", diff_v, diff_check_x),
        TaskDefinition("git.branch-create", branch_create_v, branch_create_x),
        TaskDefinition("git.branch-switch", branch_switch_v, branch_switch_x),
        TaskDefinition("git.add", add_v, add_x),
        TaskDefinition("git.commit", commit_v, commit_x),
        TaskDefinition("git.fetch", fetch_v, fetch_x),
        TaskDefinition("git.remote-head", remote_head_v, remote_head_x),
        TaskDefinition("git.push", push_v, push_x),
    )
