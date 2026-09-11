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

        payload = base / "payload.json"
        payload.write_text(
            json.dumps({
                "schema_version": 1,
                "workflow_id": "cli",
                "tasks": [{"id": "status", "task": "git.status", "parameters": {}}],
            }),
            encoding="utf-8",
        )

        cp = _run(["execute", "--repository", str(repo), str(payload)])
        assert cp.returncode == 0, cp.stderr
        result = json.loads(cp.stdout)
        assert result["status"] == "success"
        assert result["workflow_id"] == "cli"
        assert result["tasks"][0]["task"] == "git.status"

        bad = base / "bad.json"
        bad.write_text("{", encoding="utf-8")
        cp = _run(["execute", "--repository", str(repo), str(bad)])
        assert cp.returncode == 2
        result = json.loads(cp.stdout)
        assert result["error"]["code"] == "cli-failure"

        failing = base / "failing.json"
        failing.write_text(
            json.dumps({
                "schema_version": 1,
                "workflow_id": "fail",
                "tasks": [{"id": "x", "task": "git.branch", "parameters": {"expected": "wrong"}}],
            }),
            encoding="utf-8",
        )
        cp = _run(["execute", "--repository", str(repo), str(failing)])
        assert cp.returncode == 1
        result = json.loads(cp.stdout)
        assert result["status"] == "failure"

        cp = _run([
            "execute", "--repository", str(repo),
            "--execute-max-wall-seconds", "601",
            str(payload),
        ])
        assert cp.returncode == 2
        result = json.loads(cp.stdout)
        assert result["error"]["code"] == "cli-failure"

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
        assert json.loads(cp.stdout) == ["discover"]

        cp = _run(["macro-schema", "discover"])
        assert cp.returncode == 0, cp.stderr
        schema = json.loads(cp.stdout)
        assert schema["type"] == "object"
        assert schema["additionalProperties"] is False
        assert set(schema["properties"]) == {"observations"}

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

        payload = base / "execute.json"
        payload.write_text(
            json.dumps({
                "schema_version": 1,
                "workflow_id": "unchanged",
                "tasks": [{"id": "head", "task": "git.head", "parameters": {}}],
            }),
            encoding="utf-8",
        )
        cp = _run(["execute", "--repository", str(repo), str(payload)])
        assert cp.returncode == 0
        assert json.loads(cp.stdout)["workflow_id"] == "unchanged"

    return True
