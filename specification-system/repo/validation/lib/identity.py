from __future__ import annotations

import hashlib
import re
from typing import Any

from .canonical_json import canonical_json_bytes
from .contracts import (
    ValidationError,
    exact_fields,
    functional_identifier,
    normalized_field_name,
    require_disjoint,
    require_unique,
)


LOWER_HEX_64 = re.compile(r"^[0-9a-f]{64}$")
SEMANTIC_IDENTITY_FIELDS = {"family", "encoded_digest"}
VERIFICATION_RECORD_FIELDS = {"identity", "family_name", "verified"}
FAMILY_FIELDS = {
    "family_construction_identity",
    "family_name",
    "semantic_domain",
    "object_kind",
    "canonicalization_version",
    "digest_algorithm",
    "digest_encoding",
    "domain_prefix",
    "included_preimage_fields",
    "omitted_preimage_fields",
    "own_identity",
    "references",
    "aggregate",
    "verification",
    "unavailable_capabilities",
}
REQUEST_FIELDS = {
    "mode",
    "family_name",
    "value",
    "supplied_identity",
    "verification_context",
}
UNAVAILABLE_CAPABILITIES = [
    "governing-revision-binding",
    "manifest-bootstrap",
    "sealing",
    "acceptance",
]


def validate_semantic_identity(value: Any, *, location: str) -> dict[str, str]:
    identity = exact_fields(
        value,
        allowed=SEMANTIC_IDENTITY_FIELDS,
        required=SEMANTIC_IDENTITY_FIELDS,
        location=location,
    )
    family = functional_identifier(identity["family"], location=f"{location}.family")
    digest = identity["encoded_digest"]
    if not isinstance(digest, str) or not LOWER_HEX_64.fullmatch(digest):
        raise ValidationError(f"{location}.encoded_digest: invalid lowercase SHA-256")
    return {"family": family, "encoded_digest": digest}


def _identity_key(identity: dict[str, str]) -> tuple[str, str]:
    return identity["family"], identity["encoded_digest"]


def _validate_field_array(value: Any, *, location: str, non_empty: bool) -> list[str]:
    values = require_unique(value, location=location)
    if non_empty and not values:
        raise ValidationError(f"{location}: non-empty array required")
    return [
        normalized_field_name(item, location=f"{location}[{index}]")
        for index, item in enumerate(values)
    ]


def _validate_references(value: Any, *, location: str) -> dict[str, Any]:
    references = exact_fields(
        value,
        allowed={"mode", "identity_field", "value_field", "allowed_family_names"},
        required={"mode", "identity_field", "value_field", "allowed_family_names"},
        location=location,
    )
    mode = references["mode"]
    if mode not in {"none", "by-identity", "identity-plus-value"}:
        raise ValidationError(f"{location}.mode: unsupported reference mode")
    allowed = require_unique(
        references["allowed_family_names"],
        location=f"{location}.allowed_family_names",
    )
    allowed = [
        functional_identifier(item, location=f"{location}.allowed_family_names[{index}]")
        for index, item in enumerate(allowed)
    ]
    identity_field = references["identity_field"]
    value_field = references["value_field"]
    if mode == "none":
        if identity_field is not None or value_field is not None or allowed:
            raise ValidationError(f"{location}: invalid none reference declaration")
    elif mode == "by-identity":
        identity_field = normalized_field_name(
            identity_field, location=f"{location}.identity_field"
        )
        if value_field is not None or not allowed:
            raise ValidationError(f"{location}: invalid by-identity declaration")
    else:
        identity_field = normalized_field_name(
            identity_field, location=f"{location}.identity_field"
        )
        value_field = normalized_field_name(
            value_field, location=f"{location}.value_field"
        )
        if identity_field == value_field or not allowed:
            raise ValidationError(f"{location}: invalid identity-plus-value declaration")
    return {
        "mode": mode,
        "identity_field": identity_field,
        "value_field": value_field,
        "allowed_family_names": allowed,
    }


