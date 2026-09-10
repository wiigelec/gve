from __future__ import annotations

import json
import subprocess
from typing import Any

from ..authority import Authority
from ..errors import GVEError
from ..registry import TaskDefinition


class GitHubError(GVEError):
    code = "github"


class GitHubAuthorityError(GVEError):
    code = "authority"


class GitHubTransportError(GVEError):
    code = "github-transport"


def _fields(parameters: dict[str, Any], allowed: set[str], required: set[str]) -> None:
    unknown = set(parameters) - allowed
    missing = required - set(parameters)
    if unknown or missing:
        raise GitHubError(
            "invalid GitHub task parameters",
            details={"unknown": sorted(unknown), "missing": sorted(missing)},
        )


def _repository(authority: Authority) -> str:
    repository = authority.github_repository
    if repository is None:
        raise GitHubAuthorityError("GitHub repository authority is absent")
    if (
        not isinstance(repository, str)
        or repository.count("/") != 1
        or any(not part for part in repository.split("/"))
    ):
        raise GitHubAuthorityError("GitHub repository authority is invalid")
    return repository


def _positive_number(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise GitHubError("number must be a positive integer")
    return value


def _text(value: Any, field: str, *, allow_empty: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value):
        qualifier = "string" if allow_empty else "non-empty string"
        raise GitHubError(f"{field} must be a {qualifier}")
    return value


def _labels(value: Any) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise GitHubError("labels must be an array of non-empty strings")
    return list(value)


def _transport(method: str, path: str, body: dict[str, Any] | None) -> dict[str, Any]:
    args = [
        "gh",
        "api",
        "--method",
        method,
        "--header",
        "Accept: application/vnd.github+json",
        "--header",
        "X-GitHub-Api-Version: 2022-11-28",
        path,
    ]
    input_text = None
    if body is not None:
        args.extend(["--input", "-"])
        input_text = json.dumps(body)

    try:
        completed = subprocess.run(
            args,
            input=input_text,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
        )
    except FileNotFoundError as exc:
        raise GitHubTransportError(
            "GitHub CLI is unavailable",
            details={"executable": "gh"},
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise GitHubTransportError(
            "GitHub CLI request timed out",
            details={"timeout_seconds": 30},
        ) from exc
    except OSError as exc:
        raise GitHubTransportError(
            "GitHub CLI transport failed",
            details={"error": str(exc)},
        ) from exc

    if completed.returncode != 0:
        raise GitHubTransportError(
            "GitHub CLI request failed",
            details={
                "exit_code": completed.returncode,
                "stderr": completed.stderr.rstrip("\r\n"),
            },
        )

    try:
        parsed = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise GitHubTransportError(
            "GitHub CLI returned invalid JSON",
            details={"stdout": completed.stdout.rstrip("\r\n")},
        ) from exc
    if not isinstance(parsed, dict):
        raise GitHubTransportError("GitHub CLI returned a non-object response")
    return parsed


def _request(authority: Authority, method: str, suffix: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    repository = _repository(authority)
    return _transport(method, f"/repos/{repository}{suffix}", body)


def _require_issue_object(data: dict[str, Any], number: int) -> dict[str, Any]:
    if "pull_request" in data:
        raise GitHubError(
            "GitHub issue task cannot operate on a pull request",
            details={"number": number},
        )
    return data


def _issue_result(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "number": data.get("number"),
        "url": data.get("html_url"),
        "title": data.get("title"),
        "body": data.get("body"),
        "state": data.get("state"),
        "labels": [
            item.get("name")
            for item in data.get("labels", [])
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        ],
    }


def _pr_result(data: dict[str, Any]) -> dict[str, Any]:
    base = data.get("base") if isinstance(data.get("base"), dict) else {}
    head = data.get("head") if isinstance(data.get("head"), dict) else {}
    result = {
        "number": data.get("number"),
        "url": data.get("html_url"),
        "title": data.get("title"),
        "body": data.get("body"),
        "state": data.get("state"),
        "base": base.get("ref"),
        "head": head.get("ref"),
        "draft": data.get("draft"),
    }
    if "merged" in data:
        result["merged"] = data.get("merged")
    if "mergeable" in data:
        result["mergeable"] = data.get("mergeable")
    return result


def issue_read_v(p, a):
    _fields(p, {"number"}, {"number"})
    _repository(a)
    return {"number": _positive_number(p["number"])}


def issue_read_x(p, a):
    data = _request(a, "GET", f"/issues/{p['number']}")
    _require_issue_object(data, p["number"])
    result = _issue_result(data)
    return {"observations": result, "result": result}


def issue_create_v(p, a):
    _fields(p, {"title", "body", "labels"}, {"title"})
    _repository(a)
    title = _text(p["title"], "title")
    body = _text(p.get("body", ""), "body", allow_empty=True)
    labels = _labels(p.get("labels", []))
    return {"title": title, "body": body, "labels": labels}


def issue_create_x(p, a):
    result = _issue_result(
        _request(a, "POST", "/issues", {"title": p["title"], "body": p["body"], "labels": p["labels"]})
    )
    return {"effects": {"issue_created": result["number"]}, "result": result}


def issue_modify_v(p, a):
    _fields(p, {"number", "title", "body", "labels", "state"}, {"number"})
    _repository(a)
    number = _positive_number(p["number"])
    body: dict[str, Any] = {}
    if "title" in p:
        body["title"] = _text(p["title"], "title")
    if "body" in p:
        body["body"] = _text(p["body"], "body", allow_empty=True)
    if "labels" in p:
        body["labels"] = _labels(p["labels"])
    if "state" in p:
        if p["state"] not in {"open", "closed"}:
            raise GitHubError("state must be open or closed")
        body["state"] = p["state"]
    if not body:
        raise GitHubError("issue-modify requires at least one mutation field")
    return {"number": number, "body": body}


def issue_modify_x(p, a):
    current = _request(a, "GET", f"/issues/{p['number']}")
    _require_issue_object(current, p["number"])
    result = _issue_result(_request(a, "PATCH", f"/issues/{p['number']}", p["body"]))
    return {"effects": {"issue_modified": p["number"]}, "result": result}


def pr_read_v(p, a):
    _fields(p, {"number"}, {"number"})
    _repository(a)
    return {"number": _positive_number(p["number"])}


def pr_read_x(p, a):
    result = _pr_result(_request(a, "GET", f"/pulls/{p['number']}"))
    return {"observations": result, "result": result}


def pr_create_v(p, a):
    _fields(p, {"title", "body", "base", "head", "draft"}, {"title", "base", "head"})
    _repository(a)
    draft = p.get("draft", False)
    if not isinstance(draft, bool):
        raise GitHubError("draft must be boolean")
    return {
        "title": _text(p["title"], "title"),
        "body": _text(p.get("body", ""), "body", allow_empty=True),
        "base": _text(p["base"], "base"),
        "head": _text(p["head"], "head"),
        "draft": draft,
    }


def pr_create_x(p, a):
    result = _pr_result(
        _request(
            a,
            "POST",
            "/pulls",
            {"title": p["title"], "body": p["body"], "base": p["base"], "head": p["head"], "draft": p["draft"]},
        )
    )
    return {"effects": {"pull_request_created": result["number"]}, "result": result}


def pr_modify_v(p, a):
    _fields(p, {"number", "title", "body", "base", "state"}, {"number"})
    _repository(a)
    number = _positive_number(p["number"])
    body: dict[str, Any] = {}
    for field in ("title", "base"):
        if field in p:
            body[field] = _text(p[field], field)
    if "body" in p:
        body["body"] = _text(p["body"], "body", allow_empty=True)
    if "state" in p:
        if p["state"] not in {"open", "closed"}:
            raise GitHubError("state must be open or closed")
        body["state"] = p["state"]
    if not body:
        raise GitHubError("pull-request-modify requires at least one mutation field")
    return {"number": number, "body": body}


def pr_modify_x(p, a):
    result = _pr_result(_request(a, "PATCH", f"/pulls/{p['number']}", p["body"]))
    return {"effects": {"pull_request_modified": p["number"]}, "result": result}


def tasks() -> tuple[TaskDefinition, ...]:
    return (
        TaskDefinition("github.issue-read", issue_read_v, issue_read_x),
        TaskDefinition("github.issue-create", issue_create_v, issue_create_x),
        TaskDefinition("github.issue-modify", issue_modify_v, issue_modify_x),
        TaskDefinition("github.pull-request-read", pr_read_v, pr_read_x),
        TaskDefinition("github.pull-request-create", pr_create_v, pr_create_x),
        TaskDefinition("github.pull-request-modify", pr_modify_v, pr_modify_x),
    )
