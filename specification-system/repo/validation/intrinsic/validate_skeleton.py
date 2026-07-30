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
REPOSITORY_VOCABULARY_FIELDS = {
    "construction_identity", "construction_status", "responsibility",
    "normative", "repository_area_kinds", "authority_classifications",
    "lifecycle_classifications", "tree_entry_kinds", "ownership_roles", "record_contracts", "records",
    "dependency_relation", "classification_rules", "path_rules",
    "containment_rules", "ownership_rules", "tree_model_boundary",
    "expected_relationships", "unresolved_questions",
}
REPOSITORY_VOCABULARY_SCHEMA_FIELDS = {
    "construction_identity", "construction_status", "responsibility",
    "normative", "target_construction_identity", "required_fields", "closed",
    "field_constraints", "forbidden_claim_fields", "expected_relationships",
    "unresolved_questions",
}
REPOSITORY_VOCABULARY_FIXTURE_FIELDS = {
    "construction_identity", "construction_status", "responsibility",
    "normative", "cases", "expected_relationships", "unresolved_questions",
}
SPECIFICATION_ARTIFACT_FIELDS = {
    "construction_identity", "construction_status", "responsibility", "normative",
    "artifact_classes", "class_constraints", "relationship_types", "relationship_rules",
    "classification_boundary", "expected_relationships", "unresolved_questions",
}
SPECIFICATION_ARTIFACT_SCHEMA_FIELDS = {
    "construction_identity", "construction_status", "responsibility", "normative",
    "target_construction_identity", "required_fields", "closed", "field_constraints",
    "forbidden_claim_fields", "expected_relationships", "unresolved_questions",
}
SPECIFICATION_ARTIFACT_FIXTURE_FIELDS = {
    "construction_identity", "construction_status", "responsibility", "normative",
    "cases", "expected_relationships", "unresolved_questions",
}
VALIDATION_LIBRARY_FIELDS = PLACEHOLDER_FIELDS | {
    "module_inventory",
    "dependency_direction",
    "api_contracts",
    "diagnostic_contract",
    "fail_closed_behavior",
    "product_independence",
    "integration_responsibilities",
    "retained_intrinsic_behavior",
    "unavailable_capabilities",
    "authority_boundary",
}
VALIDATION_LIBRARY_PATH = "validation/lib/VALIDATION-LIBRARY.json"
CONFORMANCE_BOUNDARY_PATH = "authoritative/conformance/CONFORMANCE-BOUNDARY.json"
IDENTITY_CONFORMANCE_PATH = "authoritative/conformance/IDENTITY-CONFORMANCE.json"
CONFORMANCE_SCHEMA_PATH = "authoritative/schemas/conformance/IDENTITY-CONFORMANCE-CONSTRUCTION-SCHEMA.json"
CONFORMANCE_VECTOR_PATH = "validation/fixtures/identity/conformance/IDENTITY-CONFORMANCE-VECTORS.json"
CONFORMANCE_BOUNDARY_FIELDS = PLACEHOLDER_FIELDS | {
    "conformance_scope", "vector_classes", "execution_contract",
    "diagnostic_contract", "coverage_contract", "authority_boundary",
    "unavailable_capabilities",
}
IDENTITY_CONFORMANCE_FIELDS = PLACEHOLDER_FIELDS | {
    "vector_envelope", "uniqueness_constraints", "coverage_requirements",
    "failure_precedence", "fixture_integration", "product_independence",
    "unavailable_capabilities",
}
FRAMEWORK_BOUNDARY_PATH = "authoritative/framework-boundary/FRAMEWORK-BOUNDARY.json"
FRAMEWORK_BOUNDARY_SCHEMA_PATH = "authoritative/schemas/framework-boundary/FRAMEWORK-BOUNDARY-CONSTRUCTION-SCHEMA.json"
FRAMEWORK_BOUNDARY_FIELDS = {
    "construction_identity", "construction_status", "responsibility",
    "normative", "entity_types", "entity_constraints",
    "relationship_types", "relationship_rules",
    "authority_separation", "decision_basis",
    "expected_relationships", "unresolved_questions",
}
FRAMEWORK_BOUNDARY_SCHEMA_FIELDS = {
    "construction_identity", "construction_status", "responsibility",
    "normative", "target_construction_identity", "required_fields",
    "closed", "field_constraints", "forbidden_claim_fields",
    "expected_relationships", "unresolved_questions",
}
FRAMEWORK_BOUNDARY_FIXTURE_FIELDS = {
    "construction_identity", "construction_status", "responsibility",
    "normative", "cases", "expected_relationships", "unresolved_questions",
}
FRAMEWORK_BOUNDARY_FIXTURE_PATH = "validation/fixtures/framework-boundary/FRAMEWORK-BOUNDARY-FIXTURES.json"
DEVELOPMENT_ARTIFACT_PATH = "authoritative/development-artifacts/DEVELOPMENT-ARTIFACTS.json"
DEVELOPMENT_ARTIFACT_SCHEMA_PATH = "authoritative/schemas/development-artifacts/DEVELOPMENT-ARTIFACT-CONSTRUCTION-SCHEMA.json"
DEVELOPMENT_ARTIFACT_FIXTURE_PATH = "validation/fixtures/development-artifacts/DEVELOPMENT-ARTIFACT-FIXTURES.json"
DEVELOPMENT_ARTIFACT_FIELDS = {
    "construction_identity", "construction_status", "responsibility",
    "normative", "artifact_roles", "role_constraints",
    "overview_model", "plan_model", "role_relationships",
    "authority_separation", "decision_basis",
    "expected_relationships", "unresolved_questions",
}
DEVELOPMENT_ARTIFACT_SCHEMA_FIELDS = {
    "construction_identity", "construction_status", "responsibility",
    "normative", "target_construction_identity", "required_fields",
    "closed", "field_constraints", "forbidden_claim_fields",
    "expected_relationships", "unresolved_questions",
}
DEVELOPMENT_ARTIFACT_FIXTURE_FIELDS = {
    "construction_identity", "construction_status", "responsibility",
    "normative", "cases", "expected_relationships", "unresolved_questions",
}
DEVELOPMENT_ARTIFACT_CLOSED_ROLES: tuple[str, ...] = (
    "product-overview",
    "implementation-plan",
    "scratchpad",
    "decision-record",
    "governing-issue",
    "detailed-scope",
    "patch-plan",
    "unresolved-question-record",
    "validation-evidence-reference",
    "review-evidence-reference",
)
FUNCTIONAL_AREA_PATH = "authoritative/functional-areas/FUNCTIONAL-AREAS.json"
FUNCTIONAL_AREA_SCHEMA_PATH = "authoritative/schemas/functional-areas/FUNCTIONAL-AREA-CONSTRUCTION-SCHEMA.json"
FUNCTIONAL_AREA_FIXTURE_PATH = "validation/fixtures/functional-areas/FUNCTIONAL-AREA-FIXTURES.json"
FUNCTIONAL_AREA_FIELDS = {
    "construction_identity", "construction_status", "responsibility",
    "normative", "repository_vocabulary_identity", "functional_areas",
    "area_semantics", "kernel_classifications", "extension_rules",
    "placement_rules", "authority_separation", "decision_basis",
    "expected_relationships", "unresolved_questions",
}
FUNCTIONAL_AREA_SCHEMA_FIELDS = {
    "construction_identity", "construction_status", "responsibility",
    "normative", "target_construction_identity", "required_fields",
    "closed", "field_constraints", "forbidden_claim_fields",
    "expected_relationships", "unresolved_questions",
}
FUNCTIONAL_AREA_FIXTURE_FIELDS = {
    "construction_identity", "construction_status", "responsibility",
    "normative", "cases", "expected_relationships", "unresolved_questions",
}
FUNCTIONAL_AREA_CLOSED_AREAS: tuple[str, ...] = (
    "overview-documentation",
    "implementation-planning",
    "repository-specifications",
    "product-specifications",
    "maintained-product-source",
    "tests",
    "schemas",
    "conformance",
    "generated-artifacts",
    "validation",
    "repository-tooling",
    "packaging-and-release",
    "temporary-development-state",
)
MANIFEST_PATH = "REPOSITORY-SPECIFICATION-SET.json"
ARTIFACT_CLASSES = (
    "canonical-json-construction",
    "canonical-json-construction-schema",
    "conformance-boundary-construction",
    "development-process-placeholder",
    "identity-authority-placeholder",
    "identity-conformance-construction",
    "identity-conformance-construction-schema",
    "identity-conformance-vector-set-construction",
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
    "repository-vocabulary-construction",
    "repository-vocabulary-construction-schema",
    "repository-vocabulary-fixture-set-construction",
    "repository-validation-placeholder",
    "schema-boundary-placeholder",
    "source-layout-placeholder",
    "specification-artifact-class-construction",
    "specification-artifact-class-construction-schema",
    "specification-artifact-fixture-set-construction",
    "validation-fixtures-placeholder",
    "validation-library-construction",
    "transition-baseline-classification",
    "framework-boundary",
    "framework-boundary-construction-schema",
    "framework-boundary-fixture-set-construction",
    "development-artifact-construction",
    "development-artifact-construction-schema",
    "development-artifact-fixture-set-construction",
    "functional-area-construction",
    "functional-area-construction-schema",
    "functional-area-fixture-set-construction",
)
ARTIFACT_PATHS = (
    "authoritative/repository-model/REPOSITORY-MODEL.json",
    "authoritative/schemas/repository-model/REPOSITORY-VOCABULARY-CONSTRUCTION-SCHEMA.json",
    "validation/fixtures/repository-model/REPOSITORY-VOCABULARY-FIXTURES.json",
    "authoritative/specification-system/SPECIFICATION-ARTIFACTS.json",
    "authoritative/schemas/specification-system/SPECIFICATION-ARTIFACT-CLASS-CONSTRUCTION-SCHEMA.json",
    "validation/fixtures/specification-system/SPECIFICATION-ARTIFACT-FIXTURES.json",
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
    CONFORMANCE_BOUNDARY_PATH,
    IDENTITY_CONFORMANCE_PATH,
    CONFORMANCE_SCHEMA_PATH,
    "validation/lib/VALIDATION-LIBRARY.json",
    "validation/repository/REPOSITORY-VALIDATION.json",
    "validation/fixtures/VALIDATION-FIXTURES.json",
    "validation/fixtures/identity/identity-family/IDENTITY-FAMILY-FIXTURES.json",
    "validation/fixtures/identity/identity-behavior/IDENTITY-BEHAVIOR-FIXTURES.json",
    "validation/fixtures/identity/conformance/IDENTITY-CONFORMANCE-VECTORS.json",
    "TRANSITION-BASELINE-CLASSIFICATION.json",
    "authoritative/framework-boundary/FRAMEWORK-BOUNDARY.json",
    "authoritative/schemas/framework-boundary/FRAMEWORK-BOUNDARY-CONSTRUCTION-SCHEMA.json",
    "validation/fixtures/framework-boundary/FRAMEWORK-BOUNDARY-FIXTURES.json",
    DEVELOPMENT_ARTIFACT_PATH,
    DEVELOPMENT_ARTIFACT_SCHEMA_PATH,
    DEVELOPMENT_ARTIFACT_FIXTURE_PATH,
    FUNCTIONAL_AREA_PATH,
    FUNCTIONAL_AREA_SCHEMA_PATH,
    FUNCTIONAL_AREA_FIXTURE_PATH,
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
    CONFORMANCE_BOUNDARY_PATH,
    IDENTITY_CONFORMANCE_PATH,
    CONFORMANCE_SCHEMA_PATH,
    "validation/fixtures/identity/identity-family/IDENTITY-FAMILY-FIXTURES.json",
    "authoritative/repository-model/REPOSITORY-MODEL.json",
    "authoritative/schemas/repository-model/REPOSITORY-VOCABULARY-CONSTRUCTION-SCHEMA.json",
    "validation/fixtures/repository-model/REPOSITORY-VOCABULARY-FIXTURES.json",
    "authoritative/specification-system/SPECIFICATION-ARTIFACTS.json",
    "authoritative/schemas/specification-system/SPECIFICATION-ARTIFACT-CLASS-CONSTRUCTION-SCHEMA.json",
    "validation/fixtures/specification-system/SPECIFICATION-ARTIFACT-FIXTURES.json",
    "TRANSITION-BASELINE-CLASSIFICATION.json",
    "authoritative/framework-boundary/FRAMEWORK-BOUNDARY.json",
    "authoritative/schemas/framework-boundary/FRAMEWORK-BOUNDARY-CONSTRUCTION-SCHEMA.json",
    "validation/fixtures/framework-boundary/FRAMEWORK-BOUNDARY-FIXTURES.json",
    DEVELOPMENT_ARTIFACT_PATH,
    DEVELOPMENT_ARTIFACT_SCHEMA_PATH,
    DEVELOPMENT_ARTIFACT_FIXTURE_PATH,
    FUNCTIONAL_AREA_PATH,
    FUNCTIONAL_AREA_SCHEMA_PATH,
    FUNCTIONAL_AREA_FIXTURE_PATH,
}
PLACEHOLDER_PATHS = tuple(path for path in ARTIFACT_PATHS if path not in NON_PLACEHOLDER_PATHS)
REQUIRED_DIRECTORIES = (
    "authoritative/identity", "authoritative/repository-model",
    "authoritative/specification-system", "authoritative/development-process",
    "authoritative/normative-change", "authoritative/level-model",
    "authoritative/source-layout", "authoritative/schemas",
    "authoritative/schemas/identity", "authoritative/schemas/conformance",
    "authoritative/schemas/specification-system",
    "validation/fixtures/specification-system",
    "authoritative/schemas/repository-model",
    "authoritative/framework-boundary",
    "authoritative/schemas/framework-boundary",
    "authoritative/development-artifacts",
    "authoritative/schemas/development-artifacts",
    "authoritative/functional-areas",
    "authoritative/schemas/functional-areas",
    "validation/fixtures/framework-boundary",
    "validation/fixtures/development-artifacts",
    "validation/fixtures/functional-areas",
    "validation/fixtures/repository-model",
    "authoritative/conformance",
    "derived/markdown", "derived/markdown/identity",
    "derived/markdown/conformance", "validation/lib",
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
    "authoritative/schemas/conformance/README.md",
    "derived/markdown/conformance/README.md",
    "validation/fixtures/identity/README.md",
    "validation/fixtures/identity/conformance/IDENTITY-CONFORMANCE-VECTORS.json",
    "validation/intrinsic/identity_behavior_adapter.py",
    "validation/intrinsic/validate_skeleton.py",
    "validation/intrinsic/validate_identity_construction.py",
    "validation/intrinsic/validate_canonical_json.py",
    "validation/lib/__init__.py",
    "validation/lib/strict_json.py",
    "validation/lib/canonical_json.py",
    "validation/lib/contracts.py",
    "validation/lib/identity.py",
    VALIDATION_LIBRARY_PATH,
    "validation/tests/test_construction_skeleton.py",
    "validation/tests/test_complete_construction_skeleton.py",
    "validation/tests/test_identity_construction.py",
    "validation/tests/test_identity_family.py",
    "validation/tests/test_identity_behavior.py",
    "validation/tests/test_canonical_json.py",
    "validation/tests/test_conformance_construction.py",
    "validation/tests/test_identity_conformance_vectors.py",
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
    if "\\" in value or "\x00" in value:
        fail("REPO-SPEC-CONSTRUCTION-PATH-002", f"{label}: path contains a forbidden character")
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

def validate_repository_vocabulary(value: dict[str, Any], label: str, root: Path) -> str:
    exact_fields(value, REPOSITORY_VOCABULARY_FIELDS, label)
    identity = validate_common(value, label)
    if identity != "repository-model":
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-002", f"{label}: unexpected repository-vocabulary identity")
    expected = {
        "repository_area_kinds": ["authority", "derived", "validation", "support", "temporary"],
        "authority_classifications": ["normative", "non-normative"],
        "lifecycle_classifications": ["maintained", "generated", "temporary"],
        "tree_entry_kinds": ["file", "directory"],
        "ownership_roles": ["area-owner", "artifact-owner"],
    }
    for field, expected_value in expected.items():
        if value[field] != expected_value:
            fail("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-001", f"{label}.{field}: vocabulary mismatch")
    contracts = value["record_contracts"]
    if set(contracts) != {"areas", "tree_members", "owners", "containments", "dependencies"}:
        fail("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-001", f"{label}.record_contracts: unknown or missing contract")
    contract_fields = {
        "areas": {"fields", "unique_by", "kind_values"},
        "tree_members": {"fields", "unique_by", "entry_kind_values", "authority_values", "lifecycle_values"},
        "owners": {"fields", "unique_by", "target", "role_values"},
        "containments": {"fields", "unique_by", "parent_kind", "child_relation", "immediate_parent"},
        "dependencies": {"fields", "unique_by", "relation_values", "endpoints", "self_reference", "cycles"},
    }
    for contract_name, fields in contract_fields.items():
        exact_fields(contracts[contract_name], fields, f"{label}.record_contracts.{contract_name}")
        contract = contracts[contract_name]
        if (
            not isinstance(contract["fields"], list)
            or not contract["fields"]
            or len(contract["fields"]) != len(set(contract["fields"]))
            or not isinstance(contract["unique_by"], list)
            or not contract["unique_by"]
            or len(contract["unique_by"]) != len(set(contract["unique_by"]))
        ):
            fail("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-001", f"{label}.record_contracts.{contract_name}: invalid field contract")
    if contracts["dependencies"]["relation_values"] != ["depends-on"] or contracts["dependencies"]["self_reference"] != "forbidden" or contracts["dependencies"]["cycles"] != "forbidden":
        fail("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-001", f"{label}.record_contracts.dependencies: boundary mismatch")
    exact_fields(value["dependency_relation"], {"name", "direction", "endpoints", "self_dependency", "cycles"}, f"{label}.dependency_relation")
    if value["dependency_relation"] != {
        "name": "depends-on", "direction": "dependent-to-prerequisite",
        "endpoints": "declared-area-or-tree-member-identifiers",
        "self_dependency": "forbidden", "cycles": "forbidden",
    }:
        fail("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-001", f"{label}.dependency_relation: boundary mismatch")
    exact_fields(value["classification_rules"], {
        "tree_member_authority", "tree_member_lifecycle", "normative_requires",
        "generated_requires", "temporary_requires", "lifecycle_classifications_are_disjoint",
    }, f"{label}.classification_rules")
    exact_fields(value["path_rules"], {
        "root_representation", "root_is_implicit", "format", "components", "forbidden", "symlinks",
    }, f"{label}.path_rules")
    exact_fields(value["containment_rules"], {
        "relation", "directory_may_contain", "file_may_contain", "declared_parent", "filesystem_closure",
    }, f"{label}.containment_rules")
    exact_fields(value["ownership_rules"], {"owner_identifier", "owner_scope", "owner_role"}, f"{label}.ownership_rules")
    exact_fields(value["tree_model_boundary"], {"represents", "does_not_represent"}, f"{label}.tree_model_boundary")
    if value["path_rules"]["root_representation"] != "." or value["path_rules"]["root_is_implicit"] is not True:
        fail("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-001", f"{label}.path_rules: root boundary mismatch")
    if value["containment_rules"]["directory_may_contain"] is not True or value["containment_rules"]["file_may_contain"] is not False:
        fail("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-001", f"{label}.containment_rules: directory/file containment boundary mismatch")
    records = value["records"]
    if set(records) != {"areas", "tree_members", "owners", "containments", "dependencies"}:
        fail("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-004", f"{label}.records: unknown or missing record set")
    areas = {}
    for item in records["areas"]:
        exact_fields(item, {"id", "kind"}, f"{label}.records.areas")
        identifier = validate_identity(item["id"], f"{label}.records.areas.id")
        if identifier in areas or item["kind"] not in value["repository_area_kinds"]:
            fail("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-004", f"{label}.records.areas: duplicate or invalid area")
        areas[identifier] = item["kind"]
    members = {}
    paths = {}
    for item in records["tree_members"]:
        exact_fields(item, {"id", "path", "entry_kind", "authority_classification", "lifecycle_classification"}, f"{label}.records.tree_members")
        identifier = validate_identity(item["id"], f"{label}.records.tree_members.id")
        if identifier in members or item["path"] in paths:
            fail("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-004", f"{label}.records.tree_members: duplicate identifier or path")
        contained_path(root, item["path"], f"{label}.records.tree_members.path")
        if item["entry_kind"] not in value["tree_entry_kinds"] or item["authority_classification"] not in value["authority_classifications"] or item["lifecycle_classification"] not in value["lifecycle_classifications"]:
            fail("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-004", f"{label}.records.tree_members: unknown classification")
        if item["authority_classification"] == "normative" and item["lifecycle_classification"] != "maintained":
            fail("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-004", f"{label}.records.tree_members: normative member must be maintained")
        if item["lifecycle_classification"] in {"generated", "temporary"} and item["authority_classification"] != "non-normative":
            fail("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-004", f"{label}.records.tree_members: generated or temporary member must be non-normative")
        members[identifier] = item
        paths[item["path"]] = identifier
    targets = set(areas) | set(members)
    owner_ids = set()
    owner_pairs = set()
    for item in records["owners"]:
        exact_fields(item, {"id", "target", "role"}, f"{label}.records.owners")
        identifier = validate_identity(item["id"], f"{label}.records.owners.id")
        pair = (item["target"], item["role"])
        if identifier in owner_ids or pair in owner_pairs or item["target"] not in targets or item["role"] not in value["ownership_roles"]:
            fail("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-004", f"{label}.records.owners: duplicate or invalid owner")
        owner_ids.add(identifier)
        owner_pairs.add(pair)
    containment_pairs = set()
    for item in records["containments"]:
        exact_fields(item, {"parent", "child"}, f"{label}.records.containments")
        pair = (item["parent"], item["child"])
        if pair in containment_pairs or item["parent"] not in members or item["child"] not in members or item["parent"] == item["child"]:
            fail("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-004", f"{label}.records.containments: invalid or duplicate containment")
        parent = members[item["parent"]]
        child = members[item["child"]]
        if parent["entry_kind"] != "directory":
            fail("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-004", f"{label}.records.containments: parent must be directory")
        parent_parts = PurePosixPath(parent["path"]).parts
        child_parts = PurePosixPath(child["path"]).parts
        if len(child_parts) <= len(parent_parts) or child_parts[:len(parent_parts)] != parent_parts:
            fail("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-004", f"{label}.records.containments: child is not a descendant")
        containment_pairs.add(pair)
    dependency_edges = {}
    dependency_pairs = set()
    for item in records["dependencies"]:
        exact_fields(item, {"source", "target", "relation"}, f"{label}.records.dependencies")
        edge = (item["source"], item["target"], item["relation"])
        if edge in dependency_pairs or item["source"] not in targets or item["target"] not in targets or item["source"] == item["target"] or item["relation"] != "depends-on":
            fail("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-004", f"{label}.records.dependencies: invalid or duplicate dependency")
        dependency_pairs.add(edge)
        dependency_edges.setdefault(item["source"], set()).add(item["target"])
    visiting = set()
    visited = set()
    def visit(node: str) -> None:
        if node in visiting:
            fail("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-004", f"{label}.records.dependencies: cycle detected")
        if node in visited:
            return
        visiting.add(node)
        for target in dependency_edges.get(node, set()):
            visit(target)
        visiting.remove(node)
        visited.add(node)
    for node in targets:
        visit(node)
    return identity

def validate_repository_vocabulary_schema(value: dict[str, Any], label: str) -> str:
    exact_fields(value, REPOSITORY_VOCABULARY_SCHEMA_FIELDS, label)
    identity = validate_common(value, label)
    if identity != "repository-vocabulary-construction-schema":
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-002", f"{label}: unexpected repository-vocabulary schema identity")
    if value["target_construction_identity"] != "repository-model" or value["closed"] is not True:
        fail("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-002", f"{label}: target or closed boundary mismatch")
    if (
        not isinstance(value["required_fields"], list)
        or not value["required_fields"]
        or any(not isinstance(field, str) for field in value["required_fields"])
        or len(value["required_fields"]) != len(set(value["required_fields"]))
    ):
        fail("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-002", f"{label}: required fields are not deterministic")
    return identity

def validate_repository_vocabulary_fixtures(value: dict[str, Any], label: str) -> str:
    exact_fields(value, REPOSITORY_VOCABULARY_FIXTURE_FIELDS, label)
    identity = validate_common(value, label)
    if identity != "repository-vocabulary-fixture-set-construction":
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-002", f"{label}: unexpected repository-vocabulary fixture identity")
    cases = value["cases"]
    if not isinstance(cases, list) or not cases:
        fail("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-003", f"{label}.cases: non-empty array required")
    names = []
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"name", "expected", "model_overrides", "expected_diagnostic"}:
            fail("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-003", f"{label}.cases: closed case required")
        if not isinstance(case["name"], str) or case["name"] in names:
            fail("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-003", f"{label}.cases: unique names required")
        if case["expected"] not in {"pass", "reject"} or not isinstance(case["model_overrides"], dict):
            fail("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-003", f"{label}.cases: invalid case declaration")
        if case["expected"] == "pass" and case["expected_diagnostic"] is not None:
            fail("REPO-SPEC-CONSTRUCTION-REPOSITORY-VOCABULARY-003", f"{label}.cases: passing case diagnostic must be null")
        names.append(case["name"])
    return identity

