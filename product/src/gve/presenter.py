from __future__ import annotations

import shlex
import sys
from pathlib import Path
from typing import Mapping, TextIO


class ConsolePresenter:
    def __init__(self, stream: TextIO | None = None) -> None:
        self.stream = stream or sys.stdout
        self.phase_index = 0
        self.phase_total = 0

    def _p(self, text: str = "") -> None:
        print(text, file=self.stream, flush=True)

    def __call__(self, event: Mapping[str, object]) -> None:
        kind = event.get("type")
        if kind == "macro-start":
            self.phase_total = int(event.get("phase_count", 0))
            self._p("FS0 Script Transfer: START")
            self._p(f"Operation: {event.get('macro')}")
        elif kind == "phase-start":
            self.phase_index += 1
            label = event.get("label")
            self._p(f"[{self.phase_index:02d}/{self.phase_total:02d}] {label} governed phase")
        elif kind == "task-start":
            self._p(f"TASK {event.get('id')} {event.get('task')}")
        elif kind == "command-start":
            argv = event.get("argv")
            if isinstance(argv, list):
                self._p("$ " + shlex.join(str(x) for x in argv))
        elif kind == "command-output":
            prefix = "ERR" if event.get("stream") == "stderr" else "OUT"
            text = event.get("text")
            if isinstance(text, str):
                for line in text.splitlines(): self._p(f"{prefix} | {line}")
        elif kind == "task-success":
            self._p(f"PASS {event.get('id')}")
            if event.get("id") == "modify-status-guard":
                record = event.get("record")
                if isinstance(record, Mapping):
                    task_result = record.get("result")
                    if isinstance(task_result, Mapping):
                        entries = task_result.get("entries")
                        if isinstance(entries, list):
                            for entry in entries:
                                if isinstance(entry, Mapping):
                                    code, path = entry.get("status"), entry.get("path")
                                    if isinstance(code, str) and isinstance(path, str):
                                        self._p(f"OUT | {code} {path}")
        elif kind == "task-failure":
            msg = ""
            record = event.get("record")
            if isinstance(record, Mapping):
                error = record.get("error")
                if isinstance(error, Mapping) and isinstance(error.get("message"), str):
                    msg = ": " + error["message"]
            self._p(f"FAIL {event.get('id')}{msg}")

    def output_failure(self, exc: OSError, output_path: Path, result: Mapping[str, object]) -> None:
        self._p(f"FAIL result-json: {exc}")
        self._p("FS0 Script Transfer: FAILED")
        self._p(f"Result JSON: {output_path}")
        self._p(f"Governed Result: {result.get('status')}")

    def finish(self, result: Mapping[str, object], output_path: Path) -> None:
        failed = result.get("status") != "success"
        if failed:
            tasks = result.get("tasks")
            if isinstance(tasks, list):
                failing = next((t for t in tasks if isinstance(t, Mapping) and t.get("status") == "failure"), None)
                if isinstance(failing, Mapping):
                    self._p(f"Failed Task: {failing.get('id')}")
                    error = failing.get("error")
                    if isinstance(error, Mapping): self._p(f"Reason: {error.get('message')}")
                successful = [t.get("id") for t in tasks if isinstance(t, Mapping) and t.get("status") == "success"]
                skipped = [t.get("id") for t in tasks if isinstance(t, Mapping) and t.get("status") == "not-executed"]
                if successful: self._p("Prior Success: " + ", ".join(str(x) for x in successful))
                if skipped: self._p("Not Executed: " + ", ".join(str(x) for x in skipped))

        projected = result.get("result")
        if isinstance(projected, Mapping):
            repository = projected.get("repository")
            root = repository.get("root") if isinstance(repository, Mapping) else None
            validation = projected.get("validation")
            validation_status = validation.get("status") if isinstance(validation, Mapping) else None
            files = projected.get("files_changed")
            files_text = ", ".join(files) if isinstance(files, list) else files
            values = (
                ("Operation", result.get("macro")), ("Repository", root),
                ("Branch", projected.get("branch")), ("Expected HEAD", projected.get("expected_head")),
                ("Observed HEAD", projected.get("observed_head")), ("Files Changed", files_text),
                ("Validation", validation_status), ("Commit", projected.get("commit")),
                ("Remote HEAD", projected.get("remote_head")), ("Result JSON", str(output_path)),
            )
            for label, value in values:
                if value is not None: self._p(f"{label}: {value}")
        else:
            self._p(f"Operation: {result.get('macro')}")
            self._p(f"Result JSON: {output_path}")
        self._p("FS0 Script Transfer: " + ("FAILED" if failed else "PASS"))
