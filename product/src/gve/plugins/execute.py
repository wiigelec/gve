from __future__ import annotations

import ctypes
import ctypes.util
import errno
import os
import signal
import subprocess
import sys
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


def _result(parameters: dict[str, Any], *, exit_code: int | None, stdout: str,
            stderr: str, timed_out: bool, process_limit: str | None,
            termination: dict[str, Any], processes_observed: int,
            backend: str) -> dict[str, Any]:
    return {
        "script": parameters["script"],
        "working_directory": parameters["working_directory"],
        "args": parameters["args"],
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
        "effective_limits": dict(parameters["limits"]),
        "timed_out": timed_out,
        "process_limit": process_limit,
        "termination": termination,
        "processes_observed": processes_observed,
        "process_backend": backend,
    }


def _finish(parameters: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    if result["timed_out"] or result["process_limit"] is not None:
        if not result["termination"]["completed"]:
            raise ExecuteProcessError(
                "required process-tree termination could not be completed",
                details=result,
            )
        raise ExecuteProcessError("execute resource limit exceeded", details=result)

    if not result["termination"]["completed"]:
        raise ExecuteProcessError(
            "required process-tree termination could not be completed",
            details=result,
        )

    if result["exit_code"] != 0:
        raise ExecuteProcessError(
            "repository script returned non-zero exit status",
            details=result,
        )

    return {
        "observations": {
            "script": parameters["script"],
            "working_directory": parameters["working_directory"],
            "process_backend": result["process_backend"],
        },
        "result": result,
    }


# ---------------------------------------------------------------------------
# Linux backend: ptrace process-creation events.
# ---------------------------------------------------------------------------

PTRACE_TRACEME = 0
PTRACE_CONT = 7
PTRACE_SETOPTIONS = 0x4200
PTRACE_GETEVENTMSG = 0x4201
PTRACE_O_TRACEFORK = 0x00000002
PTRACE_O_TRACEVFORK = 0x00000004
PTRACE_O_TRACECLONE = 0x00000008
PTRACE_O_EXITKILL = 0x00100000
PTRACE_EVENT_FORK = 1
PTRACE_EVENT_VFORK = 2
PTRACE_EVENT_CLONE = 3
WAIT_WALL = 0x40000000


def _linux_ptrace_function():
    candidates: list[str | None] = []
    found = ctypes.util.find_library("c")
    if found:
        candidates.append(found)
    candidates.extend(["libc.so.6", "libc.so", None])

    tried: list[str] = []
    for candidate in candidates:
        label = candidate if candidate is not None else "<process>"
        if label in tried:
            continue
        tried.append(label)
        try:
            library = ctypes.CDLL(candidate, use_errno=True)
            function = getattr(library, "ptrace")
        except (OSError, AttributeError):
            continue
        function.restype = ctypes.c_long
        return function

    raise ExecuteProcessError(
        "Linux process-tracing backend is unavailable",
        details={"libraries_tried": tried},
    )


def _linux_ptrace_call(function, request: int, pid: int,
                       addr: int = 0, data: int | ctypes.c_void_p = 0) -> int:
    ctypes.set_errno(0)
    data_value = data if isinstance(data, ctypes.c_void_p) else ctypes.c_void_p(data)
    value = function(
        ctypes.c_ulong(request),
        ctypes.c_ulong(pid),
        ctypes.c_void_p(addr),
        data_value,
    )
    if value == -1:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))
    return int(value)


def _linux_child_setup(function) -> None:
    os.setsid()
    try:
        _linux_ptrace_call(function, PTRACE_TRACEME, 0)
    except OSError:
        os._exit(126)


def _linux_continue(function, pid: int, sig: int = 0) -> None:
    try:
        _linux_ptrace_call(function, PTRACE_CONT, pid, 0, sig)
    except OSError as exc:
        if exc.errno != errno.ESRCH:
            raise


def _linux_event_pid(function, pid: int) -> int:
    message = ctypes.c_uint32()
    pointer = ctypes.cast(ctypes.pointer(message), ctypes.c_void_p)
    _linux_ptrace_call(function, PTRACE_GETEVENTMSG, pid, 0, pointer)
    return int(message.value)


def _wait_exit_code(status: int) -> int | None:
    if os.WIFEXITED(status):
        return os.WEXITSTATUS(status)
    if os.WIFSIGNALED(status):
        return -os.WTERMSIG(status)
    return None


