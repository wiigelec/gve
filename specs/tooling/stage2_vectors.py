"""Deterministic Stage 2 conformance-vector primitives."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


class DuplicateMemberError(ValueError):
    """Raised when input JSON repeats an object member."""


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateMemberError(key)
        result[key] = value
    return result


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize one JSON value using the Issue 84 canonical byte profile."""
    text = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return (text + "\n").encode("utf-8")


def derived_identity(family: str, *parts: bytes) -> str:
    """Derive a stable vector identity from one controlled byte preimage."""
    if not family or any(ord(character) > 0x7F for character in family):
        raise ValueError("identity family must be non-empty ASCII")
    preimage = b"\x00".join((family.encode("ascii"), *parts))
    digest = hashlib.sha256(preimage).hexdigest()
    return f"gve-{family}-sha256:{digest}"


def canonical_success_result(input_bytes: bytes, payload: dict[str, Any]) -> dict[str, Any]:
    """Construct the exact successful no-op result used by the canonical vector."""
    request_id = derived_identity("request", input_bytes)
    result_id = derived_identity("result", request_id.encode("ascii"), b"success")
    workflow = payload["workflow"]
    effects = {
        "request": "not-requested",
        "authorization": "indeterminate",
        "execution": "unattempted",
        "observation": "unobserved",
        "verification": "unverified",
    }
    return {
        "schema_version": 1,
        "result_id": result_id,
        "request_id": request_id,
        "lifecycle": "no-op",
        "processing": {"status": "succeeded", "failure_stage": None},
        "workflow": {
            "workflow_id": workflow["workflow_id"],
            "status": "no-op-completed",
            "effects": dict(effects),
            "operations": [
                {
                    "operation_id": operation["operation_id"],
                    "status": "no-op",
                    "effects": dict(effects),
                }
                for operation in workflow["operations"]
            ],
        },
        "diagnostics": [],
        "process": {
            "exit_code": 0,
            "stdout": "authoritative-result",
            "stderr": "empty",
        },
    }


@dataclass(frozen=True)
class ProcessOutcome:
    exit_status: int
    stdout: bytes
    stderr: bytes


def _fatal(input_bytes: bytes, code: str, stage: str, message: str) -> ProcessOutcome:
    failure_id = derived_identity("failure", input_bytes, stage.encode("ascii"))
    envelope = {
        "schema_version": 1,
        "failure_id": failure_id,
        "code": code,
        "stage": stage,
        "message": message,
        "process": {
            "exit_code": 4,
            "stdout": "empty",
            "stderr": "fatal-failure",
        },
    }
    return ProcessOutcome(4, b"", canonical_json_bytes(envelope))



def _rejected_payload_result(input_bytes: bytes, payload: dict[str, Any], message: str) -> ProcessOutcome:
    request_id = derived_identity("request", input_bytes)
    result_id = derived_identity("result", request_id.encode("ascii"), b"invalid-input")
    diagnostic_id = derived_identity(
        "diagnostic", request_id.encode("ascii"), b"payload-validation"
    )
    workflow = payload["workflow"]
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
            "status": "rejected",
            "failure_stage": "payload-validation",
        },
        "workflow": {
            "workflow_id": workflow["workflow_id"],
            "status": "rejected",
            "effects": dict(effects),
            "operations": [
                {
                    "operation_id": operation["operation_id"],
                    "status": "unattempted",
                    "effects": dict(effects),
                }
                for operation in workflow["operations"]
            ],
        },
        "diagnostics": [
            {
                "diagnostic_id": diagnostic_id,
                "code": "GVE-S2-INVALID-PAYLOAD",
                "stage": "payload-validation",
                "scope": "request",
                "request_id": request_id,
                "message": message,
            }
        ],
        "process": {
            "exit_code": 2,
            "stdout": "authoritative-result",
            "stderr": "empty",
        },
    }
    encoded = canonical_json_bytes(result)
    return ProcessOutcome(2, encoded, b"")



