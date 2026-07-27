from __future__ import annotations

import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gve import cli
from gve.processing_failure import (
    RESULT_CONSTRUCTION_CONTROL_STATUS,
    ProcessingFailure,
    process_request,
)


FIXTURE = ROOT / "specs" / "tests" / "fixtures" / "issue_99" / "processing-failure"


class _Input:
    def __init__(self, data: bytes) -> None:
        self.buffer = io.BytesIO(data)

    def isatty(self) -> bool:
        return False


class _Output:
    def __init__(self) -> None:
        self.buffer = io.BytesIO()

    def write(self, value: str) -> int:
        return len(value)

    def flush(self) -> None:
        pass


class ProcessingFailureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.input_bytes = (FIXTURE / "input.json").read_bytes()
        self.control = json.loads(
            (FIXTURE / "processor-control.json").read_text(encoding="utf-8")
        )
        self.expected = (FIXTURE / "result.json").read_bytes()

    def test_core_failure_matches_accepted_fixture_exactly(self) -> None:
        with self.assertRaises(ProcessingFailure) as raised:
            process_request(
                self.input_bytes,
                processor_control=self.control,
            )

        self.assertEqual(raised.exception.result_bytes(), self.expected)

    def test_process_boundary_maps_authoritative_failure_exactly(self) -> None:
        outcome = cli.run_process(
            self.input_bytes,
            processor_control=self.control,
        )

        self.assertEqual(outcome.exit_status, 3)
        self.assertEqual(outcome.stdout, self.expected)
        self.assertEqual(outcome.stderr, b"")
        self.assertNotIn(b"Traceback", outcome.stdout)

        result = json.loads(outcome.stdout)
        self.assertEqual(result["processing"], {
            "failure_stage": "no-op-disposition",
            "status": "failed",
        })
        self.assertEqual(result["workflow"]["status"], "failed")
        self.assertEqual(result["workflow"]["operations"][0]["status"], "failed")
        self.assertEqual(result["diagnostics"][0]["code"], "GVE-S2-PROCESSING-FAILURE")
        self.assertEqual(result["diagnostics"][0]["scope"], "workflow")

    def test_installed_command_is_input_only(self) -> None:
        expected_success = cli.run_process(self.input_bytes)
        stdin = _Input(self.input_bytes)
        stdout = _Output()
        stderr = _Output()

        with patch.object(sys, "stdin", stdin), patch.object(
            sys, "stdout", stdout
        ), patch.object(sys, "stderr", stderr):
            exit_code = cli.main([])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.buffer.getvalue(), expected_success.stdout)
        self.assertEqual(stderr.buffer.getvalue(), b"")

    def test_processor_control_is_closed_and_result_construction_is_deferred(self) -> None:
        self.assertEqual(
            RESULT_CONSTRUCTION_CONTROL_STATUS,
            "deferred-by-issue-99-authority",
        )
        for control in (
            {},
            {"schema_version": 1},
            {**self.control, "unknown": True},
            {**self.control, "failure_stage": "result-construction"},
        ):
            with self.subTest(control=control):
                with self.assertRaisesRegex(
                    ValueError,
                    "result-construction control is deferred-by-issue-99-authority",
                ):
                    process_request(
                        self.input_bytes,
                        processor_control=control,
                    )

    def test_incomplete_identity_set_remains_fatal(self) -> None:
        incomplete = b'{"schema_version":2,"lifecycle":"no-op"}\n'
        outcome = cli.run_process(
            incomplete,
            processor_control=self.control,
        )

        self.assertEqual(outcome.exit_status, 4)
        self.assertEqual(outcome.stdout, b"")
        failure = json.loads(outcome.stderr)
        self.assertEqual(failure["stage"], "result-construction")
        self.assertEqual(failure["process"]["exit_code"], 4)


if __name__ == "__main__":
    unittest.main()
