from __future__ import annotations

import unittest
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from specs.tooling.strict_json import StrictJSONError, load_strict


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "specs/schemas/GVE-STAGE-2-COMMON-PAYLOAD.schema.json"
FIXTURES = ROOT / "specs/tests/fixtures/issue_82"
NORMATIVE = ROOT / "specs/levels/level-2/GVE-LEVEL-2-WORKFLOW-COMPOSITION.json"

EXACT_PHASE_REQUIREMENT = (
    "For a structurally valid no-op payload, the core must enter exactly input "
    "acquisition, UTF-8 decoding, JSON parsing, common-envelope schema validation, "
    "workflow and operation identity validation, routing-envelope validation, "
    "opaque-content boundary validation, and no-op lifecycle disposition. It must "
    "explicitly skip plugin discovery, loading, assignment, or interpretation; "
    "validated-contract production; authority processing; dependency and handoff "
    "processing; workflow-plan acceptance; operation execution; external effects; "
    "evidence aggregation; and authoritative-result assembly. This requirement "
    "defines phase disposition only and does not define the result contract reserved "
    "for separately governed work."
)


def validate_common_payload(
    payload: dict[str, Any],
    validator: Draft202012Validator,
) -> list[str]:
    errors = sorted(
        validator.iter_errors(payload),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    messages = [error.message for error in errors]

    if not errors:
        operation_ids = [
            operation["operation_id"]
            for operation in payload["workflow"]["operations"]
        ]
        seen: set[str] = set()
        duplicates: list[str] = []
        for operation_id in operation_ids:
            if operation_id in seen and operation_id not in duplicates:
                duplicates.append(operation_id)
            seen.add(operation_id)
        messages.extend(
            f"duplicate operation_id: {operation_id}"
            for operation_id in duplicates
        )

    return messages


class Issue82CommonPayloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_strict(SCHEMA_PATH)
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema)

    def test_canonical_no_op_payload_is_accepted(self) -> None:
        payload = load_strict(FIXTURES / "valid/canonical-no-op-payload.json")
        self.assertEqual(validate_common_payload(payload, self.validator), [])

    def test_representative_invalid_payloads_are_rejected(self) -> None:
        paths = sorted((FIXTURES / "invalid").glob("*.json"))
        schema_or_semantic_paths = [
            path
            for path in paths
            if path.name != "duplicate-top-level-member.json"
        ]
        self.assertGreaterEqual(len(schema_or_semantic_paths), 10)
        for path in schema_or_semantic_paths:
            with self.subTest(path=path.name):
                payload = load_strict(path)
                self.assertTrue(validate_common_payload(payload, self.validator))

    def test_duplicate_json_member_is_rejected_during_strict_parsing(self) -> None:
        path = FIXTURES / "invalid/duplicate-top-level-member.json"
        with self.assertRaisesRegex(
            StrictJSONError,
            "duplicate object key: lifecycle",
        ):
            load_strict(path)

    def test_unknown_members_are_rejected_at_every_closed_boundary(self) -> None:
        for filename in (
            "unknown-top-level-member.json",
            "unknown-workflow-member.json",
            "unknown-operation-member.json",
            "unknown-plugin-member.json",
        ):
            with self.subTest(filename=filename):
                payload = load_strict(FIXTURES / "invalid" / filename)
                self.assertTrue(list(self.validator.iter_errors(payload)))

    def test_opaque_content_accepts_unknown_nested_members(self) -> None:
        payload = load_strict(FIXTURES / "valid/canonical-no-op-payload.json")
        content = payload["workflow"]["operations"][0]["content"]
        content["arbitrary"] = {"plugin": [1, True, None, {"x": "y"}]}
        self.assertEqual(validate_common_payload(payload, self.validator), [])

    def test_duplicate_operation_identity_is_rejected_semantically(self) -> None:
        payload = load_strict(FIXTURES / "invalid/duplicate-operation-id.json")
        self.assertEqual(list(self.validator.iter_errors(payload)), [])
        self.assertEqual(
            validate_common_payload(payload, self.validator),
            ["duplicate operation_id: operation-1"],
        )

    def test_normative_contract_names_exact_phase_disposition(self) -> None:
        document = load_strict(NORMATIVE)
        requirements = {item["id"]: item["text"] for item in document["requirements"]}
        self.assertEqual(requirements["L2-WC-REQ-034"], EXACT_PHASE_REQUIREMENT)

    def test_normative_contract_forbids_no_op_effect_fields(self) -> None:
        document = load_strict(NORMATIVE)
        requirements = {item["id"]: item["text"] for item in document["requirements"]}
        text = requirements["L2-WC-REQ-033"]
        for term in ("effects", "authority", "dependencies", "handoffs"):
            self.assertIn(term, text)
        self.assertIn("forbidden", text)


if __name__ == "__main__":
    unittest.main()
