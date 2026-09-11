from __future__ import annotations

import posixpath
from pathlib import PurePosixPath
from collections.abc import Mapping

from ..errors import PayloadError
from ..macro import MacroDefinition, MacroPlan, MacroStage
from ..plugins.execute import HARD_LIMITS

_SHA256 = set("0123456789abcdef")

PARAMETER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["changes", "commit_message"],
    "properties": {
        "changes": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["operation", "path", "content"],
                "properties": {
                    "operation": {"enum": ["create", "modify"]},
                    "path": {"type": "string", "minLength": 1},
                    "content": {"type": "string"},
                    "expected_sha256": {
                        "type": "string",
                        "pattern": "^[0-9a-f]{64}$",
                    },
                },
            },
        },
        "commit_message": {"type": "string", "minLength": 1},
        "remote_branch": {"type": "string", "minLength": 1},
        "validate": {"type": "boolean"},
        "allow_dirty": {"type": "boolean"},
        "allowed_dirty_paths": {
            "type": "array",
            "uniqueItems": True,
            "items": {"type": "string", "minLength": 1},
        },
    },
}

STAGES = ("PRECHECK", "MUTATE", "VALIDATE", "COMMIT", "PUBLISH", "VERIFY")


def _text(value, field, *, allow_empty=False):
    if not isinstance(value, str) or (not allow_empty and not value):
        raise PayloadError(f"modify {field} has invalid value")
    return value


def _bool(value, field):
    if not isinstance(value, bool):
        raise PayloadError(f"modify {field} must be boolean")
    return value


def _path(value, field):
    value = _text(value, field).replace("\\", "/")
    if PurePosixPath(value).is_absolute():
        raise PayloadError(f"modify {field} must be repository-relative")
    normalized = posixpath.normpath(value)
    if normalized in {".", ".."} or normalized.startswith("../"):
        raise PayloadError(f"modify {field} must remain inside the repository")
    return normalized


def _digest(value):
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(ch not in _SHA256 for ch in value)
    ):
        raise PayloadError("modify expected_sha256 must be lowercase SHA-256")
    return value


def _validate(parameters: Mapping[str, object]) -> dict[str, object]:
    allowed = {
        "changes",
        "commit_message",
        "remote_branch",
        "validate",
        "allow_dirty",
        "allowed_dirty_paths",
    }
    extra = set(parameters) - allowed
    missing = {"changes", "commit_message"} - set(parameters)
    if extra or missing:
        raise PayloadError(
            "invalid modify parameters",
            details={"unknown": sorted(extra), "missing": sorted(missing)},
        )

    changes = parameters["changes"]
    if not isinstance(changes, list) or not changes:
        raise PayloadError("modify changes must be a non-empty array")

    normalized_changes = []
    seen_paths = set()
    for index, raw in enumerate(changes):
        if not isinstance(raw, Mapping):
            raise PayloadError("modify change must be an object", details={"index": index})
        op = raw.get("operation")
        if op not in {"create", "modify"}:
            raise PayloadError("modify change operation must be create or modify")
        allowed_change = {"operation", "path", "content"}
        required_change = {"operation", "path", "content"}
        if op == "modify":
            allowed_change.add("expected_sha256")
            required_change.add("expected_sha256")
        extra_change = set(raw) - allowed_change
        missing_change = required_change - set(raw)
        if extra_change or missing_change:
            raise PayloadError(
                "invalid modify change fields",
                details={
                    "index": index,
                    "unknown": sorted(extra_change),
                    "missing": sorted(missing_change),
                },
            )
        path = _path(raw["path"], f"changes[{index}].path")
        if path in seen_paths:
            raise PayloadError("modify change paths must be unique", details={"path": path})
        seen_paths.add(path)
        item = {
            "operation": op,
            "path": path,
            "content": _text(raw["content"], f"changes[{index}].content", allow_empty=True),
        }
        if op == "modify":
            item["expected_sha256"] = _digest(raw["expected_sha256"])
        normalized_changes.append(item)

    commit_message = _text(parameters["commit_message"], "commit_message")
    remote_branch = parameters.get("remote_branch")
    if remote_branch is not None:
        remote_branch = _text(remote_branch, "remote_branch")

    validate = _bool(parameters.get("validate", True), "validate")
    allow_dirty = _bool(parameters.get("allow_dirty", False), "allow_dirty")

    raw_dirty = parameters.get("allowed_dirty_paths", [])
    if not isinstance(raw_dirty, list):
        raise PayloadError("modify allowed_dirty_paths must be an array")
    dirty_paths = []
    seen_dirty = set()
    for index, raw_path in enumerate(raw_dirty):
        path = _path(raw_path, f"allowed_dirty_paths[{index}]")
        if path in seen_dirty:
            raise PayloadError("modify allowed_dirty_paths must be unique", details={"path": path})
        seen_dirty.add(path)
        dirty_paths.append(path)

    return {
        "changes": normalized_changes,
        "change_paths": [item["path"] for item in normalized_changes],
        "commit_message": commit_message,
        "remote_branch": remote_branch,
        "validate": validate,
        "allow_dirty": allow_dirty,
        "allowed_dirty_paths": dirty_paths,
    }


