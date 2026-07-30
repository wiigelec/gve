#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

CONSTRUCTION_ROOT = Path(__file__).resolve().parents[2]
if str(CONSTRUCTION_ROOT) not in sys.path:
    sys.path.insert(0, str(CONSTRUCTION_ROOT))

MODEL_PATH = "authoritative/specification-system/SPECIFICATION-IDENTITIES.json"
SCHEMA_PATH = "authoritative/schemas/specification-system/SPECIFICATION-IDENTITIES-CONSTRUCTION-SCHEMA.json"
FIXTURE_PATH = "validation/fixtures/specification-system/SPECIFICATION-IDENTITIES-FIXTURES.json"

EXPECTED_MODEL = {
    "construction_identity": "specification-identities-construction",
    "construction_status": "under-construction",
    "responsibility": "Define candidate identity families and manifest/revision rules for repository specification documents, manifests, schemas, projections, conformance artifacts, validation artifacts, and sealed specification sets without defining final authority or acceptance behavior.",
    "normative": False,
    "decision_basis": {
        "portable_behavior": [
            "specification-document-identity",
            "specification-set-revision-identity",
            "direct-member-manifest-closure",
            "explicit-self-reference-handling",
            "deterministic-binding-order",
            "duplicate-member-rejection",
            "stale-member-rejection",
            "incomplete-membership-rejection",
        ],
        "repository_generic_decisions": [
            "candidate-family-inventory",
            "schema-projection-conformance-validator-binding",
            "governing-revision-attribution",
            "manifest-and-revision-distinction",
            "template-and-product-manifest-separation",
            "own-identity-omission-or-canonical-reference",
        ],
    },
    "candidate_families": [
        "specification-document",
        "specification-set-revision",
        "manifest",
        "schema",
        "projection",
        "conformance-artifact",
        "validation-artifact",
        "sealed-specification-set",
    ],
    "family_bindings": {
        "specification-document": {
            "kind": "document",
            "membership": "direct",
            "self_reference": "omit-own-identity",
            "binding_targets": ["canonicalization_reference", "digest_declaration"],
        },
        "specification-set-revision": {
            "kind": "aggregate",
            "membership": "direct",
            "self_reference": "canonical-reference",
            "binding_targets": ["manifest_model", "revision_model"],
        },
        "manifest": {
            "kind": "aggregate",
            "membership": "direct",
            "self_reference": "omit-own-identity",
            "binding_targets": ["binding_model"],
        },
        "schema": {
            "kind": "document",
            "membership": "direct",
            "self_reference": "omit-own-identity",
            "binding_targets": ["manifest_binding"],
        },
        "projection": {
            "kind": "document",
            "membership": "direct",
            "self_reference": "omit-own-identity",
            "binding_targets": ["freshness_binding"],
        },
        "conformance-artifact": {
            "kind": "document",
            "membership": "direct",
            "self_reference": "omit-own-identity",
            "binding_targets": ["revision_binding", "validator_binding"],
        },
        "validation-artifact": {
            "kind": "document",
            "membership": "direct",
            "self_reference": "omit-own-identity",
            "binding_targets": ["validator_binding", "governing_revision_binding"],
        },
        "sealed-specification-set": {
            "kind": "aggregate",
            "membership": "derived",
            "self_reference": "external-seal-envelope",
            "binding_targets": ["governing_revision_binding", "parent_manifest_binding"],
        },
    },
    "manifest_model": {
        "self_participation": False,
        "own_identity_handling": "omit-own-identity",
        "ordering": "ascending-by-stable-specification-identity",
        "duplicate_policy": "reject",
        "stale_member_policy": "reject",
        "incomplete_membership_policy": "reject",
    },
    "revision_model": {
        "derivation": "direct-member-aggregate-revision",
        "member_scope": "direct",
        "governing_revision_binding": "required",
        "self_reference_handling": "explicit",
        "revision_attribution": "retained",
        "stale_revision_policy": "reject",
        "incomplete_revision_policy": "reject",
    },
    "binding_model": {
        "schema_binding": "required",
        "projection_binding": "required",
        "conformance_binding": "required",
        "validator_binding": "required",
    },
    "manifest_separation": {
        "template_manifest": "separate",
        "product_manifest": "separate",
    },
    "expected_relationships": [
        "specification-artifact-class-construction",
        "specification-artifact-class-construction-schema",
        "identity-model-construction",
        "repository-specification-construction-set",
    ],
    "unresolved_questions": [
        "Final accepted specification identity string syntax is not defined.",
        "Final accepted revision identity syntax and sealing model remain separately governed.",
    ],
}