def _validate_aggregate(
    value: Any,
    *,
    object_kind: str,
    allowed_family_names: list[str],
    location: str,
) -> dict[str, Any] | None:
    if object_kind == "object":
        if value is not None:
            raise ValidationError(f"{location}: object family aggregate must be null")
        return None
    aggregate = exact_fields(
        value,
        allowed={
            "membership_field",
            "member_family_names",
            "ordering",
            "duplicate_policy",
            "empty_policy",
            "closure_boundary",
            "cycle_policy",
        },
        required={
            "membership_field",
            "member_family_names",
            "ordering",
            "duplicate_policy",
            "empty_policy",
            "closure_boundary",
            "cycle_policy",
        },
        location=location,
    )
    ordering = aggregate["ordering"]
    expected = "ordered" if object_kind == "ordered-aggregate" else "unordered"
    if ordering != expected:
        raise ValidationError(f"{location}.ordering: object kind and ordering conflict")
    membership_field = normalized_field_name(
        aggregate["membership_field"], location=f"{location}.membership_field"
    )
    members = require_unique(
        aggregate["member_family_names"], location=f"{location}.member_family_names"
    )
    members = [
        functional_identifier(item, location=f"{location}.member_family_names[{index}]")
        for index, item in enumerate(members)
    ]
    if not members or members != allowed_family_names:
        raise ValidationError(f"{location}: invalid aggregate membership declaration")
    if aggregate["duplicate_policy"] != "reject":
        raise ValidationError(f"{location}.duplicate_policy: unsupported policy")
    if aggregate["empty_policy"] not in {"allow", "reject"}:
        raise ValidationError(f"{location}.empty_policy: unsupported policy")
    if aggregate["closure_boundary"] != "direct":
        raise ValidationError(f"{location}.closure_boundary: unsupported policy")
    if aggregate["cycle_policy"] != "reject":
        raise ValidationError(f"{location}.cycle_policy: unsupported policy")
    return {
        "membership_field": membership_field,
        "member_family_names": members,
        "ordering": ordering,
        "duplicate_policy": "reject",
        "empty_policy": aggregate["empty_policy"],
        "closure_boundary": "direct",
        "cycle_policy": "reject",
    }


def build_family_registry(
    declarations: Any,
    *,
    location: str = "family declarations",
) -> dict[str, dict[str, Any]]:
    if not isinstance(declarations, list) or not declarations:
        raise ValidationError(f"{location}: non-empty array required")
    registry: dict[str, dict[str, Any]] = {}
    prefixes: set[str] = set()
    for index, raw in enumerate(declarations):
        item_location = f"{location}[{index}]"
        declaration = exact_fields(
            raw,
            allowed=FAMILY_FIELDS,
            required=FAMILY_FIELDS,
            location=item_location,
        )
        functional_identifier(
            declaration["family_construction_identity"],
            location=f"{item_location}.family_construction_identity",
        )
        family_name = functional_identifier(
            declaration["family_name"], location=f"{item_location}.family_name"
        )
        functional_identifier(
            declaration["semantic_domain"], location=f"{item_location}.semantic_domain"
        )
        if family_name in registry:
            raise ValidationError(f"{item_location}.family_name: duplicate family")
        object_kind = declaration["object_kind"]
        if object_kind not in {"object", "ordered-aggregate", "unordered-aggregate"}:
            raise ValidationError(f"{item_location}.object_kind: unsupported object kind")
        if declaration["canonicalization_version"] != "canonical-json-v1":
            raise ValidationError(
                f"{item_location}.canonicalization_version: unsupported version"
            )
        if declaration["digest_algorithm"] != "sha-256":
            raise ValidationError(f"{item_location}.digest_algorithm: unsupported digest")
        if declaration["digest_encoding"] != "lowercase-hexadecimal":
            raise ValidationError(
                f"{item_location}.digest_encoding: unsupported encoding"
            )
        prefix = declaration["domain_prefix"]
        if (
            not isinstance(prefix, str)
            or not prefix
            or any(ord(character) < 0x20 or ord(character) > 0x7E for character in prefix)
            or prefix in prefixes
        ):
            raise ValidationError(f"{item_location}.domain_prefix: invalid or duplicate")
        prefixes.add(prefix)
        included = _validate_field_array(
            declaration["included_preimage_fields"],
            location=f"{item_location}.included_preimage_fields",
            non_empty=True,
        )
        omitted = _validate_field_array(
            declaration["omitted_preimage_fields"],
            location=f"{item_location}.omitted_preimage_fields",
            non_empty=False,
        )
        require_disjoint(
            included,
            omitted,
            location=f"{item_location}.preimage_fields",
        )
        own = exact_fields(
            declaration["own_identity"],
            allowed={"mode", "field"},
            required={"mode", "field"},
            location=f"{item_location}.own_identity",
        )
        if own["mode"] != "omit-own-identity":
            raise ValidationError(f"{item_location}.own_identity.mode: unsupported mode")
        own_field = normalized_field_name(
            own["field"], location=f"{item_location}.own_identity.field"
        )
        references = _validate_references(
            declaration["references"], location=f"{item_location}.references"
        )
        aggregate = _validate_aggregate(
            declaration["aggregate"],
            object_kind=object_kind,
            allowed_family_names=references["allowed_family_names"],
            location=f"{item_location}.aggregate",
        )
        verification = exact_fields(
            declaration["verification"],
            allowed={"mode", "context_source"},
            required={"mode", "context_source"},
            location=f"{item_location}.verification",
        )
        expected_verification = {
            "none": ("none", "none"),
            "by-identity": ("verified-identity-set", "caller-supplied"),
            "identity-plus-value": (
                "embedded-value-recomputation",
                "embedded-value",
            ),
        }[references["mode"]]
        if (
            verification["mode"],
            verification["context_source"],
        ) != expected_verification:
            raise ValidationError(
                f"{item_location}.verification: reference and verification modes conflict"
            )
        if declaration["unavailable_capabilities"] != UNAVAILABLE_CAPABILITIES:
            raise ValidationError(
                f"{item_location}.unavailable_capabilities: policy mismatch"
            )
        registry[family_name] = {
            **declaration,
            "family_name": family_name,
            "included_preimage_fields": included,
            "omitted_preimage_fields": omitted,
            "own_identity": {"mode": "omit-own-identity", "field": own_field},
            "references": references,
            "aggregate": aggregate,
        }
    return registry


