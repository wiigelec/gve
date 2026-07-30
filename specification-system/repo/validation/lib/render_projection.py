from __future__ import annotations

import json
from pathlib import PurePosixPath
from typing import Any, Mapping


EXCLUDED_FIELDS = frozenset({
    "construction_identity",
    "construction_status",
    "normative",
    "responsibility",
    "expected_relationships",
    "unresolved_questions",
})

SECTION_ORDER = [
    "repository_area_kinds",
    "authority_classifications",
    "lifecycle_classifications",
    "tree_entry_kinds",
    "ownership_roles",
    "entity_types",
    "entity_constraints",
    "relationship_types",
    "relationship_rules",
    "authority_separation",
    "decision_basis",
    "functional_areas",
    "area_semantics",
    "kernel_classifications",
    "extension_rules",
    "placement_rules",
    "level_definitions",
    "level_root_artifacts",
    "subordinate_artifacts",
    "dependency_rules",
    "cross_level_references",
    "manifest_requirements",
    "schema_requirements",
    "conformance_requirements",
    "derived_projection_rules",
    "completeness_criteria",
    "artifact_classes",
    "class_constraints",
    "classification_boundary",
    "candidate_families",
    "family_bindings",
    "manifest_model",
    "revision_model",
    "binding_model",
    "manifest_separation",
    "record_contracts",
    "records",
    "dependency_relation",
    "classification_rules",
    "path_rules",
    "containment_rules",
    "ownership_rules",
    "tree_model_boundary",
    "artifact_roles",
    "role_constraints",
    "overview_model",
    "plan_model",
    "role_relationships",
    "unavailable_capabilities",
    "coverage_contract",
    "execution_contract",
    "diagnostic_contract",
    "authority_boundary",
    "vector_classes",
    "conformance_scope",
    "vector_envelope",
    "uniqueness_constraints",
    "coverage_requirements",
    "failure_precedence",
    "fixture_integration",
    "product_independence",
]


def _json_value(value: object, indent: int = 2) -> str:
    return json.dumps(value, indent=indent, ensure_ascii=False)