def validate_specification_artifacts(value: dict[str, Any], label: str) -> str:
    exact_fields(value, SPECIFICATION_ARTIFACT_FIELDS, label)
    identity = validate_common(value, label)
    if identity != "specification-artifacts":
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-002", f"{label}: unexpected specification-artifact identity")
    expected_classes = [
        "authoritative-specification-artifact", "derived-artifact", "schema",
        "conformance-artifact", "validation-implementation", "fixture", "manifest-participant",
    ]
    if value["artifact_classes"] != expected_classes:
        fail("REPO-SPEC-CONSTRUCTION-ARTIFACT-001", f"{label}.artifact_classes: unexpected class inventory")
    if set(value["class_constraints"]) != set(expected_classes):
        fail("REPO-SPEC-CONSTRUCTION-ARTIFACT-001", f"{label}.class_constraints: class inventory mismatch")
    relationship_types = value["relationship_types"]
    if not isinstance(relationship_types, list) or not relationship_types or any(not isinstance(item, str) or not item for item in relationship_types) or len(relationship_types) != len(set(relationship_types)):
        fail("REPO-SPEC-CONSTRUCTION-ARTIFACT-001", f"{label}.relationship_types: non-empty unique list required")
    relationship_vocabulary = set(relationship_types)
    expected_relationship_rules = {
        "projection-source": {"acyclic": True, "deterministic": True, "max_sources": 1},
        "authoring-source": {"acyclic": True, "deterministic": True, "max_sources": 1},
    }
    if value["relationship_rules"] != expected_relationship_rules:
        fail("REPO-SPEC-CONSTRUCTION-ARTIFACT-001", f"{label}.relationship_rules: acyclicity or determinism boundary mismatch")
    expected_constraints = {
        "authoritative-specification-artifact": ([], ["projection-source", "authoring-source"]),
        "derived-artifact": (["projection-source"], ["schema-target", "conformance-target"]),
        "schema": (["schema-target"], ["projection-source"]),
        "conformance-artifact": (["conformance-target"], ["projection-source"]),
        "validation-implementation": (["validator-target"], ["schema-target", "projection-source"]),
        "fixture": (["fixture-validator"], ["schema-target", "projection-source"]),
        "manifest-participant": ([], ["semantic-identity", "revision-binding"]),
    }
    for class_name in expected_classes:
        exact_fields(value["class_constraints"][class_name], {"required_relationships", "forbidden_relationships", "manifest_eligible"}, f"{label}.class_constraints.{class_name}")
        constraints = value["class_constraints"][class_name]
        required = constraints["required_relationships"]
        forbidden = constraints["forbidden_relationships"]
        if (
            not isinstance(constraints["manifest_eligible"], bool)
            or not isinstance(required, list)
            or not isinstance(forbidden, list)
            or any(not isinstance(item, str) or item not in relationship_vocabulary for item in required + forbidden)
            or len(required) != len(set(required))
            or len(forbidden) != len(set(forbidden))
            or set(required) & set(forbidden)
            or required != expected_constraints[class_name][0]
            or forbidden != expected_constraints[class_name][1]
            or constraints["manifest_eligible"] is not True
        ):
            fail("REPO-SPEC-CONSTRUCTION-ARTIFACT-001", f"{label}.class_constraints.{class_name}: invalid manifest eligibility")
    exact_fields(value["classification_boundary"], {"class_is_distinct_from_semantic_identity", "authority_is_distinct_from_class", "construction_artifacts_are_non_normative", "semantic_identity", "revision"}, f"{label}.classification_boundary")
    boundary = value["classification_boundary"]
    if any(boundary[key] is not True for key in ("class_is_distinct_from_semantic_identity", "authority_is_distinct_from_class", "construction_artifacts_are_non_normative")) or boundary["semantic_identity"] != "unassigned" or boundary["revision"] != "unassigned":
        fail("REPO-SPEC-CONSTRUCTION-ARTIFACT-001", f"{label}.classification_boundary: identity boundary mismatch")
    return identity

