from __future__ import annotations

import posixpath
from pathlib import PurePosixPath
from collections.abc import Mapping

from ..errors import PayloadError
from ..macro import MacroDefinition, MacroPlan, MacroStage
from ..plugins.execute import HARD_LIMITS

_SHA256 = set("0123456789abcdef")

PARAMETER_SCHEMA = {'type': 'object',
 'additionalProperties': False,
 'required': ['changes', 'commit_message', 'expected_head'],
 'properties': {'changes': {'type': 'array',
                            'minItems': 1,
                            'x-gve-unique-path-field-after-normalization': 'path',
                            'items': {'oneOf': [{'type': 'object',
                                                 'additionalProperties': False,
                                                 'required': ['operation', 'path', 'content'],
                                                 'properties': {'operation': {'enum': ['create']},
                                                                'path': {'type': 'string',
                                                                         'minLength': 1,
                                                                         'x-gve-format': 'repository-relative-path'},
                                                                'content': {'type': 'string'}}},
                                                {'type': 'object',
                                                 'additionalProperties': False,
                                                 'required': ['operation',
                                                              'path',
                                                              'content',
                                                              'expected_sha256'],
                                                 'properties': {'operation': {'enum': ['modify']},
                                                                'path': {'type': 'string',
                                                                         'minLength': 1,
                                                                         'x-gve-format': 'repository-relative-path'},
                                                                'content': {'type': 'string'},
                                                                'expected_sha256': {'type': 'string',
                                                                                    'pattern': '^[0-9a-f]{64}$'}}}]}},
                'commit_message': {'type': 'string', 'minLength': 1},
                'expected_head': {'type': 'string', 'pattern': '^[0-9a-f]{40}$'},
                'branch': {'type': 'object',
                           'additionalProperties': False,
                           'required': ['create', 'name'],
                           'properties': {'create': {'enum': [True]},
                                          'name': {'type': 'string',
                                                   'minLength': 1,
                                                   'x-gve-format': 'git-branch'}}},
                'remote_branch': {'type': 'string', 'minLength': 1, 'x-gve-format': 'git-branch'},
                'validate': {'type': 'boolean'},
                'allow_dirty': {'type': 'boolean'},
                'allowed_dirty_paths': {'type': 'array',
                                        'uniqueItems': True,
                                        'x-gve-unique-after-normalization': True,
                                        'items': {'type': 'string',
                                                  'minLength': 1,
                                                  'x-gve-format': 'repository-relative-path'}}}}



STAGES = ("PRECHECK", "BRANCH", "MUTATE", "VALIDATE", "COMMIT", "PUBLISH", "VERIFY")


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


def _git_oid(value, field="expected_head"):
    if (
        not isinstance(value, str)
        or len(value) != 40
        or any(ch not in _SHA256 for ch in value)
    ):
        raise PayloadError(f"modify {field} must be lowercase 40-character Git object ID")
    return value


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
        "expected_head",
        "branch",
        "remote_branch",
        "validate",
        "allow_dirty",
        "allowed_dirty_paths",
    }
    extra = set(parameters) - allowed
    missing = {"changes", "commit_message", "expected_head"} - set(parameters)
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
    expected_head = _git_oid(parameters["expected_head"])

    branch = parameters.get("branch")
    normalized_branch = None
    if branch is not None:
        if not isinstance(branch, Mapping):
            raise PayloadError("modify branch must be an object")
        extra_branch = set(branch) - {"create", "name"}
        missing_branch = {"create", "name"} - set(branch)
        if extra_branch or missing_branch:
            raise PayloadError(
                "invalid modify branch fields",
                details={"unknown": sorted(extra_branch), "missing": sorted(missing_branch)},
            )
        if branch["create"] is not True:
            raise PayloadError("modify branch.create must be true")
        normalized_branch = {
            "create": True,
            "name": _text(branch["name"], "branch.name"),
        }

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
        "expected_head": expected_head,
        "branch": normalized_branch,
        "remote_branch": remote_branch,
        "validate": validate,
        "allow_dirty": allow_dirty,
        "allowed_dirty_paths": dirty_paths,
    }