def _linux_terminate(function, root_pid: int, active: set[int]) -> dict[str, Any]:
    errors: list[str] = []
    for pid in sorted(active, reverse=True):
        try:
            os.kill(pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except OSError as exc:
            errors.append(f"SIGKILL pid {pid}: {exc}")

    try:
        os.killpg(root_pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    except OSError as exc:
        errors.append(f"SIGKILL process-group: {exc}")

    remaining = set(active)
    deadline = time.monotonic() + 2.0
    while remaining and time.monotonic() < deadline:
        try:
            pid, status = os.waitpid(-1, os.WNOHANG | WAIT_WALL)
        except ChildProcessError:
            remaining.clear()
            break
        if pid == 0:
            time.sleep(0.005)
            continue
        if os.WIFEXITED(status) or os.WIFSIGNALED(status):
            remaining.discard(pid)
        elif os.WIFSTOPPED(status):
            try:
                _linux_continue(function, pid, signal.SIGKILL)
            except OSError as exc:
                errors.append(f"continue-kill pid {pid}: {exc}")

    return {
        "attempted": True,
        "completed": not remaining and not errors,
        "remaining_pids": sorted(remaining),
        "errors": errors,
    }


def _execute_linux(parameters: dict[str, Any]) -> dict[str, Any]:
    function = _linux_ptrace_function()
    limits = parameters["limits"]

    with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
        try:
            process = subprocess.Popen(
                [parameters["script_path"], *parameters["args"]],
                cwd=parameters["working_path"],
                stdin=subprocess.DEVNULL,
                stdout=stdout_file,
                stderr=stderr_file,
                preexec_fn=lambda: _linux_child_setup(function),
            )
        except OSError as exc:
            raise ExecuteProcessError(
                "failed to start repository script",
                details={"error": str(exc)},
            ) from exc

        root_pid = process.pid
        start = time.monotonic()
        active: set[int] = set()
        seen: set[int] = {root_pid}
        spawn_times: deque[float] = deque([start])
        root_exit_code: int | None = None
        timed_out = False
        process_limit: str | None = None
        termination = {
            "attempted": False,
            "completed": True,
            "remaining_pids": [],
            "errors": [],
        }

        try:
            pid, status = os.waitpid(root_pid, WAIT_WALL)
            if pid != root_pid or not os.WIFSTOPPED(status):
                raise ExecuteProcessError("repository script did not enter traced execution")

            active.add(root_pid)
            _linux_ptrace_call(function, PTRACE_SETOPTIONS, root_pid, 0,
                               PTRACE_O_TRACEFORK | PTRACE_O_TRACEVFORK |
                               PTRACE_O_TRACECLONE | PTRACE_O_EXITKILL)
            _linux_continue(function, root_pid)

            while active:
                now = time.monotonic()
                if now - start > limits["wall_seconds"]:
                    timed_out = True
                    termination = _linux_terminate(function, root_pid, active)
                    active.clear()
                    break

                try:
                    pid, status = os.waitpid(-1, os.WNOHANG | WAIT_WALL)
                except ChildProcessError:
                    active.clear()
                    break

                if pid == 0:
                    time.sleep(0.002)
                    continue

                if os.WIFEXITED(status) or os.WIFSIGNALED(status):
                    active.discard(pid)
                    if pid == root_pid:
                        root_exit_code = _wait_exit_code(status)
                    continue

                if not os.WIFSTOPPED(status):
                    continue

                event = status >> 16
                stop_signal = os.WSTOPSIG(status)

                if event in (PTRACE_EVENT_FORK, PTRACE_EVENT_VFORK, PTRACE_EVENT_CLONE):
                    child = _linux_event_pid(function, pid)
                    event_time = time.monotonic()
                    if child not in seen:
                        seen.add(child)
                        active.add(child)
                        spawn_times.append(event_time)

                    while spawn_times and event_time - spawn_times[0] > 1.0:
                        spawn_times.popleft()

                    if len(active) > limits["max_concurrent"]:
                        process_limit = "max_concurrent"
                    elif len(seen) > limits["max_total_spawned"]:
                        process_limit = "max_total_spawned"
                    elif len(spawn_times) > limits["max_spawns_per_second"]:
                        process_limit = "max_spawns_per_second"

                    if process_limit is not None:
                        termination = _linux_terminate(function, root_pid, active)
                        active.clear()
                        break

                    _linux_continue(function, pid)
                    continue

                if pid != root_pid:
                    try:
                        _linux_ptrace_call(
                            function, PTRACE_SETOPTIONS, pid, 0,
                            PTRACE_O_TRACEFORK | PTRACE_O_TRACEVFORK |
                            PTRACE_O_TRACECLONE | PTRACE_O_EXITKILL,
                        )
                    except OSError as exc:
                        if exc.errno != errno.ESRCH:
                            raise
                    active.add(pid)

                if stop_signal in (signal.SIGTRAP, signal.SIGSTOP):
                    _linux_continue(function, pid)
                else:
                    _linux_continue(function, pid, stop_signal)

        except ExecuteProcessError:
            if active:
                termination = _linux_terminate(function, root_pid, active)
            raise
        except OSError as exc:
            if active:
                termination = _linux_terminate(function, root_pid, active)
            raise ExecuteProcessError(
                "Linux process tracing failed",
                details={"error": str(exc), "termination": termination},
            ) from exc

        process.returncode = root_exit_code

        stdout_file.seek(0)
        stderr_file.seek(0)
        stdout = stdout_file.read().decode("utf-8", errors="replace")
        stderr = stderr_file.read().decode("utf-8", errors="replace")

    return _result(
        parameters,
        exit_code=root_exit_code,
        stdout=stdout,
        stderr=stderr,
        timed_out=timed_out,
        process_limit=process_limit,
        termination=termination,
        processes_observed=len(seen),
        backend="linux-ptrace",
    )


# ---------------------------------------------------------------------------
# Cygwin backend: Cygwin fork/exec + native Windows Job Object supervision.
# ---------------------------------------------------------------------------

JOB_OBJECT_LIMIT_ACTIVE_PROCESS = 0x00000008
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JOB_OBJECT_MSG_ACTIVE_PROCESS_ZERO = 4
JOB_OBJECT_MSG_ACTIVE_PROCESS_LIMIT = 3
JOB_OBJECT_MSG_NEW_PROCESS = 6
JOB_OBJECT_MSG_EXIT_PROCESS = 7
JOB_OBJECT_EXTENDED_LIMIT_INFORMATION = 9
JOB_OBJECT_ASSOCIATE_COMPLETION_PORT_INFORMATION = 7
PROCESS_TERMINATE = 0x0001
PROCESS_SET_QUOTA = 0x0100
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
INFINITE = 0xFFFFFFFF


class _IoCounters(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_uint64),
        ("WriteOperationCount", ctypes.c_uint64),
        ("OtherOperationCount", ctypes.c_uint64),
        ("ReadTransferCount", ctypes.c_uint64),
        ("WriteTransferCount", ctypes.c_uint64),
        ("OtherTransferCount", ctypes.c_uint64),
    ]


class _BasicLimitInformation(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_int64),
        ("PerJobUserTimeLimit", ctypes.c_int64),
        ("LimitFlags", ctypes.c_uint32),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", ctypes.c_uint32),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", ctypes.c_uint32),
        ("SchedulingClass", ctypes.c_uint32),
    ]


