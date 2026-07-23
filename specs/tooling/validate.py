"""Repository validation for GVE level specifications."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Sequence

from .render import render_markdown
from .semantics import SemanticValidationError, validate_hierarchy
from .strict_json import StrictJSONError, load_strict


class SchemaValidationError(ValueError):
    """Raised when a document fails structural validation."""


class ProjectionValidationError(ValueError):
    """Raised when committed Markdown differs from its deterministic projection."""


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
    errors = sorted(
        validator_class(schema).iter_errors(document),
        key=lambda error: list(error.path),
    )
    if not errors:
        return
    error = errors[0]
    location = "$"
    for part in error.absolute_path:
        location += f"[{part}]" if isinstance(part, int) else f".{part}"
    raise SchemaValidationError(
        f"{document_path}: {location}: {error.message}"
    )


def discover_specifications(specs_root: Path) -> list[Path]:
    levels_root = specs_root / "levels"
    paths = sorted(levels_root.glob("level-*/GVE-LEVEL-*.json"))
    if not paths:
        raise SemanticValidationError(
            f"{levels_root}: no governed level specifications found"
        )
    return paths


def validate_specification_set(specs_root: Path) -> None:
    specs_root = specs_root.resolve()
    levels_root = specs_root / "levels"
    schema_path = specs_root / "schemas" / "GVE-LEVEL.schema.json"
    records: list[tuple[Path, dict[str, Any]]] = []
    for document_path in discover_specifications(specs_root):
        validate_document(document_path, schema_path)
        document = load_strict(document_path)
        markdown_path = document_path.with_suffix(".md")
        expected_markdown = render_markdown(document)
        try:
            actual_markdown = markdown_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise ProjectionValidationError(
                f"{document['specification']['id']}: cannot read projection "
                f"{markdown_path}: {exc}"
            ) from exc
        if actual_markdown != expected_markdown:
            raise ProjectionValidationError(
                f"{document['specification']['id']}: deterministic Markdown "
                f"projection differs at {markdown_path}"
            )
        records.append((document_path, document))
    validate_hierarchy(records, levels_root=levels_root)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the accepted GVE level specification set."
    )
    parser.add_argument(
        "--specs-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="specs directory to validate (default: repository specs directory)",
    )
    args = parser.parse_args(argv)
    try:
        validate_specification_set(args.specs_root)
    except (
        ProjectionValidationError,
        RuntimeError,
        SchemaValidationError,
        SemanticValidationError,
        StrictJSONError,
    ) as exc:
        print(f"specification validation failed: {exc}", file=sys.stderr)
        return 1
    print("specification validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
