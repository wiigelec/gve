"""Offline exact-byte runner for Stage 2 Issue 84 vectors."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from specs.tooling.stage2_vectors import reference_process
from specs.tooling.strict_json import load_strict


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "specs/tests/fixtures/issue_84/manifest.json"


def run_manifest(manifest_path: Path = DEFAULT_MANIFEST) -> list[str]:
    manifest = load_strict(manifest_path)
    base = manifest_path.parent
    errors: list[str] = []
    for vector in manifest["vectors"]:
        vector_id = vector["id"]
        input_bytes = (base / vector["input"]["path"]).read_bytes()
        outcome = reference_process(input_bytes)
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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    errors = run_manifest(args.manifest)
    for error in errors:
        print(error)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
