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
from gve.core import FatalInputFailure
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

    def test_core_failure_matches_accepted_fixture_exactly(self) -> None:
        with self.assertRaises(ProcessingFailure) as raised:
            process_request(
                self.input_bytes,
                processor_control=self.control,
            )

        self.assertEqual(raised.exception.result_bytes(), self.expected)

    def test_cli_maps_authoritative_failure_to_exit_three(self) -> None:
        stdin = _Input(self.input_bytes)
        stdout = _Output()
        stderr = _Output()

        with patch.object(sys, "stdin", stdin), patch.object(
            sys, "stdout", stdout
        ), patch.object(sys, "stderr", stderr):
            exit_code = cli.main([], processor_control=self.control)

        self.assertEqual(exit_code, 3)
        self.assertEqual(stdout.buffer.getvalue(), self.expected)
        self.assertEqual(stderr.buffer.getvalue(), b"")
        self.assertNotIn(b"Traceback", stdout.buffer.getvalue())

    def test_installed_path_does_not_infer_control(self) -> None:
        expected_success = process_request(self.input_bytes)
        stdin = _Input(self.input_bytes)
        stdout = _Output()
        stderr = _Output()

        with patch.object(sys, "stdin", stdin), patch.object(
            sys, "stdout", stdout
        ), patch.object(sys, "stderr", stderr):
            exit_code = cli.main([])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.buffer.getvalue(), expected_success)
        self.assertEqual(stderr.buffer.getvalue(), b"")

    def test_processor_control_is_closed(self) -> None:
        for control in (
            {},
            {"schema_version": 1},
            {**self.control, "unknown": True},
            {**self.control, "failure_stage": "result-construction"},
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

    def test_fatal_result_construction_remains_fatal(self) -> None:
        incomplete = b'{"schema_version":2,"lifecycle":"no-op"}\n'

        with self.assertRaises(FatalInputFailure) as raised:
            process_request(
                incomplete,
                processor_control=self.control,
            )

        self.assertEqual(raised.exception.stage, "result-construction")
        self.assertEqual(
            json.loads(raised.exception.artifact_bytes())["process"]["exit_code"],
            4,
        )


if __name__ == "__main__":
    unittest.main()
