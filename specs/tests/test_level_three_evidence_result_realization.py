from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from specs.tooling.render import render_markdown
from specs.tooling.strict_json import load_strict


ROOT = Path(__file__).resolve().parents[2]
SPECS = ROOT / "specs"
RESULT_JSON = (
    SPECS
    / "levels"
    / "level-3"
    / "GVE-LEVEL-3-EVIDENCE-RESULT-REALIZATION.json"
)
RESULT_MARKDOWN = RESULT_JSON.with_suffix(".md")


class LevelThreeEvidenceResultRealizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = load_strict(RESULT_JSON)
        cls.definitions = {
            item["id"]: item["text"] for item in cls.document["definitions"]
        }
        cls.requirements = {
            item["id"]: item["text"] for item in cls.document["requirements"]
        }

    def test_identity_parentage_root_and_imports(self) -> None:
        self.assertEqual(
            self.document["specification"],
            {
                "id": "GVE-LEVEL-3-EVIDENCE-RESULT-REALIZATION",
                "level": 3,
                "title": "GVE Level 3 Evidence and Result Realization",
                "version": "1.0.0",
                "status": "normative",
                "parent": "GVE-LEVEL-3",
            },
        )
        self.assertEqual(
            self.document["document"],
            {
                "role": "subordinate",
                "root": "GVE-LEVEL-3",
                "imports": [
                    "GVE-LEVEL-3",
                    "GVE-LEVEL-3-RUNTIME-OWNERSHIP",
                    "GVE-LEVEL-3-PLUGIN-ACTION-CONTRACTS",
                    "GVE-LEVEL-3-WORKFLOW-PLANNING-LIFECYCLE",
                ],
            },
        )

    def test_evidence_identity_and_unique_attribution(self) -> None:
        requirement = self.requirements["L3-ERR-REQ-001"]
        for phrase in (
            "one stable identity",
            "workflow",
            "operation",
            "attempt",
            "plugin",
            "action",
            "governing authority",
            "evidence producer",
            "collection method",
            "observation context",
            "observation time",
        ):
            self.assertIn(phrase, requirement)
        self.assertIn("uniquely attributable", requirement)

    def test_provenance_freshness_and_integrity_are_explicit(self) -> None:
        requirement = self.requirements["L3-ERR-REQ-002"]
        for phrase in (
            "collection method",
            "producer",
            "governing authority",
            "observation time",
            "freshness boundary",
            "source context",
            "integrity facts",
        ):
            self.assertIn(phrase, requirement)

    def test_accepted_evidence_is_immutable(self) -> None:
        requirement = self.requirements["L3-ERR-REQ-003"]
        self.assertIn("must remain immutable", requirement)
        for phrase in (
            "replacement",
            "mutation",
            "deletion",
            "reinterpretation",
            "new attributable evidence",
            "fail closed",
        ):
            self.assertIn(phrase, requirement)

    def test_effect_claim_states_remain_distinct(self) -> None:
        requirement = self.requirements["L3-ERR-REQ-004"]
        for phrase in (
            "Requested",
            "authorized",
            "attempted",
            "completed",
            "observed",
            "verified",
        ):
            self.assertIn(phrase, requirement)
        self.assertIn("must remain distinct", requirement)
        self.assertIn("lifecycle status alone", requirement)

    def test_uncertainty_states_remain_explicit(self) -> None:
        requirement = self.requirements["L3-ERR-REQ-005"]
        for phrase in (
            "Unknown",
            "unavailable",
            "not-observed",
            "contradicted",
            "insufficient-evidence",
        ):
            self.assertIn(phrase, requirement)
        self.assertIn("must remain explicit", requirement)
        self.assertIn("without sufficient attributable evidence", requirement)

    def test_sufficiency_is_bound_to_exact_claim_and_authority(self) -> None:
        requirement = self.requirements["L3-ERR-REQ-006"]
        for phrase in (
            "exact effect claim",
            "governing authority",
            "accepted operation contract",
            "freshness boundary",
            "required observation context",
        ):
            self.assertIn(phrase, requirement)
        self.assertIn("rather than against generic lifecycle completion or executor success", requirement)

    def test_invalid_or_conflicting_evidence_fails_closed(self) -> None:
        requirement = self.requirements["L3-ERR-REQ-007"]
        for phrase in (
            "Duplicate",
            "stale",
            "ambiguous",
            "unauthorized",
            "malformed",
            "conflicting",
            "contradictory",
            "integrity-invalid",
            "non-uniquely attributable",
        ):
            self.assertIn(phrase, requirement)
        self.assertIn("must fail closed", requirement)
        self.assertIn("rather than silently selected or discarded", requirement)

    def test_operation_result_has_complete_binding(self) -> None:
        requirement = self.requirements["L3-ERR-REQ-008"]
        for phrase in (
            "one stable identity",
            "exactly one workflow identity",
            "one operation identity",
            "one accepted-plan snapshot identity",
            "one validated operation contract",
            "complete set of created attempts",
            "complete accepted evidence and uncertainty set",
        ):
            self.assertIn(phrase, requirement)

    def test_operation_result_accounts_for_all_facts(self) -> None:
        requirement = self.requirements["L3-ERR-REQ-009"]
        for phrase in (
            "every relevant lifecycle fact",
            "effect claim",
            "evidence record",
            "uncertainty state",
            "contradiction",
            "insufficiency",
            "unresolved condition",
            "without collapsing distinct facts",
            "without",
        ):
            self.assertIn(phrase, requirement)
        self.assertIn("omitting adverse evidence", requirement)

    def test_authoritative_workflow_result_has_exactly_one_per_operation(self) -> None:
        requirement = self.requirements["L3-ERR-REQ-010"]
        self.assertIn("exactly one realized operation result", requirement)
        self.assertIn("for every operation in the accepted workflow plan", requirement)
        for phrase in (
            "partial",
            "failed",
            "blocked",
            "skipped",
            "cancelled",
            "timed-out",
            "interrupted",
            "unattempted",
            "unresolved",
        ):
            self.assertIn(phrase, requirement)

    def test_workflow_result_assembly_fails_closed(self) -> None:
        requirement = self.requirements["L3-ERR-REQ-011"]
        for phrase in (
            "missing",
            "duplicate",
            "conflicting",
            "stale",
            "ambiguous",
            "non-unique",
            "operation-mismatched",
        ):
            self.assertIn(phrase, requirement)
        self.assertIn("must not finalize an incomplete or internally inconsistent result set", requirement)

    def test_finalization_is_complete_and_fail_closed(self) -> None:
        requirement = self.requirements["L3-ERR-REQ-012"]
        self.assertIn("one deterministic fail-closed decision", requirement)
        for phrase in (
            "all operation results",
            "lifecycle facts",
            "effect claims",
            "evidence",
            "uncertainty",
            "contradictions",
            "unresolved conditions",
        ):
            self.assertIn(phrase, requirement)

    def test_finalized_results_are_immutable(self) -> None:
        requirement = self.requirements["L3-ERR-REQ-013"]
        self.assertIn("must remain immutable", requirement)
        self.assertIn("new uniquely attributable result version", requirement)
        self.assertIn("rather than mutate accepted result history", requirement)

    def test_unsupported_claims_are_prohibited(self) -> None:
        requirement = self.requirements["L3-ERR-REQ-014"]
        for phrase in (
            "success",
            "completion",
            "observation",
            "verification",
            "publication",
            "remote effect",
            "durable state",
            "sufficient fresh uniquely attributable evidence",
            "exact claim",
        ):
            self.assertIn(phrase, requirement)

    def test_lifecycle_facts_do_not_substitute_for_evidence(self) -> None:
        requirement = self.requirements["L3-ERR-REQ-015"]
        for phrase in (
            "Lifecycle eligibility",
            "attempt creation",
            "blocking",
            "skipping",
            "cancellation",
            "timeout",
            "interruption",
            "failure",
            "completion",
            "retry",
            "terminality",
        ):
            self.assertIn(phrase, requirement)
        self.assertIn("must not substitute for evidence or effect-claim realization", requirement)

    def test_sibling_responsibilities_and_implementation_are_excluded(self) -> None:
        implementation = self.requirements["L3-ERR-REQ-016"]
        sibling = self.requirements["L3-ERR-REQ-017"]
        scope = self.requirements["L3-ERR-REQ-018"]

        for phrase in (
            "maintained runtime",
            "executor",
            "scheduler",
            "plugin",
            "action",
            "registry",
            "evidence-store",
            "database",
            "publication implementation",
            "language-specific result classes",
            "event models",
            "serialization libraries",
            "storage engines",
            "cryptographic algorithms",
        ):
            self.assertIn(phrase, implementation)

        for phrase in (
            "registration mechanics",
            "action input interpretation",
            "validated-operation-contract production",
            "workflow-plan construction",
            "dependency or handoff eligibility",
            "attempt ordering",
            "retry policy",
            "cancellation handling",
            "timeout handling",
            "lifecycle transitions",
        ):
            self.assertIn(phrase, sibling)

        for phrase in (
            "filesystem",
            "command-execution",
            "local-Git",
            "GitHub",
            "remote-service",
            "credential",
            "publication evidence schemas",
            "deployment",
            "persistence",
            "retention",
            "archival",
            "replication",
            "caching",
            "performance",
            "distributed-consensus",
            "bootstrap executor formats",
            "accepted Levels 0 through 2",
        ):
            self.assertIn(phrase, scope)

    def test_namespace_is_stable_and_distinct(self) -> None:
        definition_ids = set(self.definitions)
        requirement_ids = set(self.requirements)
        relationship_ids = {
            item["id"] for item in self.document["relationships"]
        }

        self.assertTrue(
            all(identifier.startswith("L3-ERR-") for identifier in definition_ids)
        )
        self.assertTrue(
            all(identifier.startswith("L3-ERR-REQ-") for identifier in requirement_ids)
        )
        self.assertTrue(
            all(identifier.startswith("L3-ERR-REL-") for identifier in relationship_ids)
        )
        self.assertTrue(definition_ids.isdisjoint(requirement_ids))
        self.assertTrue(definition_ids.isdisjoint(relationship_ids))
        self.assertTrue(requirement_ids.isdisjoint(relationship_ids))

    def test_markdown_is_exact_projection(self) -> None:
        self.assertEqual(
            RESULT_MARKDOWN.read_text(encoding="utf-8"),
            render_markdown(self.document),
        )

    def test_repository_specification_validation_passes(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "specs.tooling.validate",
                "--specs-root",
                str(SPECS),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("specification validation passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
