"""Binding rules for current and historical specification revisions."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .revision import (
    SpecificationRevisionError,
    validate_specification_revision,
)


class SpecificationRevisionBindingError(ValueError):
    """Raised when an artifact's governing revision binding is invalid."""


def validate_current_revision_binding(
    documents: Sequence[Mapping[str, Any]],
    binding: Mapping[str, Any],
) -> None:
    """Require an artifact to bind exactly to the current normative revision."""
    revision = binding.get("specification_revision")
    if not isinstance(revision, Mapping):
        raise SpecificationRevisionBindingError(
            "current artifact lacks a specification_revision binding"
        )
    try:
        validate_specification_revision(documents, revision)
    except SpecificationRevisionError as exc:
        raise SpecificationRevisionBindingError(
            f"current specification revision binding is invalid: {exc}"
        ) from exc


def validate_historical_revision_binding(
    binding: Mapping[str, Any],
) -> None:
    """Validate retained historical attribution without asserting current freshness."""
    revision = binding.get("specification_revision")
    if not isinstance(revision, Mapping):
        raise SpecificationRevisionBindingError(
            "historical artifact lacks a specification_revision binding"
        )
    algorithm = revision.get("algorithm")
    identity = revision.get("identity")
    manifest = revision.get("manifest")
    if algorithm != "sha256":
        raise SpecificationRevisionBindingError(
            "historical specification revision algorithm is missing or unsupported"
        )
    if not isinstance(identity, str) or len(identity) != 64:
        raise SpecificationRevisionBindingError(
            "historical specification revision identity is missing or malformed"
        )
    if not isinstance(manifest, Mapping):
        raise SpecificationRevisionBindingError(
            "historical specification revision manifest is missing or malformed"
        )
    if manifest.get("schema_version") != 1:
        raise SpecificationRevisionBindingError(
            "historical specification revision manifest schema version is unsupported"
        )
    members = manifest.get("members")
    if not isinstance(members, list) or not members:
        raise SpecificationRevisionBindingError(
            "historical specification revision manifest members are missing or malformed"
        )

    seen: set[str] = set()
    for index, member in enumerate(members):
        if not isinstance(member, Mapping):
            raise SpecificationRevisionBindingError(
                f"historical specification revision member {index} is malformed"
            )
        identifier = member.get("id")
        version = member.get("version")
        content_identity = member.get("content_sha256")
        if not isinstance(identifier, str) or not identifier:
            raise SpecificationRevisionBindingError(
                f"historical specification revision member {index} has invalid identity"
            )
        if identifier in seen:
            raise SpecificationRevisionBindingError(
                f"duplicate historical specification revision member {identifier}"
            )
        seen.add(identifier)
        if not isinstance(version, str) or not version:
            raise SpecificationRevisionBindingError(
                f"{identifier}: historical specification revision version is invalid"
            )
        if (
            not isinstance(content_identity, str)
            or len(content_identity) != 64
        ):
            raise SpecificationRevisionBindingError(
                f"{identifier}: historical content identity is malformed"
            )
