from __future__ import annotations

import copy
import unittest
from pathlib import Path

from specs.tooling.semantics import (
    SemanticValidationError,
    validate_effect_state_model,
    validate_effect_state_record,
)
from specs.tooling.strict_json import load_strict


ROOT = Path(__file__).resolve().parents[1]
ERR = ROOT / "levels/level-3/GVE-LEVEL-3-EVIDENCE-RESULT-REALIZATION.json"


class Issue75EffectStateSemanticValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = load_strict(ERR)
        cls.model = cls.document["effect_state_model"]
        cls.specification_id = cls.document["specification"]["id"]
        cls.authorities = {
            dimension["id"]: dimension["assertion_authority"]
            for dimension in cls.model["dimensions"]
        }

    def assertion(
        self,
        assertion_id: str,
        dimension: str,
        value: str,
        *,
        effect_id: str = "effect-1",
        evidence: list[str] | None = None,
        uncertainty: str | None = None,
    ) -> dict:
        return {
            "assertion_id": assertion_id,
            "effect_id": effect_id,
            "dimension": dimension,
            "value": value,
            "governing_actor": f"actor-{dimension}",
            "governing_authority": self.authorities[dimension],
            "admitted_evidence_ids": evidence or [f"evidence-{assertion_id}"],
            "asserted_at": "2026-07-25T00:00:00Z",
            "uncertainty": uncertainty,
            "supersedes_assertion_id": None,
            "correction_reason": None,
            "lineage_status": "current",
        }

    def assert_model_rejected(self, model: dict, expected: str) -> None:
        with self.assertRaisesRegex(SemanticValidationError, expected):
            validate_effect_state_model(self.specification_id, model)

    def assert_record_rejected(self, record: dict, expected: str) -> None:
        with self.assertRaisesRegex(SemanticValidationError, expected):
            validate_effect_state_record(self.model, record)

    def test_normative_model_passes_semantic_validation(self) -> None:
        validate_effect_state_model(self.specification_id, self.model)

    def test_model_rejects_missing_dimension(self) -> None:
        model = copy.deepcopy(self.model)
        model["dimensions"] = model["dimensions"][:-1]
        self.assert_model_rejected(model, "dimensions or permitted values")

    def test_model_rejects_value_under_wrong_dimension(self) -> None:
        model = copy.deepcopy(self.model)
        model["dimensions"][0]["values"][0]["id"] = "verified"
        self.assert_model_rejected(model, "dimensions or permitted values")

    def test_model_rejects_missing_required_implication(self) -> None:
        model = copy.deepcopy(self.model)
        model["implications"] = []
        self.assert_model_rejected(model, "verified-implies-observed")

    def test_model_rejects_empty_transition_evidence_requirement(self) -> None:
        model = copy.deepcopy(self.model)
        model["dimensions"][2]["values"][1]["evidence_requirement"] = ""
        self.assert_model_rejected(model, "empty evidence requirement")

    def test_explicit_record_passes_semantic_validation(self) -> None:
        validate_effect_state_record(
            self.model,
            {
                "assertions": [
                    self.assertion("request", "request", "requested"),
                    self.assertion("authorization", "authorization", "authorized"),
                    self.assertion("execution", "execution", "attempted"),
                    self.assertion("observation", "observation", "unobserved"),
                    self.assertion("verification", "verification", "unverified"),
                ]
            },
        )

    def test_record_rejects_value_outside_dimension(self) -> None:
        assertion = self.assertion("execution", "execution", "attempted")
        assertion["value"] = "verified"
        self.assert_record_rejected(
            {"assertions": [assertion]},
            "value verified outside dimension execution",
        )

    def test_record_rejects_verified_without_observed(self) -> None:
        verification = self.assertion("verification", "verification", "verified")
        verification["verified_claim_id"] = "claim-1"
        verification["verification_evidence_ids"] = verification[
            "admitted_evidence_ids"
        ]
        self.assert_record_rejected(
            {
                "assertions": [
                    self.assertion("observation", "observation", "unobserved"),
                    verification,
                ]
            },
            "prohibited state combination|verified-implies-observed",
        )

    def test_record_rejects_indeterminate_without_uncertainty(self) -> None:
        assertion = self.assertion(
            "execution", "execution", "indeterminate", uncertainty=None
        )
        self.assert_record_rejected(
            {"assertions": [assertion]},
            "indeterminate assertion requires uncertainty",
        )

    def test_record_rejects_multiple_current_heads(self) -> None:
        self.assert_record_rejected(
            {
                "assertions": [
                    self.assertion("execution-1", "execution", "attempted"),
                    self.assertion("execution-2", "execution", "completed"),
                ]
            },
            "multiple current heads",
        )


if __name__ == "__main__":
    unittest.main()
