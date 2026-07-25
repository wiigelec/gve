from __future__ import annotations

import unittest
from pathlib import Path

from specs.tooling.strict_json import load_strict

ROOT = Path(__file__).resolve().parents[1]
L0 = ROOT / "levels/level-0/GVE-LEVEL-0.json"
L1 = ROOT / "levels/level-1/GVE-LEVEL-1.json"
ERR = ROOT / "levels/level-3/GVE-LEVEL-3-EVIDENCE-RESULT-REALIZATION.json"

class Issue75EffectStateModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.l0 = load_strict(L0)
        cls.l1 = load_strict(L1)
        cls.err = load_strict(ERR)
        cls.l0_defs = {x["id"]: x["text"] for x in cls.l0["definitions"]}
        cls.l0_reqs = {x["id"]: x["text"] for x in cls.l0["requirements"]}
        cls.l1_reqs = {x["id"]: x["text"] for x in cls.l1["requirements"]}
        cls.err_reqs = {x["id"]: x["text"] for x in cls.err["requirements"]}

    def test_dimensions_are_explicit_and_independent(self):
        for identifier in ("REQUEST-STATE", "AUTHORIZATION-STATE", "EXECUTION-STATE", "OBSERVATION-STATE", "VERIFICATION-STATE"):
            self.assertIn(identifier, self.l0_defs)
        self.assertIn("independent request, authorization, execution, observation, and verification dimensions", self.l0_reqs["L0-REQ-014"])

    def test_permitted_values_remain_distinguishable(self):
        text = self.l0_reqs["L0-REQ-015"]
        for value in ("requested", "not-requested", "authorized", "refused", "unattempted", "attempted", "partial", "completed", "failed", "cancelled", "timed-out", "unobserved", "observed", "contradicted", "unverified", "verified", "indeterminate"):
            self.assertIn(value, text)

    def test_required_implication_and_non_implications_are_normative(self):
        self.assertIn("verified must imply observation state observed", self.l0_reqs["L0-REQ-017"])
        text = self.l0_reqs["L0-REQ-018"]
        for phrase in ("observed must not imply execution state completed", "completed must not imply authorization state authorized", "authorized must not imply execution state attempted", "attempted must not imply execution state completed"):
            self.assertIn(phrase, text)

    def test_assertion_authority_and_evidence_are_explicit(self):
        text = self.l0_reqs["L0-REQ-016"]
        for phrase in ("exactly one dimension", "exactly one governing actor and authority", "admitted evidence basis", "explicit uncertainty"):
            self.assertIn(phrase, text)
        authority = self.l0_reqs["L0-REQ-024"]
        for phrase in ("Request-state authority", "authorization-state authority", "execution-state authority", "observation-state authority", "verification-state authority"):
            self.assertIn(phrase, authority)

    def test_verification_identifies_claim_and_evidence(self):
        text = self.l0_reqs["L0-REQ-020"]
        self.assertIn("exact claim being verified", text)
        self.assertIn("exact admitted evidence set", text)
        self.assertIn("must fail closed", text)

    def test_correction_supersession_and_monotonic_history(self):
        text = self.l0_reqs["L0-REQ-022"]
        for phrase in ("monotonic as historical facts", "explicitly supersedes", "correction reason", "new evidence basis", "must not mutate or erase"):
            self.assertIn(phrase, text)

    def test_conflicts_uncertainty_and_overclaiming_fail_closed(self):
        self.assertIn("must fail closed", self.l0_reqs["L0-REQ-021"])
        self.assertIn("stronger than the complete admitted evidence supports", self.l0_reqs["L0-REQ-023"])

    def test_level_one_preserves_dimensions_without_lifecycle_substitution(self):
        text = self.l1_reqs["L1-REQ-017"]
        self.assertIn("independent request, authorization, execution, observation, and verification dimensions", text)
        self.assertIn("must not substitute", text)

    def test_level_three_realizes_current_heads_and_history(self):
        text = self.err_reqs["L3-ERR-REQ-029"]
        self.assertIn("at most one current unsuperseded assertion", text)
        self.assertIn("verification without evidence", text)
        self.assertIn("stronger than admitted evidence supports", text)
        preserved = self.err_reqs["L3-ERR-REQ-030"]
        for value in ("Partial", "refused", "failed", "cancelled", "timed-out", "contradicted", "superseded", "corrected", "indeterminate"):
            self.assertIn(value, preserved)

if __name__ == "__main__":
    unittest.main()
