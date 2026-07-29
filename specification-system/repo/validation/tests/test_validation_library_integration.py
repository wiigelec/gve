from __future__ import annotations

import ast
import json
import unittest
from pathlib import Path


CONSTRUCTION_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = CONSTRUCTION_ROOT / "REPOSITORY-SPECIFICATION-SET.json"
VALIDATION_MODEL_PATH = (
    CONSTRUCTION_ROOT / "validation/lib/VALIDATION-LIBRARY.json"
)
IDENTITY_VALIDATOR_PATH = (
    CONSTRUCTION_ROOT / "validation/intrinsic/validate_identity_construction.py"
)


class ValidationLibraryConstructionTests(unittest.TestCase):
    def test_construction_model_is_closed_and_non_placeholder(self) -> None:
        model = json.loads(VALIDATION_MODEL_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            set(model),
            {
                "construction_identity",
                "construction_status",
                "responsibility",
                "normative",
                "module_inventory",
                "dependency_direction",
                "api_contracts",
                "diagnostic_contract",
                "fail_closed_behavior",
                "product_independence",
                "integration_responsibilities",
                "retained_intrinsic_behavior",
                "unavailable_capabilities",
                "authority_boundary",
                "expected_relationships",
                "unresolved_questions",
            },
        )
        self.assertEqual(
            model["construction_identity"], "validation-library-construction"
        )
        self.assertEqual(model["construction_status"], "under-construction")
        self.assertIs(model["normative"], False)
        self.assertEqual(
            [item["module"] for item in model["module_inventory"]],
            [
                "validation.lib.strict_json",
                "validation.lib.canonical_json",
                "validation.lib.contracts",
                "validation.lib.identity",
            ],
        )
        self.assertEqual(
            model["diagnostic_contract"]["representation"],
            "deterministic-string",
        )
        self.assertIs(
            model["authority_boundary"]["accepted-product-authority"], False
        )

    def test_manifest_declares_validation_library_construction(self) -> None:
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertIn(
            "validation-library-construction", manifest["artifact_classes"]
        )
        self.assertNotIn(
            "validation-library-placeholder", manifest["artifact_classes"]
        )

    def test_executable_identity_validator_delegates_behavior(self) -> None:
        tree = ast.parse(
            IDENTITY_VALIDATOR_PATH.read_text(encoding="utf-8"),
            filename=str(IDENTITY_VALIDATOR_PATH),
        )
        calls = {
            node.func.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        }
        self.assertIn("reusable_build_behavior_registry", calls)
        self.assertIn("reusable_evaluate_behavior", calls)


if __name__ == "__main__":
    unittest.main()
