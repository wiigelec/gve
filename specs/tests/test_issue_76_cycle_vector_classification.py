from __future__ import annotations

import inspect
import json
import unittest
from pathlib import Path

import specs.tooling.identity as identity_module


ROOT = Path(__file__).resolve().parents[1]
VECTORS = json.loads(
    (ROOT / "tests/fixtures/issue_76/identity_vectors.json").read_text(
        encoding="utf-8"
    )
)


class CycleVectorClassificationTests(unittest.TestCase):
    def vector(self, vector_id):
        return next(
            vector for vector in VECTORS["negative"]
            if vector["id"] == vector_id
        )

    def test_negative_scenario_helper_is_defined_once(self) -> None:
        source = inspect.getsource(identity_module)
        self.assertEqual(
            1,
            source.count("def _negative_vector_scenario(vector):"),
        )

    def test_generic_cycles_use_by_value_family(self) -> None:
        for vector_id in (
            "generic-self-graph-cycle",
            "generic-mutual-graph-cycle",
        ):
            vector = self.vector(vector_id)
            self.assertEqual("gve-plan", vector["family_id"])
            self.assertEqual(
                "generic-in-memory-graph-cycle",
                vector["category"],
            )

    def test_identity_self_reference_is_distinct(self) -> None:
        vector = self.vector("identity-self-reference")
        self.assertEqual("identity-self-reference", vector["category"])
        self.assertEqual("self-referential identity", vector["expected_error"])

    def test_direct_aggregate_cycle_is_distinct(self) -> None:
        vector = self.vector("direct-aggregate-cycle")
        self.assertEqual("direct-aggregate-cycle", vector["category"])
        self.assertEqual(
            "gve-governance-composition",
            vector["family_id"],
        )


if __name__ == "__main__":
    unittest.main()
