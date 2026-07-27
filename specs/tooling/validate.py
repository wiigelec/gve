"""Repository validation for the accepted GVE normative specification set."""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

from .render import render_markdown
from .revision import SpecificationRevisionError, build_specification_revision
from .semantics import SemanticValidationError, validate_hierarchy
from .strict_json import StrictJSONError, load_strict
from .source_layout import SourceLayoutValidationError, validate_source_layout


class SchemaValidationError(ValueError):
    """Raised when a document fails structural validation."""


class ProjectionValidationError(ValueError):
    """Raised when committed Markdown differs from its deterministic projection."""


class SpecificationManifestError(ValueError):
    """Raised when the normative specification-set manifest is invalid."""


MANIFEST_FILENAME = "GVE-SPECIFICATION-SET.json"
MANIFEST_SCHEMA_FILENAME = "GVE-SPECIFICATION-SET.schema.json"


def _validator_class():
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise RuntimeError(
            "the 'jsonschema' package is required for specification validation"
        ) from exc
    return Draft202012Validator


def load_schema(path: Path) -> dict[str, Any]:
    return load_strict(path)


def _validate_instance(
    instance_path: Path,
    schema_path: Path,
    *,
    label: str,
) -> dict[str, Any]:
    validator_class = _validator_class()
    schema = load_schema(schema_path)
    validator_class.check_schema(schema)
    instance = load_strict(instance_path)
    errors = sorted(
        validator_class(schema).iter_errors(instance),
        key=lambda error: list(error.path),
    )
    if errors:
        error = errors[0]
        location = "$"
        for part in error.absolute_path:
            location += f"[{part}]" if isinstance(part, int) else f".{part}"
        raise SchemaValidationError(
            f"{instance_path}: {label} {location}: {error.message}"
        )
    return instance


def validate_document(document_path: Path, schema_path: Path) -> None:
    _validate_instance(document_path, schema_path, label="document")


def _manifest_paths(specs_root: Path) -> tuple[Path, Path]:
    return (
        specs_root / MANIFEST_FILENAME,
        specs_root / "schemas" / MANIFEST_SCHEMA_FILENAME,
    )


def load_specification_manifest(specs_root: Path) -> dict[str, Any]:
    specs_root = specs_root.resolve()
    manifest_path, schema_path = _manifest_paths(specs_root)
    try:
        manifest = _validate_instance(
            manifest_path,
            schema_path,
            label="manifest",
        )
    except OSError as exc:
        raise SpecificationManifestError(
            f"cannot read normative specification-set manifest: {exc}"
        ) from exc

    paths: set[str] = set()
    identifiers: set[str] = set()
    previous_identity: str | None = None
    for index, member in enumerate(manifest["members"]):
        path = member["path"]
        identifier = member["id"]
        if path in paths:
            raise SpecificationManifestError(
                f"duplicate normative manifest path {path}"
            )
        if identifier in identifiers:
            raise SpecificationManifestError(
                f"duplicate normative manifest identity {identifier}"
            )
        if previous_identity is not None and identifier <= previous_identity:
            raise SpecificationManifestError(
                "normative manifest members must be ordered by ascending identity"
            )
        candidate = Path(path)
        if candidate.is_absolute() or candidate.as_posix() != path or any(
            part in {"", ".", ".."} for part in candidate.parts
        ):
            raise SpecificationManifestError(
                f"normative manifest member {index} path is not normalized"
            )
        paths.add(path)
        identifiers.add(identifier)
        previous_identity = identifier
    return manifest


def discover_specifications(specs_root: Path) -> list[Path]:
    """Return only paths explicitly authorized by the normative manifest."""
    specs_root = specs_root.resolve()
    manifest = load_specification_manifest(specs_root)
    return [specs_root / member["path"] for member in manifest["members"]]


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_manifest_member_metadata(
    specs_root: Path,
    member: Mapping[str, Any],
    document_path: Path,
    document: Mapping[str, Any],
) -> None:
    identifier = document.get("specification", {}).get("id")
    if identifier != member["id"]:
        raise SpecificationManifestError(
            f"{member['path']}: manifest identity {member['id']} conflicts with "
            f"document identity {identifier}"
        )
    if member["role"] == "cross-level":
        role = document.get("authority_class")
    else:
        role = document.get("document", {}).get("role", "root")
    if role != member["role"]:
        raise SpecificationManifestError(
            f"{member['id']}: manifest role {member['role']} conflicts with "
            f"document role {role}"
        )
    try:
        document_path.resolve().relative_to(specs_root)
    except ValueError as exc:
        raise SpecificationManifestError(
            f"manifest path escapes specs root: {member['path']}"
        ) from exc


def _undeclared_normative_candidates(
    specs_root: Path,
    declared_paths: set[str],
) -> list[Path]:
    candidates = list((specs_root / "levels").glob("level-*/GVE-LEVEL-*.json"))
    candidates.extend((specs_root / "source-layout").glob("GVE-*.json"))
    return sorted(
        path
        for path in candidates
        if path.relative_to(specs_root).as_posix() not in declared_paths
    )


