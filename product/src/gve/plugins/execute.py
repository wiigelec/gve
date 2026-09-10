from __future__ import annotations

import os
import signal
import subprocess
import tempfile
import time
from collections import deque
from pathlib import Path
from typing import Any

from ..authority import Authority
from ..errors import GVEError
from ..registry import TaskDefinition

HARD_LIMITS = {
    "wall_seconds": 600,
    "max_concurrent": 32,
    "max_total_spawned": 1024,
    "max_spawns_per_second": 64,
}


class ExecuteError(GVEError):
    code = "execute"


class ExecuteAuthorityError(GVEError):
    code = "authority"


class ExecuteLimitError(GVEError):
    code = "execute-limit"


class ExecuteProcessError(GVEError):
    code = "execute-process"


def _fields(p: dict[str, Any], allowed: set[str], required: set[str]) -> None:
    unknown = set(p) - allowed
    missing = required - set(p)
    if unknown or missing:
        raise ExecuteError(
            "invalid execute.script parameters",
            details={"unknown": sorted(unknown), "missing": sorted(missing)},
        )


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ExecuteLimitError(f"{field} must be a positive integer")
    return value


def _repo(authority: Authority) -> Path:
    root = authority.repository.resolve()
    if not root.is_dir():
        raise ExecuteAuthorityError("authorized repository root is unavailable")
    return root


def _repo_relative(authority: Authority, value: Any, field: str) -> tuple[str, Path]:
    if not isinstance(value, str) or not value:
        raise ExecuteError(f"{field} must be a non-empty string")
    normalized = value.replace("\\", "/")
    raw = Path(normalized)
    if raw.is_absolute():
        raise ExecuteAuthorityError(f"{field} must be repository-relative")
    root = _repo(authority)
    resolved = (root / normalized).resolve(strict=False)
    try:
        resolved.relative_to(root)
    except ValueError:
        raise ExecuteAuthorityError(
            f"{field} escapes authorized repository",
            details={field: normalized},
        )
    return normalized, resolved


def _authority_limits(authority: Authority) -> dict[str, int]:
    supplied = authority.execute_limit_map()
    unknown = set(supplied) - set(HARD_LIMITS)
    if unknown:
        raise ExecuteLimitError(
            "active execute authority contains unknown limits",
            details={"unknown": sorted(unknown)},
        )
    result = dict(HARD_LIMITS)
    for key, value in supplied.items():
        value = _positive_int(value, key)
        if value > HARD_LIMITS[key]:
            raise ExecuteLimitError(
                "active execute authority exceeds product hard ceiling",
                details={"limit": key, "value": value, "ceiling": HARD_LIMITS[key]},
            )
        result[key] = value
    return result


def _effective_limits(authority: Authority, requested: Any) -> dict[str, int]:
    maximum = _authority_limits(authority)
    if requested is None:
        return maximum
    if not isinstance(requested, dict):
        raise ExecuteLimitError("limits must be an object")
    unknown = set(requested) - set(HARD_LIMITS)
    if unknown:
        raise ExecuteLimitError(
            "limits contain unknown keys",
            details={"unknown": sorted(unknown)},
        )
    effective = dict(maximum)
    for key, value in requested.items():
        value = _positive_int(value, key)
        if value > maximum[key]:
            raise ExecuteLimitError(
                "task execute limit may not exceed active authority",
                details={"limit": key, "requested": value, "authority_maximum": maximum[key]},
            )
        effective[key] = value
    return effective


def validate_script(parameters: dict[str, Any], authority: Authority) -> dict[str, Any]:
    _fields(parameters, {"script", "args", "working_directory", "limits"}, {"script"})

    script_name, script_path = _repo_relative(authority, parameters["script"], "script")
    if not script_path.is_file():
        raise ExecuteError("script must resolve to an existing regular file")

    args = parameters.get("args", [])
    if not isinstance(args, list) or any(not isinstance(x, str) for x in args):
        raise ExecuteError("args must be an array of strings")

    working_name, working_path = _repo_relative(
        authority, parameters.get("working_directory", "."), "working_directory"
    )
    if not working_path.is_dir():
        raise ExecuteError("working_directory must resolve to an existing directory")

    limits = _effective_limits(authority, parameters.get("limits"))
    return {
        "script": script_name,
        "script_path": str(script_path),
        "args": list(args),
        "working_directory": working_name,
        "working_path": str(working_path),
        "limits": limits,
    }


def _linux_process_table() -> dict[int, int]:
    table: dict[int, int] = {}
    proc = Path("/proc")
    if not proc.is_dir():
        raise ExecuteProcessError("execute process-tree accounting requires Linux /proc")
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            stat = (entry / "stat").read_text(encoding="utf-8")
            close = stat.rfind(")")
            rest = stat[close + 2 :].split()
            ppid = int(rest[1])
            table[int(entry.name)] = ppid
        except (OSError, ValueError, IndexError):
            continue
    return table


