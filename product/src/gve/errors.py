from __future__ import annotations


class GVEError(Exception):
    """Base governed execution failure."""

    code = "task-execution"

    def __init__(self, message: str, *, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class PayloadError(GVEError):
    code = "invalid-payload"


class UnknownTaskError(GVEError):
    code = "unknown-task"


class ResultReferenceError(GVEError):
    code = "result-reference"
