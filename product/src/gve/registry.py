from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Callable

from .authority import Authority
from .errors import UnknownTaskError

_TASK_ID = re.compile(r"^[a-z][a-z0-9-]*\.[a-z][a-z0-9-]*$")

Validator = Callable[[dict[str, Any], Authority], dict[str, Any]]
Executor = Callable[[dict[str, Any], Authority], dict[str, Any]]


@dataclass(frozen=True)
class TaskDefinition:
    identity: str
    validate: Validator
    execute: Executor

    def __post_init__(self) -> None:
        if not _TASK_ID.fullmatch(self.identity):
            raise ValueError(f"invalid task identity: {self.identity}")


class Registry:
    """Exact one-to-one mapping from qualified task identity to implementation."""

    def __init__(self, tasks: list[TaskDefinition] | tuple[TaskDefinition, ...] = ()) -> None:
        mapping: dict[str, TaskDefinition] = {}
        for task in tasks:
            if task.identity in mapping:
                raise ValueError(f"duplicate task identity: {task.identity}")
            mapping[task.identity] = task
        self._tasks = mapping

    def resolve(self, identity: str) -> TaskDefinition:
        task = self._tasks.get(identity)
        if task is None:
            raise UnknownTaskError(f"unknown task: {identity}", details={"task": identity})
        return task

    def identities(self) -> tuple[str, ...]:
        return tuple(sorted(self._tasks))
