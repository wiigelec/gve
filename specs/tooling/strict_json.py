"""Strict JSON loading for specification authority files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


class StrictJSONError(ValueError):
    """Raised when specification JSON is not strict JSON."""


def _reject_constant(value: str) -> None:
    raise StrictJSONError(f"non-standard JSON constant: {value}")


def _unique_object(pairs: Iterable[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise StrictJSONError(f"duplicate object key: {key}")
        result[key] = value
    return result


def loads_strict(text: str) -> dict[str, Any]:
    try:
        value = json.loads(
            text,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except UnicodeError as exc:
        raise StrictJSONError(f"invalid Unicode: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise StrictJSONError(f"invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise StrictJSONError("top-level JSON value must be an object")
    return value


def load_strict(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise StrictJSONError(f"cannot read strict JSON: {exc}") from exc
    return loads_strict(text)