EXPECTED_SCHEMA = {
    "construction_identity": "specification-identities-construction-schema",
    "construction_status": "under-construction",
    "responsibility": "Constrain the exact construction-only shape of the repository specification identity profile without claiming final normative schema authority.",
    "normative": False,
    "target_construction_identity": "specification-identities-construction",
    "required_fields": [
        "construction_identity",
        "construction_status",
        "responsibility",
        "normative",
        "decision_basis",
        "candidate_families",
        "family_bindings",
        "manifest_model",
        "revision_model",
        "binding_model",
        "manifest_separation",
        "expected_relationships",
        "unresolved_questions",
    ],
    "closed": True,
    "field_constraints": {
        "exact_policy": EXPECTED_MODEL,
        "unknown_fields": "reject",
        "missing_fields": "reject",
    },
    "forbidden_claim_fields": [
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
    ],
    "expected_relationships": [
        "specification-artifact-class-construction",
        "specification-artifact-class-construction-schema",
        "identity-model-construction",
        "repository-specification-construction-set",
    ],
    "unresolved_questions": [
        "Final normative specification identity profile is not defined.",
        "Final accepted revision and sealing authority remain separately governed.",
    ],
}

EXPECTED_FIXTURES = {
    "construction_identity": "specification-identities-fixture-set-construction",
    "construction_status": "under-construction",
    "responsibility": "Provide repository-neutral positive and negative validator inputs for specification identity profile construction without defining accepted manifest authority.",
    "normative": False,
    "cases": [
        {
            "name": "valid-specification-identity-profile",
            "expected": "pass",
            "model_overrides": {},
            "expected_diagnostic": None,
        },
        {
            "name": "duplicate-member-rejection",
            "expected": "reject",
            "model_overrides": {
                "manifest_model.duplicate_policy": "allow",
            },
            "expected_diagnostic": "REPO-SPEC-CONSTRUCTION-SPECIFICATION-IDENTITY-001",
        },
    ],
    "expected_relationships": [
        "specification-identities-construction",
        "specification-identities-construction-schema",
        "repository-specification-construction-set",
    ],
    "unresolved_questions": [
        "Final accepted specification identity revision semantics are not defined.",
        "Final accepted manifest and sealing semantics remain separately governed.",
    ],
}


class ValidationFailure(Exception):
    pass


def fail(code: str, detail: str) -> None:
    raise ValidationFailure(f"{code}: {detail}")


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
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
    except UnicodeDecodeError:
        fail("REPO-SPEC-SPECIFICATION-IDENTITY-JSON-001", f"{path}: invalid UTF-8")
    except OSError as exc:
        fail("REPO-SPEC-SPECIFICATION-IDENTITY-PATH-001", f"{path}: {exc}")
    except (json.JSONDecodeError, ValueError) as exc:
        fail("REPO-SPEC-SPECIFICATION-IDENTITY-JSON-001", f"{path}: {exc}")
    if not isinstance(value, dict):
        fail("REPO-SPEC-SPECIFICATION-IDENTITY-JSON-002", f"{path}: top level must be an object")
    return value


def exact_fields(value: dict[str, Any], fields: set[str], label: str) -> None:
    unknown = sorted(set(value) - fields)
    missing = sorted(fields - set(value))
    if unknown:
        fail("REPO-SPEC-SPECIFICATION-IDENTITY-FIELD-001", f"{label}: unknown fields: {', '.join(unknown)}")
    if missing:
        fail("REPO-SPEC-SPECIFICATION-IDENTITY-FIELD-002", f"{label}: missing fields: {', '.join(missing)}")


def string_list(value: Any, label: str, *, nonempty: bool = True) -> list[str]:
    if not isinstance(value, list) or (nonempty and not value):
        fail("REPO-SPEC-SPECIFICATION-IDENTITY-TYPE-001", f"{label}: must be an array with required entries")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        fail("REPO-SPEC-SPECIFICATION-IDENTITY-TYPE-001", f"{label}: entries must be non-empty strings")
    return list(value)


