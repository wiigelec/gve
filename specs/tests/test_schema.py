from __future__ import annotations

import unittest
from pathlib import Path

from specs.tooling.validate import SchemaValidationError, validate_document


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "GVE-LEVEL.schema.json"
FIXTURES = ROOT / "tests" / "fixtures"


class SchemaTests(unittest.TestCase):
    def test_shared_schema_is_valid_and_accepts_fixture(self) -> None:
        validate_document(
            FIXTURES / "valid" / "non_normative_level.json",
            SCHEMA,
        )

    def test_shared_schema_rejects_unknown_field(self) -> None:
        with self.assertRaisesRegex(SchemaValidationError, "unexpected"):
            validate_document(
                FIXTURES / "invalid" / "unknown_field.json",
                SCHEMA,
            )


if __name__ == "__main__":
    unittest.main()
