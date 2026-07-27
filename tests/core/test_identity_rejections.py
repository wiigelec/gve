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
VECTOR_ROOT = (
    REPOSITORY_ROOT
    / "specs"
    / "tests"
    / "fixtures"
    / "issue_84"
    / "duplicate-operation-identity"
)


def _run_gve(input_bytes: bytes) -> subprocess.CompletedProcess[bytes]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(SOURCE_ROOT)
    with tempfile.TemporaryDirectory(prefix="gve-identity-rejection-") as temporary:
        return subprocess.run(
            [sys.executable, "-m", "gve"],
            cwd=temporary,
            env=environment,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )


class IdentityRejectionTests(unittest.TestCase):
    def test_duplicate_operation_identity_matches_exact_process_evidence(self) -> None:
        completed = _run_gve((VECTOR_ROOT / "input.json").read_bytes())

        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, (VECTOR_ROOT / "stdout.bin").read_bytes())
        self.assertEqual(completed.stderr, (VECTOR_ROOT / "stderr.bin").read_bytes())

    def test_duplicate_operation_identity_preserves_authoritative_identities(self) -> None:
        manifest = json.loads(
            (
                REPOSITORY_ROOT
                / "specs"
                / "tests"
                / "fixtures"
                / "issue_84"
                / "manifest.json"
            ).read_text(encoding="utf-8")
        )
        expected = next(
            item["identities"]
            for item in manifest["vectors"]
            if item["id"] == "duplicate-operation-identity"
        )

        completed = _run_gve((VECTOR_ROOT / "input.json").read_bytes())
        result = json.loads(completed.stdout)

        self.assertEqual(result["request_id"], expected["request_id"])
        self.assertEqual(result["result_id"], expected["result_id"])
        self.assertEqual(result["workflow"]["workflow_id"], expected["workflow_id"])
        self.assertEqual(
            [item["operation_id"] for item in result["workflow"]["operations"]],
            expected["operation_ids"],
        )
        self.assertEqual(
            [item["diagnostic_id"] for item in result["diagnostics"]],
            expected["diagnostic_ids"],
        )
        self.assertEqual(result["processing"]["status"], "rejected")
        self.assertEqual(
            result["processing"]["failure_stage"],
            "identity-validation",
        )
        self.assertEqual(result["workflow"]["status"], "rejected")
        self.assertTrue(
            all(
                operation["status"] == "unattempted"
                for operation in result["workflow"]["operations"]
            )
        )


if __name__ == "__main__":
    unittest.main()
