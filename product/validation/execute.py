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
from gve.plugins import execute as execute_plugin


def _write_script(path: Path, body: str) -> None:
    path.write_text("#!/bin/sh\nset -eu\n" + body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _call(parameters, authority):
    task = product_registry().resolve("execute.script")
    validated = task.validate(parameters, authority)
    return task.execute(validated, authority)


def validate_execute() -> bool:
    if sys.platform.startswith("linux"):
        expected = (1 << (8 * __import__("ctypes").sizeof(__import__("ctypes").c_ulong))) - 1

        def fake_ptrace(request, pid, addr, data):
            ctypes = __import__("ctypes")
            ctypes.cast(data, ctypes.POINTER(ctypes.c_ulong))[0] = expected
            return 0

        observed = execute_plugin._linux_event_pid(fake_ptrace, 123)
        assert observed == expected, "PTRACE_GETEVENTMSG buffer is not native unsigned long"

    if not (sys.platform.startswith("linux") or sys.platform == "cygwin"):
        raise AssertionError(f"unsupported execute validation host: {sys.platform}")

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
        rapid = scripts / "rapid"
        _write_script(
            rapid,
            "i=0\n"
            "while [ \"$i\" -lt 30 ]; do\n"
            "  /bin/true\n"
            "  i=$((i + 1))\n"
            "done\n",
        )

        authority = Authority(
            repository=repo,
            execute_limits=(
                ("wall_seconds", 5),
                ("max_concurrent", 8),
                ("max_total_spawned", 64),
                ("max_spawns_per_second", 64),
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
        assert result["process_backend"] in {"linux-ptrace", "cygwin-job-object"}
        assert result["timed_out"] is False
        assert result["process_limit"] is None
        assert result["termination"]["completed"] is True

        try:
            _call({"script": "../outside"}, authority)
        except Exception as exc:
            assert getattr(exc, "code", None) == "authority"
        else:
            raise AssertionError("script traversal escape accepted")

        try:
            _call({"script": "scripts/ok", "limits": {"wall_seconds": 6}}, authority)
        except Exception as exc:
            assert getattr(exc, "code", None) == "execute-limit"
        else:
            raise AssertionError("task limit widened authority")

        try:
            _call({"script": "scripts/fail"}, authority)
        except Exception as exc:
            assert getattr(exc, "code", None) == "execute-process"
            assert getattr(exc, "details", {})["exit_code"] == 7
        else:
            raise AssertionError("non-zero exit accepted")

        timeout_authority = Authority(
            repository=repo,
            execute_limits=(
                ("wall_seconds", 1),
                ("max_concurrent", 8),
                ("max_total_spawned", 64),
                ("max_spawns_per_second", 64),
            ),
        )
        try:
            _call({"script": "scripts/sleep"}, timeout_authority)
        except Exception as exc:
            details = getattr(exc, "details", {})
            assert details["timed_out"] is True
            assert details["termination"]["attempted"] is True
            assert details["termination"]["completed"] is True
        else:
            raise AssertionError("timeout not enforced")

        concurrent_authority = Authority(
            repository=repo,
            execute_limits=(
                ("wall_seconds", 5),
                ("max_concurrent", 2),
                ("max_total_spawned", 64),
                ("max_spawns_per_second", 64),
            ),
        )
        try:
            _call({"script": "scripts/fork"}, concurrent_authority)
        except Exception as exc:
            details = getattr(exc, "details", {})
            assert details["process_limit"] == "max_concurrent"
            assert details["termination"]["completed"] is True
        else:
            raise AssertionError("concurrent process limit not enforced")

        total_authority = Authority(
            repository=repo,
            execute_limits=(
                ("wall_seconds", 5),
                ("max_concurrent", 8),
                ("max_total_spawned", 10),
                ("max_spawns_per_second", 64),
            ),
        )
        try:
            _call({"script": "scripts/rapid"}, total_authority)
        except Exception as exc:
            details = getattr(exc, "details", {})
            assert details["process_limit"] == "max_total_spawned"
            assert details["processes_observed"] > 10
            assert details["termination"]["completed"] is True
        else:
            raise AssertionError("rapid total-spawn limit not enforced")

        rate_authority = Authority(
            repository=repo,
            execute_limits=(
                ("wall_seconds", 5),
                ("max_concurrent", 8),
                ("max_total_spawned", 64),
                ("max_spawns_per_second", 5),
            ),
        )
        try:
            _call({"script": "scripts/rapid"}, rate_authority)
        except Exception as exc:
            details = getattr(exc, "details", {})
            assert details["process_limit"] == "max_spawns_per_second"
            assert details["termination"]["completed"] is True
        else:
            raise AssertionError("rapid spawn-rate limit not enforced")

    return True
