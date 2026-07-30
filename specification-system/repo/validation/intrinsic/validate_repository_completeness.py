#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import re
from pathlib import Path


CONSTRUCTION_ROOT = Path(__file__).resolve().parents[2]
if str(CONSTRUCTION_ROOT) not in sys.path:
    sys.path.insert(0, str(CONSTRUCTION_ROOT))


class ValidationFailure(Exception):
    pass


def validate(root: Path) -> None:
    _check_overview_discovery(root)
    _check_plan_discovery(root)
    _check_initialization_completeness(root)
    _check_release_structure(root)


def _check_overview_discovery(root: Path) -> None:
    overview_dir = root.parent.parent / "docs" / "overview"
    overview_path = overview_dir / "PRODUCT-OVERVIEW.md"

    if not overview_dir.is_dir():
        raise ValidationFailure(
            "REPO-COMPLETENESS-OVERVIEW-001: docs/overview/ directory not found"
        )
    if not overview_path.is_file():
        raise ValidationFailure(
            "REPO-COMPLETENESS-OVERVIEW-002: docs/overview/PRODUCT-OVERVIEW.md not found"
        )

    text = overview_path.read_text(encoding="utf-8")
    if not re.search(r"(?i)directional\s+and\s+non[- ]normative", text):
        raise ValidationFailure(
            "REPO-COMPLETENESS-OVERVIEW-003: "
            "overview must declare directional and non-normative status"
    )
    if "## Status" not in text:
        raise ValidationFailure(
            "REPO-COMPLETENESS-OVERVIEW-004: "
            "overview must contain ## Status section"
    )


def _check_plan_discovery(root: Path) -> None:
    plan_dir = root.parent.parent / "docs" / "plans"
    plan_path = plan_dir / "REPOSITORY-FRAMEWORK-CONSTRUCTION-PLAN.md"

    if not plan_dir.is_dir():
        raise ValidationFailure(
            "REPO-COMPLETENESS-PLAN-001: docs/plans/ directory not found"
        )
    if not plan_path.is_file():
        raise ValidationFailure(
            "REPO-COMPLETENESS-PLAN-002: "
            "docs/plans/REPOSITORY-FRAMEWORK-CONSTRUCTION-PLAN.md not found"
        )

    text = plan_path.read_text(encoding="utf-8")
    if "non-normative" not in text.lower():
        raise ValidationFailure(
            "REPO-COMPLETENESS-PLAN-003: "
            "plan must declare non-normative status"
    )
    if "## Status" not in text:
        raise ValidationFailure(
            "REPO-COMPLETENESS-PLAN-004: "
            "plan must contain ## Status section"
        )


def _check_initialization_completeness(root: Path) -> None:
    framework_path = root / "authoritative/framework-boundary/FRAMEWORK-BOUNDARY.json"
    if not framework_path.is_file():
        raise ValidationFailure(
            "REPO-COMPLETENESS-INIT-001: "
            "FRAMEWORK-BOUNDARY.json not found"
        )

    value = json.loads(framework_path.read_text(encoding="utf-8"))
    entity_types = value.get("entity_types", [])
    if "initialized-product-repository" not in entity_types:
        raise ValidationFailure(
            "REPO-COMPLETENESS-INIT-002: "
            "framework-boundary missing initialized-product-repository entity type"
        )

    relationships = value.get("relationship_types", [])
    if "initializes" not in relationships:
        raise ValidationFailure(
            "REPO-COMPLETENESS-INIT-003: "
            "framework-boundary missing initializes relationship type"
    )

    relationship_rules = value.get("relationship_rules", {})
    if "initializes" not in relationship_rules:
        raise ValidationFailure(
            "REPO-COMPLETENESS-INIT-004: "
            "framework-boundary missing initializes relationship rules"
        )


def _check_release_structure(root: Path) -> None:
    git_path = root / "authoritative/git-model/GIT-MODEL.json"
    if not git_path.is_file():
        raise ValidationFailure(
            "REPO-COMPLETENESS-RELEASE-001: "
            "GIT-MODEL.json not found"
        )

    value = json.loads(git_path.read_text(encoding="utf-8"))
    concepts = {}
    for section in ("repository_concepts", "revision_concepts"):
        section_data = value.get(section, {})
        if isinstance(section_data, dict):
            concepts.update(section_data)

    if "release_ref" not in concepts and "release_revision" not in concepts:
        raise ValidationFailure(
            "REPO-COMPLETENESS-RELEASE-002: "
            "git-model missing release concepts (release_ref or release_revision)"
        )

    if "maintenance_branch" not in concepts:
        raise ValidationFailure(
            "REPO-COMPLETENESS-RELEASE-003: "
            "git-model missing maintenance_branch concept"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate repository completeness for all 15 validation families"
    )
    parser.add_argument("--root", default=str(CONSTRUCTION_ROOT))
    args = parser.parse_args(argv)
    try:
        validate(Path(args.root))
    except ValidationFailure as exc:
        print(f"repository completeness validation failed: {exc}", file=sys.stderr)
        return 1
    print("repository completeness validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