def validate_specification_artifact_schema(value: dict[str, Any], label: str) -> str:
    exact_fields(value, SPECIFICATION_ARTIFACT_SCHEMA_FIELDS, label)
    identity = validate_common(value, label)
    if identity != "specification-artifact-class-construction-schema":
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-002", f"{label}: unexpected specification-artifact schema identity")
    if value["target_construction_identity"] != "specification-artifacts" or value["closed"] is not True:
        fail("REPO-SPEC-CONSTRUCTION-ARTIFACT-002", f"{label}: target or closed boundary mismatch")
    expected_required_fields = [
        "construction_identity", "construction_status", "responsibility", "normative",
        "artifact_classes", "class_constraints", "relationship_types", "relationship_rules",
        "classification_boundary", "expected_relationships", "unresolved_questions",
    ]
    if value["required_fields"] != expected_required_fields:
        fail("REPO-SPEC-CONSTRUCTION-ARTIFACT-002", f"{label}.required_fields: non-empty unique list required")
    if value["forbidden_claim_fields"] != sorted(FORBIDDEN_CLAIM_KEYS):
        fail("REPO-SPEC-CONSTRUCTION-ARTIFACT-002", f"{label}.forbidden_claim_fields: incomplete claim boundary")
    return identity

def validate_specification_artifact_fixtures(value: dict[str, Any], label: str) -> str:
    exact_fields(value, SPECIFICATION_ARTIFACT_FIXTURE_FIELDS, label)
    identity = validate_common(value, label)
    if identity != "specification-artifact-fixture-set-construction":
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-002", f"{label}: unexpected specification-artifact fixture identity")
    cases = value["cases"]
    if not isinstance(cases, list) or not cases:
        fail("REPO-SPEC-CONSTRUCTION-ARTIFACT-003", f"{label}.cases: non-empty array required")
    names = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"name", "expected", "class_overrides", "expected_diagnostic"}:
            fail("REPO-SPEC-CONSTRUCTION-ARTIFACT-003", f"{label}.cases: closed case required")
        if not isinstance(case["name"], str) or not case["name"] or case["name"] in names:
            fail("REPO-SPEC-CONSTRUCTION-ARTIFACT-003", f"{label}.cases: unique names required")
        if case["expected"] not in {"pass", "reject"} or not isinstance(case["class_overrides"], dict):
            fail("REPO-SPEC-CONSTRUCTION-ARTIFACT-003", f"{label}.cases: invalid case declaration")
        if case["expected"] == "pass" and case["expected_diagnostic"] is not None:
            fail("REPO-SPEC-CONSTRUCTION-ARTIFACT-003", f"{label}.cases: passing diagnostic must be null")
        names.add(case["name"])
    return identity