class _ExtendedLimitInformation(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _BasicLimitInformation),
        ("IoInfo", _IoCounters),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


class _AssociateCompletionPort(ctypes.Structure):
    _fields_ = [
        ("CompletionKey", ctypes.c_void_p),
        ("CompletionPort", ctypes.c_void_p),
    ]


class _CygwinJob:
    def __init__(self, max_concurrent: int):
        try:
            self.kernel32 = ctypes.CDLL("kernel32.dll")
        except OSError as exc:
            raise ExecuteProcessError(
                "Cygwin Windows process-control backend is unavailable",
                details={"error": str(exc)},
            ) from exc

        k = self.kernel32
        k.CreateJobObjectW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
        k.CreateJobObjectW.restype = ctypes.c_void_p
        k.CreateIoCompletionPort.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint32
        ]
        k.CreateIoCompletionPort.restype = ctypes.c_void_p
        k.SetInformationJobObject.argtypes = [
            ctypes.c_void_p, ctypes.c_int32, ctypes.c_void_p, ctypes.c_uint32
        ]
        k.SetInformationJobObject.restype = ctypes.c_int
        k.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        k.AssignProcessToJobObject.restype = ctypes.c_int
        k.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int32, ctypes.c_uint32]
        k.OpenProcess.restype = ctypes.c_void_p
        k.TerminateJobObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        k.TerminateJobObject.restype = ctypes.c_int
        k.CloseHandle.argtypes = [ctypes.c_void_p]
        k.CloseHandle.restype = ctypes.c_int
        k.GetQueuedCompletionStatus.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_uint32),
            ctypes.POINTER(ctypes.c_size_t),
            ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_uint32,
        ]
        k.GetQueuedCompletionStatus.restype = ctypes.c_int

        invalid_handle = ctypes.c_void_p(-1).value
        self.port = k.CreateIoCompletionPort(
            ctypes.c_void_p(invalid_handle), None, 0, 1
        )
        if not self.port:
            raise ExecuteProcessError("failed to create Cygwin job completion port")

        self.job = k.CreateJobObjectW(None, None)
        if not self.job:
            k.CloseHandle(self.port)
            raise ExecuteProcessError("failed to create Cygwin Job Object")

        association = _AssociateCompletionPort(
            CompletionKey=ctypes.c_void_p(1),
            CompletionPort=self.port,
        )
        if not k.SetInformationJobObject(
            self.job,
            JOB_OBJECT_ASSOCIATE_COMPLETION_PORT_INFORMATION,
            ctypes.byref(association),
            ctypes.sizeof(association),
        ):
            self.close()
            raise ExecuteProcessError("failed to associate Cygwin Job Object completion port")

        limits = _ExtendedLimitInformation()
        # Cygwin is LP64 while Win32 remains LLP64; Windows DWORD/ULONG
        # fields therefore require explicit 32-bit ctypes declarations.
        if ctypes.sizeof(ctypes.c_uint32) != 4 or ctypes.sizeof(ctypes.c_uint64) != 8:
            self.close()
            raise ExecuteProcessError("unexpected Windows ABI integer widths")
        limits.BasicLimitInformation.LimitFlags = (
            JOB_OBJECT_LIMIT_ACTIVE_PROCESS | JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        )
        limits.BasicLimitInformation.ActiveProcessLimit = max_concurrent
        if not k.SetInformationJobObject(
            self.job,
            JOB_OBJECT_EXTENDED_LIMIT_INFORMATION,
            ctypes.byref(limits),
            ctypes.sizeof(limits),
        ):
            self.close()
            raise ExecuteProcessError("failed to establish Cygwin Job Object limits")

    def assign_cygwin_pid(self, cygwin_pid: int) -> int:
        winpid_path = Path(f"/proc/{cygwin_pid}/winpid")
        try:
            winpid = int(winpid_path.read_text(encoding="ascii").strip())
        except (OSError, ValueError) as exc:
            raise ExecuteProcessError(
                "cannot resolve Cygwin process to Windows process identity",
                details={"pid": cygwin_pid, "error": str(exc)},
            ) from exc

        access = PROCESS_TERMINATE | PROCESS_SET_QUOTA | PROCESS_QUERY_LIMITED_INFORMATION
        handle = self.kernel32.OpenProcess(access, 0, winpid)
        if not handle:
            raise ExecuteProcessError(
                "cannot open Cygwin process for Job Object assignment",
                details={"pid": cygwin_pid, "winpid": winpid},
            )
        try:
            if not self.kernel32.AssignProcessToJobObject(self.job, handle):
                raise ExecuteProcessError(
                    "cannot assign Cygwin process to Job Object",
                    details={"pid": cygwin_pid, "winpid": winpid},
                )
        finally:
            self.kernel32.CloseHandle(handle)
        return winpid

    def event(self) -> tuple[int, int] | None:
        message = ctypes.c_uint32()
        key = ctypes.c_size_t()
        overlapped = ctypes.c_void_p()
        ok = self.kernel32.GetQueuedCompletionStatus(
            self.port,
            ctypes.byref(message),
            ctypes.byref(key),
            ctypes.byref(overlapped),
            0,
        )
        if not ok:
            return None
        pid = int(overlapped.value or 0)
        return int(message.value), pid

    def terminate(self) -> dict[str, Any]:
        errors: list[str] = []
        if not self.kernel32.TerminateJobObject(self.job, 1):
            errors.append("TerminateJobObject failed")
        return {
            "attempted": True,
            "completed": not errors,
            "remaining_pids": [],
            "errors": errors,
        }

    def close(self) -> None:
        if getattr(self, "job", None):
            self.kernel32.CloseHandle(self.job)
            self.job = None
        if getattr(self, "port", None):
            self.kernel32.CloseHandle(self.port)
            self.port = None


