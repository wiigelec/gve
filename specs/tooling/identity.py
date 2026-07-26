"""Validation helpers for the GVE unified identity framework core."""

from __future__ import annotations

import re
from typing import Any, Mapping


class IdentityFrameworkError(ValueError):
    """Raised when the identity framework is incomplete or inconsistent."""


_REQUIRED_FAIL_CLOSED = {
    "missing-family",
    "unknown-family",
    "missing-domain-prefix",
    "cross-domain-substitution",
    "missing-canonicalization-version",
    "unsupported-canonicalization-version",
    "missing-digest-algorithm",
    "unsupported-digest-algorithm",
    "ambiguous-reference-semantics",
    "implicit-embedded-identity-handling",
    "incomplete-aggregate-membership",
    "self-referential-identity",
    "circular-aggregate-identity",
    "mismatched-identity-family",
    "unverifiable-identity",
}

_REQUIRED_INVARIANTS = {
    "one_semantic_domain_per_family",
    "one_canonical_preimage_per_family",
    "one_domain_prefix_per_family",
    "domain_prefixes_unique",
    "canonicalization_version_explicit",
    "digest_algorithm_explicit",
    "future_families_must_derive_from_framework",
    "cross_domain_substitution_prohibited",
    "circular_construction_prohibited",
}


def _fail(message: str) -> None:
    raise IdentityFrameworkError(message)


def _unique_ids(records: list[Mapping[str, Any]], label: str) -> set[str]:
    identities: set[str] = set()
    for record in records:
        identity = record.get("id")
        if not isinstance(identity, str) or not identity:
            _fail(f"{label} requires a non-empty id")
        if identity in identities:
            _fail(f"duplicate {label} id {identity}")
        identities.add(identity)
    return identities


def validate_identity_framework(framework: Mapping[str, Any]) -> None:
    """Validate the common identity framework independently of family registration."""
    authority = framework["authority"]
    if authority["governing_specification"] != "GVE-LEVEL-2-DOCUMENT-AUTHORITY":
        _fail("identity framework has incorrect governing specification")
    if authority["status"] != "normative-framework-core":
        _fail("identity framework status is not normative-framework-core")

    representation = framework["representation"]
    if representation["syntax"] != "<family>-<algorithm>:<digest>":
        _fail("identity representation syntax is not canonical")
    try:
        family_pattern = re.compile(representation["family_pattern"])
    except re.error as exc:
        _fail(f"identity family pattern is invalid: {exc}")
    for valid in ("gve-effect", "gve-spec-document", "gve-authoritative-result"):
        if family_pattern.fullmatch(valid) is None:
            _fail(f"identity family pattern rejects {valid}")
    for invalid in ("sha256", "GVE-effect", "gve_effect"):
        if family_pattern.fullmatch(invalid) is not None:
            _fail(f"identity family pattern admits {invalid}")

    canonicalization_ids = _unique_ids(
        framework["canonicalization_versions"], "canonicalization version"
    )
    if "gve-canonical-json-v1" not in canonicalization_ids:
        _fail("gve-canonical-json-v1 is required")

    algorithm_ids = _unique_ids(framework["digest_algorithms"], "digest algorithm")
    if "sha256" not in algorithm_ids:
        _fail("sha256 is required")
    sha256 = next(
        algorithm
        for algorithm in framework["digest_algorithms"]
        if algorithm["id"] == "sha256"
    )
    if (
        sha256["digest_bits"] != 256
        or sha256["encoded_length"] != 64
        or sha256["encoding"] != "lowercase-hex"
    ):
        _fail("sha256 declaration is inconsistent")

    preimage = framework["canonical_preimage"]
    if preimage["construction"] != "domain-prefix-bytes || canonical-value-bytes":
        _fail("canonical preimage construction is not explicit")
    for flag in (
        "canonicalization_version_required",
        "digest_algorithm_required",
        "family_definition_required",
    ):
        if preimage[flag] is not True:
            _fail(f"canonical preimage must require {flag}")

    if set(framework["fail_closed_conditions"]) != _REQUIRED_FAIL_CLOSED:
        _fail("fail-closed condition inventory is incomplete")

    invariants = framework["framework_invariants"]
    if set(invariants) != _REQUIRED_INVARIANTS:
        _fail("framework invariant inventory is incomplete")
    if any(value is not True for value in invariants.values()):
        _fail("every framework invariant must be enabled")

    embedded = framework["embedded_identity_rules"]
    if embedded["per_family_declaration_required"] is not True:
        _fail("embedded identity handling must be declared per family")
    if embedded["implicit_handling_prohibited"] is not True:
        _fail("implicit embedded identity handling must be prohibited")

    references = framework["reference_semantics"]
    if references["per_family_declaration_required"] is not True:
        _fail("reference semantics must be declared per family")
    if references["ambiguous_reference_prohibited"] is not True:
        _fail("ambiguous reference semantics must be prohibited")

    aggregates = framework["aggregate_semantics"]
    required = {
        "membership",
        "ordering_significance",
        "duplicate_policy",
        "closure_boundary",
        "member_reference_mode",
        "empty_aggregate_rule",
        "cycle_policy",
    }
    if set(aggregates["required_for_aggregate_kinds"]) != required:
        _fail("aggregate semantic inventory is incomplete")
    if aggregates["cycle_policy"] != "reject":
        _fail("aggregate cycles must be rejected")
    if aggregates["incomplete_membership_policy"] != "reject":
        _fail("incomplete aggregate membership must be rejected")
    if framework["authority"]["integration_state"] in {
        "family-registry-defined",
        "repository-integrated",
    }:
        validate_identity_family_registry(framework)


