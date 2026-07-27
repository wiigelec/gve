from __future__ import annotations

import sys
from importlib import metadata
from typing import Any, Mapping, Sequence

from .core import FatalInputFailure, PayloadRejection
from .processing_failure import ProcessingFailure, process_request


DISTRIBUTION_NAME = "gve"
USAGE_DIAGNOSTIC = "gve: expected exactly one argument: --version"
INSTALLATION_DIAGNOSTIC = "gve: installed package metadata is unavailable"


def _installed_version() -> str:
    return metadata.version(DISTRIBUTION_NAME)


def main(
    argv: Sequence[str] | None = None,
    *,
    processor_control: Mapping[str, Any] | None = None,
) -> int:
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

    input_bytes = sys.stdin.buffer.read()
    try:
        output_bytes = process_request(
            input_bytes,
            processor_control=processor_control,
        )
    except PayloadRejection as rejection:
        sys.stdout.buffer.write(rejection.result_bytes())
        return 2
    except ProcessingFailure as failure:
        sys.stdout.buffer.write(failure.result_bytes())
        return 3
    except FatalInputFailure as failure:
        sys.stderr.buffer.write(failure.artifact_bytes())
        return 4

    sys.stdout.buffer.write(output_bytes)
    return 0
