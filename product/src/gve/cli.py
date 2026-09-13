from __future__ import annotations

import argparse
import json
import re
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import Sequence

from .authority import Authority
from .engine import Engine
from .errors import GVEError
from .macro_request import parse_macro_request
from .macro_runner import MacroRunner, RepositoryContext
from .plugins.execute import HARD_LIMITS
from .presenter import ConsolePresenter
from .product_macro_registry import product_macro_registry
from .product_registry import product_registry


_HTTPS_GITHUB = re.compile(r"^https://github\.com/([^/\s]+)/([^/\s]+?)(?:\.git)?$")
_SSH_GITHUB = re.compile(r"^git@github\.com:([^/\s]+)/([^/\s]+?)(?:\.git)?$")
_SSH_URL_GITHUB = re.compile(r"^ssh://git@github\.com/([^/\s]+)/([^/\s]+?)(?:\.git)?$")



def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gve")
    sub = parser.add_subparsers(dest="command", required=True)

    macro = sub.add_parser("macro")
    macro.add_argument("--in", dest="input_path", required=True)
    macro.add_argument("--out", dest="output_path", required=True)
    macro.add_argument("--repo")

    sub.add_parser("macro-list")

    schema = sub.add_parser("macro-schema")
    schema.add_argument("name")

    return parser


def _git(repository: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    cp = subprocess.run(
        ["git", "-C", str(repository), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and cp.returncode != 0:
        raise ValueError(cp.stderr.rstrip("\r\n") or "Git repository observation failed")
    return cp


def _github_identity(url: str) -> str | None:
    for pattern in (_HTTPS_GITHUB, _SSH_GITHUB, _SSH_URL_GITHUB):
        match = pattern.fullmatch(url)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
    return None


def _repository_context(repository: Path) -> RepositoryContext:
    repository = repository.resolve()
    observed_root = Path(
        _git(repository, "rev-parse", "--show-toplevel").stdout.rstrip("\r\n")
    ).resolve()
    if observed_root != repository:
        raise ValueError(
            f"selected repository must be Git top-level: selected={repository} observed={observed_root}"
        )

    branch_cp = _git(repository, "symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    branch = branch_cp.stdout.rstrip("\r\n") if branch_cp.returncode == 0 else None

    head_cp = _git(repository, "rev-parse", "--verify", "HEAD", check=False)
    head = head_cp.stdout.rstrip("\r\n") if head_cp.returncode == 0 else None

    remote_cp = _git(repository, "remote", "get-url", "origin", check=False)
    identity = _github_identity(remote_cp.stdout.rstrip("\r\n")) if remote_cp.returncode == 0 else None

    return RepositoryContext(repository, identity, branch, head)


def _macro_failure(message: str, *, code: str = "macro-cli-failure", details=None) -> dict:
    return {
        "schema_version": 1,
        "macro": None,
        "status": "failure",
        "stages": [],
        "tasks": [],
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
    }


def macro_command(args: argparse.Namespace) -> int:
    output_path = Path(args.output_path)
    try:
        payload = json.loads(Path(args.input_path).read_text(encoding="utf-8"))
        request = parse_macro_request(payload)
        repository = Path(args.repo).resolve() if args.repo else Path.cwd().resolve()
        context = _repository_context(repository)

        if request.macro_name in {"issue", "pr"}:
            if context.identity is None:
                raise ValueError("GitHub macro requires a supported repository origin identity")
            try:
                auth_cp = subprocess.run(
                    ["gh", "auth", "status", "--hostname", "github.com"],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            except FileNotFoundError as exc:
                raise ValueError("GitHub macro requires the gh CLI") from exc
            if auth_cp.returncode != 0:
                raise ValueError("GitHub macro requires authenticated gh configuration")
            authority = Authority(
                repository=repository,
                github_repository=context.identity,
            )
        elif request.macro_name == "modify":
            authority = Authority(
                repository=repository,
                git_remotes=frozenset({"origin"}),
                execute_limits=tuple(
                    (key, HARD_LIMITS[key]) for key in sorted(HARD_LIMITS)
                ),
            )
        else:
            authority = Authority.for_repository(repository)

        presenter = ConsolePresenter()
        result = MacroRunner(
            Engine(product_registry()),
            product_macro_registry(),
        ).execute(request, authority, context, observer=presenter)
    except GVEError as exc:
        result = _macro_failure(exc.message, code=exc.code, details=exc.details)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        result = _macro_failure(str(exc))

    try:
        output_path.write_text(json.dumps(result, sort_keys=True) + "\n", encoding="utf-8")
    except OSError as exc:
        if "presenter" in locals():
            presenter.output_failure(exc, output_path, result)
        else:
            print(json.dumps(_macro_failure(str(exc)), sort_keys=True))
        return 2

    if "presenter" in locals():
        presenter.finish(result, output_path)
    return 0 if result["status"] == "success" else 1


def macro_list_command() -> int:
    print(json.dumps(list(product_macro_registry().identities()), sort_keys=True))
    return 0


def macro_schema_command(name: str) -> int:
    try:
        definition = product_macro_registry().resolve(name)
    except KeyError as exc:
        print(json.dumps(_macro_failure(str(exc)), sort_keys=True))
        return 1
    print(json.dumps(deepcopy(dict(definition.parameter_schema)), sort_keys=True))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return int(exc.code)

    if args.command == "macro":
        return macro_command(args)
    if args.command == "macro-list":
        return macro_list_command()
    if args.command == "macro-schema":
        return macro_schema_command(args.name)
    return 2