def validate_validation_library(value: dict[str, Any], label: str) -> str:
    exact_fields(value, VALIDATION_LIBRARY_FIELDS, label)
    identity = validate_common(value, label)
    if identity != "validation-library-construction":
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-002",
             f"{label}: unexpected validation-library construction identity")
    modules = value["module_inventory"]
    expected_modules = [
        "validation.lib.strict_json",
        "validation.lib.canonical_json",
        "validation.lib.contracts",
        "validation.lib.identity",
    ]
    if (
        not isinstance(modules, list)
        or [item.get("module") for item in modules if isinstance(item, dict)]
        != expected_modules
        or any(
            set(item) != {"module", "responsibilities"}
            or not isinstance(item["responsibilities"], list)
            or not item["responsibilities"]
            or len(item["responsibilities"]) != len(set(item["responsibilities"]))
            for item in modules
            if isinstance(item, dict)
        )
        or any(not isinstance(item, dict) for item in modules)
    ):
        fail("REPO-SPEC-CONSTRUCTION-VALIDATION-LIBRARY-001",
             f"{label}: invalid module inventory")
    for field in (
        "dependency_direction",
        "fail_closed_behavior",
        "retained_intrinsic_behavior",
        "unavailable_capabilities",
    ):
        if not isinstance(value[field], list) or not value[field]:
            fail("REPO-SPEC-CONSTRUCTION-VALIDATION-LIBRARY-001",
                 f"{label}.{field}: non-empty array required")
    for field in (
        "api_contracts",
        "diagnostic_contract",
        "product_independence",
        "integration_responsibilities",
        "authority_boundary",
    ):
        if not isinstance(value[field], dict) or not value[field]:
            fail("REPO-SPEC-CONSTRUCTION-VALIDATION-LIBRARY-001",
                 f"{label}.{field}: non-empty object required")
    if value["diagnostic_contract"].get("representation") != "deterministic-string":
        fail("REPO-SPEC-CONSTRUCTION-VALIDATION-LIBRARY-001",
             f"{label}: structured or non-deterministic diagnostics are forbidden")
    if value["product_independence"] != {
        "third_party_dependencies": "forbidden",
        "maintained_product_imports": "forbidden",
        "product-identities-and-evidence": "forbidden",
        "repository-global-state": "forbidden",
    }:
        fail("REPO-SPEC-CONSTRUCTION-VALIDATION-LIBRARY-001",
             f"{label}: product-independence boundary mismatch")
    authority = value["authority_boundary"]
    if (
        authority.get("status") != "construction-only"
        or authority.get("accepted-specification-authority") is not False
        or authority.get("accepted-product-authority") is not False
        or authority.get("implementation-files-have-semantic-identities") is not False
    ):
        fail("REPO-SPEC-CONSTRUCTION-VALIDATION-LIBRARY-001",
             f"{label}: authority boundary mismatch")
    return identity