def build_modify(parameters: Mapping[str, object]) -> MacroPlan:
    p = _validate(parameters)
    branch_value = (
        p["remote_branch"]
        if p["remote_branch"] is not None
        else {"$ref": "modify-branch.result.branch"}
    )

    if p["allow_dirty"]:
        status_task = {
            "id": "modify-status",
            "task": "git.status-scope",
            "parameters": {
                "allowed_paths": p["allowed_dirty_paths"],
                "include_untracked": True,
            },
        }
    else:
        status_task = {
            "id": "modify-status",
            "task": "git.status",
            "parameters": {"expected_clean": True, "include_untracked": True},
        }

    precheck = MacroStage(
        "precheck",
        "PRECHECK",
        (
            {"id": "modify-repository", "task": "git.repository", "parameters": {}},
            {"id": "modify-branch", "task": "git.branch", "parameters": {}},
            {"id": "modify-head", "task": "git.head", "parameters": {}},
            status_task,
            {
                "id": "modify-remote-before",
                "task": "git.remote-head",
                "parameters": {"remote": "origin", "branch": branch_value},
            },
        ),
    )

    mutation_tasks = []
    for index, change in enumerate(p["changes"], 1):
        if change["operation"] == "create":
            task = "filesystem.file-create"
            task_parameters = {"path": change["path"], "content": change["content"]}
        else:
            task = "filesystem.file-modify"
            task_parameters = {
                "path": change["path"],
                "expected_sha256": change["expected_sha256"],
                "content": change["content"],
            }
        mutation_tasks.append(
            {
                "id": f"modify-change-{index:03d}",
                "task": task,
                "parameters": task_parameters,
            }
        )

    validate_tasks = ()
    if p["validate"]:
        validate_tasks = (
            {
                "id": "modify-validate",
                "task": "execute.script",
                "parameters": {
                    "script": "scripts/validate",
                    "args": [],
                    "working_directory": ".",
                    "limits": dict(HARD_LIMITS),
                },
            },
        )

    allowed_after = list(p["change_paths"])
    for path in p["allowed_dirty_paths"]:
        if path not in allowed_after:
            allowed_after.append(path)

    commit_stage = MacroStage(
        "commit",
        "COMMIT",
        (
            {
                "id": "modify-repository-guard",
                "task": "git.repository",
                "parameters": {
                    "expected_remotes": {
                        "origin": {"$ref": "modify-repository.result.remotes.origin"}
                    }
                },
            },
            {
                "id": "modify-branch-guard",
                "task": "git.branch",
                "parameters": {"expected": {"$ref": "modify-branch.result.branch"}},
            },
            {
                "id": "modify-head-guard",
                "task": "git.head",
                "parameters": {"expected": {"$ref": "modify-head.result.commit"}},
            },
            {
                "id": "modify-status-guard",
                "task": "git.status-scope",
                "parameters": {"allowed_paths": allowed_after, "include_untracked": True},
            },
            {
                "id": "modify-add",
                "task": "git.add",
                "parameters": {"paths": p["change_paths"]},
            },
            {
                "id": "modify-staged-scope",
                "task": "git.staged-scope",
                "parameters": {"allowed_paths": p["change_paths"]},
            },
            {
                "id": "modify-diff",
                "task": "git.diff",
                "parameters": {"cached": True, "paths": p["change_paths"]},
            },
            {
                "id": "modify-diff-check",
                "task": "git.diff-check",
                "parameters": {"cached": True, "paths": p["change_paths"]},
            },
            {
                "id": "modify-commit",
                "task": "git.commit",
                "parameters": {"message": p["commit_message"]},
            },
        ),
    )

    publish = MacroStage(
        "publish",
        "PUBLISH",
        (
            {
                "id": "modify-push",
                "task": "git.push",
                "parameters": {
                    "remote": "origin",
                    "local_branch": {"$ref": "modify-branch.result.branch"},
                    "remote_branch": branch_value,
                    "expected_remote_head": {"$ref": "modify-remote-before.result.commit"},
                },
            },
        ),
    )

    verify = MacroStage(
        "verify",
        "VERIFY",
        (
            {
                "id": "modify-verify",
                "task": "git.remote-head",
                "parameters": {
                    "remote": "origin",
                    "branch": branch_value,
                    "expected": {"$ref": "modify-commit.result.commit"},
                },
            },
        ),
    )

    return MacroPlan(
        "macro-modify",
        (
            precheck,
            MacroStage("mutate", "MUTATE", tuple(mutation_tasks)),
            MacroStage("validate", "VALIDATE", validate_tasks),
            commit_stage,
            publish,
            verify,
        ),
    )


MODIFY = MacroDefinition(
    identity="modify",
    parameter_schema=PARAMETER_SCHEMA,
    stages=STAGES,
    build=build_modify,
)
