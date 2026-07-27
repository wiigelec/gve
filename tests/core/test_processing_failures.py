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
from gve.processing_failure import ProcessingFailure, process_request


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
        self.result_construction_control = {
            "schema_version": 1,
            "disposition": "processing-failure",
            "failure_stage": "result-construction",
        }

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

    def test_result_construction_failure_is_authoritative_when_identities_exist(
        self,
    ) -> None:
        no_op_result = json.loads(self.expected)
        outcome = cli.run_process(
            self.input_bytes,
            processor_control=self.result_construction_control,
        )

        self.assertEqual(outcome.exit_status, 3)
        self.assertEqual(outcome.stderr, b"")
        self.assertNotIn(b"Traceback", outcome.stdout)

        result = json.loads(outcome.stdout)
        self.assertEqual(result["request_id"], no_op_result["request_id"])
        self.assertNotEqual(result["result_id"], no_op_result["result_id"])
        self.assertEqual(result["processing"], {
            "failure_stage": "result-construction",
            "status": "failed",
        })
        self.assertEqual(result["workflow"]["status"], "failed")
        self.assertEqual(result["workflow"]["operations"][0]["status"], "failed")
        self.assertEqual(
            result["diagnostics"][0]["code"],
            "GVE-S2-RESULT-CONSTRUCTION-FAILURE",
        )
        self.assertEqual(result["diagnostics"][0]["stage"], "result-construction")
        self.assertEqual(result["process"], {
            "exit_code": 3,
            "stderr": "empty",
            "stdout": "authoritative-result",
        })

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

    def test_processor_control_is_closed(self) -> None:
        for control in (
            {},
            {"schema_version": 1},
            {**self.control, "unknown": True},
            {**self.result_construction_control, "unknown": True},
            {**self.control, "failure_stage": "identity-validation"},
        ):
            with self.subTest(control=control):
                with self.assertRaisesRegex(
                    ValueError,
                    "unsupported Stage 2 processor control",
                ):
                    process_request(
                        self.input_bytes,
                        processor_control=control,
                    )

    def test_incomplete_identity_set_remains_fatal(self) -> None:
        incomplete = b'{"schema_version":2,"lifecycle":"no-op"}\n'
        for control in (self.control, self.result_construction_control):
            with self.subTest(control=control):
                outcome = cli.run_process(
                    incomplete,
                    processor_control=control,
                )

                self.assertEqual(outcome.exit_status, 4)
                self.assertEqual(outcome.stdout, b"")
                failure = json.loads(outcome.stderr)
                self.assertEqual(failure["stage"], "result-construction")
                self.assertEqual(failure["process"]["exit_code"], 4)


if __name__ == "__main__":
    unittest.main()
