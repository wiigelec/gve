#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

MANIFEST_FIELDS = {
    "construction_identity", "construction_status", "normative",
    "validation_entry_point", "artifact_classes", "artifact_paths",
    "unresolved_questions",
}
PLACEHOLDER_FIELDS = {
    "construction_identity", "construction_status", "responsibility",
    "normative", "expected_relationships", "unresolved_questions",
}
MANIFEST_PATH = "REPOSITORY-SPECIFICATION-SET.json"
ARTIFACT_CLASSES = (
    "canonical-json-construction",
    "canonical-json-construction-schema",
    "conformance-boundary-placeholder",
    "development-process-placeholder",
    "identity-authority-placeholder",
    "identity-behavior-fixture-set-construction",
    "identity-family-construction-schema",
    "identity-family-fixture-set-construction",
    "identity-family-model-construction",
    "identity-model-construction",
    "identity-model-construction-schema",
    "identity-verification-construction",
    "identity-verification-construction-schema",
    "level-model-placeholder",
    "normative-change-placeholder",
    "repository-model-placeholder",
    "repository-validation-placeholder",
    "schema-boundary-placeholder",
    "source-layout-placeholder",
    "specification-artifact-placeholder",
    "validation-fixtures-placeholder",
    "validation-library-placeholder",
)
ARTIFACT_PATHS = (
    "authoritative/repository-model/REPOSITORY-MODEL.json",
    "authoritative/specification-system/SPECIFICATION-ARTIFACTS.json",
    "authoritative/identity/IDENTITY-AUTHORITY.json",
    "authoritative/identity/IDENTITY-MODEL.json",
    "authoritative/identity/CANONICAL-JSON.json",
    "authoritative/identity/IDENTITY-FAMILY-MODEL.json",
    "authoritative/identity/IDENTITY-VERIFICATION.json",
    "authoritative/development-process/DEVELOPMENT-PROCESS.json",
    "authoritative/normative-change/NORMATIVE-CHANGE.json",
    "authoritative/level-model/LEVEL-MODEL.json",
    "authoritative/source-layout/SOURCE-LAYOUT.json",
    "authoritative/schemas/SCHEMA-BOUNDARY.json",
    "authoritative/schemas/identity/CANONICAL-JSON-CONSTRUCTION-SCHEMA.json",
    "authoritative/schemas/identity/IDENTITY-MODEL-CONSTRUCTION-SCHEMA.json",
    "authoritative/schemas/identity/IDENTITY-FAMILY-CONSTRUCTION-SCHEMA.json",
    "authoritative/schemas/identity/IDENTITY-VERIFICATION-CONSTRUCTION-SCHEMA.json",
    "authoritative/conformance/CONFORMANCE-BOUNDARY.json",
    "validation/lib/VALIDATION-LIBRARY.json",
    "validation/repository/REPOSITORY-VALIDATION.json",
    "validation/fixtures/VALIDATION-FIXTURES.json",
    "validation/fixtures/identity/identity-family/IDENTITY-FAMILY-FIXTURES.json",
    "validation/fixtures/identity/identity-behavior/IDENTITY-BEHAVIOR-FIXTURES.json",
)
NON_PLACEHOLDER_PATHS = {
    "validation/fixtures/identity/identity-behavior/IDENTITY-BEHAVIOR-FIXTURES.json",
    "authoritative/identity/IDENTITY-MODEL.json",
    "authoritative/identity/CANONICAL-JSON.json",
    "authoritative/identity/IDENTITY-FAMILY-MODEL.json",
    "authoritative/identity/IDENTITY-VERIFICATION.json",
    "authoritative/schemas/identity/CANONICAL-JSON-CONSTRUCTION-SCHEMA.json",
    "authoritative/schemas/identity/IDENTITY-MODEL-CONSTRUCTION-SCHEMA.json",
    "authoritative/schemas/identity/IDENTITY-FAMILY-CONSTRUCTION-SCHEMA.json",
    "authoritative/schemas/identity/IDENTITY-VERIFICATION-CONSTRUCTION-SCHEMA.json",
    "validation/fixtures/identity/identity-family/IDENTITY-FAMILY-FIXTURES.json",
}
PLACEHOLDER_PATHS = tuple(path for path in ARTIFACT_PATHS if path not in NON_PLACEHOLDER_PATHS)
REQUIRED_DIRECTORIES = (
    "authoritative/identity", "authoritative/repository-model",
    "authoritative/specification-system", "authoritative/development-process",
    "authoritative/normative-change", "authoritative/level-model",
    "authoritative/source-layout", "authoritative/schemas",
    "authoritative/schemas/identity", "authoritative/conformance",
    "derived/markdown", "derived/markdown/identity", "validation/lib",
    "validation/intrinsic", "validation/repository", "validation/tests",
    "validation/fixtures", "validation/fixtures/identity",
    "validation/fixtures/identity/canonical-json",
    "validation/fixtures/identity/identity-family",
    "validation/fixtures/identity/identity-behavior",
)
REQUIRED_PATHS = (
    MANIFEST_PATH, "validate", *ARTIFACT_PATHS,
    "derived/markdown/README.md",
    "authoritative/schemas/identity/README.md",
    "derived/markdown/identity/README.md",
    "validation/fixtures/identity/README.md",
    "validation/intrinsic/validate_skeleton.py",
    "validation/intrinsic/validate_identity_construction.py",
    "validation/intrinsic/validate_canonical_json.py",
    "validation/tests/test_construction_skeleton.py",
    "validation/tests/test_complete_construction_skeleton.py",
    "validation/tests/test_identity_construction.py",
    "validation/tests/test_identity_family.py",
    "validation/tests/test_identity_behavior.py",
    "validation/tests/test_canonical_json.py",
)
IDENTITY = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
FORBIDDEN_NAME_PARTS = {
    "issue", "pull", "request", "milestone", "phase", "migration",
    "temporary", "temp", "patch", "step", "chronology",
}
FORBIDDEN_CLAIM_KEYS = {
    "accepted", "complete", "completed", "sealed", "final", "digest",
    "content_digest", "revision", "specification_revision", "aggregate_revision",
}

