from __future__ import annotations

import hashlib
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


def _run_gve(input_bytes: bytes) -> subprocess.CompletedProcess[bytes]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(SOURCE_ROOT)
    with tempfile.TemporaryDirectory(prefix="gve-fatal-") as temporary:
        return subprocess.run(
            [sys.executable, "-m", "gve"],
            cwd=temporary,
            env=environment,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )


def _expected_json_failure(input_bytes: bytes) -> bytes:
    preimage = b"\x00".join((b"failure", input_bytes, b"json-parsing"))
    failure_id = "gve-failure-sha256:" + hashlib.sha256(preimage).hexdigest()
    value = {
        "schema_version": 1,
        "failure_id": failure_id,
        "code": "GVE-S2-INVALID-JSON",
        "stage": "json-parsing",
        "message": (
            "Input bytes could not be parsed as one JSON value, so no "
            "authoritative result identity could be constructed."
        ),
        "process": {
            "exit_code": 4,
            "stdout": "empty",
            "stderr": "fatal-failure",
        },
    }
    text = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return (text + "\n").encode("utf-8")


class FatalBoundaryTests(unittest.TestCase):
    def test_normative_fatal_vectors_match_exact_process_evidence(self) -> None:
        cases = (
            ("malformed-utf8", "input.bin"),
            ("malformed-json", "input.bin"),
            ("duplicate-object-members", "input.bin"),
        )
        for directory, input_name in cases:
            with self.subTest(vector=directory):
                root = VECTOR_ROOT / directory
                completed = _run_gve((root / input_name).read_bytes())
                self.assertEqual(completed.returncode, 4)
                self.assertEqual(completed.stdout, (root / "stdout.bin").read_bytes())
                self.assertEqual(completed.stderr, (root / "stderr.bin").read_bytes())

    def test_empty_input_is_a_json_parsing_fatal_failure(self) -> None:
        completed = _run_gve(b"")
        self.assertEqual(completed.returncode, 4)
        self.assertEqual(completed.stdout, b"")
        self.assertEqual(completed.stderr, _expected_json_failure(b""))

    def test_non_standard_json_constants_are_fatal(self) -> None:
        for input_bytes in (b"NaN\n", b"Infinity\n", b"-Infinity\n"):
            with self.subTest(input_bytes=input_bytes):
                completed = _run_gve(input_bytes)
                self.assertEqual(completed.returncode, 4)
                self.assertEqual(completed.stdout, b"")
                self.assertEqual(
                    completed.stderr,
                    _expected_json_failure(input_bytes),
                )


if __name__ == "__main__":
    unittest.main()
