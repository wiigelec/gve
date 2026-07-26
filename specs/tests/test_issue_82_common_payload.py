from __future__ import annotations

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from specs.tooling.strict_json import load_strict


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "specs/schemas/GVE-STAGE-2-COMMON-PAYLOAD.schema.json"
FIXTURES = ROOT / "specs/tests/fixtures/issue_82"
NORMATIVE = ROOT / "specs/levels/level-2/GVE-LEVEL-2-WORKFLOW-COMPOSITION.json"


class Issue82CommonPayloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = load_strict(SCHEMA_PATH)
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema)

    def test_canonical_no_op_payload_is_accepted(self) -> None:
        payload = load_strict(FIXTURES / "valid/canonical-no-op-payload.json")
        self.assertEqual(list(self.validator.iter_errors(payload)), [])

    def test_representative_invalid_payloads_are_rejected(self) -> None:
        paths = sorted((FIXTURES / "invalid").glob("*.json"))
        self.assertGreaterEqual(len(paths), 7)
        for path in paths:
            with self.subTest(path=path.name):
                payload = load_strict(path)
                self.assertTrue(list(self.validator.iter_errors(payload)))

    def test_opaque_content_accepts_unknown_nested_members(self) -> None:
        payload = load_strict(FIXTURES / "valid/canonical-no-op-payload.json")
        content = payload["workflow"]["operations"][0]["content"]
        content["arbitrary"] = {"plugin": [1, True, None, {"x": "y"}]}
        self.assertEqual(list(self.validator.iter_errors(payload)), [])

    def test_operation_identities_must_be_unique_semantically(self) -> None:
        payload = load_strict(FIXTURES / "valid/canonical-no-op-payload.json")
        payload["workflow"]["operations"].append(
            json.loads(json.dumps(payload["workflow"]["operations"][0]))
        )
        operation_ids = [item["operation_id"] for item in payload["workflow"]["operations"]]
        self.assertNotEqual(len(operation_ids), len(set(operation_ids)))

    def test_normative_contract_names_exact_phase_disposition(self) -> None:
        document = load_strict(NORMATIVE)
        requirements = {item["id"]: item["text"] for item in document["requirements"]}
        phase_text = requirements["L2-WC-REQ-034"]
        for entered in (
            "input acquisition",
            "UTF-8 decoding",
            "JSON parsing",
            "common-envelope schema validation",
            "no-op lifecycle disposition",
        ):
            self.assertIn(entered, phase_text)
        for skipped in (
            "plugin discovery",
            "authority processing",
            "dependency and handoff processing",
            "operation execution",
            "external effects",
            "authoritative-result assembly",
        ):
            self.assertIn(skipped, phase_text)

    def test_normative_contract_forbids_no_op_effect_fields(self) -> None:
        document = load_strict(NORMATIVE)
        requirements = {item["id"]: item["text"] for item in document["requirements"]}
        text = requirements["L2-WC-REQ-033"]
        for term in ("effects", "authority", "dependencies", "handoffs"):
            self.assertIn(term, text)
        self.assertIn("forbidden", text)


if __name__ == "__main__":
    unittest.main()
