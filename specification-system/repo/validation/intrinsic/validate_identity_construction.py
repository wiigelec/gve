#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from pathlib import Path, PurePosixPath
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
FOCUSED_PYTHON_PATHS = (
    "validation/intrinsic/validate_identity_construction.py",
    "validation/tests/test_identity_construction.py",
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
    "content-digest",
    "revision",
    "specification_revision",
    "specification-revision",
    "aggregate_revision",
    "aggregate-revision",
}
FORBIDDEN_NAME_PARTS = {
    "issue",
    "pull",
    "request",
    "milestone",
    "phase",
    "migration",
    "temporary",
    "temp",
    "patch",
    "step",
    "chronology",
}
IDENTITY = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
GVE_FAMILY = re.compile(r"\bgve-[a-z0-9]+(?:-[a-z0-9]+)*\b")
MANIFEST_PATH = "REPOSITORY-SPECIFICATION-SET.json"


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


def reject_claim_keys(value: dict[str, Any], label: str) -> None:
    present = sorted(set(value) & FORBIDDEN_CLAIM_KEYS)
    if present:
        fail(
            "GVE-RSI-CLAIM-001",
            f"{label}: forbidden final-authority fields: {', '.join(present)}",
        )


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


def validate_identity(value: Any, label: str) -> str:
    if not isinstance(value, str) or not IDENTITY.fullmatch(value):
        fail("GVE-RSI-IDENTITY-001", f"{label}: invalid construction identity")
    forbidden = sorted(set(value.split("-")) & FORBIDDEN_NAME_PARTS)
    if forbidden:
        fail(
            "GVE-RSI-NAME-001",
            f"{label}: work-derived identity parts are forbidden: {', '.join(forbidden)}",
        )
    return value


def contained_path(root: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        fail("GVE-RSI-PATH-003", f"{label}: must be a non-empty relative path")
    pure = PurePosixPath(value)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        fail("GVE-RSI-PATH-003", f"{label}: path is not normalized and relative")
    if pure.as_posix() != value:
        fail("GVE-RSI-PATH-003", f"{label}: path must use normalized POSIX form")
    lowered = {
        token
        for part in pure.parts
        for token in re.split(r"[-_.]", part.lower())
        if token
    }
    forbidden = sorted(lowered & FORBIDDEN_NAME_PARTS)
    if forbidden:
        fail(
            "GVE-RSI-NAME-001",
            f"{label}: work-derived path parts are forbidden: {', '.join(forbidden)}",
        )
    target = root.joinpath(*pure.parts)
    try:
        target.resolve(strict=False).relative_to(root.resolve())
    except ValueError:
        fail("GVE-RSI-PATH-002", f"{label}: path escapes construction root")
    current = root
    for part in pure.parts:
        current = current / part
        if current.is_symlink():
            fail("GVE-RSI-PATH-002", f"{label}: symlink is forbidden")
    return target


def validate_python_dependencies(root: Path) -> None:
    for relative in FOCUSED_PYTHON_PATHS:
        path = contained_path(root, relative, relative)
        if not path.is_file():
            fail("GVE-RSI-PATH-001", f"{relative}: required focused Python file is missing")
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


def validate_manifest(root: Path) -> None:
    manifest = strict_json(root / MANIFEST_PATH)
    paths = manifest.get("artifact_paths")
    if not isinstance(paths, list) or not paths:
        fail("GVE-RSI-MANIFEST-001", "manifest artifact_paths must be a non-empty array")
    if any(not isinstance(path, str) for path in paths):
        fail("GVE-RSI-MANIFEST-001", "manifest artifact_paths entries must be strings")
    if len(paths) != len(set(paths)):
        fail("GVE-RSI-MANIFEST-002", "manifest contains duplicate artifact paths")

    declared = set(paths)
    for index, relative in enumerate(paths):
        target = contained_path(root, relative, f"manifest.artifact_paths[{index}]")
        if relative.startswith("authoritative/identity/") and not target.is_file():
            fail("GVE-RSI-MANIFEST-003", f"{relative}: declared identity artifact is missing")

    for relative in ARTIFACTS:
        if paths.count(relative) != 1:
            fail(
                "GVE-RSI-MANIFEST-001",
                f"{relative}: must participate exactly once in the construction manifest",
            )

    participating: set[str] = set()
    identity_dir = root / "authoritative/identity"
    for path in sorted(identity_dir.glob("*.json")):
        if path.is_symlink():
            fail("GVE-RSI-PATH-002", f"{path}: symlink is forbidden")
        value = strict_json(path)
        if "construction_identity" in value:
            participating.add(path.relative_to(root).as_posix())
    undeclared = sorted(participating - declared)
    if undeclared:
        fail(
            "GVE-RSI-MANIFEST-004",
            "undeclared identity construction participants: " + ", ".join(undeclared),
        )


def validate(root: Path) -> None:
    identities: set[str] = set()
    observed: dict[str, str] = {}

    for relative in (*ARTIFACTS, *SUPPORTING_PATHS):
        path = contained_path(root, relative, relative)
        if not path.exists():
            fail("GVE-RSI-PATH-001", f"{relative}: required path is missing")
        if not path.is_file():
            fail("GVE-RSI-PATH-001", f"{relative}: required path must be a regular file")

    for relative in ARTIFACTS:
        value = strict_json(root / relative)
        reject_claim_keys(value, relative)
        exact_fields(value, relative)
        identity = validate_identity(
            value["construction_identity"], f"{relative}.construction_identity"
        )
        if identity in identities:
            fail("GVE-RSI-IDENTITY-003", f"{relative}: duplicate construction identity")
        identities.add(identity)
        observed[relative] = identity
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
        leaked = sorted(set(GVE_FAMILY.findall(text)))
        if leaked:
            fail(
                "GVE-RSI-PRODUCT-001",
                f"{relative}: GVE product identity families are forbidden: {', '.join(leaked)}",
            )

    for relative, expected in EXPECTED_IDENTITIES.items():
        if observed[relative] != expected:
            fail("GVE-RSI-IDENTITY-002", f"{relative}: unexpected construction identity")

    validate_manifest(root)
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
