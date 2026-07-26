"""Offline exact-byte runner for Stage 2 Issue 84 vectors."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path

from specs.tooling.stage2_vectors import ProcessOutcome, reference_process
from specs.tooling.strict_json import load_strict
from specs.tooling.vector_schema_validation import schema_validator


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "specs/tests/fixtures/issue_84/manifest.json"
Processor = Callable[[bytes], ProcessOutcome]


def command_processor(command: Sequence[str]) -> Processor:
    """Return a processor that executes one implementation command per vector."""
    if not command:
        raise ValueError("implementation command must not be empty")

    def process(input_bytes: bytes) -> ProcessOutcome:
        completed = subprocess.run(
            list(command),
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        return ProcessOutcome(
            exit_status=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )

    return process


def run_manifest(
    manifest_path: Path = DEFAULT_MANIFEST,
    processor: Processor = reference_process,
) -> list[str]:
    manifest = load_strict(manifest_path)
    base = manifest_path.parent
    errors: list[str] = []
    for vector in manifest["vectors"]:
        vector_id = vector["id"]
        input_bytes = (base / vector["input"]["path"]).read_bytes()
        outcome = processor(input_bytes)
        expected = vector["expected"]
        expected_stdout = (base / expected["stdout_path"]).read_bytes()
        expected_stderr = (base / expected["stderr_path"]).read_bytes()
        checks = (
            ("input length", len(input_bytes), vector["input"]["byte_length"]),
            ("input sha256", hashlib.sha256(input_bytes).hexdigest(), vector["input"]["sha256"]),
            ("exit status", outcome.exit_status, expected["exit_status"]),
            ("stdout bytes", outcome.stdout, expected_stdout),
            ("stderr bytes", outcome.stderr, expected_stderr),
            ("stdout length", len(outcome.stdout), expected["stdout_byte_length"]),
            ("stderr length", len(outcome.stderr), expected["stderr_byte_length"]),
            ("stdout sha256", hashlib.sha256(outcome.stdout).hexdigest(), expected["stdout_sha256"]),
            ("stderr sha256", hashlib.sha256(outcome.stderr).hexdigest(), expected["stderr_sha256"]),
        )
        for name, actual, wanted in checks:
            if actual != wanted:
                errors.append(f"{vector_id}: {name} mismatch")
    return errors


def run_artifact_validation_cases(
    manifest_path: Path = DEFAULT_MANIFEST,
) -> list[str]:
    manifest = load_strict(manifest_path)
    base = manifest_path.parent
    errors: list[str] = []
    validators: dict[str, object] = {}
    for case in manifest.get("artifact_validation_cases", []):
        case_id = case["id"]
        artifact_path = base / case["artifact"]["path"]
        artifact_bytes = artifact_path.read_bytes()
        checks = (
            ("artifact length", len(artifact_bytes), case["artifact"]["byte_length"]),
            (
                "artifact sha256",
                hashlib.sha256(artifact_bytes).hexdigest(),
                case["artifact"]["sha256"],
            ),
        )
        for name, actual, wanted in checks:
            if actual != wanted:
                errors.append(f"{case_id}: {name} mismatch")

        validator = validators.get(case["schema"])
        if validator is None:
            validator = schema_validator(case["schema"])
            validators[case["schema"]] = validator
        value = load_strict(artifact_path)
        rejected = bool(list(validator.iter_errors(value)))
        if case["expected"] == "schema-rejected" and not rejected:
            errors.append(f"{case_id}: schema unexpectedly accepted artifact")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument(
        "--implementation-command",
        nargs=argparse.REMAINDER,
        help=(
            "Execute this command once per vector, piping exact input bytes to "
            "stdin and comparing its exit status, stdout, and stderr. This option "
            "must be last because all remaining arguments belong to the command."
        ),
    )
    args = parser.parse_args()
    processor = (
        command_processor(args.implementation_command)
        if args.implementation_command
        else reference_process
    )
    errors = run_manifest(args.manifest, processor=processor)
    errors.extend(run_artifact_validation_cases(args.manifest))
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
