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


    def test_record_rejects_empty_governing_actor(self) -> None:
        assertion = self.assertion("execution", "execution", "attempted")
        assertion["governing_actor"] = "  "
        self.assert_record_rejected(
            {"assertions": [assertion]},
            "requires an attributable governing actor",
        )

    def test_record_rejects_missing_assertion_timestamp(self) -> None:
        assertion = self.assertion("execution", "execution", "attempted")
        assertion["asserted_at"] = None
        self.assert_record_rejected(
            {"assertions": [assertion]},
            "requires an assertion timestamp",
        )

    def test_record_rejects_malformed_assertion_timestamp(self) -> None:
        assertion = self.assertion("execution", "execution", "attempted")
        assertion["asserted_at"] = "not-a-timestamp"
        self.assert_record_rejected(
            {"assertions": [assertion]},
            "timestamp must be valid ISO-8601",
        )

    def test_record_rejects_timezone_less_assertion_timestamp(self) -> None:
        assertion = self.assertion("execution", "execution", "attempted")
        assertion["asserted_at"] = "2026-07-25T00:00:00"
        self.assert_record_rejected(
            {"assertions": [assertion]},
            "timestamp must include a timezone",
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

    def test_record_rejects_orphaned_superseded_assertion(self) -> None:
        assertion = self.assertion("execution-1", "execution", "attempted")
        assertion["lineage_status"] = "superseded"
        self.assert_record_rejected(
            {"assertions": [assertion]},
            "superseded assertion requires a successor",
        )

    def test_record_rejects_forked_supersession(self) -> None:
        prior = self.assertion("execution-1", "execution", "attempted")
        prior["lineage_status"] = "superseded"
        successor_1 = self.assertion("execution-2", "execution", "partial")
        successor_1["supersedes_assertion_id"] = "execution-1"
        successor_1["correction_reason"] = "first correction"
        successor_1["admitted_evidence_ids"] = ["evidence-2"]
        successor_1["lineage_status"] = "superseded"
        successor_2 = self.assertion("execution-3", "execution", "completed")
        successor_2["supersedes_assertion_id"] = "execution-1"
        successor_2["correction_reason"] = "second correction"
        successor_2["admitted_evidence_ids"] = ["evidence-3"]
        self.assert_record_rejected(
            {"assertions": [prior, successor_1, successor_2]},
            "exactly one successor",
        )

    def test_record_rejects_self_cycle(self) -> None:
        assertion = self.assertion("execution-1", "execution", "attempted")
        assertion["lineage_status"] = "superseded"
        assertion["supersedes_assertion_id"] = "execution-1"
        assertion["correction_reason"] = "invalid cycle"
        self.assert_record_rejected(
            {"assertions": [assertion]},
            "lineage contains a cycle",
        )

    def test_record_rejects_nonterminal_current_assertion(self) -> None:
        prior = self.assertion("execution-1", "execution", "attempted")
        successor = self.assertion("execution-2", "execution", "completed")
        successor["supersedes_assertion_id"] = "execution-1"
        successor["correction_reason"] = "completion evidence arrived"
        successor["admitted_evidence_ids"] = ["evidence-2"]
        self.assert_record_rejected(
            {"assertions": [prior, successor]},
            "nonterminal assertion cannot remain current",
        )

    def test_authoritative_result_accepts_exact_current_state_and_evidence(self) -> None:
        assertion = self.assertion(
            "assertion-1",
            "authorization",
            "authorized",
            evidence=["evidence-1"],
        )
        record = {
            "assertions": [assertion],
            "authoritative_result": {
                "result_id": "result-1",
                "effect_id": "effect-1",
                "claimed_states": {"authorization": "authorized"},
                "admitted_assertion_ids": ["assertion-1"],
                "admitted_evidence_ids": ["evidence-1"],
                "governing_actor": "result-realizer",
                "governing_authority": "authoritative-governed-result-realizer",
                "realized_at": "2026-07-25T22:31:00Z",
            },
        }
        validate_effect_state_record(self.model, record)

    def test_authoritative_result_rejects_stronger_claim(self) -> None:
        assertion = self.assertion(
            "assertion-1",
            "authorization",
            "authorized",
            evidence=["evidence-1"],
        )
        record = {
            "assertions": [assertion],
            "authoritative_result": {
                "result_id": "result-1",
                "effect_id": "effect-1",
                "claimed_states": {"authorization": "refused"},
                "admitted_assertion_ids": ["assertion-1"],
                "admitted_evidence_ids": ["evidence-1"],
                "governing_actor": "result-realizer",
                "governing_authority": "authoritative-governed-result-realizer",
                "realized_at": "2026-07-25T22:31:00Z",
            },
        }
        with self.assertRaisesRegex(
            SemanticValidationError,
            "claimed states do not exactly match current assertions",
        ):
            validate_effect_state_record(self.model, record)



if __name__ == "__main__":
    unittest.main()
