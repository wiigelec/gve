from __future__ import annotations

import hashlib
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
        cls.err = load_strict(ERR)
        cls.defs = {item["id"]: item["text"] for item in cls.err["definitions"]}
        cls.reqs = {item["id"]: item["text"] for item in cls.err["requirements"]}

    def test_foundational_and_architecture_levels_remain_unchanged(self):
        self.assertEqual(
            hashlib.sha256(L0.read_bytes()).hexdigest(),
            "972800a6a51bd05cfc119afc91febe5a64f739e8ac434342c3085c2ae62d3d67",
        )
        self.assertEqual(
            hashlib.sha256(L1.read_bytes()).hexdigest(),
            "8a7061f7fb0f066fef1a309d7ae5c6abcfaf79adbd67e7816168c6d9725c6e4c",
        )

    def test_level_three_owns_the_explicit_model(self):
        for identifier in (
            "L3-ERR-EFFECT-STATE-DIMENSION",
            "L3-ERR-EFFECT-STATE-ASSERTION",
            "L3-ERR-EFFECT-STATE-CURRENT-HEAD",
            "L3-ERR-EFFECT-STATE-CORRECTION",
        ):
            self.assertIn(identifier, self.defs)
        self.assertIn(
            "five independent dimensions",
            self.reqs["L3-ERR-REQ-027"],
        )

    def test_permitted_values_remain_distinguishable(self):
        text = self.reqs["L3-ERR-REQ-028"]
        for value in (
            "requested",
            "not-requested",
            "authorized",
            "refused",
            "unattempted",
            "attempted",
            "partial",
            "completed",
            "failed",
            "cancelled",
            "timed-out",
            "unobserved",
            "observed",
            "contradicted",
            "unverified",
            "verified",
            "indeterminate",
        ):
            self.assertIn(value, text)

    def test_assertion_authority_and_evidence_are_explicit(self):
        assertion = self.reqs["L3-ERR-REQ-029"]
        for phrase in (
            "exactly one effect",
            "one dimension",
            "one governing actor",
            "one governing authority",
            "complete admitted evidence set",
            "explicit uncertainty",
            "correction lineage",
        ):
            self.assertIn(phrase, assertion)
        authority = self.reqs["L3-ERR-REQ-030"]
        for phrase in (
            "Request-state assertions",
            "authorization-state assertions",
            "execution-state assertions",
            "observation-state assertions",
            "verification-state assertions",
        ):
            self.assertIn(phrase, authority)

    def test_transition_evidence_fails_closed(self):
        text = self.reqs["L3-ERR-REQ-031"]
        for phrase in (
            "evidence required",
            "Missing",
            "stale",
            "ambiguous",
            "contradictory",
            "unauthorized",
            "malformed",
            "insufficient",
            "indeterminate or fail-closed",
        ):
            self.assertIn(phrase, text)

    def test_required_implication_and_non_implications(self):
        self.assertIn(
            "Verified implies observed",
            self.reqs["L3-ERR-REQ-032"],
        )
        text = self.reqs["L3-ERR-REQ-033"]
        for phrase in (
            "Observed does not imply completed",
            "completed does not imply authorized",
            "authorized does not imply attempted",
            "attempted does not imply completed",
        ):
            self.assertIn(phrase, text)

    def test_verification_binds_claim_and_evidence(self):
        text = self.reqs["L3-ERR-REQ-034"]
        self.assertIn("exact claim being verified", text)
        self.assertIn("exact admitted evidence set", text)
        self.assertIn("must fail closed", text)

    def test_conflicting_or_incomplete_current_state_fails_closed(self):
        text = self.reqs["L3-ERR-REQ-035"]
        for phrase in (
            "at most one current unsuperseded assertion",
            "Contradictory current values",
            "conflicting governing authorities",
            "incomplete assertion records",
            "omitted required uncertainty",
            "must fail closed",
        ):
            self.assertIn(phrase, text)

    def test_correction_preserves_monotonic_history(self):
        text = self.reqs["L3-ERR-REQ-036"]
        for phrase in (
            "history is monotonic",
            "new immutable attributable assertion",
            "explicitly supersedes",
            "correction reason",
            "evidence basis",
            "must not be mutated or erased",
        ):
            self.assertIn(phrase, text)

    def test_failure_and_uncertainty_states_do_not_collapse(self):
        text = self.reqs["L3-ERR-REQ-037"]
        for value in (
            "Refused",
            "partial",
            "failed",
            "cancelled",
            "timed-out",
            "contradicted",
            "superseded",
            "corrected",
            "indeterminate",
        ):
            self.assertIn(value, text)

    def test_authoritative_results_cannot_overclaim(self):
        text = self.reqs["L3-ERR-REQ-038"]
        self.assertIn("must not assert", text)
        self.assertIn("stronger than its complete admitted evidence supports", text)
        for phrase in (
            "adverse",
            "partial",
            "contradictory",
            "superseded",
            "corrected",
            "indeterminate",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
