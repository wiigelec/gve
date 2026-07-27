from __future__ import annotations

import sys
from dataclasses import dataclass
from importlib import metadata
from typing import Any, Mapping, Sequence

from .core import FatalInputFailure, PayloadRejection
from .processing_failure import ProcessingFailure, process_request


DISTRIBUTION_NAME = "gve"
USAGE_DIAGNOSTIC = "gve: expected exactly one argument: --version"
INSTALLATION_DIAGNOSTIC = "gve: installed package metadata is unavailable"


@dataclass(frozen=True)
class ProcessOutcome:
    """Exact maintained Stage 2 process-boundary outcome."""

    stdout: bytes
    stderr: bytes
    exit_status: int


def _installed_version() -> str:
    return metadata.version(DISTRIBUTION_NAME)


def run_process(
    input_bytes: bytes,
    *,
    processor_control: Mapping[str, Any] | None = None,
) -> ProcessOutcome:
    """Run Stage 2 with an explicit conformance-only processor control."""

    try:
        output_bytes = process_request(
            input_bytes,
            processor_control=processor_control,
        )
    except PayloadRejection as rejection:
        return ProcessOutcome(rejection.result_bytes(), b"", 2)
    except ProcessingFailure as failure:
        return ProcessOutcome(failure.result_bytes(), b"", 3)
    except FatalInputFailure as failure:
        return ProcessOutcome(b"", failure.artifact_bytes(), 4)

    return ProcessOutcome(output_bytes, b"", 0)


def main(argv: Sequence[str] | None = None) -> int:
    """Installed input-only command; conformance controls are not CLI inputs."""

    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments == ["--version"]:
        try:
            version = _installed_version()
        except Exception:
            print(INSTALLATION_DIAGNOSTIC, file=sys.stderr)
            return 70

        print(f"gve {version}")
        return 0

    if arguments:
        print(USAGE_DIAGNOSTIC, file=sys.stderr)
        return 2

    if sys.stdin.isatty():
        print(USAGE_DIAGNOSTIC, file=sys.stderr)
        return 2

    outcome = run_process(sys.stdin.buffer.read())
    sys.stdout.buffer.write(outcome.stdout)
    sys.stderr.buffer.write(outcome.stderr)
    return outcome.exit_status
