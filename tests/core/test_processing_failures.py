from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gve import cli
from gve.processing_failure import ProcessingFailure, process_request


FIXTURE = ROOT / "specs" / "tests" / "fixtures" / "issue_99" / "processing-failure"
RUNNER = "specs.tooling.maintained_processing_failure_runner"


def _product_environment() -> dict[str, str]:
    environment = dict(os.environ)
    existing = environment.get("PYTHONPATH")
    source = str(ROOT / "src")
    environment["PYTHONPATH"] = (
        source if not existing else source + os.pathsep + existing
    )
    return environment


class ProcessingFailureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.input_bytes = (FIXTURE / "input.json").read_bytes()
        self.control_path = FIXTURE / "processor-control.json"
        self.control = json.loads(self.control_path.read_text(encoding="utf-8"))
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
        self.assertEqual(
            result["processing"],
            {
                "failure_stage": "no-op-disposition",
                "status": "failed",
            },
        )
        self.assertEqual(result["workflow"]["status"], "failed")
        self.assertEqual(result["workflow"]["operations"][0]["status"], "failed")
        self.assertEqual(
            result["diagnostics"][0]["code"],
            "GVE-S2-PROCESSING-FAILURE",
        )
        self.assertEqual(result["diagnostics"][0]["scope"], "workflow")

    def test_repository_runner_proves_exact_exit_three_without_mocking(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                RUNNER,
                "--request",
                str(FIXTURE / "input.json"),
                "--processor-control",
                str(self.control_path),
            ],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 3)
        self.assertEqual(completed.stdout, self.expected)
        self.assertEqual(completed.stderr, b"")
        self.assertNotIn(b"Traceback", completed.stdout)
        result = json.loads(completed.stdout)
        accepted = json.loads(self.expected)
        self.assertEqual(result["request_id"], accepted["request_id"])
        self.assertEqual(result["result_id"], accepted["result_id"])
        self.assertEqual(
            result["diagnostics"][0]["diagnostic_id"],
            accepted["diagnostics"][0]["diagnostic_id"],
        )
        self.assertEqual(result["process"]["exit_code"], 3)

    def test_repository_runner_rejects_unsupported_control_outside_stage2_mapping(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            control_path = Path(directory) / "control.json"
            control_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "disposition": "processing-failure",
                        "failure_stage": "result-construction",
                    }
                ),
                encoding="utf-8",
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    RUNNER,
                    "--request",
                    str(FIXTURE / "input.json"),
                    "--processor-control",
                    str(control_path),
                ],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertEqual(completed.returncode, 64)
        self.assertEqual(completed.stdout, b"")
        self.assertEqual(
            completed.stderr,
            b"gve-processing-failure-conformance: unsupported processor control\n",
        )

    def test_installed_command_is_input_only(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", "gve"],
            cwd=ROOT,
            input=self.input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_product_environment(),
            check=False,
        )
        expected_success = cli.run_process(self.input_bytes)

        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, expected_success.stdout)
        self.assertEqual(completed.stderr, b"")

    def test_environment_cannot_activate_processing_failure(self) -> None:
        environment = _product_environment()
        environment["GVE_PROCESSOR_CONTROL"] = str(self.control_path)
        completed = subprocess.run(
            [sys.executable, "-m", "gve"],
            cwd=ROOT,
            input=self.input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
            check=False,
        )

        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, cli.run_process(self.input_bytes).stdout)
        self.assertEqual(completed.stderr, b"")

    def test_arbitrary_cli_argument_cannot_activate_processing_failure(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-m", "gve", "--processor-control", str(self.control_path)],
            cwd=ROOT,
            input=self.input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_product_environment(),
            check=False,
        )

        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stdout, b"")
        self.assertEqual(
            completed.stderr,
            (cli.USAGE_DIAGNOSTIC + "\n").encode("utf-8"),
        )

    def test_request_content_cannot_activate_processing_failure(self) -> None:
        request = json.loads(self.input_bytes)
        request["processor_control"] = self.control
        modified = (
            json.dumps(
                request,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
        completed = subprocess.run(
            [sys.executable, "-m", "gve"],
            cwd=ROOT,
            input=modified,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_product_environment(),
            check=False,
        )

        self.assertEqual(completed.returncode, 2)
        self.assertNotEqual(completed.returncode, 3)
        self.assertEqual(completed.stderr, b"")

    def test_processor_control_is_closed(self) -> None:
        for control in (
            {},
            {"schema_version": 1},
            {**self.control, "unknown": True},
            {
                "schema_version": 1,
                "disposition": "processing-failure",
                "failure_stage": "result-construction",
            },
            {
                "schema_version": 1,
                "disposition": "fatal-no-result",
                "failure_stage": "result-construction",
            },
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
