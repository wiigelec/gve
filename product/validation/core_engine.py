from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "product" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gve.authority import Authority
from gve.engine import Engine
from gve.errors import GVEError
from gve.registry import Registry, TaskDefinition

DESIGN_REVISION = "6cc46250b8aac3934663be906acd41601791c04f"


def _identity(parameters: dict[str, Any], authority: Authority) -> dict[str, Any]:
    return parameters


def validate_planning_binding() -> bool:
    for relative in (
        "product/planning/FS-001-functional-set.md",
        "product/planning/FS-001-plan.md",
        "product/specs/FS-001-core-governed-repository-execution.md",
    ):
        text = (ROOT / relative).read_text(encoding="utf-8")
        if DESIGN_REVISION not in text:
            raise AssertionError(f"{relative} does not bind accepted Product Design revision")
    return True


def validate_core_engine() -> bool:
    calls: list[str] = []

    def emit(parameters: dict[str, Any], authority: Authority) -> dict[str, Any]:
        calls.append(parameters.get("name", "emit"))
        return {
            "observations": {"seen": True},
            "effects": {},
            "result": {"value": parameters.get("value"), "nested": {"x": 7}},
        }

    def consume(parameters: dict[str, Any], authority: Authority) -> dict[str, Any]:
        calls.append("consume")
        if parameters["input"] != 7:
            raise GVEError("unexpected consumed value")
        return {"result": {"accepted": parameters["input"]}}

    def fail_task(parameters: dict[str, Any], authority: Authority) -> dict[str, Any]:
        calls.append("fail")
        raise GVEError("expected failure", details={"kind": "test"})

    registry = Registry(
        [
            TaskDefinition("test.emit", _identity, emit),
            TaskDefinition("test.consume", _identity, consume),
            TaskDefinition("test.fail", _identity, fail_task),
        ]
    )
    authority = Authority.for_repository(ROOT)
    engine = Engine(registry)

    try:
        Registry(
            [
                TaskDefinition("test.same", _identity, emit),
                TaskDefinition("test.same", _identity, emit),
            ]
        )
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate registry identity was accepted")

    invalid = engine.execute(
        {"schema_version": 1, "workflow_id": "x", "tasks": [], "extra": True},
        authority,
    )
    assert invalid["status"] == "failure"
    assert invalid["error"]["code"] == "invalid-payload"
    assert invalid["tasks"] == []

    duplicate_ids = engine.execute(
        {
            "schema_version": 1,
            "workflow_id": "x",
            "tasks": [
                {"id": "same", "task": "test.emit", "parameters": {}},
                {"id": "same", "task": "test.emit", "parameters": {}},
            ],
        },
        authority,
    )
    assert duplicate_ids["status"] == "failure"
    assert duplicate_ids["error"]["code"] == "invalid-payload"

    calls.clear()
    success = engine.execute(
        {
            "schema_version": 1,
            "workflow_id": "ordered-ref",
            "tasks": [
                {
                    "id": "first",
                    "task": "test.emit",
                    "parameters": {"name": "first", "value": 3},
                },
                {
                    "id": "second",
                    "task": "test.consume",
                    "parameters": {"input": {"$ref": "first.result.nested.x"}},
                },
            ],
        },
        authority,
    )
    assert success["status"] == "success"
    assert calls == ["first", "consume"]
    assert [item["id"] for item in success["tasks"]] == ["first", "second"]
    assert success["tasks"][1]["result"]["accepted"] == 7

    calls.clear()
    bad_ref = engine.execute(
        {
            "schema_version": 1,
            "workflow_id": "bad-ref",
            "tasks": [
                {"id": "first", "task": "test.emit", "parameters": {"value": 1}},
                {
                    "id": "second",
                    "task": "test.consume",
                    "parameters": {"input": {"$ref": "first.observations.seen"}},
                },
                {"id": "third", "task": "test.emit", "parameters": {}},
            ],
        },
        authority,
    )
    assert bad_ref["status"] == "failure"
    assert bad_ref["tasks"][1]["error"]["code"] == "result-reference"
    assert bad_ref["tasks"][2]["status"] == "not-executed"
    assert bad_ref["tasks"][2]["reason"] == "prior-task-failure"
    assert calls == ["emit"]

    calls.clear()
    failed = engine.execute(
        {
            "schema_version": 1,
            "workflow_id": "fail-fast",
            "tasks": [
                {"id": "one", "task": "test.emit", "parameters": {"name": "one"}},
                {"id": "two", "task": "test.fail", "parameters": {}},
                {"id": "three", "task": "test.emit", "parameters": {"name": "three"}},
            ],
        },
        authority,
    )
    assert failed["status"] == "failure"
    assert calls == ["one", "fail"]
    assert failed["tasks"][0]["status"] == "success"
    assert failed["tasks"][1]["status"] == "failure"
    assert failed["tasks"][1]["error"]["code"] == "task-execution"
    assert failed["tasks"][2]["status"] == "not-executed"

    unknown = engine.execute(
        {
            "schema_version": 1,
            "workflow_id": "unknown",
            "tasks": [{"id": "x", "task": "not.registered", "parameters": {}}],
        },
        authority,
    )
    assert unknown["tasks"][0]["error"]["code"] == "unknown-task"

    encoded = json.dumps(success, sort_keys=True)
    assert '"status": "success"' in encoded
    return True
