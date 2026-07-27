"""Deterministic validation for the normative maintained Python source layout."""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any, Mapping, Sequence


class SourceLayoutValidationError(ValueError):
    """Raised when maintained Python source violates normative layout authority."""


def _python_paths(repository_root: Path) -> list[str]:
    source_root = repository_root / "src" / "gve"
    if not source_root.is_dir():
        raise SourceLayoutValidationError("maintained package root is missing: src/gve")
    return sorted(
        path.relative_to(repository_root).as_posix()
        for path in source_root.rglob("*.py")
        if "__pycache__" not in path.parts
    )


def _classification_map(document: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    classifications = document["current_tree_classification"]
    result: dict[str, Mapping[str, Any]] = {}
    for item in classifications:
        path = item["path"]
        if path in result:
            raise SourceLayoutValidationError(
                f"duplicate maintained Python classification: {path}"
            )
        result[path] = item
    return result


def _validate_complete_classification(
    repository_root: Path,
    document: Mapping[str, Any],
) -> dict[str, Mapping[str, Any]]:
    actual = set(_python_paths(repository_root))
    classifications = _classification_map(document)
    declared = set(classifications)
    missing = sorted(actual - declared)
    stale = sorted(declared - actual)
    if missing or stale:
        raise SourceLayoutValidationError(
            "maintained Python classification mismatch; "
            f"missing={missing}, stale={stale}"
        )
    return classifications


def _validate_names(paths: Sequence[str], document: Mapping[str, Any]) -> None:
    naming = document["naming_policy"]
    patterns = [re.compile(pattern) for pattern in naming["prohibited_patterns"]]
    ownerless = set(naming["prohibited_ownerless_names"])

    for path in paths:
        relative = Path(path).relative_to("src/gve")
        components = list(relative.parts)
        searchable = "_".join(
            part[:-3] if part.endswith(".py") else part for part in components
        )
        for pattern in patterns:
            if pattern.search(searchable):
                raise SourceLayoutValidationError(
                    f"prohibited maintained product name: {path}"
                )
        for part in components[:-1]:
            if part in ownerless:
                raise SourceLayoutValidationError(
                    f"prohibited ownerless namespace: {path}"
                )
        stem = Path(components[-1]).stem
        if stem in ownerless:
            raise SourceLayoutValidationError(
                f"prohibited ownerless module: {path}"
            )


def _validate_root_modules(
    classifications: Mapping[str, Mapping[str, Any]],
) -> None:
    active_roles = {
        "package-initialization",
        "installed-entry-point",
        "broad-orchestration",
        "supported-public-api",
    }
    expected_api_boundaries = {
        "installed-entry-point": "installed-entry-point",
        "supported-public-api": "supported-public-api",
    }

    for path, item in classifications.items():
        relative = Path(path).relative_to("src/gve")
        if len(relative.parts) != 1:
            if "root_role" in item:
                raise SourceLayoutValidationError(
                    f"non-root module declares root role: {path}"
                )
            continue
        if item["placement_class"] != "installed-product-package":
            raise SourceLayoutValidationError(
                f"root module has invalid placement class: {path}"
            )
        if item["status"] not in {"active", "grandfathered"}:
            raise SourceLayoutValidationError(
                f"root module has invalid status: {path}"
            )

        role = item.get("root_role")
        if item["status"] == "active":
            if role not in active_roles:
                raise SourceLayoutValidationError(
                    f"active root module has prohibited root role: {path}"
                )
            if item["relocation_required"]:
                raise SourceLayoutValidationError(
                    f"active root module must not require relocation: {path}"
                )
        else:
            if role != "grandfathered-single-feature":
                raise SourceLayoutValidationError(
                    f"grandfathered root module has invalid root role: {path}"
                )
            if not item["relocation_required"]:
                raise SourceLayoutValidationError(
                    f"grandfathered root module must require relocation: {path}"
                )
            if not item.get("successor_requirement"):
                raise SourceLayoutValidationError(
                    f"grandfathered root module lacks successor requirement: {path}"
                )

        expected_api = expected_api_boundaries.get(role)
        if expected_api is not None and item["api_boundary"] != expected_api:
            raise SourceLayoutValidationError(
                f"root role and API boundary conflict: {path}"
            )


def _validate_plugin_hierarchy(paths: Sequence[str]) -> None:
    prefix = Path("src/gve/plugins")
    for path in paths:
        candidate = Path(path)
        try:
            relative = candidate.relative_to(prefix)
        except ValueError:
            continue
        parts = relative.parts
        if not parts:
            continue
        if parts[0] == "__init__.py":
            continue
        if len(parts) < 2:
            raise SourceLayoutValidationError(
                f"plugin implementation lacks owning directory: {path}"
            )
        plugin_name = parts[0]
        if not re.fullmatch(r"[a-z][a-z0-9_]*", plugin_name):
            raise SourceLayoutValidationError(
                f"invalid plugin directory name: {path}"
            )
        if len(parts) >= 2 and parts[1] == "actions":
            if len(parts) == 3 and parts[2] == "__init__.py":
                continue
            if len(parts) != 3 or not re.fullmatch(
                r"action_[a-z][a-z0-9_]*\.py", parts[2]
            ):
                raise SourceLayoutValidationError(
                    f"invalid plugin action path: {path}"
                )


def _import_roots(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        raise SourceLayoutValidationError(
            f"cannot inspect imports for {path}: {exc}"
        ) from exc

    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def _validate_import_backflow(
    repository_root: Path,
    paths: Sequence[str],
    document: Mapping[str, Any],
) -> None:
    forbidden: set[str] = set()
    for rule in document["dependency_rules"]:
        if rule["rule_id"] == "product-no-repository-backflow":
            forbidden.update(rule["forbidden_import_roots"])
    if not forbidden:
        raise SourceLayoutValidationError(
            "product-no-repository-backflow rule is missing"
        )

    for path in paths:
        roots = _import_roots(repository_root / path)
        invalid = sorted(roots & forbidden)
        if invalid:
            raise SourceLayoutValidationError(
                f"{path}: forbidden repository import roots {invalid}"
            )


def validate_source_layout(
    repository_root: Path,
    document: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate maintained Python paths and return deterministic evidence."""
    repository_root = repository_root.resolve()
    expected_location = (
        repository_root / "specs" / "source-layout" / "GVE-SOURCE-LAYOUT.json"
    )
    if not expected_location.is_file():
        raise SourceLayoutValidationError(
            "standalone source-layout authority is missing from its accepted path"
        )
    levels_root = (repository_root / "specs" / "levels").resolve()
    try:
        expected_location.resolve().relative_to(levels_root)
    except ValueError:
        pass
    else:
        raise SourceLayoutValidationError(
            "standalone source-layout authority must remain outside specs/levels"
        )

    classifications = _validate_complete_classification(repository_root, document)
    paths = sorted(classifications)
    _validate_names(paths, document)
    _validate_root_modules(classifications)
    _validate_plugin_hierarchy(paths)
    _validate_import_backflow(repository_root, paths, document)

    grandfathered = sorted(
        path
        for path, item in classifications.items()
        if item["status"] == "grandfathered"
    )
    return {
        "classified_paths": paths,
        "grandfathered_paths": grandfathered,
    }
