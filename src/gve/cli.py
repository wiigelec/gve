from __future__ import annotations

import sys
from importlib import metadata
from typing import Sequence

from .core import FatalInputFailure, canonical_success


DISTRIBUTION_NAME = "gve"
USAGE_DIAGNOSTIC = "gve: expected exactly one argument: --version"
INSTALLATION_DIAGNOSTIC = "gve: installed package metadata is unavailable"


def _installed_version() -> str:
    return metadata.version(DISTRIBUTION_NAME)


def main(argv: Sequence[str] | None = None) -> int:
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
        output_bytes = canonical_success(input_bytes)
    except FatalInputFailure as failure:
        sys.stderr.buffer.write(failure.artifact_bytes())
        return 4

    sys.stdout.buffer.write(output_bytes)
    return 0
