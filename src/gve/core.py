"""Maintained Stage 2 request processing."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


UTF8_FAILURE_MESSAGE = (
    "Input bytes are not valid UTF-8, so no authoritative result identity "
    "could be constructed."
)
JSON_FAILURE_MESSAGE = (
    "Input bytes could not be parsed as one JSON value, so no authoritative "
    "result identity could be constructed."
)
DUPLICATE_MEMBER_FAILURE_MESSAGE = (
    "Input JSON contains a duplicate object member, so no authoritative result "
    "identity could be constructed."
)
RESULT_CONSTRUCTION_FAILURE_MESSAGE = (
    "The parsed input does not contain the complete authoritative workflow and "
    "operation identity set required to construct a truthful authoritative result."
)


def _canonical_json_bytes(value: Any) -> bytes:
    text = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return (text + "\n").encode("utf-8")


def _derived_identity(family: str, *parts: bytes) -> str:
    preimage = b"\x00".join((family.encode("ascii"), *parts))
    digest = hashlib.sha256(preimage).hexdigest()
    return f"gve-{family}-sha256:{digest}"


@dataclass(frozen=True)
class FatalInputFailure(Exception):
    code: str
    stage: str
    message: str
    input_bytes: bytes

    def artifact_bytes(self) -> bytes:
        failure_id = _derived_identity(
            "failure",
            self.input_bytes,
            self.stage.encode("ascii"),
        )
        return _canonical_json_bytes(
            {
                "schema_version": 1,
                "failure_id": failure_id,
                "code": self.code,
                "stage": self.stage,
                "message": self.message,
                "process": {
                    "exit_code": 4,
                    "stdout": "empty",
                    "stderr": "fatal-failure",
                },
            }
        )


@dataclass(frozen=True)
class PayloadRejection(Exception):
    input_bytes: bytes
    payload: dict[str, Any]
    message: str

    def result_bytes(self) -> bytes:
        request_id = _derived_identity("request", self.input_bytes)
        result_id = _derived_identity(
            "result", request_id.encode("ascii"), b"invalid-input"
        )
        diagnostic_id = _derived_identity(
            "diagnostic", request_id.encode("ascii"), b"payload-validation"
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
                    "message": self.message,
                    "request_id": request_id,
                }
            ],
            "process": {
                "exit_code": 2,
                "stdout": "authoritative-result",
                "stderr": "empty",
            },
        }
        return _canonical_json_bytes(result)


@dataclass(frozen=True)
class DuplicateOperationIdentity(PayloadRejection):
    def result_bytes(self) -> bytes:
        request_id = _derived_identity("request", self.input_bytes)
        result_id = _derived_identity(
            "result", request_id.encode("ascii"), b"invalid-identity"
        )
        diagnostic_id = _derived_identity(
            "diagnostic",
            request_id.encode("ascii"),
            b"identity-validation",
            b"duplicate-operation-id",
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
                    "message": self.message,
                    "request_id": request_id,
                    "workflow_id": workflow["workflow_id"],
                }
            ],
            "process": {
                "exit_code": 2,
                "stdout": "authoritative-result",
                "stderr": "empty",
            },
        }
        return _canonical_json_bytes(result)


class _DuplicateObjectMember(ValueError):
    pass


class _NonStandardConstant(ValueError):
    pass


def _object_without_duplicates(
    pairs: list[tuple[str, Any]],
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateObjectMember(key)
        result[key] = value
    return result


def _reject_non_standard_constant(value: str) -> None:
    raise _NonStandardConstant(value)


def _parse_json(input_bytes: bytes) -> Any:
    try:
        text = input_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise FatalInputFailure(
            code="GVE-S2-INVALID-UTF8",
            stage="utf8-decoding",
            message=UTF8_FAILURE_MESSAGE,
            input_bytes=input_bytes,
        ) from exc

    try:
        return json.loads(
            text,
            object_pairs_hook=_object_without_duplicates,
            parse_constant=_reject_non_standard_constant,
        )
    except _DuplicateObjectMember as exc:
        raise FatalInputFailure(
            code="GVE-S2-INVALID-JSON",
            stage="json-parsing",
            message=DUPLICATE_MEMBER_FAILURE_MESSAGE,
            input_bytes=input_bytes,
        ) from exc
    except (json.JSONDecodeError, _NonStandardConstant) as exc:
        raise FatalInputFailure(
            code="GVE-S2-INVALID-JSON",
            stage="json-parsing",
            message=JSON_FAILURE_MESSAGE,
            input_bytes=input_bytes,
        ) from exc


def _reject(
    input_bytes: bytes,
    payload: dict[str, Any],
    message: str,
) -> None:
    raise PayloadRejection(
        input_bytes=input_bytes,
        payload=payload,
        message=message,
    )


def _fatal_result_construction(input_bytes: bytes) -> None:
    raise FatalInputFailure(
        code="GVE-S2-RESULT-CONSTRUCTION-FAILURE",
        stage="result-construction",
        message=RESULT_CONSTRUCTION_FAILURE_MESSAGE,
        input_bytes=input_bytes,
    )


def _parse_canonical_request(input_bytes: bytes) -> dict[str, Any]:
    payload = _parse_json(input_bytes)
    if not isinstance(payload, dict):
        _fatal_result_construction(input_bytes)

    workflow = payload.get("workflow")
    if not isinstance(workflow, dict):
        _fatal_result_construction(input_bytes)
    if not isinstance(workflow.get("workflow_id"), str) or not workflow["workflow_id"]:
        _fatal_result_construction(input_bytes)
    operations = workflow.get("operations")
    if not isinstance(operations, list) or not operations:
        _fatal_result_construction(input_bytes)
    for operation in operations:
        if not isinstance(operation, dict):
            _fatal_result_construction(input_bytes)
        if not isinstance(operation.get("operation_id"), str) or not operation["operation_id"]:
            _fatal_result_construction(input_bytes)

    if "lifecycle" not in payload:
        _reject(
            input_bytes,
            payload,
            "The payload omits the required lifecycle member.",
        )
    if payload["lifecycle"] != "no-op":
        _reject(
            input_bytes,
            payload,
            "The payload names an unsupported lifecycle value.",
        )
    if set(payload) != {"schema_version", "lifecycle", "workflow"}:
        _reject(
            input_bytes,
            payload,
            "The common payload contains an unknown top-level governed member.",
        )
    if payload["schema_version"] != 2:
        _reject(
            input_bytes,
            payload,
            "The payload names an unsupported schema version.",
        )
    if set(workflow) != {"workflow_id", "operations"}:
        _reject(
            input_bytes,
            payload,
            "The workflow envelope contains an unknown governed member.",
        )

    for operation in operations:
        if "command" in operation:
            _reject(
                input_bytes,
                payload,
                "The operation envelope contains a forbidden execution member.",
            )
        if set(operation) != {"operation_id", "plugin", "content"}:
            _reject(
                input_bytes,
                payload,
                "The operation envelope does not match the closed common envelope.",
            )
        plugin = operation["plugin"]
        if not isinstance(plugin, dict):
            _reject(
                input_bytes,
                payload,
                "The operation plugin envelope must be an object.",
            )
        if "action" not in plugin:
            _reject(
                input_bytes,
                payload,
                "The operation plugin envelope omits the required action member.",
            )
        if set(plugin) != {"plugin_id", "action"}:
            _reject(
                input_bytes,
                payload,
                "The plugin routing envelope contains an unknown governed member.",
            )
        if not isinstance(plugin["plugin_id"], str) or not plugin["plugin_id"]:
            _reject(
                input_bytes,
                payload,
                "The plugin_id must be a non-empty string.",
            )
        if not isinstance(plugin["action"], str) or not plugin["action"]:
            _reject(
                input_bytes,
                payload,
                "The plugin action must be a non-empty string.",
            )
        if not isinstance(operation["content"], dict):
            _reject(
                input_bytes,
                payload,
                "The opaque operation content must be an object.",
            )

    operation_ids = [operation["operation_id"] for operation in operations]
    if len(set(operation_ids)) != len(operation_ids):
        raise DuplicateOperationIdentity(
            input_bytes=input_bytes,
            payload=payload,
            message="The workflow contains duplicate operation identities.",
        )

    return payload


def canonical_success(input_bytes: bytes) -> bytes:
    """Return the authoritative no-op result for canonical success."""
    payload = _parse_canonical_request(input_bytes)
    request_id = _derived_identity("request", input_bytes)
    result_id = _derived_identity("result", request_id.encode("ascii"), b"success")
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
    return _canonical_json_bytes(result)
