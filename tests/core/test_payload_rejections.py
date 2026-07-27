from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
VECTOR_ROOT = REPOSITORY_ROOT / "specs" / "tests" / "fixtures" / "issue_84"

PAYLOAD_REJECTION_VECTORS = (
    "missing-lifecycle",
    "unsupported-lifecycle",
    "malformed-workflow-envelope",
    "malformed-operation-envelope",
    "unknown-top-level-member",
    "forbidden-operation-execution-field",
    "unknown-plugin-routing-member",
)


def _run_gve(input_bytes: bytes) -> subprocess.CompletedProcess[bytes]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(SOURCE_ROOT)
    with tempfile.TemporaryDirectory(prefix="gve-payload-rejection-") as temporary:
        return subprocess.run(
            [sys.executable, "-m", "gve"],
            cwd=temporary,
            env=environment,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )


class PayloadRejectionTests(unittest.TestCase):
    def test_normative_payload_rejections_match_exact_process_evidence(self) -> None:
        for vector in PAYLOAD_REJECTION_VECTORS:
            with self.subTest(vector=vector):
                root = VECTOR_ROOT / vector
                completed = _run_gve((root / "input.json").read_bytes())
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(completed.stdout, (root / "stdout.bin").read_bytes())
                self.assertEqual(completed.stderr, (root / "stderr.bin").read_bytes())

    def test_rejected_results_preserve_authoritative_identities(self) -> None:
        manifest = json.loads((VECTOR_ROOT / "manifest.json").read_text(encoding="utf-8"))
        vectors = {item["id"]: item for item in manifest["vectors"]}
        for vector in PAYLOAD_REJECTION_VECTORS:
            with self.subTest(vector=vector):
                root = VECTOR_ROOT / vector
                completed = _run_gve((root / "input.json").read_bytes())
                result = json.loads(completed.stdout)
                expected = vectors[vector]["identities"]
                self.assertEqual(result["request_id"], expected["request_id"])
                self.assertEqual(result["result_id"], expected["result_id"])
                self.assertEqual(
                    [item["diagnostic_id"] for item in result["diagnostics"]],
                    expected["diagnostic_ids"],
                )
                self.assertEqual(
                    result["workflow"]["workflow_id"],
                    expected["workflow_id"],
                )
                self.assertEqual(
                    [item["operation_id"] for item in result["workflow"]["operations"]],
                    expected["operation_ids"],
                )
                self.assertEqual(result["processing"]["status"], "rejected")
                self.assertEqual(
                    result["processing"]["failure_stage"],
                    "payload-validation",
                )


if __name__ == "__main__":
    unittest.main()
