"""Maintained Stage 2 authoritative processing-failure boundary."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .core import (
    FatalInputFailure,
    _canonical_json_bytes,
    _derived_identity,
    _parse_canonical_request,
    canonical_success,
)


PROCESSING_FAILURE_MESSAGE = (
    "The accepted conformance disposition requires a deterministic processing "
    "failure after authoritative identities are established."
)
RESULT_CONSTRUCTION_FAILURE_MESSAGE = (
    "Authoritative result construction failed after the complete identity set "
    "was established, but a truthful failure result remained constructible."
)
FATAL_RESULT_CONSTRUCTION_MESSAGE = (
    "Result construction failed before the complete authoritative identity set "
    "could be retained for a truthful authoritative result."
)

_NO_OP_DISPOSITION_CONTROL = {
    "schema_version": 1,
    "disposition": "processing-failure",
    "failure_stage": "no-op-disposition",
}
_RESULT_CONSTRUCTION_CONTROL = {
    "schema_version": 1,
    "disposition": "processing-failure",
    "failure_stage": "result-construction",
}
_FAILURE_DETAILS = {
    "no-op-disposition": {
        "code": "GVE-S2-PROCESSING-FAILURE",
        "message": PROCESSING_FAILURE_MESSAGE,
        "identity_discriminator": b"processing-failure",
    },
    "result-construction": {
        "code": "GVE-S2-RESULT-CONSTRUCTION-FAILURE",
        "message": RESULT_CONSTRUCTION_FAILURE_MESSAGE,
        "identity_discriminator": b"result-construction-failure",
    },
}


@dataclass(frozen=True)
class _ResultContext:
    request_id: str
    result_id: str
    diagnostic_id: str
    workflow_id: str
    operation_ids: tuple[str, ...]
    failure_stage: str


class _InjectedResultConstructionFault(RuntimeError):
    pass


def _capture_result_context(
    input_bytes: bytes,
    payload: Mapping[str, Any],
    failure_stage: str,
) -> _ResultContext:
    details = _FAILURE_DETAILS[failure_stage]
    request_id = _derived_identity("request", input_bytes)
    result_id = _derived_identity(
        "result",
        request_id.encode("ascii"),
        details["identity_discriminator"],
    )
    diagnostic_id = _derived_identity(
        "diagnostic",
        request_id.encode("ascii"),
        failure_stage.encode("ascii"),
        details["identity_discriminator"],
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
        failure_stage=failure_stage,
    )


def _construct_primary_result(context: _ResultContext) -> bytes:
    del context
    raise _InjectedResultConstructionFault(
        "controlled result-construction fault after identity capture"
    )


def _construct_authoritative_failure_fallback(context: _ResultContext) -> bytes:
    details = _FAILURE_DETAILS[context.failure_stage]
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
            "failure_stage": context.failure_stage,
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
                "code": details["code"],
                "stage": context.failure_stage,
                "scope": "workflow",
                "message": details["message"],
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
        return _construct_authoritative_failure_fallback(self.context)


def _process_request_with_construction_fault(
    input_bytes: bytes,
    *,
    processor_control: Mapping[str, Any],
    fault_before_context: bool = False,
) -> bytes:
    """Internal conformance fault injection without expanding accepted controls."""

    control = dict(processor_control)
    if control != _RESULT_CONSTRUCTION_CONTROL:
        raise ValueError("construction fault requires result-construction control")

    payload = _parse_canonical_request(input_bytes)
    if fault_before_context:
        raise FatalInputFailure(
            code="GVE-S2-RESULT-CONSTRUCTION-FAILURE",
            stage="result-construction",
            message=FATAL_RESULT_CONSTRUCTION_MESSAGE,
            input_bytes=input_bytes,
        )

    context = _capture_result_context(
        input_bytes,
        payload,
        "result-construction",
    )
    try:
        return _construct_primary_result(context)
    except _InjectedResultConstructionFault:
        raise ProcessingFailure(context=context)


def process_request(
    input_bytes: bytes,
    *,
    processor_control: Mapping[str, Any] | None = None,
) -> bytes:
    """Process a request without inferring conformance controls from request bytes."""

    if processor_control is None:
        return canonical_success(input_bytes)

    control = dict(processor_control)
    if control not in (
        _NO_OP_DISPOSITION_CONTROL,
        _RESULT_CONSTRUCTION_CONTROL,
    ):
        raise ValueError("unsupported Stage 2 processor control")

    if control == _RESULT_CONSTRUCTION_CONTROL:
        return _process_request_with_construction_fault(
            input_bytes,
            processor_control=control,
        )

    payload = _parse_canonical_request(input_bytes)
    context = _capture_result_context(
        input_bytes,
        payload,
        "no-op-disposition",
    )
    raise ProcessingFailure(context=context)
