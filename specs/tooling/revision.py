"""Deterministic domain-separated normative specification-set identities."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

from .identity import (
    IdentityFrameworkError,
    compute_identity,
    verify_identity,
)


class SpecificationRevisionError(ValueError):
    """Raised when a normative specification revision cannot be constructed."""


CANONICALIZATION = "gve-canonical-json-v1"
DIGEST_ALGORITHM = "sha256"
DOCUMENT_FAMILY = "gve-spec-document"
REVISION_FAMILY = "gve-spec-revision"
DOCUMENT_IDENTITY_FORMAT = "gve-spec-document-sha256:<digest>"
REVISION_IDENTITY_FORMAT = "gve-spec-revision-sha256:<digest>"


@lru_cache(maxsize=1)
def _identity_framework() -> Mapping[str, Any]:
    path = Path(__file__).resolve().parents[1] / "identity" / "GVE-IDENTITY-FRAMEWORK.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SpecificationRevisionError(
            f"cannot load normative identity framework: {exc}"
        ) from exc
    if not isinstance(value, Mapping):
        raise SpecificationRevisionError(
            "normative identity framework must contain one JSON object"
        )
    return value


def document_content_identity(document: Mapping[str, Any]) -> str:
    """Return the gve-spec-document identity of one normative JSON document."""
    try:
        return compute_identity(
            _identity_framework(),
            DOCUMENT_FAMILY,
            document,
        )
    except IdentityFrameworkError as exc:
        raise SpecificationRevisionError(
            f"specification revision input is not canonicalizable: {exc}"
        ) from exc


def _validate_typed_identity(
    identity: Any,
    *,
    family: str,
    label: str,
) -> str:
    if not isinstance(identity, str):
        raise SpecificationRevisionError(f"{label} is missing or malformed")
    prefix = f"{family}-sha256:"
    if not identity.startswith(prefix):
        raise SpecificationRevisionError(
            f"{label} must use the {family} identity family"
        )
    digest = identity[len(prefix):]
    if len(digest) != 64 or any(
        character not in "0123456789abcdef" for character in digest
    ):
        raise SpecificationRevisionError(f"{label} is missing or malformed")
    return identity


def build_specification_revision(
    documents: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build one domain-separated identity for an exact normative document graph."""
    if not documents:
        raise SpecificationRevisionError(
            "specification revision requires at least one normative document"
        )

    members: list[dict[str, str]] = []
    seen: set[str] = set()
    for document in documents:
        specification = document.get("specification")
        if not isinstance(specification, Mapping):
            raise SpecificationRevisionError(
                "specification revision member lacks specification metadata"
            )
        identifier = specification.get("id")
        version = specification.get("version")
        status = specification.get("status")
        if not isinstance(identifier, str) or not identifier:
            raise SpecificationRevisionError(
                "specification revision member has invalid identity"
            )
        if identifier in seen:
            raise SpecificationRevisionError(
                f"duplicate specification revision member {identifier}"
            )
        seen.add(identifier)
        if not isinstance(version, str) or not version:
            raise SpecificationRevisionError(
                f"{identifier}: specification revision member has invalid version"
            )
        if status != "normative":
            raise SpecificationRevisionError(
                f"{identifier}: specification revision member must be normative; "
                f"found {status}"
            )
        members.append(
            {
                "id": identifier,
                "version": version,
                "document_identity": document_content_identity(document),
            }
        )

    members.sort(key=lambda member: member["id"])
    manifest = {
        "schema_version": 1,
        "members": members,
    }
    member_identities = [member["document_identity"] for member in members]
    identity_context = [
        {
            "identity": member["document_identity"],
            "family_id": DOCUMENT_FAMILY,
            "accepted": True,
        }
        for member in members
    ]
    try:
        revision_identity = compute_identity(
            _identity_framework(),
            REVISION_FAMILY,
            manifest,
            member_identities=member_identities,
            identity_context=identity_context,
        )
    except IdentityFrameworkError as exc:
        raise SpecificationRevisionError(
            f"specification revision cannot be identified: {exc}"
        ) from exc
    return {
        "canonicalization": CANONICALIZATION,
        "algorithm": DIGEST_ALGORITHM,
        "identity_format": REVISION_IDENTITY_FORMAT,
        "identity": revision_identity,
        "manifest": manifest,
    }