def _non_empty_unique_strings(value: Any, label: str) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
        or len(value) != len(set(value))
    ):
        fail("REPO-SPEC-CONSTRUCTION-CONFORMANCE-001",
             f"{label}: non-empty unique string array required")
    return value

def validate_conformance_boundary(value: dict[str, Any], label: str) -> str:
    exact_fields(value, CONFORMANCE_BOUNDARY_FIELDS, label)
    identity = validate_common(value, label)
    if identity != "conformance-boundary-construction":
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-002",
             f"{label}: unexpected conformance construction identity")
    _non_empty_unique_strings(value["conformance_scope"], f"{label}.conformance_scope")
    if value["vector_classes"] != ["positive", "negative"]:
        fail("REPO-SPEC-CONSTRUCTION-CONFORMANCE-001",
             f"{label}: vector classes mismatch")
    for field in ("execution_contract", "diagnostic_contract",
                  "coverage_contract", "authority_boundary"):
        if not isinstance(value[field], dict) or not value[field]:
            fail("REPO-SPEC-CONSTRUCTION-CONFORMANCE-001",
                 f"{label}.{field}: non-empty object required")
    authority = value["authority_boundary"]
    if (
        authority.get("status") != "construction-only"
        or authority.get("accepted-conformance") is not False
        or authority.get("accepted-specification-authority") is not False
        or authority.get("accepted-product-authority") is not False
        or authority.get("vectors-define-new-semantics") is not False
    ):
        fail("REPO-SPEC-CONSTRUCTION-CONFORMANCE-001",
             f"{label}: authority boundary mismatch")
    _non_empty_unique_strings(
        value["unavailable_capabilities"], f"{label}.unavailable_capabilities"
    )
    return identity

def validate_identity_conformance(value: dict[str, Any], label: str) -> str:
    exact_fields(value, IDENTITY_CONFORMANCE_FIELDS, label)
    identity = validate_common(value, label)
    if identity != "identity-conformance-construction":
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-002",
             f"{label}: unexpected identity conformance construction identity")
    envelope = value["vector_envelope"]
    if not isinstance(envelope, dict) or envelope.get("closed") is not True:
        fail("REPO-SPEC-CONSTRUCTION-CONFORMANCE-001",
             f"{label}.vector_envelope: closed object required")
    expected_required = [
        "vector_id", "behavior_class", "classification", "input",
        "expected_outcome", "fixture_owner", "validator_owner", "coverage_tags",
    ]
    if envelope.get("required_fields") != expected_required:
        fail("REPO-SPEC-CONSTRUCTION-CONFORMANCE-001",
             f"{label}: vector envelope required fields mismatch")
    for field in (
        "uniqueness_constraints", "coverage_requirements",
        "failure_precedence", "unavailable_capabilities",
    ):
        _non_empty_unique_strings(value[field], f"{label}.{field}")
    for field in ("fixture_integration", "product_independence"):
        if not isinstance(value[field], dict) or not value[field]:
            fail("REPO-SPEC-CONSTRUCTION-CONFORMANCE-001",
                 f"{label}.{field}: non-empty object required")
    return identity

def validate_identity_conformance_schema(value: dict[str, Any], label: str) -> str:
    required = {
        "construction_identity", "construction_status", "responsibility",
        "normative", "target_construction_identity", "required_fields",
        "closed", "field_constraints", "forbidden_claim_fields",
        "expected_relationships", "unresolved_questions",
    }
    exact_fields(value, required, label)
    identity = validate_common(value, label)
    if (
        identity != "identity-conformance-construction-schema"
        or value["target_construction_identity"] != "identity-conformance-construction"
        or value["closed"] is not True
        or not isinstance(value["required_fields"], list)
        or len(value["required_fields"]) != len(IDENTITY_CONFORMANCE_FIELDS)
        or set(value["required_fields"]) != IDENTITY_CONFORMANCE_FIELDS
    ):
        fail("REPO-SPEC-CONSTRUCTION-CONFORMANCE-001",
             f"{label}: conformance schema mismatch")
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

FRAMEWORK_BOUNDARY_CLOSED_ENTITY_TYPES: tuple[str, ...] = (
    "framework-source-repository",
    "distributable-template",
    "initialized-product-repository",
    "product-overview",
    "product-implementation-plan",
    "product-level-specification",
    "product-artifact",
    "framework-revision",
    "template-provenance",
    "instance-local-customization",
    "framework-update",
    "product-derivation",
)

FRAMEWORK_BOUNDARY_CLOSED_RELATIONSHIP_TYPES: tuple[str, ...] = (
    "initializes",
    "is-initialized-from",
    "derives",
    "is-derived-from",
    "depends-on",
    "traces-to",
    "customizes",
    "updates",
    "separates-into",
)


def validate_framework_boundary(value: dict[str, Any], label: str) -> str:
    exact_fields(value, FRAMEWORK_BOUNDARY_FIELDS, label)
    identity = validate_common(value, label)
    if identity != "framework-boundary":
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-002",
             f"{label}: unexpected framework-boundary identity")
    if value["entity_types"] != list(FRAMEWORK_BOUNDARY_CLOSED_ENTITY_TYPES):
        fail("REPO-SPEC-CONSTRUCTION-FRAMEWORK-BOUNDARY-001",
             f"{label}.entity_types: closed set violation")
    if value["relationship_types"] != list(FRAMEWORK_BOUNDARY_CLOSED_RELATIONSHIP_TYPES):
        fail("REPO-SPEC-CONSTRUCTION-FRAMEWORK-BOUNDARY-001",
             f"{label}.relationship_types: closed set violation")
    if not isinstance(value["relationship_rules"], dict) or not value["relationship_rules"]:
        fail("REPO-SPEC-CONSTRUCTION-FRAMEWORK-BOUNDARY-001",
             f"{label}.relationship_rules: non-empty object required")
    for rel_name, rel_rule in value["relationship_rules"].items():
        if rel_name not in FRAMEWORK_BOUNDARY_CLOSED_RELATIONSHIP_TYPES:
            fail("REPO-SPEC-CONSTRUCTION-FRAMEWORK-BOUNDARY-001",
                 f"{label}.relationship_rules.{rel_name}: unknown relationship type")
        exact_fields(rel_rule, {"source_types", "target_types", "cardinality", "acyclic"},
                     f"{label}.relationship_rules.{rel_name}")
        if not isinstance(rel_rule["source_types"], list) or not rel_rule["source_types"]:
            fail("REPO-SPEC-CONSTRUCTION-FRAMEWORK-BOUNDARY-001",
                 f"{label}.relationship_rules.{rel_name}.source_types: non-empty array required")
        if not isinstance(rel_rule["target_types"], list) or not rel_rule["target_types"]:
            fail("REPO-SPEC-CONSTRUCTION-FRAMEWORK-BOUNDARY-001",
                 f"{label}.relationship_rules.{rel_name}.target_types: non-empty array required")
        for src in rel_rule["source_types"]:
            if src not in FRAMEWORK_BOUNDARY_CLOSED_ENTITY_TYPES:
                fail("REPO-SPEC-CONSTRUCTION-FRAMEWORK-BOUNDARY-001",
                     f"{label}.relationship_rules.{rel_name}.source_types: unknown entity type '{src}'")
        for tgt in rel_rule["target_types"]:
            if tgt not in FRAMEWORK_BOUNDARY_CLOSED_ENTITY_TYPES:
                fail("REPO-SPEC-CONSTRUCTION-FRAMEWORK-BOUNDARY-001",
                     f"{label}.relationship_rules.{rel_name}.target_types: unknown entity type '{tgt}'")
        if rel_rule["acyclic"] is not True:
            fail("REPO-SPEC-CONSTRUCTION-FRAMEWORK-BOUNDARY-001",
                 f"{label}.relationship_rules.{rel_name}.acyclic: must be true")
    if isinstance(value.get("entity_constraints"), dict):
        for entity_name in value["entity_constraints"]:
            if entity_name not in FRAMEWORK_BOUNDARY_CLOSED_ENTITY_TYPES:
                fail("REPO-SPEC-CONSTRUCTION-FRAMEWORK-BOUNDARY-001",
                     f"{label}.entity_constraints.{entity_name}: unknown entity type")
    if not isinstance(value["authority_separation"], dict) or not value["authority_separation"]:
        fail("REPO-SPEC-CONSTRUCTION-FRAMEWORK-BOUNDARY-001",
             f"{label}.authority_separation: non-empty object required")
    if not isinstance(value["decision_basis"], dict) or not value["decision_basis"]:
        fail("REPO-SPEC-CONSTRUCTION-FRAMEWORK-BOUNDARY-001",
             f"{label}.decision_basis: non-empty object required")
    return identity