_REQUIRED_FAMILIES = {
    "gve-spec-document",
    "gve-spec-revision",
    "gve-governance-composition",
    "gve-effect",
    "gve-plan",
    "gve-contract",
    "gve-production",
    "gve-evidence",
    "gve-execution-record",
    "gve-authoritative-result",
    "gve-finalization",
}


def validate_identity_family_registry(framework: Mapping[str, Any]) -> None:
    """Validate the closed current GVE identity-family registry."""
    families = framework.get("identity_families")
    if not isinstance(families, list) or not families:
        _fail("identity family registry is required")

    family_ids = _unique_ids(families, "identity family")
    if family_ids != _REQUIRED_FAMILIES:
        _fail("identity family registry is incomplete")

    canonicalization_ids = {
        record["id"] for record in framework["canonicalization_versions"]
    }
    algorithm_ids = {record["id"] for record in framework["digest_algorithms"]}
    prefixes: set[str] = set()
    adjacency: dict[str, list[str]] = {}

    for family in families:
        family_id = family["id"]
        domain = family["semantic_domain"]
        if not isinstance(domain, str) or not domain.strip():
            _fail(f"identity family {family_id} requires one semantic domain")
        prefix = family["domain_separation_prefix"]
        if prefix in prefixes:
            _fail(f"duplicate domain-separation prefix {prefix!r}")
        prefixes.add(prefix)
        if not prefix.endswith("\x00"):
            _fail(f"identity family {family_id} prefix must end in NUL")
        if family["canonicalization_version"] not in canonicalization_ids:
            _fail(f"identity family {family_id} uses unknown canonicalization version")
        if family["digest_algorithm"] not in algorithm_ids:
            _fail(f"identity family {family_id} uses unknown digest algorithm")
        expected_prefix = family_id.replace("gve-", "gve/", 1) + "/v1\x00"
        if prefix != expected_prefix:
            _fail(f"identity family {family_id} prefix does not match its domain")
        if not isinstance(family["canonical_value"], str) or not family[
            "canonical_value"
        ].strip():
            _fail(f"identity family {family_id} requires an exact canonical value rule")

        aggregate = family["aggregate"]
        if family["object_kind"] == "object":
            if aggregate is not None:
                _fail(f"object identity family {family_id} must not define aggregate rules")
            adjacency[family_id] = []
            continue
        if not isinstance(aggregate, Mapping):
            _fail(f"aggregate identity family {family_id} requires aggregate rules")
        members = aggregate["member_family_ids"]
        if not members:
            _fail(f"aggregate identity family {family_id} requires members")
        for member_id in members:
            if member_id not in family_ids:
                _fail(f"aggregate identity family {family_id} references unknown member")
            if member_id == family_id:
                _fail(f"identity family {family_id} is self-referential")
        adjacency[family_id] = list(members)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(family_id: str) -> None:
        if family_id in visiting:
            _fail("identity family registry contains a circular aggregate")
        if family_id in visited:
            return
        visiting.add(family_id)
        for member_id in adjacency.get(family_id, []):
            visit(member_id)
        visiting.remove(family_id)
        visited.add(family_id)

    for family_id in family_ids:
        visit(family_id)


