"""Binding rules for current and historical specification revisions."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .revision import (
    DOCUMENT_FAMILY,
    REVISION_FAMILY,
    SpecificationRevisionError,
    validate_specification_revision,
)


class SpecificationRevisionBindingError(ValueError):
    """Raised when an artifact's governing revision binding is invalid."""


def _typed_identity(
    value: Any,
    *,
    family: str,
    label: str,
) -> str:
    if not isinstance(value, str):
        raise SpecificationRevisionBindingError(f"{label} is missing or malformed")
    prefix = f"{family}-sha256:"
    if not value.startswith(prefix):
        raise SpecificationRevisionBindingError(
            f"{label} must use the {family} identity family"
        )
    digest = value[len(prefix):]
    if len(digest) != 64 or any(
        character not in "0123456789abcdef" for character in digest
    ):
        raise SpecificationRevisionBindingError(f"{label} is missing or malformed")
    return value


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
    if revision.get("canonicalization") != "gve-canonical-json-v1":
        raise SpecificationRevisionBindingError(
            "historical specification revision canonicalization is missing or unsupported"
        )
    if revision.get("algorithm") != "sha256":
        raise SpecificationRevisionBindingError(
            "historical specification revision algorithm is missing or unsupported"
        )
    if revision.get("identity_format") != "gve-spec-revision-sha256:<digest>":
        raise SpecificationRevisionBindingError(
            "historical specification revision identity format is missing or unsupported"
        )
    _typed_identity(
        revision.get("identity"),
        family=REVISION_FAMILY,
        label="historical specification revision identity",
    )
    manifest = revision.get("manifest")
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
        _typed_identity(
            member.get("document_identity"),
            family=DOCUMENT_FAMILY,
            label=f"{identifier}: historical specification document identity",
        )
