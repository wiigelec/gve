from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INSTALL = ROOT / "product" / "scripts" / "install"


def _run(args, *, cwd, env):
    return subprocess.run(
        [str(x) for x in args],
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def validate_installation() -> bool:
    if not INSTALL.is_file():
        raise AssertionError("repository install mechanism is missing")
    if not os.access(INSTALL, os.X_OK):
        raise AssertionError("repository install mechanism is not executable")

    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        home = base / "home"
        outside = base / "outside"
        repo = base / "repo"
        home.mkdir()
        outside.mkdir()
        repo.mkdir()

        env = os.environ.copy()
        env["HOME"] = str(home)

        first = _run([INSTALL], cwd=outside, env=env)
        if first.returncode != 0:
            raise AssertionError(
                f"first installation failed: stdout={first.stdout!r} stderr={first.stderr!r}"
            )

        launcher = home / ".local" / "bin" / "gve"
        if not launcher.is_symlink():
            raise AssertionError("installation did not create gve symlink")
        expected = (ROOT / "product" / "scripts" / "gve").resolve()
        if launcher.resolve() != expected:
            raise AssertionError(
                f"installed launcher points elsewhere: {launcher.resolve()} != {expected}"
            )

        second = _run([INSTALL], cwd=outside, env=env)
        if second.returncode != 0:
            raise AssertionError(
                f"repeat installation was not idempotent: "
                f"stdout={second.stdout!r} stderr={second.stderr!r}"
            )
        if launcher.resolve() != expected:
            raise AssertionError("repeat installation changed launcher target")

        env["PATH"] = str(launcher.parent) + os.pathsep + env.get("PATH", "")

        cp = _run(["gve", "macro-list"], cwd=outside, env=env)
        if cp.returncode != 0:
            raise AssertionError(f"installed macro-list failed: {cp.stderr}")
        if json.loads(cp.stdout) != ["discover", "issue", "pr", "modify"]:
            raise AssertionError(f"installed macro-list mismatch: {cp.stdout!r}")

        cp = _run(["gve", "macro-schema", "discover"], cwd=outside, env=env)
        if cp.returncode != 0:
            raise AssertionError(f"installed macro-schema failed: {cp.stderr}")
        schema = json.loads(cp.stdout)
        if schema.get("type") != "object" or schema.get("additionalProperties") is not False:
            raise AssertionError("installed discover schema mismatch")

        init = _run(["git", "init", "-b", "main"], cwd=repo, env=env)
        if init.returncode != 0:
            raise AssertionError(f"temporary repository init failed: {init.stderr}")
        (repo / "README.md").write_text("installed validation\n", encoding="utf-8")
        for args in (
            ["git", "add", "README.md"],
            [
                "git", "-c", "user.name=GVE Installer Validator",
                "-c", "user.email=validator@example.invalid",
                "commit", "-m", "baseline",
            ],
        ):
            cp = _run(args, cwd=repo, env=env)
            if cp.returncode != 0:
                raise AssertionError(f"temporary repository setup failed: {cp.stderr}")

        request = base / "request.json"
        result_path = base / "result.json"
        request.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "header": {"repository": {"branch": "main"}},
                    "macro": {
                        "name": "discover",
                        "parameters": {"observations": ["head", "status"]},
                    },
                }
            ),
            encoding="utf-8",
        )
        cp = _run(
            [
                "gve", "macro",
                "--in", request,
                "--out", result_path,
                "--repo", repo,
            ],
            cwd=outside,
            env=env,
        )
        if cp.returncode != 0:
            raise AssertionError(
                f"installed discover execution failed: stdout={cp.stdout!r} stderr={cp.stderr!r}"
            )
        result = json.loads(result_path.read_text(encoding="utf-8"))
        if result["status"] != "success" or result["macro"] != "discover":
            raise AssertionError(f"installed discover result mismatch: {result!r}")
        if [task["task"] for task in result["tasks"]] != ["git.head", "git.status"]:
            raise AssertionError("installed discover task composition mismatch")

    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        home = base / "home"
        outside = base / "outside"
        target_dir = home / ".local" / "bin"
        home.mkdir()
        outside.mkdir()
        target_dir.mkdir(parents=True)
        conflict = target_dir / "gve"
        conflict.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")

        env = os.environ.copy()
        env["HOME"] = str(home)
        cp = _run([INSTALL], cwd=outside, env=env)
        if cp.returncode == 0:
            raise AssertionError("installer overwrote or accepted conflicting launcher")
        if not conflict.is_file() or conflict.is_symlink():
            raise AssertionError("installer altered conflicting launcher")

    return True
