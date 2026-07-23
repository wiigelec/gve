"""JSON Schema validation for GVE level specifications."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .strict_json import load_strict


class SchemaValidationError(ValueError):
    """Raised when a document fails structural validation."""


def _validator_class():
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise RuntimeError(
            "the 'jsonschema' package is required for specification validation"
        ) from exc
    return Draft202012Validator


def load_schema(path: Path) -> dict[str, Any]:
    return load_strict(path)


def validate_document(document_path: Path, schema_path: Path) -> None:
    validator_class = _validator_class()
    schema = load_schema(schema_path)
    validator_class.check_schema(schema)
    document = load_strict(document_path)
    errors = sorted(validator_class(schema).iter_errors(document), key=lambda e: list(e.path))
    if not errors:
        return
    error = errors[0]
    location = "$"
    for part in error.absolute_path:
        location += f"[{part}]" if isinstance(part, int) else f".{part}"
    raise SchemaValidationError(f"{location}: {error.message}")
