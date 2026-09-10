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

    return True
