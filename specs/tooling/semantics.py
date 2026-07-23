"""Semantic graph and hierarchy validation for GVE level specifications."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence


class SemanticValidationError(ValueError):
    """Raised when a structurally valid level specification is inconsistent."""


def _fail(specification_id: str, message: str) -> None:
    raise SemanticValidationError(f"{specification_id}: {message}")


def _identifier_inventory(
    document: Mapping[str, Any],
) -> tuple[set[str], set[str], set[str]]:
    specification_id = document["specification"]["id"]
    classes = {
        "definition": [item["id"] for item in document["definitions"]],
        "requirement": [item["id"] for item in document["requirements"]],
        "relationship": [item["id"] for item in document["relationships"]],
    }
    owners: dict[str, str] = {}
    for class_name, identifiers in classes.items():
        seen: set[str] = set()
        for identifier in identifiers:
            if identifier in seen:
                _fail(
                    specification_id,
                    f"duplicate {class_name} identifier {identifier}",
                )
            seen.add(identifier)
            prior = owners.get(identifier)
            if prior is not None:
                _fail(
                    specification_id,
                    f"ambiguous identifier {identifier} occurs as both "
                    f"{prior} and {class_name}",
                )
            owners[identifier] = class_name
    return set(classes["definition"]), set(classes["requirement"]), set(
        classes["relationship"]
    )


def validate_semantics(
    document: Mapping[str, Any],
    path: Path,
    *,
    levels_root: Path | None = None,
) -> None:
    """Validate one specification's identity and local semantic graph."""
    specification = document["specification"]
    specification_id = specification["id"]
    level = specification["level"]
    expected_id = f"GVE-LEVEL-{level}"
    expected_name = f"{expected_id}.json"
    if specification_id != expected_id:
        _fail(
            specification_id,
            f"specification id does not match numeric level {level}; "
            f"expected {expected_id}",
        )
    if path.name != expected_name:
        _fail(
            specification_id,
            f"filename {path.name!r} does not match numeric level {level}; "
            f"expected {expected_name}",
        )
    root = (
        Path(__file__).resolve().parents[1] / "levels"
        if levels_root is None
        else levels_root
    )
    expected_path = root / f"level-{level}" / expected_name
    if path.resolve() != expected_path.resolve():
        _fail(
            specification_id,
            f"path {path} does not match authoritative path {expected_path}",
        )

    definitions, requirements, _relationships = _identifier_inventory(document)

    for requirement in document["requirements"]:
        for reference in requirement["references"]:
            if reference not in definitions:
                _fail(
                    specification_id,
                    f"requirement {requirement['id']} has unresolved definition "
                    f"reference {reference}",
                )

    permitted_endpoints = definitions | requirements
    for relationship in document["relationships"]:
        for field in ("source", "target"):
            endpoint = relationship[field]
            if endpoint not in permitted_endpoints:
                _fail(
                    specification_id,
                    f"relationship {relationship['id']} has unresolved "
                    f"{field} endpoint {endpoint}",
                )


def validate_hierarchy(
    specifications: Sequence[tuple[Path, Mapping[str, Any]]],
    *,
    levels_root: Path,
) -> None:
    """Validate specification identity, parent resolution, ordering, and cycles."""
    by_id: dict[str, tuple[Path, Mapping[str, Any]]] = {}
    for path, document in specifications:
        validate_semantics(document, path, levels_root=levels_root)
        specification_id = document["specification"]["id"]
        if specification_id in by_id:
            _fail(
                specification_id,
                f"duplicate specification identifier {specification_id}",
            )
        by_id[specification_id] = (path, document)

    for specification_id, (_path, document) in by_id.items():
        specification = document["specification"]
        level = specification["level"]
        parent = specification["parent"]
        if level == 0:
            if parent is not None:
                _fail(specification_id, f"Level 0 must not declare parent {parent}")
            continue
        if parent is None:
            _fail(specification_id, "nonzero level has unresolved parent None")
        if parent == specification_id:
            _fail(specification_id, f"self-parenting is invalid: {parent}")
        if parent not in by_id:
            _fail(specification_id, f"unresolved parent specification {parent}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(specification_id: str) -> None:
        if specification_id in visited:
            return
        if specification_id in visiting:
            _fail(specification_id, f"inheritance cycle includes {specification_id}")
        visiting.add(specification_id)
        parent = by_id[specification_id][1]["specification"]["parent"]
        if parent is not None:
            visit(parent)
        visiting.remove(specification_id)
        visited.add(specification_id)

    for specification_id in sorted(by_id):
        visit(specification_id)

    for specification_id, (_path, document) in by_id.items():
        specification = document["specification"]
        level = specification["level"]
        parent = specification["parent"]
        if parent is None:
            continue
        parent_level = by_id[parent][1]["specification"]["level"]
        if parent_level >= level:
            _fail(
                specification_id,
                f"invalid parent level ordering: parent {parent} is level "
                f"{parent_level}, child is level {level}",
            )
