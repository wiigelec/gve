from __future__ import annotations

import posixpath
from collections.abc import Mapping
from pathlib import PurePosixPath

from ..errors import PayloadError
from ..macro import MacroDefinition, MacroPlan, MacroStage


OBSERVATIONS = ("repository", "branch", "head", "status", "root_entries", "tree_status")
DEFAULT_OBSERVATIONS = ("repository", "branch", "head", "status")

PARAMETER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "observations": {
            "type": "array",
            "minItems": 1,
            "uniqueItems": True,
            "items": {"enum": list(OBSERVATIONS)},
        },
        "list_folder": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["path"],
                "properties": {
                    "path": {
                        "type": "string",
                        "minLength": 1,
                        "x-gve-format": "repository-relative-path",
                    }
                },
            },
        },
        "read_file": {
            "type": "object",
            "additionalProperties": False,
            "required": ["paths"],
            "properties": {
                "paths": {
                    "type": "array",
                    "minItems": 1,
                    "uniqueItems": True,
                    "x-gve-unique-after-normalization": True,
                    "items": {
                        "type": "string",
                        "minLength": 1,
                        "x-gve-format": "repository-relative-path",
                    },
                }
            },
        },
    },
}

_TASKS = {
    "repository": ("git.repository", {}),
    "branch": ("git.branch", {}),
    "head": ("git.head", {}),
    "status": ("git.status", {"include_untracked": True}),
    "root_entries": ("filesystem.list", {"path": ".", "recursive": False}),
    "tree_status": ("git.tree-status", {}),
}


def _path(value, field):
    if not isinstance(value, str) or not value:
        raise PayloadError(f"discover {field} must be a non-empty string")
    value = value.replace("\\", "/")
    if PurePosixPath(value).is_absolute():
        raise PayloadError(f"discover {field} must be repository-relative")
    normalized = posixpath.normpath(value)
    if normalized in {".."} or normalized.startswith("../"):
        raise PayloadError(f"discover {field} must remain inside the repository")
    return normalized


def _validate(parameters: Mapping[str, object]) -> dict[str, object]:
    allowed = {"observations", "list_folder", "read_file"}
    extra = set(parameters) - allowed
    if extra:
        raise PayloadError(
            "discover parameters contain unknown fields",
            details={"extra": sorted(extra)},
        )

    if "observations" not in parameters:
        selected = DEFAULT_OBSERVATIONS
    else:
        value = parameters["observations"]
        if not isinstance(value, list) or not value:
            raise PayloadError("discover observations must be a non-empty array")
        if any(not isinstance(item, str) for item in value):
            raise PayloadError("discover observations must contain strings")
        if len(set(value)) != len(value):
            raise PayloadError("discover observations must be unique")
        unknown = sorted(set(value) - set(OBSERVATIONS))
        if unknown:
            raise PayloadError(
                "discover observations contain unknown values",
                details={"unknown": unknown},
            )
        wanted = set(value)
        selected = tuple(item for item in OBSERVATIONS if item in wanted)

    folders = []
    if "list_folder" in parameters:
        raw_folders = parameters["list_folder"]
        if not isinstance(raw_folders, list) or not raw_folders:
            raise PayloadError("discover list_folder must be a non-empty array")
        seen = set()
        for index, item in enumerate(raw_folders):
            if not isinstance(item, Mapping) or set(item) != {"path"}:
                raise PayloadError(
                    "discover list_folder item must contain only path",
                    details={"index": index},
                )
            path = _path(item["path"], f"list_folder[{index}].path")
            if path in seen:
                raise PayloadError(
                    "discover list_folder paths must be unique",
                    details={"path": path},
                )
            seen.add(path)
            folders.append(path)

    files = []
    raw_read = parameters.get("read_file")
    if raw_read is not None:
        if not isinstance(raw_read, Mapping) or set(raw_read) != {"paths"}:
            raise PayloadError("discover read_file must contain only paths")
        raw_paths = raw_read["paths"]
        if not isinstance(raw_paths, list) or not raw_paths:
            raise PayloadError("discover read_file.paths must be a non-empty array")
        seen = set()
        for index, value in enumerate(raw_paths):
            path = _path(value, f"read_file.paths[{index}]")
            if path in seen:
                raise PayloadError(
                    "discover read_file paths must be unique",
                    details={"path": path},
                )
            seen.add(path)
            files.append(path)

    return {"observations": selected, "folders": folders, "files": files}


def build_discover(parameters: Mapping[str, object]) -> MacroPlan:
    p = _validate(parameters)
    tasks = []
    for observation in p["observations"]:
        task, task_parameters = _TASKS[observation]
        tasks.append(
            {
                "id": f"discover-{observation.replace('_', '-')}",
                "task": task,
                "parameters": dict(task_parameters),
            }
        )
    for index, path in enumerate(p["folders"], 1):
        tasks.append(
            {
                "id": f"discover-folder-{index:03d}",
                "task": "filesystem.list",
                "parameters": {"path": path, "recursive": False},
            }
        )
    for index, path in enumerate(p["files"], 1):
        tasks.append(
            {
                "id": f"discover-file-{index:03d}",
                "task": "filesystem.file-read",
                "parameters": {"path": path},
            }
        )
    return MacroPlan(
        "macro-discover",
        (MacroStage("discover", "DISCOVER", tuple(tasks)),),
    )


def _record(engine_result, invocation_id):
    tasks = engine_result.get("tasks", [])
    if not isinstance(tasks, list):
        return None
    for record in tasks:
        if isinstance(record, Mapping) and record.get("id") == invocation_id:
            return record
    return None


def project_discover_result(parameters, plan, engine_result, context):
    p = _validate(parameters)
    observations = {}
    for name in p["observations"]:
        record = _record(engine_result, f"discover-{name.replace('_', '-')}")
        if isinstance(record, Mapping) and record.get("status") == "success":
            value = record.get("result")
            if isinstance(value, Mapping):
                observations[name] = dict(value)

    folders = []
    for index, path in enumerate(p["folders"], 1):
        record = _record(engine_result, f"discover-folder-{index:03d}")
        item = {"path": path, "entries": None}
        if isinstance(record, Mapping) and record.get("status") == "success":
            evidence = record.get("observations")
            if isinstance(evidence, Mapping) and isinstance(evidence.get("entries"), list):
                item["entries"] = list(evidence["entries"])
        folders.append(item)

    files = []
    for index, path in enumerate(p["files"], 1):
        record = _record(engine_result, f"discover-file-{index:03d}")
        item = {"path": path, "content": None, "sha256": None}
        if isinstance(record, Mapping) and record.get("status") == "success":
            value = record.get("result")
            if isinstance(value, Mapping):
                item["content"] = value.get("content")
                item["sha256"] = value.get("sha256")
        files.append(item)

    return {
        "repository": {
            "root": str(context.root) if context is not None else None,
            "identity": context.identity if context is not None else None,
        },
        "observations": observations,
        "folders": folders,
        "files": files,
    }


DISCOVER = MacroDefinition(
    identity="discover",
    parameter_schema=PARAMETER_SCHEMA,
    stages=("DISCOVER",),
    build=build_discover,
    project_result=project_discover_result,
)
