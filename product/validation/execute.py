from __future__ import annotations

import os
import stat
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "product" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gve.authority import Authority
from gve.product_registry import product_registry


def _write_script(path: Path, body: str) -> None:
    path.write_text("#!/bin/sh\nset -eu\n" + body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _call(parameters, authority):
    task = product_registry().resolve("execute.script")
    validated = task.validate(parameters, authority)
    return task.execute(validated, authority)


def validate_execute() -> bool:
    identities = set(product_registry().identities())
    if "execute.script" not in identities:
        raise AssertionError("execute.script is not registered")

    with tempfile.TemporaryDirectory() as td:
        repo = Path(td).resolve()
        scripts = repo / "scripts"
        scripts.mkdir()

        ok = scripts / "ok"
        _write_script(ok, 'printf "out:%s" "$1"\nprintf "err" >&2\n')
        fail = scripts / "fail"
        _write_script(fail, "exit 7\n")
        sleeper = scripts / "sleep"
        _write_script(sleeper, "sleep 5\n")
        fork = scripts / "fork"
        _write_script(fork, "sleep 2 &\nsleep 2 &\nwait\n")

        authority = Authority(
            repository=repo,
            execute_limits=(
                ("wall_seconds", 5),
                ("max_concurrent", 8),
                ("max_total_spawned", 32),
                ("max_spawns_per_second", 16),
            ),
        )

        result = _call(
            {
                "script": "scripts/ok",
                "args": ["hello"],
                "limits": {
                    "wall_seconds": 2,
                    "max_concurrent": 4,
                    "max_total_spawned": 8,
                    "max_spawns_per_second": 8,
                },
            },
            authority,
        )["result"]
        assert result["exit_code"] == 0
        assert result["stdout"] == "out:hello"
        assert result["stderr"] == "err"
        assert result["effective_limits"]["wall_seconds"] == 2
        assert result["effective_limits"]["max_concurrent"] == 4
        assert result["timed_out"] is False
        assert result["process_limit"] is None
        assert result["termination"]["completed"] is True

        try:
            _call({"script": "../outside"}, authority)
        except Exception as exc:
            assert getattr(exc, "code", None) == "authority"
        else:
            raise AssertionError("script traversal escape accepted")

        outside = repo.parent / f"{repo.name}-outside"
        _write_script(outside, "exit 0\n")
        try:
            os.symlink(outside, scripts / "escape")
            try:
                _call({"script": "scripts/escape"}, authority)
            except Exception as exc:
                assert getattr(exc, "code", None) == "authority"
            else:
                raise AssertionError("script symlink escape accepted")
        finally:
            outside.unlink(missing_ok=True)

        try:
            _call({"script": "scripts/ok", "args": "hello"}, authority)
        except Exception as exc:
            assert getattr(exc, "code", None) == "execute"
        else:
            raise AssertionError("raw/unstructured args accepted")

        try:
            _call({"script": "scripts/ok", "limits": {"wall_seconds": 6}}, authority)
        except Exception as exc:
            assert getattr(exc, "code", None) == "execute-limit"
        else:
            raise AssertionError("task limit widened authority")

        too_wide = Authority(
            repository=repo,
            execute_limits=(("wall_seconds", 601),),
        )
        try:
            _call({"script": "scripts/ok"}, too_wide)
        except Exception as exc:
            assert getattr(exc, "code", None) == "execute-limit"
        else:
            raise AssertionError("authority above product ceiling accepted")

        try:
            _call({"script": "scripts/fail"}, authority)
        except Exception as exc:
            assert getattr(exc, "code", None) == "execute-process"
            details = getattr(exc, "details", {})
            assert details["exit_code"] == 7
        else:
            raise AssertionError("non-zero script exit accepted")

        timeout_authority = Authority(
            repository=repo,
            execute_limits=(
                ("wall_seconds", 1),
                ("max_concurrent", 8),
                ("max_total_spawned", 32),
                ("max_spawns_per_second", 16),
            ),
        )
        try:
            _call({"script": "scripts/sleep"}, timeout_authority)
        except Exception as exc:
            assert getattr(exc, "code", None) == "execute-process"
            details = getattr(exc, "details", {})
            assert details["timed_out"] is True
            assert details["termination"]["attempted"] is True
            assert details["termination"]["completed"] is True
        else:
            raise AssertionError("timeout was not enforced")

        count_authority = Authority(
            repository=repo,
            execute_limits=(
                ("wall_seconds", 5),
                ("max_concurrent", 2),
                ("max_total_spawned", 32),
                ("max_spawns_per_second", 16),
            ),
        )
        try:
            _call({"script": "scripts/fork"}, count_authority)
        except Exception as exc:
            assert getattr(exc, "code", None) == "execute-process"
            details = getattr(exc, "details", {})
            assert details["process_limit"] == "max_concurrent"
            assert details["termination"]["attempted"] is True
            assert details["termination"]["completed"] is True
        else:
            raise AssertionError("concurrent process limit was not enforced")

    return True
