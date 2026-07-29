from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any


FUNCTIONAL_IDENTIFIER = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
NORMALIZED_FIELD_NAME = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")


class ValidationError(ValueError):
    """Deterministic repository-specification construction validation failure."""


def exact_fields(
    value: Any,
    *,
    allowed: Iterable[str],
    required: Iterable[str],
    location: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValidationError(f"{location}: expected object")
    allowed_set = set(allowed)
    required_set = set(required)
    unknown = sorted(set(value) - allowed_set)
    missing = sorted(required_set - set(value))
    if unknown:
        raise ValidationError(
            f"{location}: unknown fields: {', '.join(unknown)}"
        )
    if missing:
        raise ValidationError(
            f"{location}: missing fields: {', '.join(missing)}"
        )
    return value


def functional_identifier(value: Any, *, location: str) -> str:
    if not isinstance(value, str) or not FUNCTIONAL_IDENTIFIER.fullmatch(value):
        raise ValidationError(f"{location}: invalid functional identifier")
    return value


def normalized_field_name(value: Any, *, location: str) -> str:
    if not isinstance(value, str) or not NORMALIZED_FIELD_NAME.fullmatch(value):
        raise ValidationError(f"{location}: invalid normalized field name")
    return value


def require_unique(values: Any, *, location: str) -> list[Any]:
    if not isinstance(values, list):
        raise ValidationError(f"{location}: expected array")
    seen: list[Any] = []
    for index, value in enumerate(values):
        if any(value == prior for prior in seen):
            raise ValidationError(
                f"{location}: duplicate value at index {index}"
            )
        seen.append(value)
    return values


def require_disjoint(
    left: Iterable[Any],
    right: Iterable[Any],
    *,
    location: str,
) -> None:
    overlap = [value for value in left if any(value == other for other in right)]
    if overlap:
        rendered = ", ".join(sorted(str(value) for value in overlap))
        raise ValidationError(f"{location}: overlapping values: {rendered}")