def validate_common(value: dict[str, Any], label: str) -> str:
    identity = value.get("construction_identity")
    if not isinstance(identity, str) or not identity:
        fail("REPO-SPEC-SPECIFICATION-IDENTITY-IDENTITY-001", f"{label}.construction_identity: invalid construction identity")
    if value.get("construction_status") != "under-construction":
        fail("REPO-SPEC-SPECIFICATION-IDENTITY-STATUS-001", f"{label}: status must be under-construction")
    if value.get("normative") is not False:
        fail("REPO-SPEC-SPECIFICATION-IDENTITY-STATUS-002", f"{label}: normative must be false")
    if not isinstance(value.get("responsibility"), str) or not value["responsibility"].strip():
        fail("REPO-SPEC-SPECIFICATION-IDENTITY-TYPE-001", f"{label}.responsibility must be non-empty")
    string_list(value["expected_relationships"], f"{label}.expected_relationships")
    string_list(value["unresolved_questions"], f"{label}.unresolved_questions")
    return identity


def validate_exact_policy(value: dict[str, Any], expected: dict[str, Any], fields: set[str], label: str, code: str) -> str:
    exact_fields(value, fields, label)
    identity = validate_common(value, label)
    if value != expected:
        fail(code, f"{label}: construction claims do not match policy")
    return identity


def validate_model(value: dict[str, Any], label: str) -> str:
    identity = validate_exact_policy(
        value,
        EXPECTED_MODEL,
        set(EXPECTED_SCHEMA["required_fields"]),
        label,
        "REPO-SPEC-SPECIFICATION-IDENTITY-001",
    )
    candidate_families = value["candidate_families"]
    if candidate_families != [
        "specification-document",
        "specification-set-revision",
        "manifest",
        "schema",
        "projection",
        "conformance-artifact",
        "validation-artifact",
        "sealed-specification-set",
    ]:
        fail("REPO-SPEC-SPECIFICATION-IDENTITY-001", f"{label}.candidate_families: unexpected family inventory")
    return identity


def validate_schema(value: dict[str, Any], label: str) -> str:
    exact_fields(
        value,
        {
            "construction_identity",
            "construction_status",
            "responsibility",
            "normative",
            "target_construction_identity",
            "required_fields",
            "closed",
            "field_constraints",
            "forbidden_claim_fields",
            "expected_relationships",
            "unresolved_questions",
        },
        label,
    )
    identity = validate_common(value, label)
    if value != EXPECTED_SCHEMA:
        fail("REPO-SPEC-SPECIFICATION-IDENTITY-002", f"{label}: construction claims do not match policy")
    return identity


def validate_fixtures(value: dict[str, Any], label: str) -> str:
    exact_fields(value, {"construction_identity", "construction_status", "responsibility", "normative", "cases", "expected_relationships", "unresolved_questions"}, label)
    identity = validate_common(value, label)
    if value != EXPECTED_FIXTURES:
        fail("REPO-SPEC-SPECIFICATION-IDENTITY-003", f"{label}: construction fixtures do not match policy")
    cases = value["cases"]
    if not isinstance(cases, list) or not cases:
        fail("REPO-SPEC-SPECIFICATION-IDENTITY-003", f"{label}.cases: non-empty array required")
    names = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"name", "expected", "model_overrides", "expected_diagnostic"}:
            fail("REPO-SPEC-SPECIFICATION-IDENTITY-003", f"{label}.cases: closed case required")
        if not isinstance(case["name"], str) or not case["name"] or case["name"] in names:
            fail("REPO-SPEC-SPECIFICATION-IDENTITY-003", f"{label}.cases: unique names required")
        if case["expected"] not in {"pass", "reject"} or not isinstance(case["model_overrides"], dict):
            fail("REPO-SPEC-SPECIFICATION-IDENTITY-003", f"{label}.cases: invalid case declaration")
        if case["expected"] == "pass" and case["expected_diagnostic"] is not None:
            fail("REPO-SPEC-SPECIFICATION-IDENTITY-003", f"{label}.cases: passing case diagnostic must be null")
        names.add(case["name"])
    return identity


def validate(root: Path) -> tuple[str, str, str]:
    model = strict_json(root / MODEL_PATH)
    model_identity = validate_model(model, MODEL_PATH)

    schema = strict_json(root / SCHEMA_PATH)
    schema_identity = validate_schema(schema, SCHEMA_PATH)

    fixtures = strict_json(root / FIXTURE_PATH)
    fixtures_identity = validate_fixtures(fixtures, FIXTURE_PATH)
    return model_identity, schema_identity, fixtures_identity


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(CONSTRUCTION_ROOT))
    args = parser.parse_args(argv)
    try:
        validate(Path(args.root))
    except ValidationFailure as exc:
        print(f"specification identities validation failed: {exc}", file=sys.stderr)
        return 1
    print("specification identities validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