class ValidationFailure(Exception):
    pass

def fail(code: str, detail: str) -> None:
    raise ValidationFailure(f"{code}: {detail}")

def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate object member {key}")
        result[key] = value
    return result

def strict_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_unique_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-standard JSON constant {token}")
            ),
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        fail("REPO-SPEC-CONSTRUCTION-JSON-001", f"{path}: {exc}")
    if not isinstance(value, dict):
        fail("REPO-SPEC-CONSTRUCTION-JSON-002", f"{path}: top level must be an object")
    return value

def exact_fields(value: dict[str, Any], fields: set[str], label: str) -> None:
    unknown = sorted(set(value) - fields)
    missing = sorted(fields - set(value))
    if unknown:
        fail("REPO-SPEC-CONSTRUCTION-FIELD-001", f"{label}: unknown fields: {', '.join(unknown)}")
    if missing:
        fail("REPO-SPEC-CONSTRUCTION-FIELD-002", f"{label}: missing fields: {', '.join(missing)}")

def contained_path(root: Path, value: str, label: str) -> Path:
    pure = PurePosixPath(value)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        fail("REPO-SPEC-CONSTRUCTION-PATH-002", f"{label}: path is not normalized and relative")
    target = root.joinpath(*pure.parts)
    try:
        target.resolve(strict=False).relative_to(root.resolve())
    except ValueError:
        fail("REPO-SPEC-CONSTRUCTION-PATH-003", f"{label}: path escapes construction root")
    current = root
    for part in pure.parts:
        current = current / part
        if current.is_symlink():
            fail("REPO-SPEC-CONSTRUCTION-PATH-003", f"{label}: symlink is forbidden")
    return target

def validate_identity(value: Any, label: str) -> str:
    if not isinstance(value, str) or not IDENTITY.fullmatch(value):
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-001", f"{label}: invalid functional identity")
    if set(value.split("-")) & FORBIDDEN_NAME_PARTS:
        fail("REPO-SPEC-CONSTRUCTION-NAME-001", f"{label}: work-derived name is forbidden")
    return value

def validate_common(value: dict[str, Any], label: str) -> str:
    if set(value) & FORBIDDEN_CLAIM_KEYS:
        fail("REPO-SPEC-CONSTRUCTION-CLAIM-001", f"{label}: forbidden final-authority fields")
    identity = validate_identity(value["construction_identity"], label)
    if value["construction_status"] != "under-construction":
        fail("REPO-SPEC-CONSTRUCTION-STATUS-001", f"{label}: invalid construction status")
    if value["normative"] is not False:
        fail("REPO-SPEC-CONSTRUCTION-STATUS-002", f"{label}: normative must be false")
    questions = value["unresolved_questions"]
    if not isinstance(questions, list) or not questions:
        fail("REPO-SPEC-CONSTRUCTION-TYPE-001", f"{label}: unresolved questions required")
    return identity

