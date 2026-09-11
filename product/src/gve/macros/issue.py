from __future__ import annotations

from collections.abc import Mapping
from ..errors import PayloadError
from ..macro import MacroDefinition, MacroPlan, MacroStage

PARAMETER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["operation"],
    "properties": {
        "operation": {"enum": ["read", "create", "modify"]},
        "number": {"type": "integer", "minimum": 1},
        "title": {"type": "string", "minLength": 1},
        "body": {"type": "string"},
        "labels": {"type": "array", "items": {"type": "string", "minLength": 1}},
        "state": {"enum": ["open", "closed"]},
    },
}

def _number(v):
    if isinstance(v, bool) or not isinstance(v, int) or v <= 0:
        raise PayloadError("issue number must be a positive integer")
    return v

def _text(v, field, allow_empty=False):
    if not isinstance(v, str) or (not allow_empty and not v):
        raise PayloadError(f"issue {field} has invalid value")
    return v

def _labels(v):
    if not isinstance(v, list) or any(not isinstance(x, str) or not x for x in v):
        raise PayloadError("issue labels must be an array of non-empty strings")
    return list(v)

def _validate(p: Mapping[str, object]):
    op = p.get("operation")
    if op not in {"read", "create", "modify"}:
        raise PayloadError("issue operation must be read, create, or modify")

    if op == "read":
        extra = set(p) - {"operation", "number"}
        if extra:
            raise PayloadError("issue read contains unknown fields", details={"extra": sorted(extra)})
        if "number" not in p:
            raise PayloadError("issue read requires number")
        return op, {"number": _number(p["number"])}

    if op == "create":
        extra = set(p) - {"operation", "title", "body", "labels"}
        if extra:
            raise PayloadError("issue create contains unknown fields", details={"extra": sorted(extra)})
        if "title" not in p:
            raise PayloadError("issue create requires title")
        return op, {
            "title": _text(p["title"], "title"),
            "body": _text(p.get("body", ""), "body", True),
            "labels": _labels(p.get("labels", [])),
        }

    extra = set(p) - {"operation", "number", "title", "body", "labels", "state"}
    if extra:
        raise PayloadError("issue modify contains unknown fields", details={"extra": sorted(extra)})
    if "number" not in p:
        raise PayloadError("issue modify requires number")
    out = {"number": _number(p["number"])}
    fields = [x for x in ("title", "body", "labels", "state") if x in p]
    if not fields:
        raise PayloadError("issue modify requires at least one mutation field")
    if "title" in p:
        out["title"] = _text(p["title"], "title")
    if "body" in p:
        out["body"] = _text(p["body"], "body", True)
    if "labels" in p:
        out["labels"] = _labels(p["labels"])
    if "state" in p:
        if p["state"] not in {"open", "closed"}:
            raise PayloadError("issue state must be open or closed")
        out["state"] = p["state"]
    return op, out

def build_issue(parameters: Mapping[str, object]) -> MacroPlan:
    op, task_parameters = _validate(parameters)
    task = {
        "read": "github.issue-read",
        "create": "github.issue-create",
        "modify": "github.issue-modify",
    }[op]
    return MacroPlan(
        f"macro-issue-{op}",
        (MacroStage("issue", "ISSUE", ({
            "id": f"issue-{op}",
            "task": task,
            "parameters": task_parameters,
        },)),),
    )

ISSUE = MacroDefinition(
    identity="issue",
    parameter_schema=PARAMETER_SCHEMA,
    stages=("ISSUE",),
    build=build_issue,
)
