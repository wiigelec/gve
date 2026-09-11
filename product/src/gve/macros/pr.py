from __future__ import annotations

from collections.abc import Mapping
from ..errors import PayloadError
from ..macro import MacroDefinition, MacroPlan, MacroStage

PARAMETER_SCHEMA = {'type': 'object',
 'oneOf': [{'additionalProperties': False,
            'required': ['operation', 'number'],
            'properties': {'operation': {'enum': ['read']},
                           'number': {'type': 'integer', 'minimum': 1}}},
           {'additionalProperties': False,
            'required': ['operation', 'title', 'base', 'head'],
            'properties': {'operation': {'enum': ['create']},
                           'title': {'type': 'string', 'minLength': 1},
                           'body': {'type': 'string'},
                           'base': {'type': 'string', 'minLength': 1},
                           'head': {'type': 'string', 'minLength': 1},
                           'draft': {'type': 'boolean'}}},
           {'additionalProperties': False,
            'required': ['operation', 'number'],
            'anyOf': [{'required': ['title']},
                      {'required': ['body']},
                      {'required': ['base']},
                      {'required': ['state']}],
            'properties': {'operation': {'enum': ['modify']},
                           'number': {'type': 'integer', 'minimum': 1},
                           'title': {'type': 'string', 'minLength': 1},
                           'body': {'type': 'string'},
                           'base': {'type': 'string', 'minLength': 1},
                           'state': {'enum': ['open', 'closed']}}}]}


def _number(v):
    if isinstance(v, bool) or not isinstance(v, int) or v <= 0:
        raise PayloadError("pull request number must be a positive integer")
    return v

def _text(v, field, allow_empty=False):
    if not isinstance(v, str) or (not allow_empty and not v):
        raise PayloadError(f"pull request {field} has invalid value")
    return v

def _validate(p: Mapping[str, object]):
    op = p.get("operation")
    if op not in {"read", "create", "modify"}:
        raise PayloadError("pr operation must be read, create, or modify")

    if op == "read":
        extra = set(p) - {"operation", "number"}
        if extra:
            raise PayloadError("pr read contains unknown fields", details={"extra": sorted(extra)})
        if "number" not in p:
            raise PayloadError("pr read requires number")
        return op, {"number": _number(p["number"])}

    if op == "create":
        allowed = {"operation", "title", "body", "base", "head", "draft"}
        extra = set(p) - allowed
        if extra:
            raise PayloadError("pr create contains unknown fields", details={"extra": sorted(extra)})
        missing = {"title", "base", "head"} - set(p)
        if missing:
            raise PayloadError("pr create missing required fields", details={"missing": sorted(missing)})
        draft = p.get("draft", False)
        if not isinstance(draft, bool):
            raise PayloadError("pr draft must be boolean")
        return op, {
            "title": _text(p["title"], "title"),
            "body": _text(p.get("body", ""), "body", True),
            "base": _text(p["base"], "base"),
            "head": _text(p["head"], "head"),
            "draft": draft,
        }

    allowed = {"operation", "number", "title", "body", "base", "state"}
    extra = set(p) - allowed
    if extra:
        raise PayloadError("pr modify contains unknown fields", details={"extra": sorted(extra)})
    if "number" not in p:
        raise PayloadError("pr modify requires number")
    out = {"number": _number(p["number"])}
    fields = [x for x in ("title", "body", "base", "state") if x in p]
    if not fields:
        raise PayloadError("pr modify requires at least one mutation field")
    if "title" in p:
        out["title"] = _text(p["title"], "title")
    if "body" in p:
        out["body"] = _text(p["body"], "body", True)
    if "base" in p:
        out["base"] = _text(p["base"], "base")
    if "state" in p:
        if p["state"] not in {"open", "closed"}:
            raise PayloadError("pr state must be open or closed")
        out["state"] = p["state"]
    return op, out

def build_pr(parameters: Mapping[str, object]) -> MacroPlan:
    op, task_parameters = _validate(parameters)
    task = {
        "read": "github.pull-request-read",
        "create": "github.pull-request-create",
        "modify": "github.pull-request-modify",
    }[op]
    return MacroPlan(
        f"macro-pr-{op}",
        (MacroStage("pr", "PR", ({
            "id": f"pr-{op}",
            "task": task,
            "parameters": task_parameters,
        },)),),
    )

PR = MacroDefinition(
    identity="pr",
    parameter_schema=PARAMETER_SCHEMA,
    stages=("PR",),
    build=build_pr,
)
