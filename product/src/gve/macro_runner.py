from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .authority import Authority
from .engine import Engine
from .errors import PayloadError
from .events import emit_to
from .macro import MacroPlan, MacroRegistry
from .macro_request import MacroRequest


@dataclass(frozen=True)
class RepositoryContext:
    root: Path
    identity: str | None
    branch: str | None
    head: str | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "root", Path(self.root).resolve())


def _verify_expectations(request: MacroRequest, context: RepositoryContext) -> None:
    expected = request.repository
    checks = (
        ("identity", expected.identity, context.identity),
        ("branch", expected.branch, context.branch),
        ("head", expected.head, context.head),
    )
    for field, wanted, observed in checks:
        if wanted is not None and wanted != observed:
            raise PayloadError(
                f"repository {field} expectation mismatch",
                details={"field": field, "expected": wanted, "observed": observed},
            )


def _validate_plan(definition_stages: tuple[str, ...], plan: MacroPlan) -> None:
    observed = tuple(stage.label for stage in plan.stages)
    if definition_stages and observed != definition_stages:
        raise PayloadError(
            "macro plan stages do not match public stage contract",
            details={"expected": list(definition_stages), "observed": list(observed)},
        )

    invocation_ids: set[str] = set()
    for stage in plan.stages:
        for invocation in stage.tasks:
            invocation_id = invocation.get("id")
            if not isinstance(invocation_id, str) or not invocation_id:
                raise PayloadError("generated macro invocation requires non-empty id")
            if invocation_id in invocation_ids:
                raise PayloadError(
                    "generated macro invocation ids must be unique",
                    details={"id": invocation_id},
                )
            invocation_ids.add(invocation_id)


def _flatten(plan: MacroPlan) -> list[dict]:
    tasks: list[dict] = []
    for stage in plan.stages:
        for invocation in stage.tasks:
            tasks.append(dict(invocation))
    if not tasks:
        raise PayloadError("macro plan must generate at least one FS-001 task invocation")
    return tasks


def _group(plan: MacroPlan, engine_result: Mapping[str, object]) -> list[dict]:
    records = engine_result.get("tasks", [])
    if not isinstance(records, list):
        raise PayloadError("Engine result tasks must be an array")

    expected_ids = [
        invocation["id"]
        for stage in plan.stages
        for invocation in stage.tasks
    ]
    observed_ids: list[str] = []
    for record in records:
        if not isinstance(record, dict):
            raise PayloadError("Engine task record must be an object")
        invocation_id = record.get("id")
        if not isinstance(invocation_id, str):
            raise PayloadError("Engine task record requires string id")
        observed_ids.append(invocation_id)

    if len(set(observed_ids)) != len(observed_ids):
        raise PayloadError(
            "Engine task record ids must be unique",
            details={"observed": observed_ids},
        )

    if observed_ids != expected_ids:
        raise PayloadError(
            "Engine task records do not match generated macro invocation order",
            details={"expected": expected_ids, "observed": observed_ids},
        )

    grouped: list[dict] = []
    cursor = 0
    for stage in plan.stages:
        count = len(stage.tasks)
        grouped.append(
            {
                "id": stage.identity,
                "label": stage.label,
                "tasks": records[cursor:cursor + count],
            }
        )
        cursor += count
    return grouped


class MacroRunner:
    def __init__(self, engine: Engine, macros: MacroRegistry) -> None:
        self.engine = engine
        self.macros = macros

    def execute(
        self,
        request: MacroRequest,
        authority: Authority,
        context: RepositoryContext,
        observer=None,
    ) -> dict:
        if authority.repository.resolve() != context.root:
            raise PayloadError(
                "repository context does not match active repository authority",
                details={
                    "authority_repository": str(authority.repository.resolve()),
                    "context_repository": str(context.root),
                },
            )

        _verify_expectations(request, context)

        try:
            definition = self.macros.resolve(request.macro_name)
        except KeyError as exc:
            raise PayloadError(str(exc)) from exc

        plan = definition.build(dict(request.parameters))
        if not isinstance(plan, MacroPlan):
            raise PayloadError("macro builder must return MacroPlan")

        _validate_plan(definition.stages, plan)
        tasks = _flatten(plan)

        phase_by_task = {}
        for stage in plan.stages:
            for invocation in stage.tasks:
                phase_by_task[invocation["id"]] = stage.label
        emit_to(observer, "macro-start", macro=request.macro_name, phase_count=len(plan.stages))
        current_phase = None
        def engine_observer(event):
            nonlocal current_phase
            if event.get("type") == "task-start":
                phase = phase_by_task.get(event.get("id"))
                if phase is not None and phase != current_phase:
                    current_phase = phase
                    emit_to(observer, "phase-start", label=phase)
            if observer is not None:
                observer(event)

        engine_result = self.engine.execute(
            {
                "schema_version": 1,
                "workflow_id": plan.workflow_id,
                "tasks": tasks,
            },
            authority,
            observer=engine_observer,
        )
        if not isinstance(engine_result, dict):
            raise PayloadError("Engine returned non-object result")

        status = engine_result.get("status")
        if status not in {"success", "failure"}:
            raise PayloadError("Engine result has invalid status")

        result = {
            "schema_version": 1,
            "macro": request.macro_name,
            "status": status,
            "stages": _group(plan, engine_result),
            "tasks": engine_result.get("tasks", []),
        }
        if definition.project_result is not None:
            projected = definition.project_result(
                dict(request.parameters),
                plan,
                engine_result,
                context,
            )
            if not isinstance(projected, Mapping):
                raise PayloadError("macro result projector must return an object")
            result["result"] = dict(projected)
        if "error" in engine_result:
            result["error"] = engine_result["error"]
        return result
