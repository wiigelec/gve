from __future__ import annotations

from collections.abc import Mapping

from ..errors import PayloadError
from ..macro import MacroDefinition, MacroPlan, MacroStage


OBSERVATIONS = ("repository", "branch", "head", "status", "root_entries")
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
        }
    },
}

_TASKS = {
    "repository": ("git.repository", {}),
    "branch": ("git.branch", {}),
    "head": ("git.head", {}),
    "status": ("git.status", {"include_untracked": True}),
    "root_entries": ("filesystem.list", {"path": ".", "recursive": False}),
}


def _validate(parameters: Mapping[str, object]) -> tuple[str, ...]:
    if set(parameters) - {"observations"}:
        raise PayloadError(
            "discover parameters contain unknown fields",
            details={"extra": sorted(set(parameters) - {"observations"})},
        )
    if "observations" not in parameters:
        return DEFAULT_OBSERVATIONS

    value = parameters["observations"]
    if not isinstance(value, list) or not value:
        raise PayloadError("discover observations must be a non-empty array")
    if any(not isinstance(item, str) for item in value):
        raise PayloadError("discover observations must contain strings")
    if len(set(value)) != len(value):
        raise PayloadError("discover observations must be unique")
    unknown = sorted(set(value) - set(OBSERVATIONS))
    if unknown:
        raise PayloadError("discover observations contain unknown values", details={"unknown": unknown})
    selected = set(value)
    return tuple(item for item in OBSERVATIONS if item in selected)


def build_discover(parameters: Mapping[str, object]) -> MacroPlan:
    selected = _validate(parameters)
    tasks = []
    for observation in selected:
        task, task_parameters = _TASKS[observation]
        tasks.append(
            {
                "id": f"discover-{observation.replace('_', '-')}",
                "task": task,
                "parameters": dict(task_parameters),
            }
        )
    return MacroPlan(
        "macro-discover",
        (MacroStage("discover", "DISCOVER", tuple(tasks)),),
    )


DISCOVER = MacroDefinition(
    identity="discover",
    parameter_schema=PARAMETER_SCHEMA,
    stages=("DISCOVER",),
    build=build_discover,
)
