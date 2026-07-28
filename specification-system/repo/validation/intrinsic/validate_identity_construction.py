#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

FIELDS = {
    "construction_identity",
    "construction_status",
    "responsibility",
    "normative",
    "expected_relationships",
    "unresolved_questions",
}
ARTIFACTS = (
    "authoritative/identity/IDENTITY-MODEL.json",
    "authoritative/identity/CANONICAL-JSON.json",
    "authoritative/identity/IDENTITY-FAMILY-MODEL.json",
    "authoritative/identity/IDENTITY-VERIFICATION.json",
)
SUPPORTING_PATHS = (
    "authoritative/schemas/identity/README.md",
    "derived/markdown/identity/README.md",
    "validation/fixtures/identity/README.md",
)
EXPECTED_IDENTITIES = {
    "authoritative/identity/IDENTITY-MODEL.json": "identity-model-construction",
    "authoritative/identity/CANONICAL-JSON.json": "canonical-json-construction",
    "authoritative/identity/IDENTITY-FAMILY-MODEL.json": "identity-family-model-construction",
    "authoritative/identity/IDENTITY-VERIFICATION.json": "identity-verification-construction",
}
FORBIDDEN_CLAIM_KEYS = {
    "accepted",
    "complete",
    "completed",
    "sealed",
    "final",
    "digest",
    "content_digest",
    "revision",
    "specification_revision",
    "aggregate_revision",
}
PRODUCT_FAMILIES = {
    "gve-plan",
    "gve-contract",
    "gve-governance-composition",
    "gve-effect",
    "gve-production",
    "gve-evidence",
    "gve-execution-record",
    "gve-authoritative-result",
    "gve-finalization",
}
IDENTITY = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


class ValidationFailure(Exception):
    pass


def fail(code: str, detail: str) -> None:
    raise ValidationFailure(f"{code}: {detail}")


def strict_json(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        fail("GVE-RSI-JSON-001", f"{path}: invalid UTF-8")
    except OSError as exc:
        fail("GVE-RSI-PATH-001", f"{path}: {exc}")
    try:
        value = json.loads(
            raw,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-standard JSON constant {token}")
            ),
        )
    except (json.JSONDecodeError, ValueError) as exc:
        fail("GVE-RSI-JSON-001", f"{path}: {exc}")
    if not isinstance(value, dict):
        fail("GVE-RSI-JSON-002", f"{path}: top level must be an object")
    return value


def exact_fields(value: dict[str, Any], label: str) -> None:
    unknown = sorted(set(value) - FIELDS)
    missing = sorted(FIELDS - set(value))
    if unknown:
        fail("GVE-RSI-FIELD-001", f"{label}: unknown fields: {', '.join(unknown)}")
    if missing:
        fail("GVE-RSI-FIELD-002", f"{label}: missing fields: {', '.join(missing)}")


def string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        fail("GVE-RSI-TYPE-001", f"{label}: must be a non-empty array")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        fail("GVE-RSI-TYPE-001", f"{label}: entries must be non-empty strings")
    return list(value)


def validate_python_dependencies(root: Path) -> None:
    for path in sorted(root.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, UnicodeDecodeError, SyntaxError) as exc:
            fail("GVE-RSI-PYTHON-001", f"{path}: {exc}")
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [node.module or ""]
            else:
                continue
            for module in modules:
                if module == "gve" or module.startswith("gve."):
                    fail(
                        "GVE-RSI-DEPENDENCY-001",
                        f"{path}: maintained product import {module!r} is forbidden",
                    )


def validate(root: Path) -> None:
    identities: set[str] = set()
    for relative in (*ARTIFACTS, *SUPPORTING_PATHS):
        path = root / relative
        if not path.exists():
            fail("GVE-RSI-PATH-001", f"{relative}: required path is missing")
        if path.is_symlink():
            fail("GVE-RSI-PATH-002", f"{relative}: symlink is forbidden")

    for relative in ARTIFACTS:
        value = strict_json(root / relative)
        exact_fields(value, relative)
        forbidden = sorted(set(value) & FORBIDDEN_CLAIM_KEYS)
        if forbidden:
            fail(
                "GVE-RSI-CLAIM-001",
                f"{relative}: forbidden final-authority fields: {', '.join(forbidden)}",
            )
        identity = value["construction_identity"]
        if not isinstance(identity, str) or not IDENTITY.fullmatch(identity):
            fail("GVE-RSI-IDENTITY-001", f"{relative}: invalid construction identity")
        if identity != EXPECTED_IDENTITIES[relative]:
            fail("GVE-RSI-IDENTITY-002", f"{relative}: unexpected construction identity")
        if identity in identities:
            fail("GVE-RSI-IDENTITY-003", f"{relative}: duplicate construction identity")
        identities.add(identity)
        if value["construction_status"] != "under-construction":
            fail("GVE-RSI-STATUS-001", f"{relative}: status must be under-construction")
        if value["normative"] is not False:
            fail("GVE-RSI-STATUS-002", f"{relative}: normative must be false")
        if not isinstance(value["responsibility"], str) or not value["responsibility"].strip():
            fail("GVE-RSI-TYPE-001", f"{relative}.responsibility must be non-empty")
        relationships = string_list(
            value["expected_relationships"], f"{relative}.expected_relationships"
        )
        questions = string_list(
            value["unresolved_questions"], f"{relative}.unresolved_questions"
        )
        text = "\n".join([value["responsibility"], *relationships, *questions]).lower()
        leaked = sorted(family for family in PRODUCT_FAMILIES if family in text)
        if leaked:
            fail(
                "GVE-RSI-PRODUCT-001",
                f"{relative}: product identity families are forbidden: {', '.join(leaked)}",
            )

    manifest = strict_json(root / "REPOSITORY-SPECIFICATION-SET.json")
    paths = manifest.get("artifact_paths")
    if not isinstance(paths, list):
        fail("GVE-RSI-MANIFEST-001", "manifest artifact_paths must be an array")
    for relative in ARTIFACTS:
        if paths.count(relative) != 1:
            fail(
                "GVE-RSI-MANIFEST-001",
                f"{relative}: must participate exactly once in the construction manifest",
            )

    validate_python_dependencies(root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="construction root to validate",
    )
    args = parser.parse_args(argv)
    try:
        validate(args.root)
    except ValidationFailure as exc:
        print(f"identity construction validation failed: {exc}", file=sys.stderr)
        return 1
    print("identity construction validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
