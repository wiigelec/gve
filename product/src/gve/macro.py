from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Callable, Mapping, Sequence


MacroBuilder = Callable[..., object]


@dataclass(frozen=True)
class MacroDefinition:
    """Stable public macro metadata plus the authoritative product builder."""

    identity: str
    parameter_schema: Mapping[str, object]
    stages: tuple[str, ...]
    build: MacroBuilder

    def __post_init__(self) -> None:
        if not isinstance(self.identity, str) or not self.identity:
            raise ValueError("macro identity must be a non-empty string")
        if not callable(self.build):
            raise TypeError("macro build must be callable")
        if not isinstance(self.parameter_schema, Mapping):
            raise TypeError("macro parameter_schema must be a mapping")

        schema = MappingProxyType(dict(self.parameter_schema))
        stage_values = tuple(self.stages)
        if any(not isinstance(stage, str) or not stage for stage in stage_values):
            raise ValueError("macro stages must contain non-empty strings")
        if len(set(stage_values)) != len(stage_values):
            raise ValueError("macro stages must be unique")

        object.__setattr__(self, "parameter_schema", schema)
        object.__setattr__(self, "stages", stage_values)


class MacroRegistry:
    """Immutable product-owned registry of complete macro definitions."""

    def __init__(self, definitions: Sequence[MacroDefinition] = ()) -> None:
        ordered = tuple(definitions)
        by_identity: dict[str, MacroDefinition] = {}
        for definition in ordered:
            if not isinstance(definition, MacroDefinition):
                raise TypeError("macro registry entries must be MacroDefinition values")
            if definition.identity in by_identity:
                raise ValueError(f"duplicate macro identity: {definition.identity}")
            by_identity[definition.identity] = definition

        self._definitions = ordered
        self._by_identity = MappingProxyType(by_identity)

    def identities(self) -> tuple[str, ...]:
        return tuple(definition.identity for definition in self._definitions)

    def definitions(self) -> tuple[MacroDefinition, ...]:
        return self._definitions

    def resolve(self, identity: str) -> MacroDefinition:
        try:
            return self._by_identity[identity]
        except KeyError as exc:
            raise KeyError(f"unknown macro identity: {identity}") from exc


@dataclass(frozen=True)
class MacroStage:
    identity: str
    label: str
    tasks: tuple[Mapping[str, object], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.identity, str) or not self.identity:
            raise ValueError("macro stage identity must be a non-empty string")
        if not isinstance(self.label, str) or not self.label:
            raise ValueError("macro stage label must be a non-empty string")
        task_values = tuple(self.tasks)
        for task in task_values:
            if not isinstance(task, Mapping):
                raise TypeError("macro stage tasks must be mappings")
        object.__setattr__(
            self,
            "tasks",
            tuple(MappingProxyType(dict(task)) for task in task_values),
        )


@dataclass(frozen=True)
class MacroPlan:
    workflow_id: str
    stages: tuple[MacroStage, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.workflow_id, str) or not self.workflow_id:
            raise ValueError("macro workflow_id must be a non-empty string")
        stage_values = tuple(self.stages)
        if not stage_values:
            raise ValueError("macro plan must contain at least one stage")
        identities = [stage.identity for stage in stage_values]
        if len(set(identities)) != len(identities):
            raise ValueError("macro stage identities must be unique")
        object.__setattr__(self, "stages", stage_values)
