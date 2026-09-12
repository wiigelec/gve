from __future__ import annotations

import json
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTRY = ROOT / "product" / "scripts" / "gve"


def _run(args):
    return subprocess.run(
        [sys.executable, "-B", str(ENTRY), *args],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def validate_cli() -> bool:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        repo = base / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, stdout=subprocess.PIPE)

        cp = _run(["execute"])
        assert cp.returncode == 2
        assert "invalid choice" in cp.stderr

    validate_macro_cli()
    return True

def validate_macro_cli() -> bool:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        repo = base / "repo"
        repo.mkdir()
        subprocess.run(
            ["git", "init", "-b", "main"],
            cwd=repo,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        (repo / "README.md").write_text("test\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
        subprocess.run(
            ["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid",
             "commit", "-m", "init"],
            cwd=repo,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        cp = _run(["macro-list"])
        assert cp.returncode == 0, cp.stderr
        assert json.loads(cp.stdout) == ["discover", "issue", "pr", "modify"]

        cp = _run(["macro-schema", "discover"])
        assert cp.returncode == 0, cp.stderr
        schema = json.loads(cp.stdout)
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
        assert set(schema["properties"]) == {"observations"}

        cp = _run(["macro-schema", "issue"])
        assert cp.returncode == 0, cp.stderr
        issue_schema = json.loads(cp.stdout)
        issue_ops = {x["properties"]["operation"]["enum"][0]: x for x in issue_schema["oneOf"]}
        assert set(issue_ops) == {"read", "create", "modify"}
        assert set(issue_ops["read"]["required"]) == {"operation", "number"}
        assert set(issue_ops["create"]["required"]) == {"operation", "title"}

        cp = _run(["macro-schema", "pr"])
        assert cp.returncode == 0, cp.stderr
        pr_schema = json.loads(cp.stdout)
        pr_ops = {x["properties"]["operation"]["enum"][0]: x for x in pr_schema["oneOf"]}
        assert set(pr_ops) == {"read", "create", "modify"}
        assert set(pr_ops["create"]["required"]) == {"operation", "title", "base", "head"}

        cp = _run(["macro-schema", "modify"])
        assert cp.returncode == 0, cp.stderr
        modify_schema = json.loads(cp.stdout)
        change_ops = {x["properties"]["operation"]["enum"][0]: x for x in modify_schema["properties"]["changes"]["items"]["oneOf"]}
        assert set(change_ops) == {"create", "modify"}
        assert "expected_sha256" not in change_ops["create"]["properties"]
        assert "expected_sha256" in change_ops["modify"]["required"]
        assert set(modify_schema["required"]) == {"changes", "commit_message", "expected_head"}
        assert modify_schema["properties"]["branch"]["required"] == ["create", "name"]

        cp = _run(["macro-schema", "unknown"])
        assert cp.returncode == 1
        assert json.loads(cp.stdout)["status"] == "failure"

        request = base / "request.json"
        result_path = base / "result.json"
        request.write_text(
            json.dumps({
                "schema_version": 1,
                "header": {"repository": {"branch": "main"}},
                "macro": {
                    "name": "discover",
                    "parameters": {"observations": ["head", "status"]},
                },
            }),
            encoding="utf-8",
        )
        cp = _run([
            "macro",
            "--in", str(request),
            "--out", str(result_path),
            "--repo", str(repo),
        ])
        assert cp.returncode == 0, cp.stderr
        result = json.loads(result_path.read_text(encoding="utf-8"))
        assert result["macro"] == "discover"
        assert result["status"] == "success"
        assert [task["task"] for task in result["tasks"]] == ["git.head", "git.status"]
        assert [stage["label"] for stage in result["stages"]] == ["DISCOVER"]
        assert "GVE discover: START" in cp.stdout
        assert "===== CONTEXT =====" in cp.stdout
        assert "Operation: discover" in cp.stdout
        assert "Repository: " + str(repo.resolve()) in cp.stdout
        assert "Branch: main" in cp.stdout
        assert "[01/01] DISCOVER governed phase" in cp.stdout
        assert "$ git -C " in cp.stdout
        assert "===== REPO DISCOVERY =====" in cp.stdout
        assert "HEAD: " in cp.stdout
        assert "Worktree: clean" in cp.stdout
        assert "===== FINAL =====" in cp.stdout
        assert "Observed HEAD: " in cp.stdout
        assert "Status: clean" in cp.stdout
        assert "GVE discover: PASS" in cp.stdout
        assert f"Result JSON: {result_path}" in cp.stdout

        bad_request = base / "bad-request.json"
        bad_result = base / "bad-result.json"
        bad_request.write_text(
            json.dumps({
                "schema_version": 1,
                "header": {"repository": {"branch": "wrong"}},
                "macro": {"name": "discover", "parameters": {}},
            }),
            encoding="utf-8",
        )
        cp = _run([
            "macro",
            "--in", str(bad_request),
            "--out", str(bad_result),
            "--repo", str(repo),
        ])
        assert cp.returncode == 1
        bad = json.loads(bad_result.read_text(encoding="utf-8"))
        assert bad["status"] == "failure"
        assert bad["error"]["code"] == "invalid-payload"


        modify_request = base / "modify-request.json"
        modify_result = base / "modify-result.json"
        modify_request.write_text(
            json.dumps({
                "schema_version": 1,
                "header": {"repository": {}},
                "macro": {
                    "name": "modify",
                    "parameters": {
                        "changes": [
                            {"operation": "create", "path": "generated.txt", "content": "x\n"}
                        ],
                        "commit_message": "generated",
                        "expected_head": subprocess.run(
                            ["git", "rev-parse", "HEAD"],
                            cwd=repo, text=True, stdout=subprocess.PIPE, check=True,
                        ).stdout.strip(),
                        "validate": False,
                    },
                },
            }),
            encoding="utf-8",
        )
        cp = _run([
            "macro", "--in", str(modify_request), "--out", str(modify_result),
            "--repo", str(repo),
        ])
        assert cp.returncode == 1
        failed_modify = json.loads(modify_result.read_text(encoding="utf-8"))
        assert failed_modify["status"] == "failure"
        assert "GVE modify: START" in cp.stdout
        assert "GVE modify: FAILED" in cp.stdout
        assert "Failed Task:" in cp.stdout
        assert "Reason:" in cp.stdout
        failed_task = next(
            task for task in failed_modify["tasks"] if task["status"] == "failure"
        )
        assert "authorized Git remote is not configured" in failed_task["error"]["message"]
        assert not (repo / "generated.txt").exists()

        issue_request = base / "issue-request.json"
        issue_result = base / "issue-result.json"
        issue_request.write_text(
            json.dumps({
                "schema_version": 1,
                "header": {"repository": {}},
                "macro": {
                    "name": "issue",
                    "parameters": {"operation": "read", "number": 1},
                },
            }),
            encoding="utf-8",
        )
        cp = _run([
            "macro",
            "--in", str(issue_request),
            "--out", str(issue_result),
            "--repo", str(repo),
        ])
        assert cp.returncode == 1
        failed_issue = json.loads(issue_result.read_text(encoding="utf-8"))
        assert failed_issue["status"] == "failure"
        assert "supported repository origin identity" in failed_issue["error"]["message"]

    return True