def _cygwin_child_exec(parameters: dict[str, Any], stdout_fd: int, stderr_fd: int) -> None:
    try:
        os.setsid()
        os.chdir(parameters["working_path"])
        os.kill(os.getpid(), signal.SIGSTOP)
        devnull = os.open("/dev/null", os.O_RDONLY)
        os.dup2(devnull, 0)
        os.close(devnull)
        os.dup2(stdout_fd, 1)
        os.dup2(stderr_fd, 2)
        os.execv(
            parameters["script_path"],
            [parameters["script_path"], *parameters["args"]],
        )
    except BaseException:
        os._exit(126)


def _execute_cygwin(parameters: dict[str, Any]) -> dict[str, Any]:
    limits = parameters["limits"]
    job = _CygwinJob(limits["max_concurrent"])

    with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
        try:
            pid = os.fork()
        except OSError as exc:
            job.close()
            raise ExecuteProcessError(
                "failed to create stopped Cygwin execution process",
                details={"error": str(exc)},
            ) from exc

        if pid == 0:
            _cygwin_child_exec(parameters, stdout_file.fileno(), stderr_file.fileno())
            os._exit(126)

        start = time.monotonic()
        spawn_times: deque[float] = deque([start])
        processes_seen: set[int] = set()
        root_exit_code: int | None = None
        timed_out = False
        process_limit: str | None = None
        termination = {
            "attempted": False,
            "completed": True,
            "remaining_pids": [],
            "errors": [],
        }

        try:
            stopped_pid, stopped_status = os.waitpid(pid, os.WUNTRACED)
            if stopped_pid != pid or not os.WIFSTOPPED(stopped_status):
                raise ExecuteProcessError("Cygwin child did not stop before supervision")

            root_winpid = job.assign_cygwin_pid(pid)
            processes_seen.add(root_winpid)
            os.kill(pid, signal.SIGCONT)

            root_done = False
            while not root_done:
                now = time.monotonic()
                if now - start > limits["wall_seconds"]:
                    timed_out = True
                    termination = job.terminate()
                    break

                while True:
                    event = job.event()
                    if event is None:
                        break
                    message, winpid = event
                    event_time = time.monotonic()

                    if message == JOB_OBJECT_MSG_NEW_PROCESS:
                        if winpid not in processes_seen:
                            processes_seen.add(winpid)
                            spawn_times.append(event_time)

                        while spawn_times and event_time - spawn_times[0] > 1.0:
                            spawn_times.popleft()

                        if len(processes_seen) > limits["max_total_spawned"]:
                            process_limit = "max_total_spawned"
                        elif len(spawn_times) > limits["max_spawns_per_second"]:
                            process_limit = "max_spawns_per_second"

                    elif message == JOB_OBJECT_MSG_ACTIVE_PROCESS_LIMIT:
                        process_limit = "max_concurrent"
                    elif message == JOB_OBJECT_MSG_ACTIVE_PROCESS_ZERO:
                        root_done = True

                    if process_limit is not None:
                        termination = job.terminate()
                        root_done = True
                        break

                waited, status = os.waitpid(pid, os.WNOHANG)
                if waited == pid:
                    root_exit_code = _wait_exit_code(status)
                    root_done = True

                if not root_done:
                    time.sleep(0.002)

            if termination["attempted"]:
                deadline = time.monotonic() + 2.0
                while time.monotonic() < deadline:
                    try:
                        waited, status = os.waitpid(pid, os.WNOHANG)
                    except ChildProcessError:
                        break
                    if waited == pid:
                        root_exit_code = _wait_exit_code(status)
                        break
                    time.sleep(0.005)

        except ExecuteProcessError:
            if not termination["attempted"]:
                termination = job.terminate()
            raise
        finally:
            job.close()

        stdout_file.seek(0)
        stderr_file.seek(0)
        stdout = stdout_file.read().decode("utf-8", errors="replace")
        stderr = stderr_file.read().decode("utf-8", errors="replace")

    return _result(
        parameters,
        exit_code=root_exit_code,
        stdout=stdout,
        stderr=stderr,
        timed_out=timed_out,
        process_limit=process_limit,
        termination=termination,
        processes_observed=len(processes_seen),
        backend="cygwin-job-object",
    )


def execute_script(parameters: dict[str, Any], authority: Authority) -> dict[str, Any]:
    if sys.platform.startswith("linux"):
        result = _execute_linux(parameters)
    elif sys.platform == "cygwin":
        result = _execute_cygwin(parameters)
    else:
        raise ExecuteProcessError(
            "execute.script is unsupported on this host",
            details={"platform": sys.platform},
        )
    return _finish(parameters, result)


def tasks() -> tuple[TaskDefinition, ...]:
    return (TaskDefinition("execute.script", validate_script, execute_script),)
