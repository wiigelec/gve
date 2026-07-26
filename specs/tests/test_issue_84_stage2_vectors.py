from __future__ import annotations

import hashlib
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from specs.tooling.stage2_vector_runner import command_processor, run_manifest
from specs.tooling.stage2_vectors import (
    canonical_json_bytes,
    canonical_success_result,
    derived_identity,
    reference_process,
)
from specs.tooling.strict_json import load_strict


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "specs/tests/fixtures/issue_84"
RESULT_SCHEMA = ROOT / "specs/schemas/GVE-STAGE-2-AUTHORITATIVE-RESULT.schema.json"
FATAL_SCHEMA = ROOT / "specs/schemas/GVE-STAGE-2-FATAL-FAILURE.schema.json"


class Issue84Stage2VectorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = load_strict(FIXTURES / "manifest.json")
        cls.result_validator = Draft202012Validator(load_strict(RESULT_SCHEMA))
        cls.fatal_validator = Draft202012Validator(load_strict(FATAL_SCHEMA))

    def test_complete_manifest_runs_byte_exactly(self) -> None:
        self.assertEqual(run_manifest(), [])

    def test_external_implementation_command_receives_exact_bytes(self) -> None:
        vector = self.manifest["vectors"][0]
        input_path = FIXTURES / vector["input"]["path"]
        expected_input = input_path.read_bytes()
        expected_stdout = (
            FIXTURES / vector["expected"]["stdout_path"]
        ).read_bytes()

        with tempfile.TemporaryDirectory() as directory:
            script = Path(directory) / "implementation.py"
            script.write_text(
                textwrap.dedent(
                    f"""\
                    import pathlib
                    import sys

                    received = sys.stdin.buffer.read()
                    if received != {expected_input!r}:
                        sys.stderr.buffer.write(b"unexpected input")
                        raise SystemExit(99)
                    sys.stdout.buffer.write({expected_stdout!r})
                    raise SystemExit({vector["expected"]["exit_status"]})
                    """
                )
            )
            processor = command_processor([sys.executable, str(script)])
            outcome = processor(expected_input)

        self.assertEqual(outcome.exit_status, vector["expected"]["exit_status"])
        self.assertEqual(outcome.stdout, expected_stdout)
        self.assertEqual(outcome.stderr, b"")

    def test_runner_can_compare_an_external_implementation(self) -> None:
        vector = self.manifest["vectors"][0]
        with tempfile.TemporaryDirectory() as directory:
            manifest_path = Path(directory) / "manifest.json"
            manifest_path.write_text(
                __import__("json").dumps(
                    {
                        **self.manifest,
                        "vectors": [vector],
                    }
                )
            )
            fixture_root = manifest_path.parent
            for relative in (
                vector["input"]["path"],
                vector["expected"]["stdout_path"],
                vector["expected"]["stderr_path"],
            ):
                source = FIXTURES / relative
                target = fixture_root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())

            expected_input = (FIXTURES / vector["input"]["path"]).read_bytes()
            expected_stdout = (
                FIXTURES / vector["expected"]["stdout_path"]
            ).read_bytes()
            script = Path(directory) / "implementation.py"
            script.write_text(
                textwrap.dedent(
                    f"""\
                    import sys

                    if sys.stdin.buffer.read() != {expected_input!r}:
                        raise SystemExit(99)
                    sys.stdout.buffer.write({expected_stdout!r})
                    """
                )
            )
            errors = run_manifest(
                manifest_path,
                processor=command_processor([sys.executable, str(script)]),
            )

        self.assertEqual(errors, [])

    def test_canonical_result_reproduces_from_input_bytes(self) -> None:
        base = FIXTURES / "canonical-success"
        input_bytes = (base / "input.json").read_bytes()
        payload = load_strict(base / "input.json")
        expected_result = (base / "result.json").read_bytes()
        actual = canonical_success_result(input_bytes, payload)
        self.assertEqual(canonical_json_bytes(actual), expected_result)
        self.assertEqual(list(self.result_validator.iter_errors(actual)), [])

    def test_fatal_vectors_are_schema_valid(self) -> None:
        for vector_id in ("malformed-utf8", "malformed-json", "duplicate-object-members"):
            with self.subTest(vector_id=vector_id):
                stderr = (FIXTURES / vector_id / "stderr.bin").read_bytes()
                value = load_strict(FIXTURES / vector_id / "stderr.bin")
                self.assertEqual(list(self.fatal_validator.iter_errors(value)), [])
                self.assertEqual(reference_process((FIXTURES / vector_id / "input.bin").read_bytes()).stderr, stderr)

    def test_malformed_utf8_is_genuinely_invalid(self) -> None:
        data = (FIXTURES / "malformed-utf8/input.bin").read_bytes()
        with self.assertRaises(UnicodeDecodeError):
            data.decode("utf-8")

    def test_malformed_json_is_valid_utf8(self) -> None:
        data = (FIXTURES / "malformed-json/input.bin").read_bytes()
        data.decode("utf-8")
        self.assertEqual(reference_process(data).exit_status, 4)

    def test_duplicate_members_are_preserved(self) -> None:
        data = (FIXTURES / "duplicate-object-members/input.bin").read_bytes()
        self.assertEqual(data.count(b'"lifecycle":"no-op"'), 2)
        self.assertEqual(reference_process(data).exit_status, 4)

    def test_identity_derivation_is_stable_and_domain_separated(self) -> None:
        input_bytes = (FIXTURES / "canonical-success/input.json").read_bytes()
        request_id = derived_identity("request", input_bytes)
        result_id = derived_identity("result", request_id.encode("ascii"), b"success")
        vector_ids = self.manifest["vectors"][0]["identities"]
        self.assertEqual(request_id, vector_ids["request_id"])
        self.assertEqual(result_id, vector_ids["result_id"])
        self.assertNotEqual(request_id, result_id)

    def test_every_fixture_hash_and_length_matches_manifest(self) -> None:
        for vector in self.manifest["vectors"]:
            with self.subTest(vector=vector["id"]):
                input_bytes = (FIXTURES / vector["input"]["path"]).read_bytes()
                self.assertEqual(len(input_bytes), vector["input"]["byte_length"])
                self.assertEqual(hashlib.sha256(input_bytes).hexdigest(), vector["input"]["sha256"])


    def test_lifecycle_rejections_are_distinct_authoritative_results(self) -> None:
        vectors = {vector["id"]: vector for vector in self.manifest["vectors"]}
        missing = vectors["missing-lifecycle"]
        unsupported = vectors["unsupported-lifecycle"]
        self.assertEqual(missing["expected"]["exit_status"], 2)
        self.assertEqual(unsupported["expected"]["exit_status"], 2)
        self.assertNotEqual(
            missing["identities"]["request_id"],
            unsupported["identities"]["request_id"],
        )
        self.assertNotEqual(
            (FIXTURES / missing["expected"]["result_path"]).read_bytes(),
            (FIXTURES / unsupported["expected"]["result_path"]).read_bytes(),
        )


    def test_workflow_and_operation_envelopes_are_independently_rejected(self) -> None:
        vectors = {vector["id"]: vector for vector in self.manifest["vectors"]}
        workflow = vectors["malformed-workflow-envelope"]
        operation = vectors["malformed-operation-envelope"]
        self.assertEqual(workflow["expected"]["exit_status"], 2)
        self.assertEqual(operation["expected"]["exit_status"], 2)
        self.assertNotEqual(workflow["identities"]["request_id"], operation["identities"]["request_id"])
        self.assertNotEqual(
            (FIXTURES / workflow["expected"]["result_path"]).read_bytes(),
            (FIXTURES / operation["expected"]["result_path"]).read_bytes(),
        )

    def test_closed_boundaries_reject_unknown_and_execution_members(self) -> None:
        vectors = {vector["id"]: vector for vector in self.manifest["vectors"]}
        ids = (
            "unknown-top-level-member",
            "forbidden-operation-execution-field",
            "unknown-plugin-routing-member",
        )
        request_ids = []
        result_bytes = []
        for vector_id in ids:
            vector = vectors[vector_id]
            self.assertEqual(vector["expected"]["exit_status"], 2)
            request_ids.append(vector["identities"]["request_id"])
            result_bytes.append(
                (FIXTURES / vector["expected"]["result_path"]).read_bytes()
            )
        self.assertEqual(len(set(request_ids)), len(ids))
        self.assertEqual(len(set(result_bytes)), len(ids))

    def test_duplicate_operation_identity_is_an_identity_rejection(self) -> None:
        vectors = {vector["id"]: vector for vector in self.manifest["vectors"]}
        vector = vectors["duplicate-operation-identity"]
        self.assertEqual(vector["expected"]["exit_status"], 2)
        self.assertEqual(vector["diagnostics"][0]["stage"], "identity-validation")
        self.assertEqual(
            vector["diagnostics"][0]["code"],
            "GVE-S2-DUPLICATE-IDENTITY",
        )
        self.assertEqual(
            vector["identities"]["operation_ids"],
            ["operation-1", "operation-1"],
        )

    def test_opaque_content_accepts_unknown_and_execution_shaped_members(self) -> None:
        vectors = {vector["id"]: vector for vector in self.manifest["vectors"]}
        vector = vectors["opaque-content-unknown-members"]
        self.assertEqual(vector["expected"]["exit_status"], 0)
        payload = load_strict(FIXTURES / vector["input"]["path"])
        content = payload["workflow"]["operations"][0]["content"]
        self.assertIn("execution_like_but_opaque", content)
        self.assertIn("command", content["execution_like_but_opaque"])

    def test_all_authoritative_result_fixtures_are_schema_valid(self) -> None:
        for vector in self.manifest["vectors"]:
            if not vector["authoritative_result"]:
                continue
            with self.subTest(vector=vector["id"]):
                result = load_strict(FIXTURES / vector["expected"]["result_path"])
                self.assertEqual(list(self.result_validator.iter_errors(result)), [])

    def test_unknown_members_are_rejected_at_every_issue_83_boundary(self) -> None:
        validators = {
            "GVE-STAGE-2-AUTHORITATIVE-RESULT.schema.json": self.result_validator,
            "GVE-STAGE-2-FATAL-FAILURE.schema.json": self.fatal_validator,
        }
        for probe in self.manifest["boundary_probes"]:
            with self.subTest(probe=probe["id"]):
                value = load_strict(FIXTURES / probe["fixture"])
                target = value
                pointer = probe["json_pointer"]
                if pointer:
                    for token in pointer.lstrip("/").split("/"):
                        token = token.replace("~1", "/").replace("~0", "~")
                        target = target[int(token)] if isinstance(target, list) else target[token]
                self.assertIsInstance(target, dict)
                target[probe["member"]] = "must-be-rejected"
                errors = list(validators[probe["schema"]].iter_errors(value))
                self.assertNotEqual(errors, [])
                self.assertEqual(probe["expected"], "schema-rejected")

    def test_identity_derivation_manifest_is_complete(self) -> None:
        derivation = self.manifest["identity_derivation"]
        self.assertEqual(derivation["algorithm"], "sha256")
        self.assertEqual(derivation["separator"], "00")
        self.assertEqual(
            set(derivation["families"]),
            {
                "request",
                "result-success",
                "result-invalid-input",
                "result-invalid-identity",
                "diagnostic-payload-validation",
                "diagnostic-duplicate-operation-identity",
                "fatal-failure",
            },
        )

    def test_every_manifest_identity_reproduces_from_normative_preimages(self) -> None:
        for vector in self.manifest["vectors"]:
            with self.subTest(vector=vector["id"]):
                input_bytes = (FIXTURES / vector["input"]["path"]).read_bytes()
                identities = vector["identities"]

                if identities["request_id"] is not None:
                    request_id = derived_identity("request", input_bytes)
                    self.assertEqual(request_id, identities["request_id"])
                else:
                    request_id = None

                if identities.get("failure_id") is not None:
                    stage = vector["fatal_failure"]["stage"]
                    self.assertEqual(
                        derived_identity("failure", input_bytes, stage.encode("ascii")),
                        identities["failure_id"],
                    )

                if identities["result_id"] is not None:
                    self.assertIsNotNone(request_id)
                    if vector["acceptance"] in {"accepted", "accepted-no-op"}:
                        discriminator = b"success"
                    elif vector["acceptance"] == "identity-mismatch-result":
                        discriminator = b"invalid-identity"
                    else:
                        discriminator = b"invalid-input"
                    self.assertEqual(
                        derived_identity(
                            "result",
                            request_id.encode("ascii"),
                            discriminator,
                        ),
                        identities["result_id"],
                    )

                expected_diagnostic_ids = []
                for diagnostic in vector["diagnostics"]:
                    self.assertIsNotNone(request_id)
                    if diagnostic["code"] == "GVE-S2-DUPLICATE-IDENTITY":
                        diagnostic_id = derived_identity(
                            "diagnostic",
                            request_id.encode("ascii"),
                            b"identity-validation",
                            b"duplicate-operation-id",
                        )
                    else:
                        diagnostic_id = derived_identity(
                            "diagnostic",
                            request_id.encode("ascii"),
                            b"payload-validation",
                        )
                    self.assertEqual(diagnostic_id, diagnostic["diagnostic_id"])
                    expected_diagnostic_ids.append(diagnostic_id)
                self.assertEqual(
                    expected_diagnostic_ids,
                    identities["diagnostic_ids"],
                )

if __name__ == "__main__":
    unittest.main()
