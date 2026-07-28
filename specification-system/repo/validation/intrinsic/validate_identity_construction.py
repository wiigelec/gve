#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

PLACEHOLDER_FIELDS = {
    "construction_identity", "construction_status", "responsibility",
    "normative", "expected_relationships", "unresolved_questions",
}
CANONICAL_FIELDS = {
    "construction_identity", "construction_status", "responsibility", "normative",
    "canonicalization_version", "decision_basis", "input_domain", "encoding",
    "object_rules", "array_rules", "string_rules", "number_rules",
    "output_rules", "expected_relationships",
    "unresolved_questions",
}
SCHEMA_FIELDS = {
    "construction_identity", "construction_status", "responsibility", "normative",
    "target_construction_identity", "required_fields", "closed",
    "field_constraints", "forbidden_claim_fields", "expected_relationships",
    "unresolved_questions",
}
ARTIFACTS = (
    "authoritative/identity/IDENTITY-MODEL.json",
    "authoritative/identity/CANONICAL-JSON.json",
    "authoritative/identity/IDENTITY-FAMILY-MODEL.json",
    "authoritative/identity/IDENTITY-VERIFICATION.json",
)
SCHEMA_PATH = "authoritative/schemas/identity/CANONICAL-JSON-CONSTRUCTION-SCHEMA.json"
SUPPORTING_PATHS = (
    "authoritative/schemas/identity/README.md",
    "derived/markdown/identity/README.md",
    "validation/fixtures/identity/README.md",
    SCHEMA_PATH,
    "validation/intrinsic/validate_canonical_json.py",
    "validation/tests/test_canonical_json.py",
    "validation/fixtures/identity/canonical-json",
)
EXPECTED_IDENTITIES = {
    "authoritative/identity/IDENTITY-MODEL.json": "identity-model-construction",
    "authoritative/identity/CANONICAL-JSON.json": "canonical-json-construction",
    "authoritative/identity/IDENTITY-FAMILY-MODEL.json": "identity-family-model-construction",
    "authoritative/identity/IDENTITY-VERIFICATION.json": "identity-verification-construction",
    SCHEMA_PATH: "canonical-json-construction-schema",
}
FORBIDDEN_CLAIM_KEYS = {
    "accepted", "complete", "completed", "sealed", "final", "digest",
    "content_digest", "content-digest", "revision", "specification_revision",
    "specification-revision", "aggregate_revision", "aggregate-revision",
}
SCHEMA_FORBIDDEN_CLAIM_FIELDS = {
    "accepted", "complete", "completed", "sealed", "final", "digest",
    "content_digest", "revision", "specification_revision", "aggregate_revision",
}
FORBIDDEN_NAME_PARTS = {
    "issue", "pull", "request", "milestone", "phase", "migration",
    "temporary", "temp", "patch", "step", "chronology",
}
IDENTITY = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
MANIFEST_PATH = "REPOSITORY-SPECIFICATION-SET.json"

EXPECTED_CANONICAL_CONSTRAINTS = {'canonicalization_version': ['canonical-json-v1'], 'decision_basis': [{'portable_behavior': ['strict-json-and-utf-8-boundary', 'object-member-ordering', 'array-order-preservation', 'deterministic-string-escaping', 'duplicate-member-rejection', 'non-standard-constant-rejection', 'exact-utf-8-output'], 'repository_generic_decisions': ['canonicalization-version-name', 'signed-64-bit-integer-domain', 'no-unicode-normalization']}], 'input_domain': [{'accepted_value_kinds': ['null', 'boolean', 'integer', 'string', 'array', 'object'], 'integer_range': 'signed-64-bit', 'object_member_names': 'string-only'}], 'encoding': [{'input': 'strict-utf-8', 'output': 'utf-8', 'byte_order_mark': 'forbidden', 'unicode_normalization': 'none'}], 'object_rules': [{'member_order': 'ascending-unicode-code-point-sequence', 'source_declaration_order_significant': False, 'duplicate_member_names': 'reject'}], 'array_rules': [{'input_order': 'preserve', 'semantic_sorting': 'outside-canonical-json'}], 'string_rules': [{'quotation_mark': 'escape', 'reverse_solidus': 'escape', 'control_characters': 'deterministic-json-escapes', 'solidus': 'unescaped', 'non_ascii': 'literal-utf-8', 'surrogate_code_points': 'reject'}], 'number_rules': [{'accepted': 'signed-64-bit-integers-only', 'representation': 'minimal-base-10', 'negative_zero': 'not-distinct', 'fractions': 'reject', 'exponents': 'reject', 'non_finite': 'reject'}], 'output_rules': [{'insignificant_whitespace': 'omit', 'trailing_newline': 'forbidden', 'output_boundary': 'exact-canonical-utf-8-bytes'}]}