def _reject_undeclared_candidates(
    specs_root: Path,
    declared_paths: set[str],
) -> None:
    candidates = _undeclared_normative_candidates(specs_root, declared_paths)
    if not candidates:
        return
    by_root: dict[str, list[str]] = {}
    malformed: list[str] = []
    for path in candidates:
        try:
            document = load_strict(path)
            identifier = document["specification"]["id"]
            root = document.get("document", {}).get("root", identifier)
        except (KeyError, TypeError, StrictJSONError):
            malformed.append(path.relative_to(specs_root).as_posix())
            continue
        by_root.setdefault(root, []).append(identifier)
    if malformed:
        raise SpecificationManifestError(
            "undeclared normative candidate is malformed: " + ", ".join(malformed)
        )
    root = sorted(by_root)[0]
    unexpected = sorted(by_root[root])
    raise SemanticValidationError(
        f"{root}: specification-set membership mismatch; "
        f"missing=[], unexpected={unexpected}"
    )


def validate_specification_set(specs_root: Path) -> dict[str, Any]:
    specs_root = specs_root.resolve()
    levels_root = specs_root / "levels"
    level_schema_path = specs_root / "schemas" / "GVE-LEVEL.schema.json"
    manifest = load_specification_manifest(specs_root)
    declared_paths = {member["path"] for member in manifest["members"]}
    _reject_undeclared_candidates(specs_root, declared_paths)

    records: list[tuple[Path, dict[str, Any]]] = []
    level_records: list[tuple[Path, dict[str, Any]]] = []
    members_by_path = {member["path"]: member for member in manifest["members"]}
    for document_path in discover_specifications(specs_root):
        relative = document_path.relative_to(specs_root).as_posix()
        if not document_path.is_file():
            continue
        member = members_by_path[relative]
        schema_path = (
            specs_root / member["schema_path"]
            if member["role"] == "cross-level"
            else level_schema_path
        )
        validate_document(document_path, schema_path)
        document = load_strict(document_path)
        _validate_manifest_member_metadata(
            specs_root,
            member,
            document_path,
            document,
        )
        if member["role"] != "cross-level":
            markdown_path = document_path.with_suffix(".md")
            expected_markdown = render_markdown(document)
            try:
                actual_markdown = markdown_path.read_text(encoding="utf-8")
            except OSError as exc:
                raise ProjectionValidationError(
                    f"{document['specification']['id']}: cannot read projection "
                    f"{markdown_path}: {exc}"
                ) from exc
            if actual_markdown != expected_markdown:
                raise ProjectionValidationError(
                    f"{document['specification']['id']}: deterministic Markdown "
                    f"projection differs at {markdown_path}"
                )
            level_records.append((document_path, document))
        records.append((document_path, document))

    validate_hierarchy(level_records, levels_root=levels_root)
    for document_path, document in records:
        relative = document_path.relative_to(specs_root).as_posix()
        member = members_by_path[relative]
        actual_identity = _sha256_file(document_path)
        if actual_identity != member["content_sha256"]:
            raise SpecificationManifestError(
                f"{member['id']}: manifest content_sha256 conflicts with "
                "authoritative JSON bytes"
            )
    if len(records) != len(manifest["members"]):
        present = {document["specification"]["id"] for _path, document in records}
        missing = sorted(
            member["id"] for member in manifest["members"] if member["id"] not in present
        )
        raise SpecificationManifestError(
            f"normative manifest members are missing from repository: {missing}"
        )

    source_layout_document = next(
        (
            document
            for _path, document in records
            if document.get("specification", {}).get("id")
            == "GVE-SOURCE-LAYOUT"
        ),
        None,
    )
    if source_layout_document is not None:
        validate_source_layout(specs_root.parent, source_layout_document)

    return build_specification_revision([document for _path, document in records])


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the accepted GVE normative specification set."
    )
    parser.add_argument(
        "--specs-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="specs directory to validate (default: repository specs directory)",
    )
    args = parser.parse_args(argv)
    try:
        validate_specification_set(args.specs_root)
        source_layout_path = (
            args.specs_root
            / "source-layout"
            / "GVE-SOURCE-LAYOUT.json"
        )
        source_layout_evidence = (
            validate_source_layout(
                args.specs_root.resolve().parent,
                load_strict(source_layout_path),
            )
            if source_layout_path.is_file()
            else None
        )
    except (
        ProjectionValidationError,
        RuntimeError,
        SchemaValidationError,
        SemanticValidationError,
        SpecificationManifestError,
        SpecificationRevisionError,
        SourceLayoutValidationError,
        StrictJSONError,
    ) as exc:
        print(f"specification validation failed: {exc}", file=sys.stderr)
        return 1
    if source_layout_evidence is not None:
        grandfathered = source_layout_evidence["grandfathered_paths"]
        print(
            "grandfathered maintained Python paths: "
            + (", ".join(grandfathered) if grandfathered else "none")
        )
    print("specification validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
