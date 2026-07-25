"""Deterministic normative specification-set revision identities."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence


class SpecificationRevisionError(ValueError):
    """Raised when a normative specification revision cannot be constructed."""


def _canonical_json(value: Any) -> bytes:
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise SpecificationRevisionError(
            f"specification revision input is not canonicalizable: {exc}"
        ) from exc
    return text.encode("utf-8")


def document_content_identity(document: Mapping[str, Any]) -> str:
    """Return the deterministic SHA-256 identity of one normative JSON document."""
    return hashlib.sha256(_canonical_json(document)).hexdigest()


def build_specification_revision(
    documents: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build one deterministic identity for an exact normative document graph."""
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
                "content_sha256": document_content_identity(document),
            }
        )

    members.sort(key=lambda member: member["id"])
    manifest = {
        "schema_version": 1,
        "members": members,
    }
    return {
        "algorithm": "sha256",
        "identity": hashlib.sha256(_canonical_json(manifest)).hexdigest(),
        "manifest": manifest,
    }


def validate_specification_revision(
    documents: Sequence[Mapping[str, Any]],
    revision: Mapping[str, Any],
) -> None:
    """Fail closed unless a supplied revision exactly matches the normative graph."""
    expected = build_specification_revision(documents)
    if revision.get("algorithm") != expected["algorithm"]:
        raise SpecificationRevisionError(
            "specification revision algorithm is missing or unsupported"
        )
    identity = revision.get("identity")
    if not isinstance(identity, str) or len(identity) != 64:
        raise SpecificationRevisionError(
            "specification revision identity is missing or malformed"
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
        for field in ("version", "content_sha256"):
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
    calculated_identity = hashlib.sha256(
        _canonical_json(canonical_supplied)
    ).hexdigest()
    if identity != calculated_identity:
        raise SpecificationRevisionError(
            "specification revision identity conflicts with its manifest"
        )
    if identity != expected["identity"]:
        raise SpecificationRevisionError(
            "specification revision is not current for the normative graph"
        )
