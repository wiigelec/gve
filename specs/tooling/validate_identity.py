"""Repository integration validation for the normative GVE identity framework."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator

from .identity import (
    IdentityFrameworkError,
    render_identity_framework_markdown,
    validate_fixed_identity_vectors,
    validate_identity_framework,
)
from .revision import (
    DOCUMENT_IDENTITY_FORMAT,
    REVISION_IDENTITY_FORMAT,
    build_specification_revision,
    document_content_identity,
)


class IdentityIntegrationError(ValueError):
    """Raised when repository identity-framework integration fails closed."""


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise IdentityIntegrationError(f"cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise IdentityIntegrationError(f"{path} must contain one JSON object")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _positive_vector(
    vectors: Mapping[str, Any],
    vector_id: str,
) -> Mapping[str, Any]:
    positive = vectors.get("positive")
    if not isinstance(positive, list):
        raise IdentityIntegrationError("positive identity vectors are missing")
    matches = [
        vector
        for vector in positive
        if isinstance(vector, Mapping) and vector.get("id") == vector_id
    ]
    if len(matches) != 1:
        raise IdentityIntegrationError(
            f"identity vector {vector_id} must exist exactly once"
        )
    return matches[0]


def validate_revision_tooling_binding(
    manifest: Mapping[str, Any],
    vectors: Mapping[str, Any],
) -> None:
    """Require manifest metadata, fixed vectors, and revision tooling to agree."""
    if manifest.get("canonicalization") != "gve-canonical-json-v1":
        raise IdentityIntegrationError(
            "specification manifest canonicalization conflicts with revision tooling"
        )
    if manifest.get("digest_algorithm") != "sha256":
        raise IdentityIntegrationError(
            "specification manifest digest algorithm conflicts with revision tooling"
        )
    if manifest.get("identity_format") != REVISION_IDENTITY_FORMAT:
        raise IdentityIntegrationError(
            "specification manifest identity format conflicts with revision tooling"
        )
    if DOCUMENT_IDENTITY_FORMAT != "gve-spec-document-sha256:<digest>":
        raise IdentityIntegrationError(
            "specification document identity format is not domain-separated"
        )

    document_vector = _positive_vector(
        vectors,
        "spec-document-tooling-vector",
    )
    revision_vector = _positive_vector(
        vectors,
        "spec-revision-tooling-vector",
    )
    document = document_vector.get("value")
    if not isinstance(document, Mapping):
        raise IdentityIntegrationError(
            "specification document tooling vector value is malformed"
        )
    actual_document_identity = document_content_identity(document)
    if actual_document_identity != document_vector.get("expected_identity"):
        raise IdentityIntegrationError(
            "specification document tooling conflicts with fixed vector"
        )

    revision = build_specification_revision([document])
    if revision["identity"] != revision_vector.get("expected_identity"):
        raise IdentityIntegrationError(
            "specification revision tooling conflicts with fixed vector"
        )
    if revision["manifest"] != revision_vector.get("value"):
        raise IdentityIntegrationError(
            "specification revision manifest conflicts with fixed vector"
        )
    member_identities = revision_vector.get("member_identities")
    if member_identities != [actual_document_identity]:
        raise IdentityIntegrationError(
            "specification revision member binding conflicts with fixed vector"
        )


def validate_repository_identity(specs_root: Path) -> None:
    specs_root = specs_root.resolve()
    manifest = _load(specs_root / "GVE-SPECIFICATION-SET.json")
    binding = manifest.get("identity_framework")
    if not isinstance(binding, dict):
        raise IdentityIntegrationError(
            "specification manifest lacks identity_framework binding"
        )

    paths = {
        "content_sha256": specs_root / binding["path"],
        "schema_sha256": specs_root / binding["schema_path"],
        "projection_sha256": specs_root / binding["projection_path"],
        "vectors_sha256": specs_root / binding["vectors_path"],
    }
    for field, path in paths.items():
        if not path.is_file():
            raise IdentityIntegrationError(f"identity framework artifact missing: {path}")
        actual = _sha256(path)
        if actual != binding[field]:
            raise IdentityIntegrationError(
                f"identity framework {field} conflicts with repository bytes"
            )

    framework = _load(paths["content_sha256"])
    schema = _load(paths["schema_sha256"])
    vectors = _load(paths["vectors_sha256"])

    Draft202012Validator.check_schema(schema)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(framework),
        key=lambda error: list(error.path),
    )
    if errors:
        raise IdentityIntegrationError(
            f"identity framework schema validation failed: {errors[0].message}"
        )

    validate_identity_framework(framework)
    validate_fixed_identity_vectors(framework, vectors)
    validate_revision_tooling_binding(manifest, vectors)
    expected_markdown = render_identity_framework_markdown(framework)
    actual_markdown = paths["projection_sha256"].read_text(encoding="utf-8")
    if actual_markdown != expected_markdown:
        raise IdentityIntegrationError(
            "identity framework deterministic Markdown projection differs"
        )


def main() -> int:
    specs_root = Path(__file__).resolve().parents[1]
    try:
        validate_repository_identity(specs_root)
    except (IdentityFrameworkError, IdentityIntegrationError) as exc:
        print(f"identity framework validation failed: {exc}", file=sys.stderr)
        return 1
    print("identity framework validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
