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


def _require_exact_members(
    value: dict[str, Any],
    expected: set[str],
    location: str,
) -> None:
    if set(value) != expected:
        raise ValueError(f"{location} does not match the canonical-success envelope")


def _parse_canonical_request(input_bytes: bytes) -> dict[str, Any]:
    payload = _parse_json(input_bytes)
    if not isinstance(payload, dict):
        raise ValueError("canonical request must be a JSON object")

    _require_exact_members(
        payload,
        {"schema_version", "lifecycle", "workflow"},
        "request",
    )
    if payload["schema_version"] != 2 or payload["lifecycle"] != "no-op":
        raise ValueError("request is not the canonical-success lifecycle")

    workflow = payload["workflow"]
    if not isinstance(workflow, dict):
        raise ValueError("workflow must be an object")
    _require_exact_members(workflow, {"workflow_id", "operations"}, "workflow")
    if not isinstance(workflow["workflow_id"], str) or not workflow["workflow_id"]:
        raise ValueError("workflow_id must be a non-empty string")

    operations = workflow["operations"]
    if not isinstance(operations, list) or not operations:
        raise ValueError("operations must be a non-empty array")
    for operation in operations:
        if not isinstance(operation, dict):
            raise ValueError("operation must be an object")
        _require_exact_members(
            operation,
            {"operation_id", "plugin", "content"},
            "operation",
        )
        if not isinstance(operation["operation_id"], str) or not operation["operation_id"]:
            raise ValueError("operation_id must be a non-empty string")
        plugin = operation["plugin"]
        if not isinstance(plugin, dict):
            raise ValueError("plugin must be an object")
        _require_exact_members(plugin, {"plugin_id", "action"}, "plugin")
        if not isinstance(plugin["plugin_id"], str) or not plugin["plugin_id"]:
            raise ValueError("plugin_id must be a non-empty string")
        if not isinstance(plugin["action"], str) or not plugin["action"]:
            raise ValueError("plugin action must be a non-empty string")

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