def build_modify(parameters: Mapping[str, object]) -> MacroPlan:
    p = _validate(parameters)
    branch_requested = p["branch"] is not None
    effective_local_branch = (
        p["branch"]["name"]
        if branch_requested
        else {"$ref": "modify-branch.result.branch"}
    )
    publication_branch = (
        p["remote_branch"]
        if p["remote_branch"] is not None
        else effective_local_branch
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
            {
                "id": "modify-head",
                "task": "git.head",
                "parameters": {"expected": p["expected_head"]},
            },
            status_task,
            {
                "id": "modify-staged-before",
                "task": "git.staged-scope",
                "parameters": {"allowed_paths": p["change_paths"]},
            },
            {
                "id": "modify-remote-before",
                "task": "git.remote-head",
                "parameters": {"remote": "origin", "branch": publication_branch},
            },
        ),
    )

    branch_tasks = ()
    if branch_requested:
        branch_tasks = (
            {
                "id": "modify-branch-create",
                "task": "git.branch-create",
                "parameters": {"name": p["branch"]["name"], "start": p["expected_head"]},
            },
            {
                "id": "modify-branch-switch",
                "task": "git.branch-switch",
                "parameters": {"name": p["branch"]["name"]},
            },
            {
                "id": "modify-branch-created-guard",
                "task": "git.branch",
                "parameters": {"expected": p["branch"]["name"]},
            },
            {
                "id": "modify-branch-head-guard",
                "task": "git.head",
                "parameters": {"expected": p["expected_head"]},
            },
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
                "parameters": {"expected": effective_local_branch},
            },
            {
                "id": "modify-head-guard",
                "task": "git.head",
                "parameters": {"expected": p["expected_head"]},
            },
            {
                "id": "modify-status-guard",
                "task": "git.status-scope",
                "parameters": {"allowed_paths": allowed_after, "include_untracked": True},
            },
            {
                "id": "modify-pending-diff-check",
                "task": "git.pending-diff-check",
                "parameters": {"paths": p["change_paths"]},
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
                    "local_branch": effective_local_branch,
                    "remote_branch": publication_branch,
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
                    "branch": publication_branch,
                    "expected": {"$ref": "modify-commit.result.commit"},
                },
            },
        ),
    )

    return MacroPlan(
        "macro-modify",
        (
            precheck,
            MacroStage("branch", "BRANCH", branch_tasks),
            MacroStage("mutate", "MUTATE", tuple(mutation_tasks)),
            MacroStage("validate", "VALIDATE", validate_tasks),
            commit_stage,
            publish,
            verify,
        ),
    )


def _record_by_id(engine_result: Mapping[str, object], invocation_id: str):
    tasks = engine_result.get("tasks", [])
    if not isinstance(tasks, list):
        return None
    for record in tasks:
        if isinstance(record, Mapping) and record.get("id") == invocation_id:
            return record
    return None


def _successful_result(engine_result: Mapping[str, object], invocation_id: str):
    record = _record_by_id(engine_result, invocation_id)
    if not isinstance(record, Mapping) or record.get("status") != "success":
        return None
    value = record.get("result")
    return value if isinstance(value, Mapping) else None


def project_modify_result(parameters, plan, engine_result, context):
    p = _validate(parameters)

    pre_branch = _successful_result(engine_result, "modify-branch")
    created_branch = _successful_result(engine_result, "modify-branch-created-guard")
    effective_branch = None
    if p["branch"] is not None:
        if created_branch is not None:
            effective_branch = created_branch.get("branch")
    elif pre_branch is not None:
        effective_branch = pre_branch.get("branch")

    publication_branch = p["remote_branch"] if p["remote_branch"] is not None else effective_branch

    head_result = _successful_result(engine_result, "modify-head")
    observed_head = head_result.get("commit") if head_result is not None else None

    branch_created = False if p["branch"] is None else None
    if p["branch"] is not None and _successful_result(engine_result, "modify-branch-create") is not None:
        branch_created = True

    validation_status = "not-requested"
    if p["validate"]:
        validation_record = _record_by_id(engine_result, "modify-validate")
        if validation_record is None or validation_record.get("status") == "not-executed":
            validation_status = "not-executed"
        elif validation_record.get("status") == "success":
            validation_status = "success"
        else:
            validation_status = "failed"

    diff_result = _successful_result(engine_result, "modify-diff")
    diff = diff_result.get("diff") if diff_result is not None else None
    files_changed = list(p["change_paths"]) if diff_result is not None else None

    commit_result = _successful_result(engine_result, "modify-commit")
    commit = commit_result.get("commit") if commit_result is not None else None

    verify_result = _successful_result(engine_result, "modify-verify")
    remote_head = verify_result.get("commit") if verify_result is not None else None

    return {
        "repository": {
            "root": str(context.root) if context is not None else None,
            "identity": context.identity if context is not None else None,
        },
        "branch": effective_branch,
        "publication_branch": publication_branch,
        "expected_head": p["expected_head"],
        "observed_head": observed_head,
        "branch_created": branch_created,
        "files_changed": files_changed,
        "validation": {"requested": p["validate"], "status": validation_status},
        "diff": diff,
        "commit": commit,
        "commit_count": 1 if commit is not None else 0,
        "push_mode": "normal",
        "remote_head": remote_head,
        "history_rewrite_or_force_push_occurred": False,
        "merge_occurred": False,
    }


MODIFY = MacroDefinition(
    identity="modify",
    parameter_schema=PARAMETER_SCHEMA,
    stages=STAGES,
    build=build_modify,
    project_result=project_modify_result,
)