def validate_specification_revision(
    documents: Sequence[Mapping[str, Any]],
    revision: Mapping[str, Any],
) -> None:
    """Fail closed unless a supplied revision exactly matches the normative graph."""
    expected = build_specification_revision(documents)
    if revision.get("canonicalization") != expected["canonicalization"]:
        raise SpecificationRevisionError(
            "specification revision canonicalization is missing or unsupported"
        )
    if revision.get("algorithm") != expected["algorithm"]:
        raise SpecificationRevisionError(
            "specification revision algorithm is missing or unsupported"
        )
    if revision.get("identity_format") != expected["identity_format"]:
        raise SpecificationRevisionError(
            "specification revision identity format is missing or unsupported"
        )
    identity = _validate_typed_identity(
        revision.get("identity"),
        family=REVISION_FAMILY,
        label="specification revision identity",
    )
    manifest = revision.get("manifest")
    if not isinstance(manifest, Mapping):
        raise SpecificationRevisionError(
            "specification revision manifest is missing or malformed"
        )
    if manifest.get("schema_version") != 1:
        raise SpecificationRevisionError(
            "specification revision manifest schema version is unsupported"
        )
    members = manifest.get("members")
    if not isinstance(members, list):
        raise SpecificationRevisionError(
            "specification revision manifest members are missing or malformed"
        )

    supplied_by_id: dict[str, Mapping[str, Any]] = {}
    for index, member in enumerate(members):
        if not isinstance(member, Mapping):
            raise SpecificationRevisionError(
                f"specification revision member {index} is malformed"
            )
        identifier = member.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise SpecificationRevisionError(
                f"specification revision member {index} has invalid identity"
            )
        if identifier in supplied_by_id:
            raise SpecificationRevisionError(
                f"duplicate specification revision member {identifier}"
            )
        _validate_typed_identity(
            member.get("document_identity"),
            family=DOCUMENT_FAMILY,
            label=f"{identifier}: specification document identity",
        )
        supplied_by_id[identifier] = member

    expected_by_id = {
        member["id"]: member
        for member in expected["manifest"]["members"]
    }
    missing = sorted(set(expected_by_id) - set(supplied_by_id))
    unexpected = sorted(set(supplied_by_id) - set(expected_by_id))
    if missing or unexpected:
        raise SpecificationRevisionError(
            "specification revision membership mismatch; "
            f"missing={missing}, unexpected={unexpected}"
        )

    for identifier in sorted(expected_by_id):
        supplied = supplied_by_id[identifier]
        expected_member = expected_by_id[identifier]
        for field in ("version", "document_identity"):
            if supplied.get(field) != expected_member[field]:
                raise SpecificationRevisionError(
                    f"{identifier}: conflicting specification revision {field}"
                )

    canonical_supplied = {
        "schema_version": 1,
        "members": [
            dict(supplied_by_id[identifier])
            for identifier in sorted(supplied_by_id)
        ],
    }
    member_identities = [
        supplied_by_id[identifier]["document_identity"]
        for identifier in sorted(supplied_by_id)
    ]
    identity_context = [
        {
            "identity": identity,
            "family_id": DOCUMENT_FAMILY,
            "accepted": True,
        }
        for identity in member_identities
    ]
    try:
        verify_identity(
            _identity_framework(),
            REVISION_FAMILY,
            identity,
            canonical_supplied,
            member_identities=member_identities,
            identity_context=identity_context,
        )
    except IdentityFrameworkError as exc:
        raise SpecificationRevisionError(
            "specification revision identity conflicts with its manifest"
        ) from exc
    if identity != expected["identity"]:
        raise SpecificationRevisionError(
            "specification revision is not current for the normative graph"
        )