def validate_framework_boundary_fixtures(value: dict[str, Any], label: str) -> str:
    exact_fields(value, FRAMEWORK_BOUNDARY_FIXTURE_FIELDS, label)
    identity = validate_common(value, label)
    if identity != "framework-boundary-fixture-set-construction":
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-002",
             f"{label}: unexpected framework-boundary fixture identity")
    cases = value["cases"]
    if not isinstance(cases, list) or not cases:
        fail("REPO-SPEC-CONSTRUCTION-FRAMEWORK-BOUNDARY-003",
             f"{label}.cases: non-empty array required")
    names = []
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"name", "expected", "model_overrides", "expected_diagnostic"}:
            fail("REPO-SPEC-CONSTRUCTION-FRAMEWORK-BOUNDARY-003",
                 f"{label}.cases: closed case required")
        if not isinstance(case["name"], str) or case["name"] in names:
            fail("REPO-SPEC-CONSTRUCTION-FRAMEWORK-BOUNDARY-003",
                 f"{label}.cases: unique names required")
        if case["expected"] not in {"pass", "reject"} or not isinstance(case["model_overrides"], dict):
            fail("REPO-SPEC-CONSTRUCTION-FRAMEWORK-BOUNDARY-003",
                 f"{label}.cases: invalid case declaration")
        if case["expected"] == "pass" and case["expected_diagnostic"] is not None:
            fail("REPO-SPEC-CONSTRUCTION-FRAMEWORK-BOUNDARY-003",
                 f"{label}.cases: passing case diagnostic must be null")
        names.append(case["name"])
    return identity

def validate_framework_boundary_schema(value: dict[str, Any], label: str) -> str:
    exact_fields(value, FRAMEWORK_BOUNDARY_SCHEMA_FIELDS, label)
    identity = validate_common(value, label)
    if identity != "framework-boundary-construction-schema":
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-002",
             f"{label}: unexpected framework-boundary schema identity")
    if value["target_construction_identity"] != "framework-boundary" or value["closed"] is not True:
        fail("REPO-SPEC-CONSTRUCTION-FRAMEWORK-BOUNDARY-002",
             f"{label}: target or closed boundary mismatch")
    if not isinstance(value["required_fields"], list) or not value["required_fields"]:
        fail("REPO-SPEC-CONSTRUCTION-FRAMEWORK-BOUNDARY-002",
             f"{label}.required_fields: non-empty array required")
    if not isinstance(value["forbidden_claim_fields"], list):
        fail("REPO-SPEC-CONSTRUCTION-FRAMEWORK-BOUNDARY-002",
             f"{label}.forbidden_claim_fields: array required")
    return identity

def validate_development_artifact(value: dict[str, Any], label: str) -> str:
    exact_fields(value, DEVELOPMENT_ARTIFACT_FIELDS, label)
    identity = validate_common(value, label)
    if identity != "development-artifacts":
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-002",
             f"{label}: unexpected development-artifact identity")
    if value["artifact_roles"] != list(DEVELOPMENT_ARTIFACT_CLOSED_ROLES):
        fail("REPO-SPEC-CONSTRUCTION-DEVELOPMENT-ARTIFACT-001",
             f"{label}.artifact_roles: closed set violation")
    if not isinstance(value["role_constraints"], dict) or not value["role_constraints"]:
        fail("REPO-SPEC-CONSTRUCTION-DEVELOPMENT-ARTIFACT-001",
             f"{label}.role_constraints: non-empty object required")
    for role_name in value["role_constraints"]:
        if role_name not in DEVELOPMENT_ARTIFACT_CLOSED_ROLES:
            fail("REPO-SPEC-CONSTRUCTION-DEVELOPMENT-ARTIFACT-001",
                 f"{label}.role_constraints.{role_name}: unknown role")
        exact_fields(value["role_constraints"][role_name],
                     {"description", "authority_role", "may_become_normative",
                      "discovery", "supersession", "may_override_accepted_specifications"},
                     f"{label}.role_constraints.{role_name}")
    if not isinstance(value.get("overview_model"), dict) or not value["overview_model"].get("required_aspects"):
        fail("REPO-SPEC-CONSTRUCTION-DEVELOPMENT-ARTIFACT-001",
             f"{label}.overview_model: required aspects required")
    if not isinstance(value.get("plan_model"), dict) or not value["plan_model"].get("required_aspects"):
        fail("REPO-SPEC-CONSTRUCTION-DEVELOPMENT-ARTIFACT-001",
             f"{label}.plan_model: required aspects required")
    if not isinstance(value["role_relationships"], dict) or not value["role_relationships"]:
        fail("REPO-SPEC-CONSTRUCTION-DEVELOPMENT-ARTIFACT-001",
             f"{label}.role_relationships: non-empty object required")
    if not isinstance(value["authority_separation"], dict) or not value["authority_separation"]:
        fail("REPO-SPEC-CONSTRUCTION-DEVELOPMENT-ARTIFACT-001",
             f"{label}.authority_separation: non-empty object required")
    if not isinstance(value["decision_basis"], dict) or not value["decision_basis"]:
        fail("REPO-SPEC-CONSTRUCTION-DEVELOPMENT-ARTIFACT-001",
             f"{label}.decision_basis: non-empty object required")
    return identity


def validate_development_artifact_fixtures(value: dict[str, Any], label: str) -> str:
    exact_fields(value, DEVELOPMENT_ARTIFACT_FIXTURE_FIELDS, label)
    identity = validate_common(value, label)
    if identity != "development-artifact-fixture-set-construction":
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-002",
             f"{label}: unexpected development-artifact fixture identity")
    cases = value["cases"]
    if not isinstance(cases, list) or not cases:
        fail("REPO-SPEC-CONSTRUCTION-DEVELOPMENT-ARTIFACT-003",
             f"{label}.cases: non-empty array required")
    names = []
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"name", "expected", "model_overrides", "expected_diagnostic"}:
            fail("REPO-SPEC-CONSTRUCTION-DEVELOPMENT-ARTIFACT-003",
                 f"{label}.cases: closed case required")
        if not isinstance(case["name"], str) or case["name"] in names:
            fail("REPO-SPEC-CONSTRUCTION-DEVELOPMENT-ARTIFACT-003",
                 f"{label}.cases: unique names required")
        if case["expected"] not in {"pass", "reject"} or not isinstance(case["model_overrides"], dict):
            fail("REPO-SPEC-CONSTRUCTION-DEVELOPMENT-ARTIFACT-003",
                 f"{label}.cases: invalid case declaration")
        if case["expected"] == "pass" and case["expected_diagnostic"] is not None:
            fail("REPO-SPEC-CONSTRUCTION-DEVELOPMENT-ARTIFACT-003",
                 f"{label}.cases: passing case diagnostic must be null")
        names.append(case["name"])
    return identity


