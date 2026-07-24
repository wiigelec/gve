from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from specs.tooling.render import render_markdown
from specs.tooling.strict_json import load_strict


ROOT = Path(__file__).resolve().parents[2]
SPECS = ROOT / "specs"
LIFECYCLE_JSON = (
    SPECS
    / "levels"
    / "level-3"
    / "GVE-LEVEL-3-WORKFLOW-PLANNING-LIFECYCLE.json"
)
LIFECYCLE_MARKDOWN = LIFECYCLE_JSON.with_suffix(".md")


class LevelThreeWorkflowPlanningLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.document = load_strict(LIFECYCLE_JSON)
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
                "id": "GVE-LEVEL-3-WORKFLOW-PLANNING-LIFECYCLE",
                "level": 3,
                "title": "GVE Level 3 Workflow Planning and Lifecycle",
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
                ],
            },
        )

    def test_complete_plan_and_fail_closed_acceptance(self) -> None:
        complete = self.requirements["L3-WPL-REQ-001"]
        acceptance = self.requirements["L3-WPL-REQ-002"]

        for phrase in (
            "full operation membership",
            "unique operation identities",
            "selected plugin and action bindings",
            "exactly one fresh validated operation contract per operation",
            "all ordering constraints",
            "all dependency edges",
            "all handoff declarations",
            "immutable registry and runtime snapshots",
        ):
            self.assertIn(phrase, complete)

        self.assertIn("one deterministic fail-closed pre-execution decision", acceptance)
        for phrase in (
            "missing",
            "duplicate",
            "conflicting",
            "ambiguous",
            "stale",
            "unauthorized",
            "incomplete",
            "non-uniquely attributable",
        ):
            self.assertIn(phrase, acceptance)
        self.assertIn("before any operation is attempted", acceptance)

    def test_accepted_plan_snapshot_is_immutable(self) -> None:
        requirement = self.requirements["L3-WPL-REQ-003"]
        self.assertIn("one stable accepted-plan snapshot identity", requirement)
        for phrase in (
            "operation",
            "contract",
            "authority",
            "registry",
            "runtime",
        ):
            self.assertIn(phrase, requirement)
        self.assertIn("must remain immutable", requirement)

    def test_ordering_dependencies_and_handoffs_fail_closed(self) -> None:
        ordering = self.requirements["L3-WPL-REQ-004"]
        dependencies = self.requirements["L3-WPL-REQ-005"]
        handoffs = self.requirements["L3-WPL-REQ-006"]

        for phrase in (
            "missing operations",
            "duplicate identities",
            "contradictory constraints",
            "cycles",
            "duplicate positions",
            "multiple unresolved valid orders",
        ):
            self.assertIn(phrase, ordering)
        self.assertIn("must fail closed", ordering)

        for phrase in (
            "every prerequisite edge",
            "satisfaction condition",
            "unknown or duplicate operation identities",
            "self-dependencies",
            "conflicting edges",
            "prohibited cycles",
        ):
            self.assertIn(phrase, dependencies)
        self.assertIn("must remain immutable after plan acceptance", dependencies)

        for phrase in (
            "exactly one producer operation",
            "one consumer operation",
            "one handoff identity",
            "explicit acceptance conditions",
            "missing",
            "duplicate",
            "ambiguous",
            "stale",
            "incompatible",
            "non-uniquely attributable",
        ):
            self.assertIn(phrase, handoffs)
        self.assertIn("must fail closed", handoffs)

    def test_eligibility_precedes_attempt(self) -> None:
        eligibility = self.requirements["L3-WPL-REQ-007"]
        attempt = self.requirements["L3-WPL-REQ-008"]

        for phrase in (
            "accepted-plan snapshot",
            "governing authority",
            "valid fresh operation contract",
            "deterministic ordering",
            "satisfied dependencies",
            "valid handoffs",
            "current lifecycle facts",
        ):
            self.assertIn(phrase, eligibility)

        self.assertIn("No operation attempt may be created or begun", attempt)
        self.assertIn("before operation eligibility is established", attempt)
        self.assertIn("must fail closed", attempt)

    def test_attempt_identity_and_order_are_deterministic(self) -> None:
        identity = self.requirements["L3-WPL-REQ-009"]
        order = self.requirements["L3-WPL-REQ-010"]

        for phrase in (
            "one fresh unique attempt identity",
            "exactly one operation identity",
            "one accepted-plan snapshot identity",
            "one deterministic attempt ordinal",
        ):
            self.assertIn(phrase, identity)
        self.assertIn("identity reuse or ambiguous attribution must fail closed", identity)

        for phrase in (
            "declaration order",
            "discovery order",
            "filesystem order",
            "registry iteration order",
            "validator iteration order",
            "process timing",
            "unspecified concurrency",
        ):
            self.assertIn(phrase, order)

    def test_lifecycle_states_remain_distinct(self) -> None:
        states = self.requirements["L3-WPL-REQ-011"]
        for phrase in (
            "Eligible",
            "blocked",
            "skipped",
            "unattempted",
            "attempted",
            "interrupted",
            "cancelled",
            "timed-out",
            "failed",
            "completed",
        ):
            self.assertIn(phrase, states)
        self.assertIn("must remain distinct", states)

    def test_cancellation_and_timeout_facts_remain_distinct(self) -> None:
        cancellation = self.requirements["L3-WPL-REQ-012"]
        timeout = self.requirements["L3-WPL-REQ-013"]

        for phrase in (
            "cancellation request",
            "cancellation observation",
            "interruption caused by cancellation",
            "terminal cancelled state",
        ):
            self.assertIn(phrase, cancellation)
        self.assertIn("distinct uniquely attributable lifecycle facts", cancellation)

        for phrase in (
            "timeout configuration or request",
            "timeout observation",
            "interruption caused by timeout",
            "terminal timed-out state",
        ):
            self.assertIn(phrase, timeout)
        self.assertIn("distinct uniquely attributable lifecycle facts", timeout)

    def test_retry_requires_fresh_attempt_and_re_evaluation(self) -> None:
        requirement = self.requirements["L3-WPL-REQ-014"]
        for phrase in (
            "explicit governing authority",
            "fresh unique attempt identity",
            "new deterministic attempt ordinal",
            "re-evaluation",
            "plan",
            "contract",
            "registry",
            "runtime",
            "dependency",
            "handoff",
            "lifecycle freshness conditions",
        ):
            self.assertIn(phrase, requirement)

    def test_partial_progress_and_workflow_terminality_are_complete(self) -> None:
        progress = self.requirements["L3-WPL-REQ-015"]
        terminality = self.requirements["L3-WPL-REQ-016"]

        self.assertIn("every operation and every created attempt", progress)
        for phrase in (
            "blocked",
            "skipped",
            "unattempted",
            "interrupted",
            "cancelled",
            "timed-out",
            "failed",
            "nonterminal",
        ):
            self.assertIn(phrase, progress)

        self.assertIn("every operation and every created attempt", terminality)
        self.assertIn("complete, consistent, uniquely attributable terminal lifecycle accounting", terminality)
        for phrase in ("unresolved", "conflicting", "missing", "ambiguous"):
            self.assertIn(phrase, terminality)
        self.assertIn("must prevent terminality", terminality)

    def test_lifecycle_does_not_substitute_for_effect_claims(self) -> None:
        requirement = self.requirements["L3-WPL-REQ-017"]
        for phrase in (
            "requested",
            "authorized",
            "attempted",
            "completed",
            "observed",
            "verified",
        ):
            self.assertIn(phrase, requirement)
        self.assertIn("are lifecycle facts only", requirement)

    def test_sibling_responsibilities_are_excluded(self) -> None:
        sibling = self.requirements["L3-WPL-REQ-018"]
        implementation = self.requirements["L3-WPL-REQ-019"]

        for phrase in (
            "detailed plugin or action contract fields",
            "registration mechanics",
            "action input interpretation",
            "validated-operation-contract production",
            "evidence schemas",
            "evidence sufficiency",
            "effect-claim realization",
            "operation-result schemas",
            "uncertainty semantics",
            "authoritative workflow-result assembly",
        ):
            self.assertIn(phrase, sibling)

        for phrase in (
            "maintained runtime",
            "scheduler",
            "executor",
            "queue",
            "language-specific state-machine",
            "concurrency primitives",
            "deployment",
            "persistence",
            "caching",
            "performance",
            "distributed-coordination",
            "bootstrap executor formats",
            "accepted Levels 0 through 2",
        ):
            self.assertIn(phrase, implementation)

    def test_namespace_is_stable_and_distinct(self) -> None:
        definition_ids = set(self.definitions)
        requirement_ids = set(self.requirements)
        relationship_ids = {
            item["id"] for item in self.document["relationships"]
        }

        self.assertTrue(
            all(identifier.startswith("L3-WPL-") for identifier in definition_ids)
        )
        self.assertTrue(
            all(identifier.startswith("L3-WPL-REQ-") for identifier in requirement_ids)
        )
        self.assertTrue(
            all(identifier.startswith("L3-WPL-REL-") for identifier in relationship_ids)
        )
        self.assertTrue(definition_ids.isdisjoint(requirement_ids))
        self.assertTrue(definition_ids.isdisjoint(relationship_ids))
        self.assertTrue(requirement_ids.isdisjoint(relationship_ids))

    def test_markdown_is_exact_projection(self) -> None:
        self.assertEqual(
            LIFECYCLE_MARKDOWN.read_text(encoding="utf-8"),
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
