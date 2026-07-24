"""Final acceptance audit for the accepted GVE Level 2 specification set."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from .render import render_markdown
from .strict_json import load_strict
from .validate import discover_specifications


class LevelTwoAuditError(ValueError):
    """Raised when accepted Level 2 authority is incomplete or ambiguous."""


EXPECTED_LEVEL_TWO_DOCUMENTS = {
    "GVE-LEVEL-2",
    "GVE-LEVEL-2-DOCUMENT-AUTHORITY",
    "GVE-LEVEL-2-WORKFLOW-COMPOSITION",
    "GVE-LEVEL-2-DEPENDENCIES-HANDOFFS",
    "GVE-LEVEL-2-RESULT-ASSEMBLY",
    "GVE-LEVEL-2-LOCAL-PLUGIN-BOUNDARIES",
}

REQUIRED_DEFINITIONS = {
    "GVE-LEVEL-2": {
        "LEVEL-2-ROOT",
        "LEVEL-2-SPECIFICATION-SET",
        "LEVEL-2-COMPOSITION-LAYER",
        "LEVEL-2-DOCUMENT-AUTHORITY",
        "LEVEL-2-WORKFLOW-COMPOSITION",
        "LEVEL-2-DEPENDENCIES-HANDOFFS",
        "LEVEL-2-RESULT-ASSEMBLY",
        "LEVEL-2-LOCAL-PLUGIN-BOUNDARIES",
    },
    "GVE-LEVEL-2-DOCUMENT-AUTHORITY": {
        "L2-DA-IMPORT",
        "L2-DA-DETERMINISTIC-RESOLUTION",
        "L2-DA-CONFLICT",
        "L2-DA-RELATIONSHIP-VISIBILITY",
    },
    "GVE-LEVEL-2-WORKFLOW-COMPOSITION": {
        "L2-WC-OPERATION-IDENTITY",
        "L2-WC-PLUGIN-BINDING",
        "L2-WC-CONTRACT-ATTRIBUTION",
        "L2-WC-CONTRACT-FRESHNESS",
        "L2-WC-PLAN-ACCEPTANCE",
        "L2-WC-PLUGIN-MEANING-BOUNDARY",
    },
    "GVE-LEVEL-2-DEPENDENCIES-HANDOFFS": {
        "L2-DH-OPERATION-DEPENDENCY",
        "L2-DH-HANDOFF-DECLARATION",
        "L2-DH-ACTUAL-HANDOFF",
        "L2-DH-BLOCKED-OPERATION",
        "L2-DH-SKIPPED-OPERATION",
        "L2-DH-FAILED-OPERATION",
        "L2-DH-UNATTEMPTED-OPERATION",
        "L2-DH-PARTIAL-PROGRESS",
    },
    "GVE-LEVEL-2-RESULT-ASSEMBLY": {
        "L2-RA-OPERATION-RESULT",
        "L2-RA-OPERATION-EVIDENCE",
        "L2-RA-AUTHORITATIVE-WORKFLOW-RESULT",
        "L2-RA-PREEXECUTION-FAILURE-RESULT",
        "L2-RA-PARTIAL-EFFECT",
        "L2-RA-INCOMPLETE-EVIDENCE",
        "L2-RA-RESULT-TRACEABILITY",
    },
    "GVE-LEVEL-2-LOCAL-PLUGIN-BOUNDARIES": {
        "L2-LPB-FILESYSTEM-DOMAIN",
        "L2-LPB-COMMAND-DOMAIN",
        "L2-LPB-LOCAL-GIT-DOMAIN",
        "L2-LPB-DETERMINISTIC-ASSIGNMENT",
        "L2-LPB-DOMAIN-NONOVERLAP",
        "L2-LPB-CORE-DOMAIN-BOUNDARY",
        "L2-LPB-FOLLOWON-WORK",
    },
}

REQUIRED_REQUIREMENTS = {
    "GVE-LEVEL-2": {
        "L2-ROOT-REQ-001",
        "L2-ROOT-REQ-003",
        "L2-ROOT-REQ-005",
        "L2-ROOT-REQ-006",
        "L2-ROOT-REQ-009",
    },
    "GVE-LEVEL-2-DOCUMENT-AUTHORITY": {
        "L2-DA-REQ-002",
        "L2-DA-REQ-004",
        "L2-DA-REQ-006",
        "L2-DA-REQ-007",
        "L2-DA-REQ-008",
        "L2-DA-REQ-009",
        "L2-DA-REQ-011",
    },
    "GVE-LEVEL-2-WORKFLOW-COMPOSITION": {
        "L2-WC-REQ-003",
        "L2-WC-REQ-004",
        "L2-WC-REQ-005",
        "L2-WC-REQ-006",
        "L2-WC-REQ-008",
        "L2-WC-REQ-009",
        "L2-WC-REQ-010",
        "L2-WC-REQ-011",
        "L2-WC-REQ-014",
    },
    "GVE-LEVEL-2-DEPENDENCIES-HANDOFFS": {
        "L2-DH-REQ-004",
        "L2-DH-REQ-005",
        "L2-DH-REQ-007",
        "L2-DH-REQ-008",
        "L2-DH-REQ-009",
        "L2-DH-REQ-010",
        "L2-DH-REQ-011",
        "L2-DH-REQ-012",
        "L2-DH-REQ-014",
        "L2-DH-REQ-015",
        "L2-DH-REQ-016",
    },
    "GVE-LEVEL-2-RESULT-ASSEMBLY": {
        "L2-RA-REQ-001",
        "L2-RA-REQ-004",
        "L2-RA-REQ-005",
        "L2-RA-REQ-006",
        "L2-RA-REQ-007",
        "L2-RA-REQ-011",
        "L2-RA-REQ-012",
        "L2-RA-REQ-013",
        "L2-RA-REQ-014",
        "L2-RA-REQ-015",
        "L2-RA-REQ-016",
        "L2-RA-REQ-018",
    },
    "GVE-LEVEL-2-LOCAL-PLUGIN-BOUNDARIES": {
        "L2-LPB-REQ-001",
        "L2-LPB-REQ-002",
        "L2-LPB-REQ-003",
        "L2-LPB-REQ-004",
        "L2-LPB-REQ-005",
        "L2-LPB-REQ-006",
        "L2-LPB-REQ-007",
        "L2-LPB-REQ-008",
        "L2-LPB-REQ-009",
        "L2-LPB-REQ-010",
        "L2-LPB-REQ-011",
        "L2-LPB-REQ-013",
        "L2-LPB-REQ-014",
        "L2-LPB-REQ-015",
        "L2-LPB-REQ-016",
        "L2-LPB-REQ-017",
    },
}


def _ids(document: Mapping[str, Any], field: str) -> set[str]:
    return {item["id"] for item in document[field]}


def audit_level_two(specs_root: Path) -> dict[str, Any]:
    """Audit accepted Level 2 discovery, projection, and semantic safeguards."""
    paths = discover_specifications(specs_root)
    level_two_paths = [
        path for path in paths if path.parent.name == "level-2"
    ]
    documents = {
        document["specification"]["id"]: (path, document)
        for path in level_two_paths
        for document in [load_strict(path)]
    }

    discovered = set(documents)
    if discovered != EXPECTED_LEVEL_TWO_DOCUMENTS:
        missing = sorted(EXPECTED_LEVEL_TWO_DOCUMENTS - discovered)
        unexpected = sorted(discovered - EXPECTED_LEVEL_TWO_DOCUMENTS)
        raise LevelTwoAuditError(
            f"Level 2 discovery mismatch; missing={missing}, unexpected={unexpected}"
        )

    for specification_id in sorted(EXPECTED_LEVEL_TWO_DOCUMENTS):
        path, document = documents[specification_id]
        markdown_path = path.with_suffix(".md")
        try:
            actual_markdown = markdown_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise LevelTwoAuditError(
                f"{specification_id}: cannot read deterministic projection: {exc}"
            ) from exc
        expected_markdown = render_markdown(document)
        if actual_markdown != expected_markdown:
            raise LevelTwoAuditError(
                f"{specification_id}: deterministic Markdown projection drift"
            )

        definitions = _ids(document, "definitions")
        missing_definitions = sorted(
            REQUIRED_DEFINITIONS[specification_id] - definitions
        )
        if missing_definitions:
            raise LevelTwoAuditError(
                f"{specification_id}: missing required definitions "
                f"{missing_definitions}"
            )

        requirements = _ids(document, "requirements")
        missing_requirements = sorted(
            REQUIRED_REQUIREMENTS[specification_id] - requirements
        )
        if missing_requirements:
            raise LevelTwoAuditError(
                f"{specification_id}: missing required requirements "
                f"{missing_requirements}"
            )

    local_boundaries = documents[
        "GVE-LEVEL-2-LOCAL-PLUGIN-BOUNDARIES"
    ][1]
    requirement_text = {
        item["id"]: item["text"] for item in local_boundaries["requirements"]
    }
    if "exactly one eligible plugin domain" not in requirement_text["L2-LPB-REQ-002"]:
        raise LevelTwoAuditError(
            "local plugin boundaries no longer require unique domain assignment"
        )
    if "must not interpret" not in requirement_text["L2-LPB-REQ-010"]:
        raise LevelTwoAuditError(
            "local plugin boundaries no longer prohibit core domain interpretation"
        )
    if "must fail specification validation closed" not in requirement_text[
        "L2-LPB-REQ-013"
    ]:
        raise LevelTwoAuditError(
            "local plugin boundaries no longer reject overlapping ownership"
        )

    result_assembly = documents["GVE-LEVEL-2-RESULT-ASSEMBLY"][1]
    result_text = {
        item["id"]: item["text"] for item in result_assembly["requirements"]
    }
    required_states = (
        "Requested, authorized, attempted, completed, observed, and verified"
    )
    if required_states not in result_text["L2-RA-REQ-004"]:
        raise LevelTwoAuditError(
            "result assembly no longer preserves inherited effect-state distinctions"
        )

    return {
        "documents": sorted(discovered),
        "document_count": len(discovered),
        "projection_count": len(discovered),
        "status": "passed",
    }