def _rejected_identity_result(
    input_bytes: bytes,
    payload: dict[str, Any],
    message: str,
) -> ProcessOutcome:
    request_id = derived_identity("request", input_bytes)
    result_id = derived_identity(
        "result", request_id.encode("ascii"), b"invalid-identity"
    )
    diagnostic_id = derived_identity(
        "diagnostic",
        request_id.encode("ascii"),
        b"identity-validation",
        b"duplicate-operation-id",
    )
    workflow = payload["workflow"]
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
            "status": "rejected",
            "failure_stage": "identity-validation",
        },
        "workflow": {
            "workflow_id": workflow["workflow_id"],
            "status": "rejected",
            "effects": dict(effects),
            "operations": [
                {
                    "operation_id": operation["operation_id"],
                    "status": "unattempted",
                    "effects": dict(effects),
                }
                for operation in workflow["operations"]
            ],
        },
        "diagnostics": [
            {
                "diagnostic_id": diagnostic_id,
                "code": "GVE-S2-DUPLICATE-IDENTITY",
                "stage": "identity-validation",
                "scope": "workflow",
                "request_id": request_id,
                "workflow_id": workflow["workflow_id"],
                "message": message,
            }
        ],
        "process": {
            "exit_code": 2,
            "stdout": "authoritative-result",
            "stderr": "empty",
        },
    }
    encoded = canonical_json_bytes(result)
    return ProcessOutcome(2, encoded, b"")


def reference_process(input_bytes: bytes) -> ProcessOutcome:
    """Run the byte-critical Stage 2 decoding/parsing and canonical success path."""
    try:
        text = input_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return _fatal(
            input_bytes,
            "GVE-S2-INVALID-UTF8",
            "utf8-decoding",
            "Input bytes are not valid UTF-8, so no authoritative result identity could be constructed.",
        )
    try:
        payload = json.loads(text, object_pairs_hook=_unique_object)
    except DuplicateMemberError:
        return _fatal(
            input_bytes,
            "GVE-S2-INVALID-JSON",
            "json-parsing",
            "Input JSON contains a duplicate object member, so no authoritative result identity could be constructed.",
        )
    except json.JSONDecodeError:
        return _fatal(
            input_bytes,
            "GVE-S2-INVALID-JSON",
            "json-parsing",
            "Input bytes could not be parsed as one JSON value, so no authoritative result identity could be constructed.",
        )
    if not isinstance(payload, dict):
        return _fatal(
            input_bytes,
            "GVE-S2-INVALID-JSON",
            "json-parsing",
            "Input bytes could not be parsed as one JSON object, so no authoritative result identity could be constructed.",
        )
    if "workflow" in payload and isinstance(payload["workflow"], dict):
        if "lifecycle" not in payload:
            return _rejected_payload_result(
                input_bytes,
                payload,
                "The payload omits the required lifecycle member.",
            )
        if payload["lifecycle"] != "no-op":
            return _rejected_payload_result(
                input_bytes,
                payload,
                "The payload names an unsupported lifecycle value.",
            )
        workflow = payload["workflow"]
        if "unexpected" in workflow:
            return _rejected_payload_result(
                input_bytes,
                payload,
                "The workflow envelope contains an unknown governed member.",
            )
        if "unexpected" in payload:
            return _rejected_payload_result(
                input_bytes,
                payload,
                "The common payload contains an unknown top-level governed member.",
            )
        operations = workflow.get("operations")
        if isinstance(operations, list) and operations:
            operation = operations[0]
            if "command" in operation:
                return _rejected_payload_result(
                    input_bytes,
                    payload,
                    "The operation envelope contains a forbidden execution member.",
                )
            plugin = operation.get("plugin")
            if isinstance(plugin, dict) and "action" not in plugin:
                return _rejected_payload_result(
                    input_bytes,
                    payload,
                    "The operation plugin envelope omits the required action member.",
                )
            if isinstance(plugin, dict) and "executable" in plugin:
                return _rejected_payload_result(
                    input_bytes,
                    payload,
                    "The plugin routing envelope contains an unknown governed member.",
                )
            operation_ids = [
                candidate.get("operation_id")
                for candidate in operations
                if isinstance(candidate, dict)
            ]
            if len(operation_ids) != len(set(operation_ids)):
                return _rejected_identity_result(
                    input_bytes,
                    payload,
                    "The workflow contains duplicate operation identities.",
                )
    result = canonical_json_bytes(canonical_success_result(input_bytes, payload))
    return ProcessOutcome(0, result, b"")