class ValidationFailure(Exception):
    pass


def fail(code: str, detail: str) -> None:
    raise ValidationFailure(f"{code}: {detail}")


def strict_json(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        fail("REPO-SPEC-IDENTITY-JSON-001", f"{path}: invalid UTF-8")
    except OSError as exc:
        fail("REPO-SPEC-IDENTITY-PATH-001", f"{path}: {exc}")
    try:
        value = json.loads(
            raw,
            object_pairs_hook=_unique_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-standard JSON constant {token}")
            ),
        )
    except (json.JSONDecodeError, ValueError) as exc:
        fail("REPO-SPEC-IDENTITY-JSON-001", f"{path}: {exc}")
    if not isinstance(value, dict):
        fail("REPO-SPEC-IDENTITY-JSON-002", f"{path}: top level must be an object")
    return value


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate object member {key}")
        result[key] = value
    return result


def exact_fields(value: dict[str, Any], fields: set[str], label: str) -> None:
    unknown = sorted(set(value) - fields)
    missing = sorted(fields - set(value))
    if unknown:
        fail("REPO-SPEC-IDENTITY-FIELD-001", f"{label}: unknown fields: {', '.join(unknown)}")
    if missing:
        fail("REPO-SPEC-IDENTITY-FIELD-002", f"{label}: missing fields: {', '.join(missing)}")


def string_list(value: Any, label: str) -> list[str]:
    if not isinstance(value, list) or not value:
        fail("REPO-SPEC-IDENTITY-TYPE-001", f"{label}: must be a non-empty array")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        fail("REPO-SPEC-IDENTITY-TYPE-001", f"{label}: entries must be non-empty strings")
    return list(value)


def validate_identity(value: Any, label: str) -> str:
    if not isinstance(value, str) or not IDENTITY.fullmatch(value):
        fail("REPO-SPEC-IDENTITY-IDENTITY-001", f"{label}: invalid construction identity")
    forbidden = sorted(set(value.split("-")) & FORBIDDEN_NAME_PARTS)
    if forbidden:
        fail("REPO-SPEC-IDENTITY-NAME-001", f"{label}: work-derived identity parts are forbidden")
    return value