import hashlib
import json
from collections.abc import Sequence


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize one value according to gve-canonical-json-v1."""
    def normalize(item: Any) -> Any:
        if item is None or isinstance(item, bool):
            return item
        if isinstance(item, int) and not isinstance(item, bool):
            if item < -(2**63) or item > 2**63 - 1:
                _fail("integer is outside the signed 64-bit canonical range")
            return item
        if isinstance(item, float):
            _fail("floating-point values are not canonicalizable")
        if isinstance(item, str):
            for character in item:
                codepoint = ord(character)
                if 0xD800 <= codepoint <= 0xDFFF:
                    _fail("surrogate code points are not canonicalizable")
            return item
        if isinstance(item, list):
            return [normalize(member) for member in item]
        if isinstance(item, Mapping):
            normalized: dict[str, Any] = {}
            for key, member in item.items():
                if not isinstance(key, str):
                    _fail("non-string object member names are not canonicalizable")
                normalized[key] = normalize(member)
            return normalized
        _fail(f"value of type {type(item).__name__} is not canonicalizable")

    normalized = normalize(value)
    return json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _family_map(framework: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    validate_identity_framework(framework)
    return {family["id"]: family for family in framework["identity_families"]}


def _canonical_family_value(
    family: Mapping[str, Any],
    value: Any,
    *,
    member_identities: Sequence[str] | None = None,
) -> Any:
    mode = family["embedded_identity_mode"]
    if isinstance(value, Mapping):
        prepared = dict(value)
        if mode == "omit-own-identity":
            prepared.pop("identity", None)
    else:
        prepared = value

    kind = family["object_kind"]
    if kind == "object":
        if member_identities is not None:
            _fail("object identity does not accept aggregate member identities")
        return prepared

    aggregate = family["aggregate"]
    if member_identities is None:
        _fail("aggregate identity requires complete member identities")
    if not member_identities and aggregate["empty_aggregate_rule"] == "reject":
        _fail("aggregate identity rejects empty membership")
    if len(member_identities) != len(set(member_identities)):
        if aggregate["duplicate_policy"] == "reject":
            _fail("aggregate identity contains duplicate members")

    members = list(member_identities)
    if kind == "unordered-aggregate":
        members.sort()
    elif kind == "transitive-closure":
        members.sort()

    return {
        "value": prepared,
        "member_identities": members,
    }


def compute_identity(
    framework: Mapping[str, Any],
    family_id: str,
    value: Any,
    *,
    member_identities: Sequence[str] | None = None,
) -> str:
    """Compute one domain-separated identity using the normative framework."""
    families = _family_map(framework)
    family = families.get(family_id)
    if family is None:
        _fail(f"unknown identity family {family_id}")

    canonical_value = _canonical_family_value(
        family,
        value,
        member_identities=member_identities,
    )
    prefix = family["domain_separation_prefix"].encode("utf-8")
    preimage = prefix + canonical_json_bytes(canonical_value)
    digest = hashlib.sha256(preimage).hexdigest()
    return f"{family_id}-sha256:{digest}"


def verify_identity(
    framework: Mapping[str, Any],
    family_id: str,
    claimed_identity: str,
    value: Any,
    *,
    member_identities: Sequence[str] | None = None,
) -> None:
    """Fail closed unless the claimed identity exactly matches the computed identity."""
    expected_prefix = f"{family_id}-sha256:"
    if not claimed_identity.startswith(expected_prefix):
        _fail("claimed identity family does not match the required family")
    expected = compute_identity(
        framework,
        family_id,
        value,
        member_identities=member_identities,
    )
    if claimed_identity != expected:
        _fail("claimed identity does not match its canonical preimage")


def validate_fixed_identity_vectors(
    framework: Mapping[str, Any],
    vectors: Mapping[str, Any],
) -> None:
    """Validate all fixed positive and negative identity vectors."""
    if vectors.get("schema_version") != 1:
        _fail("identity vectors schema_version must be 1")

    positive = vectors.get("positive")
    negative = vectors.get("negative")
    if not isinstance(positive, list) or not positive:
        _fail("positive identity vectors are required")
    if not isinstance(negative, list) or not negative:
        _fail("negative identity vectors are required")

    seen: set[str] = set()
    for vector in positive:
        vector_id = vector["id"]
        if vector_id in seen:
            _fail(f"duplicate identity vector id {vector_id}")
        seen.add(vector_id)
        actual = compute_identity(
            framework,
            vector["family_id"],
            vector["value"],
            member_identities=vector.get("member_identities"),
        )
        if actual != vector["expected_identity"]:
            _fail(f"fixed identity vector {vector_id} does not match")

    for vector in negative:
        vector_id = vector["id"]
        if vector_id in seen:
            _fail(f"duplicate identity vector id {vector_id}")
        seen.add(vector_id)
        try:
            verify_identity(
                framework,
                vector["family_id"],
                vector["claimed_identity"],
                vector["value"],
                member_identities=vector.get("member_identities"),
            )
        except IdentityFrameworkError as exc:
            expected_error = vector["expected_error"]
            if expected_error not in str(exc):
                _fail(
                    f"negative identity vector {vector_id} failed for the wrong reason"
                )
        else:
            _fail(f"negative identity vector {vector_id} was accepted")



def render_identity_framework_markdown(framework: Mapping[str, Any]) -> str:
    """Render the deterministic Markdown projection of the identity framework."""
    validate_identity_framework(framework)
    lines = [
        "# GVE Unified Domain-Separated Identity Framework",
        "",
        "> This Markdown is a deterministic projection of "
        "`GVE-IDENTITY-FRAMEWORK.json`. The JSON is normative.",
        "",
        "## Authority",
        "",
        f"- Governing specification: "
        f"`{framework['authority']['governing_specification']}`",
        f"- Integration state: `{framework['authority']['integration_state']}`",
        "",
        "## Representation",
        "",
        f"- Syntax: `{framework['representation']['syntax']}`",
        f"- Digest encoding: `{framework['representation']['digest_encoding']}`",
        "",
        "## Identity Families",
        "",
    ]
    for family in framework["identity_families"]:
        lines.extend(
            [
                f"### `{family['id']}`",
                "",
                f"- Semantic domain: `{family['semantic_domain']}`",
                f"- Domain prefix: "
                f"`{family['domain_separation_prefix'][:-1]}\\\\0`",
                f"- Canonicalization: `{family['canonicalization_version']}`",
                f"- Digest: `{family['digest_algorithm']}`",
                f"- Reference mode: `{family['reference_mode']}`",
                f"- Object kind: `{family['object_kind']}`",
                f"- Embedded identity mode: `{family['embedded_identity_mode']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Fail-Closed Conditions",
            "",
        ]
    )
    for condition in framework["fail_closed_conditions"]:
        lines.append(f"- `{condition}`")
    lines.extend(
        [
            "",
            "## Canonical Normative JSON",
            "",
            "```json",
            json.dumps(
                framework,
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
            ),
            "```",
            "",
        ]
    )
    return "\n".join(lines)