def _sections(value: Mapping[str, Any], source_path: str) -> list[str]:
    lines: list[str] = []
    for key in SECTION_ORDER:
        if key not in value:
            continue
        item = value[key]
        title = " ".join(word.capitalize() for word in key.replace("-", " ").split())
        lines.extend(["", f"## {title}", ""])

        if isinstance(item, str):
            lines.append(item)
            lines.append("")
        elif isinstance(item, bool):
            lines.append("Yes" if item else "No")
            lines.append("")
        elif isinstance(item, list):
            if all(isinstance(e, str) for e in item):
                for entry in item:
                    lines.append(f"- `{entry}`")
                lines.append("")
            elif all(isinstance(e, dict) for e in item):
                for entry in item:
                    entry_id = (
                        entry.get("id") or entry.get("name") or entry.get("kind") or str(entry.get("decision", ""))
                    )
                    header = f"### {entry_id}"
                    if entry_id in lines:
                        header = f"### {entry_id} (duplicate)"
                    lines.append(header)
                    lines.append("")
                    for k, v in entry.items():
                        if k in ("id", "name"):
                            continue
                        if isinstance(v, str):
                            lines.append(f"- **{k}:** {v}")
                        elif isinstance(v, list):
                            items_str = ", ".join(f"`{x}`" for x in v)
                            lines.append(f"- **{k}:** {items_str}")
                        elif isinstance(v, bool):
                            lines.append(f"- **{k}:** {'Yes' if v else 'No'}")
                        elif isinstance(v, dict):
                            lines.append(f"- **{k}:**")
                            for sk, sv in v.items():
                                if isinstance(sv, str):
                                    lines.append(f"  - {sk}: {sv}")
                                elif isinstance(sv, list):
                                    items = ", ".join(f"`{x}`" for x in sv)
                                    lines.append(f"  - {sk}: [{items}]")
                                elif isinstance(sv, bool):
                                    lines.append(f"  - {sk}: {'Yes' if sv else 'No'}")
                                else:
                                    lines.append(f"  - {sk}: `{_json_value(sv)}`")
                        else:
                            lines.append(f"- **{k}:** `{_json_value(v)}`")
                    lines.append("")
            else:
                for entry in item:
                    lines.append(f"- {entry}")
                lines.append("")
        elif isinstance(item, dict):
            for k, v in item.items():
                pretty_key = " ".join(word.capitalize() for word in k.replace("-", " ").split())
                if isinstance(v, str):
                    lines.append(f"- **{pretty_key}:** {v}")
                elif isinstance(v, list):
                    items = "\n".join(f"  - {x}" if isinstance(x, str) else f"  - `{_json_value(x)}`" for x in v)
                    lines.append(f"- **{pretty_key}:**\n{items}")
                elif isinstance(v, bool):
                    lines.append(f"- **{pretty_key}:** {'Yes' if v else 'No'}")
                elif isinstance(v, dict):
                    lines.append(f"- **{pretty_key}:**")
                    for sk, sv in v.items():
                        if isinstance(sv, str):
                            lines.append(f"  - **{sk}:** {sv}")
                        elif isinstance(sv, list):
                            sv_items = ", ".join(f"`{x}`" for x in sv)
                            lines.append(f"  - **{sk}:** [{sv_items}]")
                        elif isinstance(sv, dict):
                            lines.append(f"  - **{sk}:** `{_json_value(sv)}`")
                        elif isinstance(sv, bool):
                            lines.append(f"  - **{sk}:** {'Yes' if sv else 'No'}")
                        else:
                            lines.append(f"  - **{sk}:** `{_json_value(sv)}`")
                else:
                    lines.append(f"- **{pretty_key}:** `{_json_value(v)}`")
            lines.append("")

    remaining = sorted(set(value) - EXCLUDED_FIELDS - set(SECTION_ORDER))
    for key in remaining:
        item = value[key]
        title = " ".join(word.capitalize() for word in key.replace("-", " ").split())
        lines.extend(["", f"## {title}", ""])
        if isinstance(item, str):
            lines.append(item)
        elif isinstance(item, list):
            for entry in item:
                lines.append(f"- {_json_value(entry)}")
        elif isinstance(item, dict):
            lines.append(f"```json\n{_json_value(item)}\n```")
        elif isinstance(item, bool):
            lines.append("Yes" if item else "No")
        else:
            lines.append(_json_value(item))
        lines.append("")

    return lines


def render_document(value: Mapping[str, Any], source_path: str) -> str:
    identity = value.get("construction_identity", "unknown")
    title = " ".join(word.capitalize() for word in identity.replace("-", " ").split())
    source_name = PurePosixPath(source_path).name
    status = value.get("construction_status", "unknown")
    normative = value.get("normative", None)
    responsibility = value.get("responsibility", "")

    lines = [
        f"# {title}",
        "",
        f"> Generated deterministically from `{source_name}`. "
        "Do not edit this file independently. The authoritative JSON "
        "construction artifact remains controlling.",
        "",
        f"**Construction identity:** `{identity}`  ",
        f"**Construction status:** `{status}`  ",
        f"**Normative:** {'Yes' if normative else 'No'}  ",
        f"**Source:** `{source_path}`",
        "",
    ]

    if responsibility:
        lines.extend(["## Responsibility", "", responsibility, ""])

    lines.extend(_sections(value, source_path))

    relationships = value.get("expected_relationships", [])
    if relationships:
        lines.extend(["", "## Expected Relationships", ""])
        for rel in relationships:
            lines.append(f"- {rel}")
        lines.append("")

    unresolved = value.get("unresolved_questions", [])
    if unresolved:
        lines.extend(["", "## Unresolved Questions", ""])
        for q in unresolved:
            lines.append(f"- {q}")
        lines.append("")

    return "\n".join(lines) + "\n"