def validate_verification_context(
    value: Any,
    *,
    location: str = "verification context",
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise ValidationError(f"{location}: expected array")
    records: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for index, raw in enumerate(value):
        item_location = f"{location}[{index}]"
        record = exact_fields(
            raw,
            allowed=VERIFICATION_RECORD_FIELDS,
            required=VERIFICATION_RECORD_FIELDS,
            location=item_location,
        )
        identity = validate_semantic_identity(
            record["identity"], location=f"{item_location}.identity"
        )
        key = _identity_key(identity)
        if key in seen:
            raise ValidationError(f"{item_location}.identity: duplicate identity")
        seen.add(key)
        if record["family_name"] != identity["family"]:
            raise ValidationError(f"{item_location}.family_name: family conflict")
        if record["verified"] is not True:
            raise ValidationError(f"{item_location}.verified: identity is not verified")
        records.append(
            {
                "identity": identity,
                "family_name": identity["family"],
                "verified": True,
            }
        )
    return records


def derive_identity(
    family_name: str,
    value: Any,
    registry: dict[str, dict[str, Any]],
    context: list[dict[str, Any]],
    *,
    supplied_identity: dict[str, str] | None = None,
    construction_stack: tuple[tuple[str, str], ...] = (),
) -> tuple[dict[str, str], dict[str, Any]]:
    if family_name not in registry:
        raise ValidationError("unknown-family")
    if not isinstance(value, dict):
        raise ValidationError("malformed-request")
    family = registry[family_name]
    own_field = family["own_identity"]["field"]
    raw_own_identity = value.get(own_field)
    provided_own_identity = (
        None
        if raw_own_identity is None
        else validate_semantic_identity(
            raw_own_identity, location=f"{family_name}.{own_field}"
        )
    )
    canonical_value: dict[str, Any] = {}
    for field in family["included_preimage_fields"]:
        if field != own_field and field in value:
            canonical_value[field] = value[field]

    references = family["references"]
    reference_count = 0
    aggregate_member_count = 0
    aggregate_ordering = None
    if references["mode"] != "none":
        collection_field = (
            family["aggregate"]["membership_field"]
            if family["aggregate"] is not None
            else "references"
        )
        raw_items = value.get(collection_field, [])
        if not isinstance(raw_items, list):
            raise ValidationError("malformed-reference")
        processed: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for raw_item in raw_items:
            if not isinstance(raw_item, dict):
                raise ValidationError("malformed-reference")
            expected_fields = {references["identity_field"]}
            if references["value_field"] is not None:
                expected_fields.add(references["value_field"])
            if set(raw_item) != expected_fields:
                raise ValidationError("malformed-reference")
            identity = validate_semantic_identity(
                raw_item[references["identity_field"]],
                location=f"{family_name}.{collection_field}.identity",
            )
            key = _identity_key(identity)
            if supplied_identity is not None and identity == supplied_identity:
                if family["aggregate"] is not None:
                    raise ValidationError("self-membership")
            if key in construction_stack:
                raise ValidationError("aggregate-cycle")
            if key in seen:
                if family["aggregate"] is not None:
                    raise ValidationError("duplicate-aggregate-member")
                raise ValidationError("malformed-reference")
            seen.add(key)
            if identity["family"] not in references["allowed_family_names"]:
                raise ValidationError("reference-family-mismatch")
            if references["mode"] == "by-identity":
                matches = [record for record in context if record["identity"] == identity]
                if len(matches) != 1:
                    raise ValidationError("missing-reference-context")
                processed.append({"identity": identity})
            else:
                embedded = raw_item[references["value_field"]]
                if not isinstance(embedded, dict):
                    raise ValidationError("malformed-reference")
                computed, _ = derive_identity(
                    identity["family"],
                    embedded,
                    registry,
                    context,
                    construction_stack=construction_stack + (key,),
                )
                if computed != identity:
                    raise ValidationError("embedded-reference-identity-mismatch")
                canonical_embedded = dict(embedded)
                canonical_embedded.pop(
                    registry[identity["family"]]["own_identity"]["field"], None
                )
                processed.append(
                    {"identity": identity, "value": canonical_embedded}
                )
        reference_count = len(processed)
        if family["aggregate"] is not None:
            aggregate_member_count = len(processed)
            aggregate_ordering = family["aggregate"]["ordering"]
            if not processed and family["aggregate"]["empty_policy"] == "reject":
                raise ValidationError("empty-aggregate-forbidden")
            if aggregate_ordering == "unordered":
                processed.sort(key=lambda item: _identity_key(item["identity"]))
        canonical_value[collection_field] = processed

    canonical_bytes = canonical_json_bytes(canonical_value, location="canonical-value")
    preimage = family["domain_prefix"].encode("utf-8") + b"\x00" + canonical_bytes
    computed = {
        "family": family_name,
        "encoded_digest": hashlib.sha256(preimage).hexdigest(),
    }
    if provided_own_identity is not None and provided_own_identity != computed:
        raise ValidationError("contradictory-own-identity")
    evidence = {
        "family_name": family_name,
        "canonicalization_version": family["canonicalization_version"],
        "digest_algorithm": family["digest_algorithm"],
        "domain_prefix": family["domain_prefix"],
        "own_identity_field_omitted": own_field,
        "reference_count": reference_count,
        "aggregate_member_count": aggregate_member_count,
        "aggregate_ordering": aggregate_ordering,
        "canonical_value_sha256": hashlib.sha256(canonical_bytes).hexdigest(),
        "computed_identity": computed,
    }
    return computed, evidence


def evaluate_request(
    request: Any,
    registry: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    request = exact_fields(
        request,
        allowed=REQUEST_FIELDS,
        required=REQUEST_FIELDS,
        location="request",
    )
    mode = request["mode"]
    if mode not in {"derive", "verify"}:
        raise ValidationError("malformed-request")
    family_name = functional_identifier(
        request["family_name"], location="request.family_name"
    )
    supplied = request["supplied_identity"]
    if mode == "derive":
        if supplied is not None:
            raise ValidationError("malformed-request")
        supplied_identity = None
    else:
        supplied_identity = validate_semantic_identity(
            supplied, location="request.supplied_identity"
        )
        if supplied_identity["family"] != family_name:
            return {
                "status": "rejected",
                "family_name": family_name,
                "computed_identity": None,
                "supplied_identity": supplied_identity,
                "evidence": None,
                "diagnostic": "family-mismatch",
            }
    context = validate_verification_context(request["verification_context"])
    try:
        computed, evidence = derive_identity(
            family_name,
            request["value"],
            registry,
            context,
            supplied_identity=supplied_identity,
            construction_stack=(
                (_identity_key(supplied_identity),)
                if supplied_identity is not None
                else ()
            ),
        )
    except ValidationError as exc:
        diagnostic = str(exc)
        if diagnostic not in {
            "unknown-family",
            "malformed-request",
            "malformed-reference",
            "missing-reference-context",
            "reference-family-mismatch",
            "embedded-reference-identity-mismatch",
            "duplicate-aggregate-member",
            "empty-aggregate-forbidden",
            "self-membership",
            "aggregate-cycle",
            "contradictory-own-identity",
        }:
            raise
        return {
            "status": "rejected",
            "family_name": family_name,
            "computed_identity": None,
            "supplied_identity": supplied_identity,
            "evidence": None,
            "diagnostic": diagnostic,
        }
    if mode == "verify" and computed != supplied_identity:
        return {
            "status": "rejected",
            "family_name": family_name,
            "computed_identity": None,
            "supplied_identity": supplied_identity,
            "evidence": evidence,
            "diagnostic": "supplied-identity-mismatch",
        }
    return {
        "status": "verified" if mode == "verify" else "derived",
        "family_name": family_name,
        "computed_identity": computed,
        "supplied_identity": supplied_identity,
        "evidence": evidence,
        "diagnostic": None,
    }
