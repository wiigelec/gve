"""Semantic graph and hierarchy validation for GVE level specifications."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping, Sequence


class SemanticValidationError(ValueError):
    """Raised when a structurally valid level specification is inconsistent."""


def _fail(specification_id: str, message: str) -> None:
    raise SemanticValidationError(f"{specification_id}: {message}")


def _metadata(document: Mapping[str, Any]) -> dict[str, Any]:
    specification_id = document["specification"]["id"]
    metadata = document.get("document")
    if metadata is None:
        return {"role": "root", "root": specification_id, "imports": []}
    return dict(metadata)


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
    """Validate one document's identity, governed path, and local identifiers."""
    specification = document["specification"]
    specification_id = specification["id"]
    level = specification["level"]
    prefix = f"GVE-LEVEL-{level}"
    if specification_id != prefix and not specification_id.startswith(prefix + "-"):
        _fail(
            specification_id,
            f"specification id does not match numeric level {level}; "
            f"expected {prefix} or {prefix}-<DOCUMENT>",
        )
    expected_name = f"{specification_id}.json"
    if path.name != expected_name:
        _fail(
            specification_id,
            f"filename {path.name!r} does not match specification identity; "
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
    _identifier_inventory(document)


def _visit_graph(
    graph: Mapping[str, Sequence[str]],
    *,
    label: str,
) -> None:
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(identifier: str) -> None:
        if identifier in visited:
            return
        if identifier in visiting:
            _fail(identifier, f"{label} cycle includes {identifier}")
        visiting.add(identifier)
        for target in graph.get(identifier, ()):
            visit(target)
        visiting.remove(identifier)
        visited.add(identifier)

    for identifier in sorted(graph):
        visit(identifier)


def validate_hierarchy(
    specifications: Sequence[tuple[Path, Mapping[str, Any]]],
    *,
    levels_root: Path,
) -> None:
    """Validate document sets, inheritance, imports, and semantic resolution."""
    by_id: dict[str, tuple[Path, Mapping[str, Any]]] = {}
    by_level: dict[int, list[str]] = defaultdict(list)
    metadata: dict[str, dict[str, Any]] = {}
    inventories: dict[str, tuple[set[str], set[str], set[str]]] = {}

    for path, document in specifications:
        validate_semantics(document, path, levels_root=levels_root)
        specification_id = document["specification"]["id"]
        if specification_id in by_id:
            _fail(
                specification_id,
                f"duplicate specification identifier {specification_id}",
            )
        by_id[specification_id] = (path, document)
        by_level[document["specification"]["level"]].append(specification_id)
        metadata[specification_id] = _metadata(document)
        inventories[specification_id] = _identifier_inventory(document)

    roots_by_level: dict[int, str] = {}
    for level, identifiers in sorted(by_level.items()):
        roots = [
            identifier
            for identifier in identifiers
            if metadata[identifier]["role"] == "root"
        ]
        if len(roots) != 1:
            _fail(
                f"GVE-LEVEL-{level}",
                f"level {level} must contain exactly one root document; "
                f"found {len(roots)}",
            )
        root_id = roots[0]
        roots_by_level[level] = root_id
        if root_id != f"GVE-LEVEL-{level}":
            _fail(
                root_id,
                f"root document identity must be GVE-LEVEL-{level}",
            )
        if metadata[root_id]["root"] != root_id:
            _fail(root_id, f"root document must name itself as set root {root_id}")
        if metadata[root_id]["imports"]:
            _fail(root_id, "root document must not import subordinate documents")

        for identifier in identifiers:
            item = metadata[identifier]
            if item["root"] != root_id:
                _fail(
                    identifier,
                    f"unresolved specification-set root {item['root']}; "
                    f"expected {root_id}",
                )
            if identifier != root_id and item["role"] != "subordinate":
                _fail(identifier, "non-root document must have subordinate role")

    inheritance: dict[str, list[str]] = {}
    imports: dict[str, list[str]] = {}
    for specification_id, (_path, document) in by_id.items():
        specification = document["specification"]
        level = specification["level"]
        parent = specification["parent"]
        role = metadata[specification_id]["role"]

        if level == 0:
            if parent is not None:
                _fail(specification_id, f"Level 0 must not declare parent {parent}")
        elif parent is None:
            _fail(specification_id, "nonzero level has unresolved parent None")
        elif parent == specification_id:
            _fail(specification_id, f"self-parenting is invalid: {parent}")
        elif parent not in by_id:
            _fail(specification_id, f"unresolved parent specification {parent}")
        else:
            parent_level = by_id[parent][1]["specification"]["level"]
            if role == "subordinate":
                expected_parent = roots_by_level[level]
                if parent != expected_parent:
                    _fail(
                        specification_id,
                        f"subordinate parent must be specification-set root "
                        f"{expected_parent}; found {parent}",
                    )
        inheritance[specification_id] = [] if parent is None else [parent]

        targets = list(metadata[specification_id]["imports"])
        imports[specification_id] = targets
        for target in targets:
            if target == specification_id:
                _fail(specification_id, f"self import is invalid: {target}")
            if target not in by_id:
                _fail(specification_id, f"unresolved import target {target}")
            target_level = by_id[target][1]["specification"]["level"]
            if target_level != level:
                _fail(
                    specification_id,
                    f"import target {target} is outside level {level}",
                )

    _visit_graph(inheritance, label="inheritance")
    _visit_graph(imports, label="import")

    for specification_id, (_path, document) in by_id.items():
        specification = document["specification"]
        parent = specification["parent"]
        if parent is None or metadata[specification_id]["role"] == "subordinate":
            continue
        parent_level = by_id[parent][1]["specification"]["level"]
        if parent_level >= specification["level"]:
            _fail(
                specification_id,
                f"invalid parent level ordering: parent {parent} is level "
                f"{parent_level}, child is level {specification['level']}",
            )

    global_owner: dict[str, tuple[str, str]] = {}
    for specification_id in sorted(by_id):
        definitions, requirements, relationships = inventories[specification_id]
        for class_name, identifiers in (
            ("definition", definitions),
            ("requirement", requirements),
            ("relationship", relationships),
        ):
            for identifier in sorted(identifiers):
                prior = global_owner.get(identifier)
                if prior is not None:
                    _fail(
                        specification_id,
                        f"cross-document identifier conflict {identifier}: "
                        f"{prior[0]} declares {prior[1]}, "
                        f"{specification_id} declares {class_name}",
                    )
                global_owner[identifier] = (specification_id, class_name)

    def visible_documents(specification_id: str) -> set[str]:
        visible = {specification_id}
        pending = list(imports[specification_id])
        while pending:
            target = pending.pop()
            if target in visible:
                continue
            visible.add(target)
            pending.extend(imports[target])
        return visible

    for specification_id, (_path, document) in by_id.items():
        visible = visible_documents(specification_id)
        visible_definitions: set[str] = set()
        visible_requirements: set[str] = set()
        for target in visible:
            definitions, requirements, _relationships = inventories[target]
            visible_definitions.update(definitions)
            visible_requirements.update(requirements)

        for requirement in document["requirements"]:
            for reference in requirement["references"]:
                if reference not in visible_definitions:
                    _fail(
                        specification_id,
                        f"requirement {requirement['id']} has unresolved definition "
                        f"reference {reference} in visible imports",
                    )

        permitted_endpoints = visible_definitions | visible_requirements
        for relationship in document["relationships"]:
            for field in ("source", "target"):
                endpoint = relationship[field]
                if endpoint not in permitted_endpoints:
                    _fail(
                        specification_id,
                        f"relationship {relationship['id']} has unresolved "
                        f"{field} endpoint {endpoint} in visible imports",
                    )
