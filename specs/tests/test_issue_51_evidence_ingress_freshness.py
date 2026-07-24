from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def by_id(items: list[dict], identifier: str) -> dict:
    return next(item for item in items if item.get("id") == identifier)


class Issue51EvidenceIngressFreshnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.level2_result = load(
            "specs/levels/level-2/GVE-LEVEL-2-RESULT-ASSEMBLY.json"
        )
        cls.level3_evidence = load(
            "specs/levels/level-3/"
            "GVE-LEVEL-3-EVIDENCE-RESULT-REALIZATION.json"
        )
        cls.level3_contracts = load(
            "specs/levels/level-3/GVE-LEVEL-3-PLUGIN-ACTION-CONTRACTS.json"
        )

    def test_evidence_ingress_and_disposition_are_explicit(self) -> None:
        definitions = self.level3_evidence["definitions"]
        ingress = by_id(definitions, "L3-ERR-EVIDENCE-INGRESS")
        disposition = by_id(definitions, "L3-ERR-EVIDENCE-DISPOSITION")

        ingress_text = ingress["text"].lower()
        for phrase in (
            "produced or received",
            "durably recorded",
            "structurally classified",
            "provenance evaluated",
            "applicability evaluated",
        ):
            self.assertIn(phrase, ingress_text)

        disposition_text = disposition["text"].lower()
        self.assertIn("admitted or rejected with reason", disposition_text)
        self.assertIn("result realization", disposition_text)

    def test_admission_does_not_imply_claim_support(self) -> None:
        requirement = by_id(
            self.level3_evidence["requirements"],
            "L3-ERR-REQ-EVIDENCE-ADMISSION",
        )
        text = requirement["text"].lower()
        self.assertIn("admission does not imply support", text)
        self.assertIn("contradictory evidence", text)
        self.assertIn("admitted", text)
        self.assertIn("unresolved", text)

    def test_all_claim_relevant_received_evidence_retains_disposition(self) -> None:
        requirement = by_id(
            self.level3_evidence["requirements"],
            "L3-ERR-REQ-EVIDENCE-DISPOSITION-COMPLETENESS",
        )
        text = requirement["text"].lower()
        for phrase in (
            "every",
            "claim-relevant",
            "received evidence",
            "attributable disposition",
            "rejected",
            "malformed",
            "stale",
            "unauthorized",
            "contradictory",
            "inapplicable",
        ):
            self.assertIn(phrase, text)

    def test_freshness_binds_stable_governed_identities(self) -> None:
        requirement = by_id(
            self.level3_contracts["requirements"],
            "L3-PAC-REQ-FRESHNESS-BINDING-IDENTITIES",
        )
        text = requirement["text"].lower()
        for phrase in (
            "operation content",
            "selected plugin identity",
            "governed instruction set revision",
            "governing authority context",
            "workflow-plan attempt",
            "result-realization attempt",
            "observation context",
            "freshness boundary",
        ):
            self.assertIn(phrase, text)
        self.assertIn("stable", text)
        self.assertNotIn("sha-256", text)
        self.assertNotIn("database", text)

    def test_result_assembly_preserves_non_admitted_evidence(self) -> None:
        serialized = json.dumps(self.level2_result, ensure_ascii=False).lower()
        self.assertIn("evidence disposition", serialized)
        self.assertIn("rejected evidence", serialized)
        self.assertIn("admission does not imply support", serialized)
        self.assertNotIn("complete accepted evidence set", serialized)


if __name__ == "__main__":
    unittest.main()
