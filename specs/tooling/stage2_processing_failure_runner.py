"""Exact-byte runner for the Issue #99 processing-failure vector."""

from __future__ import annotations

import hashlib
from pathlib import Path

from specs.tooling.stage2_processing_failure import processing_failure_process
from specs.tooling.strict_json import load_strict


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "specs/tests/fixtures/issue_99/manifest.json"


def run_manifest(manifest_path: Path = DEFAULT_MANIFEST) -> list[str]:
    manifest = load_strict(manifest_path)
    base = manifest_path.parent
    errors: list[str] = []
    for vector in manifest["vectors"]:
        input_bytes = (base / vector["input"]["path"]).read_bytes()
        control_path = base / vector["processor_control"]["path"]
        control_bytes = control_path.read_bytes()
        control = load_strict(control_path)
        outcome = processing_failure_process(input_bytes, control)
        expected = vector["expected"]
        expected_stdout = (base / expected["stdout_path"]).read_bytes()
        expected_stderr = (base / expected["stderr_path"]).read_bytes()
        checks = (
            ("input length", len(input_bytes), vector["input"]["byte_length"]),
            ("input sha256", hashlib.sha256(input_bytes).hexdigest(), vector["input"]["sha256"]),
            ("control length", len(control_bytes), vector["processor_control"]["byte_length"]),
            ("control sha256", hashlib.sha256(control_bytes).hexdigest(), vector["processor_control"]["sha256"]),
            ("exit status", outcome.exit_status, expected["exit_status"]),
            ("stdout bytes", outcome.stdout, expected_stdout),
            ("stderr bytes", outcome.stderr, expected_stderr),
            ("stdout sha256", hashlib.sha256(outcome.stdout).hexdigest(), expected["stdout_sha256"]),
            ("stderr sha256", hashlib.sha256(outcome.stderr).hexdigest(), expected["stderr_sha256"]),
        )
        for name, actual, wanted in checks:
            if actual != wanted:
                errors.append(f"{vector['id']}: {name} mismatch")
    return errors


def main() -> int:
    errors = run_manifest()
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
