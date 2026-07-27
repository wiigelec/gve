"""Issue #99 closed Stage 2 processing-failure conformance process."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ProcessOutcome:
    exit_status: int
    stdout: bytes
    stderr: bytes


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def derived_identity(family: str, *parts: bytes) -> str:
    preimage = b"\x00".join((family.encode("ascii"), *parts))
    return f"gve-{family}-sha256:{hashlib.sha256(preimage).hexdigest()}"


def processing_failure_process(
    input_bytes: bytes,
    processor_control: Mapping[str, Any],
) -> ProcessOutcome:
    expected_control = {
        "schema_version": 1,
        "disposition": "processing-failure",
        "failure_stage": "no-op-disposition",
    }
    if dict(processor_control) != expected_control:
        raise ValueError("unsupported closed processor control")

    payload = json.loads(input_bytes.decode("utf-8"))
    workflow = payload["workflow"]
    request_id = derived_identity("request", input_bytes)
    result_id = derived_identity(
        "result",
        request_id.encode("ascii"),
        b"processing-failure",
    )
    diagnostic_id = derived_identity(
        "diagnostic",
        request_id.encode("ascii"),
        b"no-op-disposition",
        b"processing-failure",
    )
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
            "failure_stage": "no-op-disposition",
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
                "code": "GVE-S2-PROCESSING-FAILURE",
                "stage": "no-op-disposition",
                "scope": "workflow",
                "message": (
                    "The accepted conformance disposition requires a deterministic "
                    "processing failure after authoritative identities are established."
                ),
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
    encoded = canonical_json_bytes(result)
    return ProcessOutcome(3, encoded, b"")