def contained_path(root: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        fail("REPO-SPEC-IDENTITY-PATH-003", f"{label}: must be a non-empty relative path")
    pure = PurePosixPath(value)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        fail("REPO-SPEC-IDENTITY-PATH-003", f"{label}: path is not normalized and relative")
    target = root.joinpath(*pure.parts)
    try:
        target.resolve(strict=False).relative_to(root.resolve())
    except ValueError:
        fail("REPO-SPEC-IDENTITY-PATH-002", f"{label}: path escapes construction root")
    current = root
    for part in pure.parts:
        current = current / part
        if current.is_symlink():
            fail("REPO-SPEC-IDENTITY-PATH-002", f"{label}: symlink is forbidden")
    return target


def validate_common(value: dict[str, Any], label: str) -> str:
    present = sorted(set(value) & FORBIDDEN_CLAIM_KEYS)
    if present:
        fail("REPO-SPEC-IDENTITY-CLAIM-001", f"{label}: forbidden final-authority fields")
    identity = validate_identity(value["construction_identity"], f"{label}.construction_identity")
    if value["construction_status"] != "under-construction":
        fail("REPO-SPEC-IDENTITY-STATUS-001", f"{label}: status must be under-construction")
    if value["normative"] is not False:
        fail("REPO-SPEC-IDENTITY-STATUS-002", f"{label}: normative must be false")
    if not isinstance(value["responsibility"], str) or not value["responsibility"].strip():
        fail("REPO-SPEC-IDENTITY-TYPE-001", f"{label}.responsibility must be non-empty")
    string_list(value["expected_relationships"], f"{label}.expected_relationships")
    string_list(value["unresolved_questions"], f"{label}.unresolved_questions")
    return identity


def validate_canonical(value: dict[str, Any], label: str) -> None:
    exact_fields(value, CANONICAL_FIELDS, label)
    validate_common(value, label)
    actual = {field: value[field] for field in EXPECTED_CANONICAL_CONSTRAINTS}
    expected = {field: allowed[0] for field, allowed in EXPECTED_CANONICAL_CONSTRAINTS.items()}
    if actual != expected:
        fail("REPO-SPEC-IDENTITY-CANONICAL-001", f"{label}: canonical construction claims do not match policy")


def validate_schema(value: dict[str, Any], label: str) -> None:
    exact_fields(value, SCHEMA_FIELDS, label)
    validate_common(value, label)
    if value["target_construction_identity"] != "canonical-json-construction":
        fail("REPO-SPEC-IDENTITY-SCHEMA-001", f"{label}: invalid schema target")
    required_fields = value["required_fields"]
    if (
        not isinstance(required_fields, list)
        or len(required_fields) != len(CANONICAL_FIELDS)
        or set(required_fields) != CANONICAL_FIELDS
    ):
        fail("REPO-SPEC-IDENTITY-SCHEMA-001", f"{label}: required fields do not match model")
    if value["closed"] is not True:
        fail("REPO-SPEC-IDENTITY-SCHEMA-001", f"{label}: schema must be closed")
    if value["field_constraints"] != EXPECTED_CANONICAL_CONSTRAINTS:
        fail("REPO-SPEC-IDENTITY-SCHEMA-001", f"{label}: field constraints do not match model")
    forbidden_fields = value["forbidden_claim_fields"]
    if (
        not isinstance(forbidden_fields, list)
        or len(forbidden_fields) != len(SCHEMA_FORBIDDEN_CLAIM_FIELDS)
        or set(forbidden_fields) != SCHEMA_FORBIDDEN_CLAIM_FIELDS
    ):
        fail("REPO-SPEC-IDENTITY-SCHEMA-001", f"{label}: forbidden claim fields do not match policy")


def validate_manifest(root: Path) -> None:
    manifest = strict_json(root / MANIFEST_PATH)
    paths = manifest.get("artifact_paths")
    if not isinstance(paths, list) or not paths or len(paths) != len(set(paths)):
        fail("REPO-SPEC-IDENTITY-MANIFEST-002", "manifest paths are malformed or duplicate")
    declared = set(paths)
    for relative in (*ARTIFACTS, SCHEMA_PATH):
        if paths.count(relative) != 1:
            fail("REPO-SPEC-IDENTITY-MANIFEST-001", f"{relative}: must participate exactly once")
    for index, relative in enumerate(paths):
        target = contained_path(root, relative, f"manifest.artifact_paths[{index}]")
        if relative.startswith("authoritative/identity/") or relative == SCHEMA_PATH:
            if not target.is_file():
                fail("REPO-SPEC-IDENTITY-MANIFEST-003", f"{relative}: declared identity artifact is missing")
    participating = set()
    for directory in (root / "authoritative/identity", root / "authoritative/schemas/identity"):
        for path in sorted(directory.glob("*.json")):
            value = strict_json(path)
            if "construction_identity" in value:
                participating.add(path.relative_to(root).as_posix())
    undeclared = sorted(participating - declared)
    if undeclared:
        fail("REPO-SPEC-IDENTITY-MANIFEST-004", "undeclared identity construction participants")


def validate(root: Path) -> None:
    identities = set()
    observed = {}
    for relative in (*ARTIFACTS, *SUPPORTING_PATHS):
        path = contained_path(root, relative, relative)
        if not path.exists():
            fail("REPO-SPEC-IDENTITY-PATH-001", f"{relative}: required path is missing")
    for relative in ARTIFACTS:
        value = strict_json(root / relative)
        if relative.endswith("CANONICAL-JSON.json"):
            validate_canonical(value, relative)
        else:
            exact_fields(value, PLACEHOLDER_FIELDS, relative)
            validate_common(value, relative)
        identity = value["construction_identity"]
        if identity in identities:
            fail("REPO-SPEC-IDENTITY-IDENTITY-003", f"{relative}: duplicate construction identity")
        identities.add(identity)
        observed[relative] = identity
    schema_value = strict_json(root / SCHEMA_PATH)
    validate_schema(schema_value, SCHEMA_PATH)
    observed[SCHEMA_PATH] = schema_value["construction_identity"]
    for relative, expected in EXPECTED_IDENTITIES.items():
        if observed.get(relative) != expected:
            fail("REPO-SPEC-IDENTITY-IDENTITY-002", f"{relative}: unexpected construction identity")
    validate_manifest(root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    try:
        validate(args.root)
    except (ValidationFailure, OSError, UnicodeDecodeError, SyntaxError) as exc:
        print(f"identity construction validation failed: {exc}", file=sys.stderr)
        return 1
    print("identity construction validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
