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
RESULT_CONSTRUCTION_FAILURE_MESSAGE = (
    "Authoritative result construction failed after the complete identity set "
    "was established, but a truthful failure result remained constructible."
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
class ProcessingFailure(Exception):
    """Authoritative failure after the complete identity set exists."""

    input_bytes: bytes
    payload: dict[str, Any]
    failure_stage: str

    def result_bytes(self) -> bytes:
        details = _FAILURE_DETAILS[self.failure_stage]
        request_id = _derived_identity("request", self.input_bytes)
        result_id = _derived_identity(
            "result",
            request_id.encode("ascii"),
            details["identity_discriminator"],
        )
        diagnostic_id = _derived_identity(
            "diagnostic",
            request_id.encode("ascii"),
            self.failure_stage.encode("ascii"),
            details["identity_discriminator"],
        )
        workflow = self.payload["workflow"]
        effects = {
            "request": "not-requested",
            "authorization": "indeterminate",
            "execution": "unattempted",
            "observation": "unobserved",
            "verification": "unverified",
        }
        result = {
            "schema_version": 1,
            "result_id": result_id,
            "request_id": request_id,
            "lifecycle": "no-op",
            "processing": {
                "status": "failed",
                "failure_stage": self.failure_stage,
            },
            "workflow": {
                "workflow_id": workflow["workflow_id"],
                "status": "failed",
                "effects": dict(effects),
                "operations": [
                    {
                        "operation_id": operation["operation_id"],
                        "status": "failed",
                        "effects": dict(effects),
                    }
                    for operation in workflow["operations"]
                ],
            },
            "diagnostics": [
                {
                    "diagnostic_id": diagnostic_id,
                    "code": details["code"],
                    "stage": self.failure_stage,
                    "scope": "workflow",
                    "message": details["message"],
                    "request_id": request_id,
                    "workflow_id": workflow["workflow_id"],
                }
            ],
            "process": {
                "exit_code": 3,
                "stdout": "authoritative-result",
                "stderr": "empty",
            },
        }
        return _canonical_json_bytes(result)


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

    payload = _parse_canonical_request(input_bytes)
    raise ProcessingFailure(
        input_bytes=input_bytes,
        payload=payload,
        failure_stage=control["failure_stage"],
    )
