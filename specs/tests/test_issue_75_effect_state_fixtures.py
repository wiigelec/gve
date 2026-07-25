from __future__ import annotations

import unittest
from pathlib import Path

from specs.tooling.semantics import (
    SemanticValidationError,
    validate_effect_state_record,
)
from specs.tooling.strict_json import load_strict


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = (
    ROOT
    / "levels/level-3/GVE-LEVEL-3-EVIDENCE-RESULT-REALIZATION.json"
)
FIXTURE_PATH = ROOT / "tests/fixtures/issue_75/effect_state_records.json"


class Issue75EffectStateFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.model = load_strict(MODEL_PATH)["effect_state_model"]
        cls.fixtures = load_strict(FIXTURE_PATH)

    def test_fixture_inventory_matches_issue_75(self) -> None:
        self.assertEqual(
            [case["name"] for case in self.fixtures["valid_cases"]],
            [
                "authorized_effect",
                "attempted_effect",
                "completed_but_unobserved_effect",
                "observed_but_unverified_effect",
                "verified_observed_completion",
                "partial_execution",
                "indeterminate_execution",
                "correction",
                "supersession",
            ],
        )
        self.assertEqual(
            [case["name"] for case in self.fixtures["invalid_cases"]],
            [
                "authorized_treated_as_attempted",
                "authorized_treated_as_completed",
                "attempted_treated_as_completed",
                "completed_treated_as_observed",
                "completed_treated_as_verified",
                "verification_without_evidence",
                "contradictory_terminal_states",
                "omitted_uncertainty",
                "authoritative_result_stronger_than_admitted_evidence",
            ],
        )

    def test_positive_fixtures_are_accepted(self) -> None:
        for case in self.fixtures["valid_cases"]:
            with self.subTest(case=case["name"]):
                validate_effect_state_record(self.model, case["record"])

    def test_negative_fixtures_fail_closed(self) -> None:
        for case in self.fixtures["invalid_cases"]:
            with self.subTest(case=case["name"]):
                with self.assertRaisesRegex(
                    SemanticValidationError,
                    case["expected_error"],
                ):
                    validate_effect_state_record(self.model, case["record"])


if __name__ == "__main__":
    unittest.main()