def _discover_governed(root_pid: int, known: set[int]) -> set[int]:
    table = _linux_process_table()
    governed = set(known)
    governed.add(root_pid)
    changed = True
    while changed:
        changed = False
        for pid, ppid in table.items():
            if pid not in governed and ppid in governed:
                governed.add(pid)
                changed = True
    return {pid for pid in governed if pid in table}


def _terminate_tree(process: subprocess.Popen[bytes], tracked: set[int]) -> dict[str, Any]:
    attempted = True
    errors: list[str] = []

    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    except OSError as exc:
        errors.append(f"SIGTERM process-group: {exc}")

    deadline = time.monotonic() + 1.0
    while time.monotonic() < deadline:
        alive = _discover_governed(process.pid, tracked)
        if not alive:
            break
        time.sleep(0.02)

    alive = _discover_governed(process.pid, tracked)
    for pid in sorted(alive, reverse=True):
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except OSError as exc:
            errors.append(f"SIGKILL pid {pid}: {exc}")

    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except OSError as exc:
        errors.append(f"SIGKILL process-group: {exc}")

    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        errors.append("root process did not exit after termination")

    remaining = _discover_governed(process.pid, tracked)
    completed = not remaining and process.poll() is not None and not errors
    return {
        "attempted": attempted,
        "completed": completed,
        "remaining_pids": sorted(remaining),
        "errors": errors,
    }


def execute_script(parameters: dict[str, Any], authority: Authority) -> dict[str, Any]:
    limits = parameters["limits"]
    script_path = parameters["script_path"]
    working_path = parameters["working_path"]

    with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
        try:
            process = subprocess.Popen(
                [script_path, *parameters["args"]],
                cwd=working_path,
                stdin=subprocess.DEVNULL,
                stdout=stdout_file,
                stderr=stderr_file,
                start_new_session=True,
            )
        except OSError as exc:
            raise ExecuteProcessError(
                "failed to start repository script",
                details={"error": str(exc)},
            ) from exc

        start = time.monotonic()
        tracked: set[int] = {process.pid}
        seen: set[int] = {process.pid}
        spawn_times: deque[float] = deque([start])
        violation: str | None = None
        timed_out = False
        termination = {
            "attempted": False,
            "completed": True,
            "remaining_pids": [],
            "errors": [],
        }

        while process.poll() is None:
            now = time.monotonic()
            governed = _discover_governed(process.pid, tracked)
            new = governed - seen
            for pid in new:
                seen.add(pid)
                spawn_times.append(now)
            tracked |= governed

            while spawn_times and now - spawn_times[0] > 1.0:
                spawn_times.popleft()

            if now - start > limits["wall_seconds"]:
                timed_out = True
                violation = "wall_seconds"
            elif len(governed) > limits["max_concurrent"]:
                violation = "max_concurrent"
            elif len(seen) > limits["max_total_spawned"]:
                violation = "max_total_spawned"
            elif len(spawn_times) > limits["max_spawns_per_second"]:
                violation = "max_spawns_per_second"

            if violation is not None:
                termination = _terminate_tree(process, tracked)
                break
            time.sleep(0.02)

        if process.poll() is None:
            termination = _terminate_tree(process, tracked)

        try:
            exit_code = process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            exit_code = None
            if not termination["attempted"]:
                termination = _terminate_tree(process, tracked)

        stdout_file.seek(0)
        stderr_file.seek(0)
        stdout = stdout_file.read().decode("utf-8", errors="replace")
        stderr = stderr_file.read().decode("utf-8", errors="replace")

    result = {
        "script": parameters["script"],
        "working_directory": parameters["working_directory"],
        "args": parameters["args"],
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "effective_limits": dict(limits),
        "timed_out": timed_out,
        "process_limit": violation if violation != "wall_seconds" else None,
        "termination": termination,
        "processes_observed": len(seen),
    }

    if violation is not None:
        if not termination["completed"]:
            raise ExecuteProcessError(
                "required process-tree termination could not be completed",
                details=result,
            )
        raise ExecuteProcessError(
            "execute resource limit exceeded",
            details=result,
        )

    if not termination["completed"]:
        raise ExecuteProcessError(
            "required process-tree termination could not be completed",
            details=result,
        )

    if exit_code != 0:
        raise ExecuteProcessError(
            "repository script returned non-zero exit status",
            details=result,
        )

    return {
        "observations": {
            "script": parameters["script"],
            "working_directory": parameters["working_directory"],
        },
        "result": result,
    }


def tasks() -> tuple[TaskDefinition, ...]:
    return (TaskDefinition("execute.script", validate_script, execute_script),)