def validate_development_artifact_schema(value: dict[str, Any], label: str) -> str:
    exact_fields(value, DEVELOPMENT_ARTIFACT_SCHEMA_FIELDS, label)
    identity = validate_common(value, label)
    if identity != "development-artifact-construction-schema":
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-002",
             f"{label}: unexpected development-artifact schema identity")
    if value["target_construction_identity"] != "development-artifacts" or value["closed"] is not True:
        fail("REPO-SPEC-CONSTRUCTION-DEVELOPMENT-ARTIFACT-002",
             f"{label}: target or closed boundary mismatch")
    if not isinstance(value["required_fields"], list) or not value["required_fields"]:
        fail("REPO-SPEC-CONSTRUCTION-DEVELOPMENT-ARTIFACT-002",
             f"{label}.required_fields: non-empty array required")
    if not isinstance(value["forbidden_claim_fields"], list):
        fail("REPO-SPEC-CONSTRUCTION-DEVELOPMENT-ARTIFACT-002",
             f"{label}.forbidden_claim_fields: array required")
    return identity


def validate_functional_area(value: dict[str, Any], label: str) -> str:
    exact_fields(value, FUNCTIONAL_AREA_FIELDS, label)
    identity = validate_common(value, label)
    if identity != "functional-areas":
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-002",
             f"{label}: unexpected functional-area identity")
    if value["functional_areas"] != list(FUNCTIONAL_AREA_CLOSED_AREAS):
        fail("REPO-SPEC-CONSTRUCTION-FUNCTIONAL-AREA-001",
             f"{label}.functional_areas: closed set violation")
    if not isinstance(value["area_semantics"], dict) or not value["area_semantics"]:
        fail("REPO-SPEC-CONSTRUCTION-FUNCTIONAL-AREA-001",
             f"{label}.area_semantics: non-empty object required")
    for area_name in value["area_semantics"]:
        if area_name not in FUNCTIONAL_AREA_CLOSED_AREAS:
            fail("REPO-SPEC-CONSTRUCTION-FUNCTIONAL-AREA-001",
                 f"{label}.area_semantics.{area_name}: unknown area")
        exact_fields(value["area_semantics"][area_name],
                     {"description", "kind", "authority_classification",
                      "lifecycle_classification", "ownership_role", "containment",
                      "dependency", "path_significance", "ignored_content",
                      "required", "product_profile_extensible"},
                     f"{label}.area_semantics.{area_name}")
    if not isinstance(value["kernel_classifications"], dict) or not value["kernel_classifications"]:
        fail("REPO-SPEC-CONSTRUCTION-FUNCTIONAL-AREA-001",
             f"{label}.kernel_classifications: non-empty object required")
    if not isinstance(value["extension_rules"], dict) or not value["extension_rules"]:
        fail("REPO-SPEC-CONSTRUCTION-FUNCTIONAL-AREA-001",
             f"{label}.extension_rules: non-empty object required")
    if not isinstance(value["placement_rules"], dict) or not value["placement_rules"]:
        fail("REPO-SPEC-CONSTRUCTION-FUNCTIONAL-AREA-001",
             f"{label}.placement_rules: non-empty object required")
    if not isinstance(value["authority_separation"], dict) or not value["authority_separation"]:
        fail("REPO-SPEC-CONSTRUCTION-FUNCTIONAL-AREA-001",
             f"{label}.authority_separation: non-empty object required")
    if not isinstance(value["decision_basis"], dict) or not value["decision_basis"]:
        fail("REPO-SPEC-CONSTRUCTION-FUNCTIONAL-AREA-001",
             f"{label}.decision_basis: non-empty object required")
    return identity


def validate_functional_area_fixtures(value: dict[str, Any], label: str) -> str:
    exact_fields(value, FUNCTIONAL_AREA_FIXTURE_FIELDS, label)
    identity = validate_common(value, label)
    if identity != "functional-area-fixture-set-construction":
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-002",
             f"{label}: unexpected functional-area fixture identity")
    cases = value["cases"]
    if not isinstance(cases, list) or not cases:
        fail("REPO-SPEC-CONSTRUCTION-FUNCTIONAL-AREA-003",
             f"{label}.cases: non-empty array required")
    names = []
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"name", "expected", "model_overrides", "expected_diagnostic"}:
            fail("REPO-SPEC-CONSTRUCTION-FUNCTIONAL-AREA-003",
                 f"{label}.cases: closed case required")
        if not isinstance(case["name"], str) or case["name"] in names:
            fail("REPO-SPEC-CONSTRUCTION-FUNCTIONAL-AREA-003",
                 f"{label}.cases: unique names required")
        if case["expected"] not in {"pass", "reject"} or not isinstance(case["model_overrides"], dict):
            fail("REPO-SPEC-CONSTRUCTION-FUNCTIONAL-AREA-003",
                 f"{label}.cases: invalid case declaration")
        if case["expected"] == "pass" and case["expected_diagnostic"] is not None:
            fail("REPO-SPEC-CONSTRUCTION-FUNCTIONAL-AREA-003",
                 f"{label}.cases: passing case diagnostic must be null")
        names.append(case["name"])
    return identity


