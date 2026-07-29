from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contracts import ValidationError


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate object member {key}")
        result[key] = value
    return result


def load_json_bytes(data: bytes, *, source: str) -> Any:
    try:
        text = data.decode("utf-8", errors="strict")
        return json.loads(
            text,
            object_pairs_hook=_unique_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-standard JSON constant {token}")
            ),
            parse_float=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-integer JSON number {token}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValidationError(f"{source}: {exc}") from exc


def load_json_path(path: Path) -> Any:
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ValidationError(f"{path}: {exc}") from exc
    return load_json_bytes(data, source=str(path))