def _local_import_exists(root: Path, module: str) -> bool:
    parts = module.split(".")
    return root.joinpath(*parts).with_suffix(".py").is_file() or root.joinpath(*parts).is_dir()

def validate_python_dependencies(root: Path) -> None:
    standard_library = set(sys.stdlib_module_names) | {"__future__"}
    for path in sorted(root.rglob("*.py")):
        if path.is_symlink():
            fail("REPO-SPEC-CONSTRUCTION-PATH-003", f"{path}: symlink is forbidden")
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.Import):
                modules = [(alias.name, 0) for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                modules = [(node.module or "", node.level)]
            for module, level in modules:
                if level:
                    continue
                top_level = module.split(".", 1)[0]
                if top_level in standard_library or _local_import_exists(root, module):
                    continue
                fail("REPO-SPEC-CONSTRUCTION-DEPENDENCY-001",
                     f"{path}: non-standard, non-local import forbidden: {module}")

def validate_focused_identity(root: Path) -> None:
    path = root / "validation/intrinsic/validate_identity_construction.py"
    spec = importlib.util.spec_from_file_location("identity_construction_validator", path)
    if spec is None or spec.loader is None:
        fail("REPO-SPEC-CONSTRUCTION-PYTHON-001", f"{path}: cannot load focused validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        module.validate(root)
    except module.ValidationFailure as exc:
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-CONSTRUCTION-001", str(exc))

def validate(root: Path) -> None:
    for relative in REQUIRED_DIRECTORIES:
        if not contained_path(root, relative, relative).is_dir():
            fail("REPO-SPEC-CONSTRUCTION-PATH-001", f"{relative}: required directory is missing")
    for relative in REQUIRED_PATHS:
        if not contained_path(root, relative, relative).exists():
            fail("REPO-SPEC-CONSTRUCTION-PATH-001", f"{relative}: required path is missing")

    manifest = strict_json(root / MANIFEST_PATH)
    exact_fields(manifest, MANIFEST_FIELDS, MANIFEST_PATH)
    identities = {validate_common(manifest, MANIFEST_PATH)}
    if manifest["construction_identity"] != "repository-specification-construction-set":
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-002", f"{MANIFEST_PATH}: unexpected construction identity")
    if manifest["validation_entry_point"] != "validate":
        fail("REPO-SPEC-CONSTRUCTION-PATH-004", f"{MANIFEST_PATH}: invalid validation entry point")
    if manifest["artifact_classes"] != list(ARTIFACT_CLASSES):
        fail("REPO-SPEC-CONSTRUCTION-CLASS-001", f"{MANIFEST_PATH}: unexpected artifact classes")
    paths = manifest["artifact_paths"]
    if paths != list(ARTIFACT_PATHS):
        fail("REPO-SPEC-CONSTRUCTION-PATH-004", f"{MANIFEST_PATH}: artifact paths do not match complete inventory")
    if len(paths) != len(set(paths)):
        fail("REPO-SPEC-CONSTRUCTION-PATH-005", f"{MANIFEST_PATH}: duplicate artifact path")
    for item in paths:
        if not contained_path(root, item, item).is_file():
            fail("REPO-SPEC-CONSTRUCTION-PATH-001", f"{item}: declared artifact is missing")

    participating = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*.json")
        if path.name != MANIFEST_PATH
        and "construction_identity" in path.read_text(encoding="utf-8")
    }
    undeclared = sorted(participating - set(paths))
    if undeclared:
        fail("REPO-SPEC-CONSTRUCTION-PATH-006",
             f"undeclared construction artifacts: {', '.join(undeclared)}")

    for relative in PLACEHOLDER_PATHS:
        value = strict_json(root / relative)
        exact_fields(value, PLACEHOLDER_FIELDS, relative)
        identity = validate_common(value, relative)
        if identity in identities:
            fail("REPO-SPEC-CONSTRUCTION-IDENTITY-003",
                 f"{relative}: duplicate construction identity")
        identities.add(identity)

    validate_python_dependencies(root)
    validate_focused_identity(root)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    try:
        validate(args.root)
    except (ValidationFailure, OSError, UnicodeDecodeError, SyntaxError) as exc:
        print(f"repository-specification construction validation failed: {exc}", file=sys.stderr)
        return 1
    print("repository-specification construction validation passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
