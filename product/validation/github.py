from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "product" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gve.authority import Authority
from gve.product_registry import product_registry
import gve.plugins.github as github_plugin


def validate_github() -> bool:
    expected = {
        "github.issue-read",
        "github.issue-create",
        "github.issue-modify",
        "github.pull-request-read",
        "github.pull-request-create",
        "github.pull-request-modify",
    }
    identities = set(product_registry().identities())
    if not expected.issubset(identities):
        raise AssertionError("GitHub registry incomplete")

    calls = []

    def fake_transport(method, path, body):
        calls.append((method, path, body))
        if path.endswith("/issues") and method == "POST":
            return {
                "number": 7, "html_url": "https://example/issue/7", "title": body["title"],
                "body": body["body"], "state": "open",
                "labels": [{"name": x} for x in body["labels"]],
            }
        if "/issues/" in path:
            number = int(path.rsplit("/", 1)[1])
            data = {
                "number": number, "html_url": f"https://example/issue/{number}",
                "title": "issue", "body": "", "state": "open", "labels": [],
            }
            if number == 99:
                data["pull_request"] = {"url": "https://api.example/pulls/99"}
            if method == "PATCH":
                data.update(body)
                data["labels"] = [{"name": x} for x in body.get("labels", [])]
            return data
        if path.endswith("/pulls") and method == "POST":
            return {
                "number": 9, "html_url": "https://example/pr/9", "title": body["title"],
                "body": body["body"], "state": "open", "draft": body["draft"],
                "base": {"ref": body["base"]}, "head": {"ref": body["head"]},
                "merged": False, "mergeable": True,
            }
        if "/pulls/" in path:
            number = int(path.rsplit("/", 1)[1])
            data = {
                "number": number, "html_url": f"https://example/pr/{number}",
                "title": "pr", "body": "", "state": "open", "draft": False,
                "base": {"ref": "main"}, "head": {"ref": "work"},
                "merged": False, "mergeable": True,
            }
            if method == "PATCH":
                if "title" in body: data["title"] = body["title"]
                if "body" in body: data["body"] = body["body"]
                if "state" in body: data["state"] = body["state"]
                if "base" in body: data["base"] = {"ref": body["base"]}
            return data
        raise AssertionError((method, path, body))

    old = github_plugin._transport
    github_plugin._transport = fake_transport
    try:
        auth = Authority.for_repository(ROOT)
        auth = Authority(repository=auth.repository, github_repository="wiigelec/gve")

        def call(name, params):
            task = product_registry().resolve(name)
            return task.execute(task.validate(params, auth), auth)

        assert call("github.issue-read", {"number": 2})["result"]["number"] == 2
        created = call("github.issue-create", {"title": "x", "labels": ["bug"]})
        assert created["result"]["number"] == 7
        assert created["effects"]["issue_created"] == 7

        modified = call("github.issue-modify", {"number": 2, "state": "closed"})
        assert modified["result"]["state"] == "closed"

        try:
            call("github.issue-read", {"number": 99})
        except Exception as exc:
            assert getattr(exc, "code", None) == "github"
        else:
            raise AssertionError("issue-read accepted pull-request object")

        before = len(calls)
        try:
            call("github.issue-modify", {"number": 99, "labels": ["blocked"]})
        except Exception as exc:
            assert getattr(exc, "code", None) == "github"
        else:
            raise AssertionError("issue-modify accepted pull-request object")
        pr_issue_calls = calls[before:]
        assert pr_issue_calls == [("GET", "/repos/wiigelec/gve/issues/99", None)]

        assert call("github.pull-request-read", {"number": 3})["result"]["base"] == "main"
        pr = call(
            "github.pull-request-create",
            {"title": "p", "base": "main", "head": "work", "draft": True},
        )
        assert pr["result"]["number"] == 9
        assert pr["result"]["draft"] is True

        changed = call(
            "github.pull-request-modify",
            {"number": 3, "title": "new", "base": "release"},
        )
        assert changed["result"]["title"] == "new"
        assert changed["result"]["base"] == "release"

        for method, path, body in calls:
            assert path.startswith("/repos/wiigelec/gve/")
            assert "http" not in path

        no_auth = Authority.for_repository(ROOT)
        task = product_registry().resolve("github.issue-read")
        try:
            task.validate({"number": 1}, no_auth)
        except Exception as exc:
            assert getattr(exc, "code", None) == "authority"
        else:
            raise AssertionError("GitHub task accepted absent repository authority")

        task = product_registry().resolve("github.issue-create")
        try:
            task.validate({"title": "x", "url": "https://evil.invalid"}, auth)
        except Exception as exc:
            assert getattr(exc, "code", None) == "github"
        else:
            raise AssertionError("GitHub task accepted generic request escape hatch")

        task = product_registry().resolve("github.pull-request-modify")
        try:
            task.validate({"number": 1, "merge": True}, auth)
        except Exception as exc:
            assert getattr(exc, "code", None) == "github"
        else:
            raise AssertionError("pull-request-modify accepted merge escape hatch")
    finally:
        github_plugin._transport = old

    return True
