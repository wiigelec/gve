from __future__ import annotations
import copy, json, unittest
from pathlib import Path
from specs.tooling.identity import IdentityFrameworkError, compute_identity

ROOT=Path(__file__).resolve().parents[1]
FRAMEWORK=json.loads((ROOT/"identity/GVE-IDENTITY-FRAMEWORK.json").read_text())
VECTORS=json.loads((ROOT/"tests/fixtures/issue_76/identity_vectors.json").read_text())

def vector(identifier):
    return next(v for v in VECTORS["positive"] if v["id"]==identifier)

class AggregateMemberEnforcementTests(unittest.TestCase):
    def test_wrong_family_is_rejected(self):
        contract=vector("contract-object")
        with self.assertRaisesRegex(IdentityFrameworkError,"aggregate member identity family does not match"):
            compute_identity(FRAMEWORK,"gve-spec-revision",
                {"revision":"x","members":[{"document_identity":contract["expected_identity"]}]},
                member_identities=[contract["expected_identity"]])

    def test_identity_plus_value_verifies_every_pair(self):
        composition=vector("ordered-governance-composition")
        changed=copy.deepcopy(composition["value"])
        changed["members"][1]["value"]["contract_id"]="tampered"
        with self.assertRaisesRegex(IdentityFrameworkError,"claimed identity does not match its canonical preimage"):
            compute_identity(FRAMEWORK,composition["family_id"],changed,
                member_identities=composition["member_identities"])

    def test_unordered_is_permutation_invariant(self):
        revision=vector("unordered-spec-revision")
        changed=copy.deepcopy(revision["value"])
        changed["members"].reverse()
        self.assertEqual(revision["expected_identity"],
            compute_identity(FRAMEWORK,revision["family_id"],changed,
                member_identities=list(reversed(revision["member_identities"]))))

    def test_ordered_is_order_sensitive(self):
        composition=vector("ordered-governance-composition")
        changed=copy.deepcopy(composition["value"])
        changed["members"].reverse()
        self.assertNotEqual(composition["expected_identity"],
            compute_identity(FRAMEWORK,composition["family_id"],changed,
                member_identities=list(reversed(composition["member_identities"]))))

    def test_incomplete_membership_is_rejected(self):
        revision=vector("unordered-spec-revision")
        with self.assertRaisesRegex(IdentityFrameworkError,"aggregate membership is incomplete or inconsistent"):
            compute_identity(FRAMEWORK,revision["family_id"],revision["value"],
                member_identities=revision["member_identities"][:-1])

if __name__=="__main__": unittest.main()
