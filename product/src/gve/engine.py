from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from .authority import Authority
from .errors import GVEError, PayloadError, ResultReferenceError
from .events import bind_observer, emit_to
from .registry import Registry

_INVOCATION_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
_TOP_FIELDS = {"schema_version", "workflow_id", "tasks"}
_INVOCATION_FIELDS = {"id", "task", "parameters"}


def _error(exc: GVEError) -> dict[str, Any]:
    return {
        "code": exc.code,
        "message": exc.message,
        "details": deepcopy(exc.details),
    }


def _empty_task_record(invocation_id: str, task: str, status: str) -> dict[str, Any]:
    return {
        "id": invocation_id,
        "task": task,
        "status": status,
        "observations": {},
        "effects": {},
        "result": {},
        "error": None,
        "reason": None,
    }


class Engine:
    def __init__(self, registry: Registry) -> None:
        self.registry = registry

    def execute(self, payload: Any, authority: Authority, observer=None) -> dict[str, Any]:
        try:
            workflow_id, invocations = self._validate_envelope(payload)
        except PayloadError as exc:
            return {
                "schema_version": 1,
                "workflow_id": None,
                "status": "failure",
                "tasks": [],
                "error": _error(exc),
            }

        records: list[dict[str, Any]] = []
        records_by_id: dict[str, dict[str, Any]] = {}

        for index, invocation in enumerate(invocations):
            invocation_id = invocation["id"]
            task_identity = invocation["task"]
            record = _empty_task_record(invocation_id, task_identity, "failure")

            emit_to(observer, "task-start", id=invocation_id, task=task_identity)
            try:
                with bind_observer(observer):
                    definition = self.registry.resolve(task_identity)
                    resolved = self._resolve_value(
                        invocation["parameters"],
                        current_index=index,
                        invocations=invocations,
                        records_by_id=records_by_id,
                    )
                    validated = definition.validate(resolved, authority)
                    outcome = definition.execute(validated, authority)
                if not isinstance(outcome, dict):
                    raise GVEError("task implementation returned a non-object outcome")
                unknown = set(outcome) - {"observations", "effects", "result"}
                if unknown:
                    raise GVEError(
                        "task implementation returned unknown outcome fields",
                        details={"fields": sorted(unknown)},
                    )
                for key in ("observations", "effects", "result"):
                    value = outcome.get(key, {})
                    if not isinstance(value, dict):
                        raise GVEError(f"task outcome {key} must be an object")
                    record[key] = deepcopy(value)
                record["status"] = "success"
            except GVEError as exc:
                record["error"] = _error(exc)

            emit_to(observer, "task-success" if record["status"] == "success" else "task-failure", id=invocation_id, task=task_identity, record=deepcopy(record))
            records.append(record)
            records_by_id[invocation_id] = record

            if record["status"] != "success":
                for later in invocations[index + 1 :]:
                    skipped = _empty_task_record(later["id"], later["task"], "not-executed")
                    skipped["reason"] = "prior-task-failure"
                    records.append(skipped)
                    records_by_id[later["id"]] = skipped
                return {
                    "schema_version": 1,
                    "workflow_id": workflow_id,
                    "status": "failure",
                    "tasks": records,
                }

        return {
            "schema_version": 1,
            "workflow_id": workflow_id,
            "status": "success",
            "tasks": records,
        }

    def _validate_envelope(self, payload: Any) -> tuple[str, list[dict[str, Any]]]:
        if not isinstance(payload, dict):
            raise PayloadError("payload must be a JSON object")
        unknown = set(payload) - _TOP_FIELDS
        missing = _TOP_FIELDS - set(payload)
        if unknown or missing:
            raise PayloadError(
                "payload fields are invalid",
                details={"unknown": sorted(unknown), "missing": sorted(missing)},
            )
        if payload["schema_version"] != 1 or isinstance(payload["schema_version"], bool):
            raise PayloadError("schema_version must be integer 1")
        workflow_id = payload["workflow_id"]
        if not isinstance(workflow_id, str) or not workflow_id:
            raise PayloadError("workflow_id must be a non-empty string")
        tasks = payload["tasks"]
        if not isinstance(tasks, list) or not tasks:
            raise PayloadError("tasks must be a non-empty array")

        seen: set[str] = set()
        normalized: list[dict[str, Any]] = []
        for invocation in tasks:
            if not isinstance(invocation, dict):
                raise PayloadError("each task invocation must be an object")
            unknown = set(invocation) - _INVOCATION_FIELDS
            missing = _INVOCATION_FIELDS - set(invocation)
            if unknown or missing:
                raise PayloadError(
                    "task invocation fields are invalid",
                    details={"unknown": sorted(unknown), "missing": sorted(missing)},
                )
            invocation_id = invocation["id"]
            task = invocation["task"]
            parameters = invocation["parameters"]
            if not isinstance(invocation_id, str) or not _INVOCATION_ID.fullmatch(invocation_id):
                raise PayloadError("invalid invocation id", details={"id": invocation_id})
            if invocation_id in seen:
                raise PayloadError("duplicate invocation id", details={"id": invocation_id})
            seen.add(invocation_id)
            if not isinstance(task, str) or not task:
                raise PayloadError("task identity must be a non-empty string")
            if not isinstance(parameters, dict):
                raise PayloadError("task parameters must be an object")
            normalized.append(
                {"id": invocation_id, "task": task, "parameters": deepcopy(parameters)}
            )
        return workflow_id, normalized

    def _resolve_value(
        self,
        value: Any,
        *,
        current_index: int,
        invocations: list[dict[str, Any]],
        records_by_id: dict[str, dict[str, Any]],
    ) -> Any:
        if isinstance(value, list):
            return [
                self._resolve_value(
                    item,
                    current_index=current_index,
                    invocations=invocations,
                    records_by_id=records_by_id,
                )
                for item in value
            ]
        if isinstance(value, dict):
            if "$ref" in value:
                if set(value) != {"$ref"} or not isinstance(value["$ref"], str):
                    raise ResultReferenceError("a result reference must contain only string $ref")
                return self._resolve_ref(
                    value["$ref"],
                    current_index=current_index,
                    invocations=invocations,
                    records_by_id=records_by_id,
                )
            return {
                key: self._resolve_value(
                    item,
                    current_index=current_index,
                    invocations=invocations,
                    records_by_id=records_by_id,
                )
                for key, item in value.items()
            }
        return deepcopy(value)

    def _resolve_ref(
        self,
        reference: str,
        *,
        current_index: int,
        invocations: list[dict[str, Any]],
        records_by_id: dict[str, dict[str, Any]],
    ) -> Any:
        parts = reference.split(".")
        if len(parts) < 3 or parts[1] != "result" or any(not part for part in parts):
            raise ResultReferenceError(
                "invalid result reference syntax",
                details={"reference": reference},
            )
        invocation_id = parts[0]
        prior_ids = {item["id"] for item in invocations[:current_index]}
        all_ids = {item["id"] for item in invocations}
        if invocation_id not in all_ids:
            raise ResultReferenceError(
                "result reference names an unknown invocation",
                details={"reference": reference},
            )
        if invocation_id not in prior_ids:
            raise ResultReferenceError(
                "result reference does not name an earlier invocation",
                details={"reference": reference},
            )
        record = records_by_id.get(invocation_id)
        if record is None or record["status"] != "success":
            raise ResultReferenceError(
                "referenced invocation did not complete successfully",
                details={"reference": reference},
            )
        current: Any = record["result"]
        for field in parts[2:]:
            if not isinstance(current, dict) or field not in current:
                raise ResultReferenceError(
                    "referenced result field does not exist",
                    details={"reference": reference},
                )
            current = current[field]
        return deepcopy(current)
