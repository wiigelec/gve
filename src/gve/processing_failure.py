"""Maintained Stage 2 authoritative processing-failure boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .core import (
    _canonical_json_bytes,
    _derived_identity,
    _parse_canonical_request,
    canonical_success,
)


PROCESSING_FAILURE_MESSAGE = (
    "The accepted conformance disposition requires a deterministic processing "
    "failure after authoritative identities are established."
)

_NO_OP_DISPOSITION_CONTROL = {
    "schema_version": 1,
    "disposition": "processing-failure",
    "failure_stage": "no-op-disposition",
}


@dataclass(frozen=True)
class _ResultContext:
    request_id: str
    result_id: str
    diagnostic_id: str
    workflow_id: str
    operation_ids: tuple[str, ...]


def _capture_result_context(
    input_bytes: bytes,
    payload: Mapping[str, Any],
) -> _ResultContext:
    request_id = _derived_identity("request", input_bytes)
    result_id = _derived_identity(
        "result",
        request_id.encode("ascii"),
        b"processing-failure",
    )
    diagnostic_id = _derived_identity(
        "diagnostic",
        request_id.encode("ascii"),
        b"no-op-disposition",
        b"processing-failure",
    )
    workflow = payload["workflow"]
    return _ResultContext(
        request_id=request_id,
        result_id=result_id,
        diagnostic_id=diagnostic_id,
        workflow_id=workflow["workflow_id"],
        operation_ids=tuple(
            operation["operation_id"] for operation in workflow["operations"]
        ),
    )


def _construct_authoritative_failure(context: _ResultContext) -> bytes:
    effects = {
        "request": "not-requested",
        "authorization": "indeterminate",
        "execution": "unattempted",
        "observation": "unobserved",
        "verification": "unverified",
    }
    result = {
        "schema_version": 1,
        "result_id": context.result_id,
        "request_id": context.request_id,
        "lifecycle": "no-op",
        "processing": {
            "status": "failed",
            "failure_stage": "no-op-disposition",
        },
        "workflow": {
            "workflow_id": context.workflow_id,
            "status": "failed",
            "effects": dict(effects),
            "operations": [
                {
                    "operation_id": operation_id,
                    "status": "failed",
                    "effects": dict(effects),
                }
                for operation_id in context.operation_ids
            ],
        },
        "diagnostics": [
            {
                "diagnostic_id": context.diagnostic_id,
                "code": "GVE-S2-PROCESSING-FAILURE",
                "stage": "no-op-disposition",
                "scope": "workflow",
                "message": PROCESSING_FAILURE_MESSAGE,
                "request_id": context.request_id,
                "workflow_id": context.workflow_id,
            }
        ],
        "process": {
            "exit_code": 3,
            "stdout": "authoritative-result",
            "stderr": "empty",
        },
    }
    return _canonical_json_bytes(result)


@dataclass(frozen=True)
class ProcessingFailure(Exception):
    """Authoritative failure after the complete identity set exists."""

    context: _ResultContext

    def result_bytes(self) -> bytes:
        return _construct_authoritative_failure(self.context)


def process_request(
    input_bytes: bytes,
    *,
    processor_control: Mapping[str, Any] | None = None,
) -> bytes:
    """Process a request without inferring conformance controls from request bytes."""

    if processor_control is None:
        return canonical_success(input_bytes)

    control = dict(processor_control)
    if control != _NO_OP_DISPOSITION_CONTROL:
        raise ValueError("unsupported Stage 2 processor control")

    payload = _parse_canonical_request(input_bytes)
    context = _capture_result_context(input_bytes, payload)
    raise ProcessingFailure(context=context)
