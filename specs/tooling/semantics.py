"""Focused semantic validation for authoritative GVE level documents."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping


class SemanticValidationError(ValueError):
    """Raised when a structurally valid level document is inconsistent."""


def validate_semantics(document: Mapping[str, Any], path: Path) -> None:
    specification = document["specification"]
    expected_name = f"GVE-LEVEL-{specification['level']}.json"
    if path.name != expected_name:
        raise SemanticValidationError(
            f"filename {path.name!r} does not match level {specification['level']}"
        )
    if specification["id"] != f"GVE-LEVEL-{specification['level']}":
        raise SemanticValidationError("specification id does not match level")
    if specification["level"] == 0 and specification["parent"] is not None:
        raise SemanticValidationError("Level 0 must not declare a parent")
    if specification["level"] > 0 and specification["parent"] is None:
        raise SemanticValidationError("nonzero levels must declare a parent")

    definitions = {item["id"] for item in document["definitions"]}
    requirements = {item["id"] for item in document["requirements"]}
    relationships = {item["id"] for item in document["relationships"]}
    all_ids = definitions | requirements | relationships
    total = (
        len(document["definitions"])
        + len(document["requirements"])
        + len(document["relationships"])
    )
    if len(all_ids) != total:
        raise SemanticValidationError("identifiers must be globally unique")

    for requirement in document["requirements"]:
        missing = sorted(set(requirement["references"]) - definitions)
        if missing:
            raise SemanticValidationError(
                f"{requirement['id']} has unresolved references: {', '.join(missing)}"
            )

    relationship_targets = definitions | requirements
    for relationship in document["relationships"]:
        for field in ("source", "target"):
            reference = relationship[field]
            if reference not in relationship_targets:
                raise SemanticValidationError(
                    f"{relationship['id']} has unresolved {field}: {reference}"
                )