def validate_functional_area_schema(value: dict[str, Any], label: str) -> str:
    exact_fields(value, FUNCTIONAL_AREA_SCHEMA_FIELDS, label)
    identity = validate_common(value, label)
    if identity != "functional-area-construction-schema":
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-002",
             f"{label}: unexpected functional-area schema identity")
    if value["target_construction_identity"] != "functional-areas" or value["closed"] is not True:
        fail("REPO-SPEC-CONSTRUCTION-FUNCTIONAL-AREA-002",
             f"{label}: target or closed boundary mismatch")
    if not isinstance(value["required_fields"], list) or not value["required_fields"]:
        fail("REPO-SPEC-CONSTRUCTION-FUNCTIONAL-AREA-002",
             f"{label}.required_fields: non-empty array required")
    if not isinstance(value["forbidden_claim_fields"], list):
        fail("REPO-SPEC-CONSTRUCTION-FUNCTIONAL-AREA-002",
             f"{label}.forbidden_claim_fields: array required")
    return identity


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
        if relative in {
            VALIDATION_LIBRARY_PATH,
            CONFORMANCE_BOUNDARY_PATH,
            IDENTITY_CONFORMANCE_PATH,
            CONFORMANCE_SCHEMA_PATH,
            CONFORMANCE_VECTOR_PATH,
        }:
            continue
        value = strict_json(root / relative)
        exact_fields(value, PLACEHOLDER_FIELDS, relative)
        identity = validate_common(value, relative)
        if identity in identities:
            fail("REPO-SPEC-CONSTRUCTION-IDENTITY-003",
                 f"{relative}: duplicate construction identity")
        identities.add(identity)

    specification_artifacts = strict_json(root / "authoritative/specification-system/SPECIFICATION-ARTIFACTS.json")
    specification_artifacts_candidate_identity = validate_common(
        specification_artifacts, "authoritative/specification-system/SPECIFICATION-ARTIFACTS.json"
    )
    repository_model_candidate_identity = validate_common(
        strict_json(root / "authoritative/repository-model/REPOSITORY-MODEL.json"),
        "authoritative/repository-model/REPOSITORY-MODEL.json",
    )
    if specification_artifacts_candidate_identity in identities or specification_artifacts_candidate_identity == repository_model_candidate_identity:
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-003", "authoritative/specification-system/SPECIFICATION-ARTIFACTS.json: duplicate construction identity")
    specification_artifacts_identity = validate_specification_artifacts(
        specification_artifacts, "authoritative/specification-system/SPECIFICATION-ARTIFACTS.json"
    )
    identities.add(specification_artifacts_identity)

    specification_artifact_schema = strict_json(
        root / "authoritative/schemas/specification-system/SPECIFICATION-ARTIFACT-CLASS-CONSTRUCTION-SCHEMA.json"
    )
    specification_artifact_schema_candidate_identity = validate_common(
        specification_artifact_schema,
        "authoritative/schemas/specification-system/SPECIFICATION-ARTIFACT-CLASS-CONSTRUCTION-SCHEMA.json",
    )
    if specification_artifact_schema_candidate_identity in identities:
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-003", "authoritative/schemas/specification-system/SPECIFICATION-ARTIFACT-CLASS-CONSTRUCTION-SCHEMA.json: duplicate construction identity")
    specification_artifact_schema_identity = validate_specification_artifact_schema(
        specification_artifact_schema,
        "authoritative/schemas/specification-system/SPECIFICATION-ARTIFACT-CLASS-CONSTRUCTION-SCHEMA.json",
    )
    identities.add(specification_artifact_schema_identity)

    specification_artifact_fixtures = strict_json(
        root / "validation/fixtures/specification-system/SPECIFICATION-ARTIFACT-FIXTURES.json"
    )
    specification_artifact_fixtures_identity = validate_specification_artifact_fixtures(
        specification_artifact_fixtures,
        "validation/fixtures/specification-system/SPECIFICATION-ARTIFACT-FIXTURES.json",
    )
    if specification_artifact_fixtures_identity in identities:
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-003", "validation/fixtures/specification-system/SPECIFICATION-ARTIFACT-FIXTURES.json: duplicate construction identity")
    identities.add(specification_artifact_fixtures_identity)

    repository_vocabulary = strict_json(root / "authoritative/repository-model/REPOSITORY-MODEL.json")
    repository_vocabulary_identity = validate_repository_vocabulary(
        repository_vocabulary, "authoritative/repository-model/REPOSITORY-MODEL.json", root
    )
    if repository_vocabulary_identity in identities:
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-003",
             "authoritative/repository-model/REPOSITORY-MODEL.json: duplicate construction identity")
    identities.add(repository_vocabulary_identity)

    repository_vocabulary_schema = strict_json(
        root / "authoritative/schemas/repository-model/REPOSITORY-VOCABULARY-CONSTRUCTION-SCHEMA.json"
    )
    repository_vocabulary_schema_identity = validate_repository_vocabulary_schema(
        repository_vocabulary_schema,
        "authoritative/schemas/repository-model/REPOSITORY-VOCABULARY-CONSTRUCTION-SCHEMA.json",
    )
    if repository_vocabulary_schema_identity in identities:
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-003",
             "authoritative/schemas/repository-model/REPOSITORY-VOCABULARY-CONSTRUCTION-SCHEMA.json: duplicate construction identity")
    identities.add(repository_vocabulary_schema_identity)

    repository_vocabulary_fixtures = strict_json(
        root / "validation/fixtures/repository-model/REPOSITORY-VOCABULARY-FIXTURES.json"
    )
    repository_vocabulary_fixtures_identity = validate_repository_vocabulary_fixtures(
        repository_vocabulary_fixtures,
        "validation/fixtures/repository-model/REPOSITORY-VOCABULARY-FIXTURES.json",
    )
    if repository_vocabulary_fixtures_identity in identities:
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-003",
             "validation/fixtures/repository-model/REPOSITORY-VOCABULARY-FIXTURES.json: duplicate construction identity")
    identities.add(repository_vocabulary_fixtures_identity)

    conformance_boundary = strict_json(root / CONFORMANCE_BOUNDARY_PATH)
    conformance_boundary_identity = validate_conformance_boundary(
        conformance_boundary, CONFORMANCE_BOUNDARY_PATH
    )
    if conformance_boundary_identity in identities:
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-003",
             f"{CONFORMANCE_BOUNDARY_PATH}: duplicate construction identity")
    identities.add(conformance_boundary_identity)

    identity_conformance = strict_json(root / IDENTITY_CONFORMANCE_PATH)
    identity_conformance_identity = validate_identity_conformance(
        identity_conformance, IDENTITY_CONFORMANCE_PATH
    )
    if identity_conformance_identity in identities:
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-003",
             f"{IDENTITY_CONFORMANCE_PATH}: duplicate construction identity")
    identities.add(identity_conformance_identity)

    conformance_schema = strict_json(root / CONFORMANCE_SCHEMA_PATH)
    conformance_schema_identity = validate_identity_conformance_schema(
        conformance_schema, CONFORMANCE_SCHEMA_PATH
    )
    if conformance_schema_identity in identities:
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-003",
             f"{CONFORMANCE_SCHEMA_PATH}: duplicate construction identity")
    identities.add(conformance_schema_identity)

    validation_library = strict_json(root / VALIDATION_LIBRARY_PATH)
    validation_library_identity = validate_validation_library(
        validation_library, VALIDATION_LIBRARY_PATH
    )
    if validation_library_identity in identities:
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-003",
             f"{VALIDATION_LIBRARY_PATH}: duplicate construction identity")

    framework_boundary = strict_json(root / FRAMEWORK_BOUNDARY_PATH)
    framework_boundary_identity = validate_framework_boundary(
        framework_boundary, FRAMEWORK_BOUNDARY_PATH
    )
    if framework_boundary_identity in identities:
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-003",
             f"{FRAMEWORK_BOUNDARY_PATH}: duplicate construction identity")
    identities.add(framework_boundary_identity)

    framework_boundary_schema = strict_json(root / FRAMEWORK_BOUNDARY_SCHEMA_PATH)
    framework_boundary_schema_identity = validate_framework_boundary_schema(
        framework_boundary_schema, FRAMEWORK_BOUNDARY_SCHEMA_PATH
    )
    if framework_boundary_schema_identity in identities:
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-003",
             f"{FRAMEWORK_BOUNDARY_SCHEMA_PATH}: duplicate construction identity")

    framework_boundary_fixtures = strict_json(root / FRAMEWORK_BOUNDARY_FIXTURE_PATH)
    framework_boundary_fixtures_identity = validate_framework_boundary_fixtures(
        framework_boundary_fixtures, FRAMEWORK_BOUNDARY_FIXTURE_PATH
    )
    if framework_boundary_fixtures_identity in identities:
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-003",
             f"{FRAMEWORK_BOUNDARY_FIXTURE_PATH}: duplicate construction identity")
    identities.add(framework_boundary_fixtures_identity)

    development_artifacts = strict_json(root / DEVELOPMENT_ARTIFACT_PATH)
    development_artifacts_identity = validate_development_artifact(
        development_artifacts, DEVELOPMENT_ARTIFACT_PATH
    )
    if development_artifacts_identity in identities:
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-003",
             f"{DEVELOPMENT_ARTIFACT_PATH}: duplicate construction identity")
    identities.add(development_artifacts_identity)

    development_artifact_schema = strict_json(root / DEVELOPMENT_ARTIFACT_SCHEMA_PATH)
    development_artifact_schema_identity = validate_development_artifact_schema(
        development_artifact_schema, DEVELOPMENT_ARTIFACT_SCHEMA_PATH
    )
    if development_artifact_schema_identity in identities:
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-003",
             f"{DEVELOPMENT_ARTIFACT_SCHEMA_PATH}: duplicate construction identity")
    identities.add(development_artifact_schema_identity)

    development_artifact_fixtures = strict_json(root / DEVELOPMENT_ARTIFACT_FIXTURE_PATH)
    development_artifact_fixtures_identity = validate_development_artifact_fixtures(
        development_artifact_fixtures, DEVELOPMENT_ARTIFACT_FIXTURE_PATH
    )
    if development_artifact_fixtures_identity in identities:
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-003",
             f"{DEVELOPMENT_ARTIFACT_FIXTURE_PATH}: duplicate construction identity")
    identities.add(development_artifact_fixtures_identity)

    functional_area = strict_json(root / FUNCTIONAL_AREA_PATH)
    functional_area_identity = validate_functional_area(
        functional_area, FUNCTIONAL_AREA_PATH
    )
    if functional_area_identity in identities:
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-003",
             f"{FUNCTIONAL_AREA_PATH}: duplicate construction identity")
    identities.add(functional_area_identity)

    functional_area_schema = strict_json(root / FUNCTIONAL_AREA_SCHEMA_PATH)
    functional_area_schema_identity = validate_functional_area_schema(
        functional_area_schema, FUNCTIONAL_AREA_SCHEMA_PATH
    )
    if functional_area_schema_identity in identities:
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-003",
             f"{FUNCTIONAL_AREA_SCHEMA_PATH}: duplicate construction identity")
    identities.add(functional_area_schema_identity)

    functional_area_fixtures = strict_json(root / FUNCTIONAL_AREA_FIXTURE_PATH)
    functional_area_fixtures_identity = validate_functional_area_fixtures(
        functional_area_fixtures, FUNCTIONAL_AREA_FIXTURE_PATH
    )
    if functional_area_fixtures_identity in identities:
        fail("REPO-SPEC-CONSTRUCTION-IDENTITY-003",
             f"{FUNCTIONAL_AREA_FIXTURE_PATH}: duplicate construction identity")
    identities.add(functional_area_fixtures_identity)

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
