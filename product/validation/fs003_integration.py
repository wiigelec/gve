from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENTRY = ROOT / "product" / "scripts" / "gve"


def _sh(args, cwd, *, env=None, check=True):
    effective = os.environ.copy()
    effective["PYTHONDONTWRITEBYTECODE"] = "1"
    if env:
        effective.update(env)
    cp = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=effective,
    )
    if check and cp.returncode:
        raise AssertionError(f"command failed {args!r}: {cp.stderr}")
    return cp


def _oid(repo):
    return _sh(["git", "rev-parse", "HEAD"], repo).stdout.strip()


def _run_macro(repo, request_path, result_path, *, env=None):
    return _sh(
        [
            sys.executable, "-B", str(ENTRY),
            "macro", "--in", str(request_path), "--out", str(result_path),
            "--repo", str(repo),
        ],
        ROOT,
        env=env,
        check=False,
    )


def _write_request(path, parameters):
    path.write_text(
        json.dumps({
            "schema_version": 1,
            "header": {"repository": {}},
            "macro": {"name": "modify", "parameters": parameters},
        }),
        encoding="utf-8",
    )


def validate_fs003_integration() -> bool:
    with tempfile.TemporaryDirectory() as td:
        base = Path(td)
        repo = base / "repo"
        remote = base / "remote.git"
        repo.mkdir()

        _sh(["git", "init", "-b", "main"], repo)
        _sh(["git", "config", "user.name", "GVE FS003 Validator"], repo)
        _sh(["git", "config", "user.email", "fs003@example.invalid"], repo)
        _sh(["git", "init", "--bare", str(remote)], base)
        _sh(["git", "remote", "add", "origin", str(remote)], repo)

        scripts = repo / "scripts"
        scripts.mkdir()
        validate = scripts / "validate"
        validate.write_text(
            "#!/bin/sh\n"
            "set -eu\n"
            "echo validation-live-ok\n"
            "if [ \"${GVE_TEST_REMOTE_RACE:-0}\" = 1 ]; then\n"
            f"  git --git-dir={remote} update-ref refs/heads/race/live \"$GVE_TEST_RACE_OID\"\n"
            "fi\n",
            encoding="utf-8",
        )
        validate.chmod(validate.stat().st_mode | stat.S_IXUSR)

        (repo / "base.txt").write_text("base\n", encoding="utf-8")
        _sh(["git", "add", "base.txt", "scripts/validate"], repo)
        _sh(["git", "commit", "-m", "baseline"], repo)
        baseline = _oid(repo)

        request1 = base / "success-request.json"
        result1 = base / "success-result.json"
        _write_request(
            request1,
            {
                "changes": [
                    {"operation": "create", "path": "generated.txt", "content": "generated\n"}
                ],
                "commit_message": "generated",
                "expected_head": baseline,
                "branch": {"create": True, "name": "dev/live"},
                "remote_branch": "published/live",
                "validate": True,
            },
        )
        cp = _run_macro(repo, request1, result1)
        assert cp.returncode == 0, cp.stderr
        success = json.loads(result1.read_text(encoding="utf-8"))
        assert success["status"] == "success"
        projected = success["result"]
        assert projected["branch"] == "dev/live"
        assert projected["publication_branch"] == "published/live"
        assert projected["expected_head"] == baseline
        assert projected["observed_head"] == baseline
        assert projected["branch_created"] is True
        assert projected["files_changed"] == ["generated.txt"]
        assert projected["validation"] == {"requested": True, "status": "success"}
        assert "diff --git a/generated.txt b/generated.txt" in projected["diff"]
        assert projected["commit_count"] == 1
        assert projected["push_mode"] == "normal"
        assert projected["history_rewrite_or_force_push_occurred"] is False
        assert projected["merge_occurred"] is False
        assert projected["commit"] == projected["remote_head"]
        remote_success = _sh(
            ["git", "--git-dir", str(remote), "rev-parse", "refs/heads/published/live"],
            base,
        ).stdout.strip()
        assert remote_success == projected["commit"]

        transcript = cp.stdout
        for label in ("PRECHECK", "BRANCH", "MUTATE", "VALIDATE", "COMMIT", "PUBLISH", "VERIFY"):
            assert label in transcript
        assert "FS0 Script Transfer: START" in transcript
        assert "FS0 Script Transfer: PASS" in transcript
        assert "validation-live-ok" in transcript
        assert "OUT | ?? generated.txt" in transcript
        assert "Expected HEAD: " + baseline in transcript
        assert "Branch: dev/live" in transcript
        assert "Commit: " + projected["commit"] in transcript
        assert "Remote HEAD: " + projected["commit"] in transcript
        assert "Result JSON: " + str(result1) in transcript
        assert "diff --git a/generated.txt b/generated.txt" not in transcript

        mismatch_request = base / "mismatch-request.json"
        mismatch_result = base / "mismatch-result.json"
        _write_request(
            mismatch_request,
            {
                "changes": [
                    {"operation": "create", "path": "must-not-exist.txt", "content": "no\n"}
                ],
                "commit_message": "should fail",
                "expected_head": "0" * 40,
                "validate": False,
            },
        )
        cp = _run_macro(repo, mismatch_request, mismatch_result)
        assert cp.returncode == 1
        mismatch = json.loads(mismatch_result.read_text(encoding="utf-8"))
        assert mismatch["status"] == "failure"
        assert not (repo / "must-not-exist.txt").exists()
        failed = next(t for t in mismatch["tasks"] if t["status"] == "failure")
        assert failed["id"] == "modify-head"
        assert "Failed Phase: PRECHECK" in cp.stdout
        assert "Failed Task: modify-head" in cp.stdout
        assert "Reason: HEAD expectation mismatch" in cp.stdout
        assert "Prior Success:" in cp.stdout
        assert "Not Executed:" in cp.stdout
        assert "FS0 Script Transfer: FAILED" in cp.stdout

        existing_request = base / "existing-request.json"
        existing_result = base / "existing-result.json"
        current = _oid(repo)
        _write_request(
            existing_request,
            {
                "changes": [
                    {"operation": "create", "path": "existing-fail.txt", "content": "no\n"}
                ],
                "commit_message": "existing branch failure",
                "expected_head": current,
                "branch": {"create": True, "name": "dev/live"},
                "remote_branch": "existing-test/live",
                "validate": False,
            },
        )
        cp = _run_macro(repo, existing_request, existing_result)
        assert cp.returncode == 1
        existing = json.loads(existing_result.read_text(encoding="utf-8"))
        assert existing["status"] == "failure"
        assert not (repo / "existing-fail.txt").exists()
        failed = next(t for t in existing["tasks"] if t["status"] == "failure")
        assert failed["id"] == "modify-branch-create"

        _sh(
            [
                "git", "--git-dir", str(remote), "update-ref",
                "refs/heads/race/live", baseline,
            ],
            base,
        )
        existing_race_request = base / "existing-race-request.json"
        existing_race_result = base / "existing-race-result.json"
        before_existing_race = _oid(repo)
        _write_request(
            existing_race_request,
            {
                "changes": [
                    {
                        "operation": "create",
                        "path": "existing-race.txt",
                        "content": "existing race\n",
                    }
                ],
                "commit_message": "existing remote race candidate",
                "expected_head": before_existing_race,
                "remote_branch": "race/live",
                "validate": True,
            },
        )
        cp = _run_macro(
            repo,
            existing_race_request,
            existing_race_result,
            env={
                "GVE_TEST_REMOTE_RACE": "1",
                "GVE_TEST_RACE_OID": projected["commit"],
            },
        )
        assert cp.returncode == 1
        existing_raced = json.loads(
            existing_race_result.read_text(encoding="utf-8")
        )
        assert existing_raced["status"] == "failure"
        existing_race_projected = existing_raced["result"]
        assert existing_race_projected["diff"] is not None
        assert (
            "diff --git a/existing-race.txt b/existing-race.txt"
            in existing_race_projected["diff"]
        )
        assert existing_race_projected["commit"] is not None
        assert existing_race_projected["commit_count"] == 1
        assert existing_race_projected["remote_head"] is None
        failed = next(
            task for task in existing_raced["tasks"] if task["status"] == "failure"
        )
        assert failed["id"] == "modify-push"
        assert "push remote race guard mismatch" in failed["error"]["message"]
        assert "Failed Phase: PUBLISH" in cp.stdout
        assert "Failed Task: modify-push" in cp.stdout
        assert "Not Executed: modify-verify" in cp.stdout
        observed_existing_remote = _sh(
            [
                "git", "--git-dir", str(remote), "rev-parse",
                "refs/heads/race/live",
            ],
            base,
        ).stdout.strip()
        assert observed_existing_remote == projected["commit"]
        _sh(
            [
                "git", "--git-dir", str(remote), "update-ref",
                "-d", "refs/heads/race/live",
            ],
            base,
        )

        race_request = base / "race-request.json"
        race_result = base / "race-result.json"
        before_race = _oid(repo)
        _write_request(
            race_request,
            {
                "changes": [
                    {"operation": "create", "path": "race.txt", "content": "race\n"}
                ],
                "commit_message": "race candidate",
                "expected_head": before_race,
                "remote_branch": "race/live",
                "validate": True,
            },
        )
        cp = _run_macro(
            repo,
            race_request,
            race_result,
            env={
                "GVE_TEST_REMOTE_RACE": "1",
                "GVE_TEST_RACE_OID": baseline,
            },
        )
        assert cp.returncode == 1
        raced = json.loads(race_result.read_text(encoding="utf-8"))
        assert raced["status"] == "failure"
        race_projected = raced["result"]
        assert race_projected["diff"] is not None
        assert "diff --git a/race.txt b/race.txt" in race_projected["diff"]
        assert race_projected["commit"] is not None
        assert race_projected["commit_count"] == 1
        assert race_projected["remote_head"] is None
        failed = next(t for t in raced["tasks"] if t["status"] == "failure")
        assert failed["id"] == "modify-push"
        assert "push remote race guard mismatch" in failed["error"]["message"]
        assert "Failed Phase: PUBLISH" in cp.stdout
        assert "Failed Task: modify-push" in cp.stdout
        assert "Not Executed: modify-verify" in cp.stdout
        assert "diff --git a/race.txt b/race.txt" not in cp.stdout

        discover_request = base / "discover-request.json"
        discover_request.write_text(
            json.dumps({
                "schema_version": 1,
                "header": {"repository": {}},
                "macro": {"name": "discover", "parameters": {"observations": ["head"]}},
            }),
            encoding="utf-8",
        )
        bad_destination = base / "result-directory"
        bad_destination.mkdir()
        cp = _sh(
            [
                sys.executable, "-B", str(ENTRY),
                "macro", "--in", str(discover_request),
                "--out", str(bad_destination),
                "--repo", str(repo),
            ],
            ROOT,
            check=False,
        )
        assert cp.returncode == 2
        assert "FAIL result-json:" in cp.stdout
        assert "Governed Result: success" in cp.stdout
        assert "FS0 Script Transfer: FAILED" in cp.stdout

    return True
