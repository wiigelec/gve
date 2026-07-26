from __future__ import annotations

import sys
from importlib import metadata
from typing import Sequence


DISTRIBUTION_NAME = "gve"
USAGE_DIAGNOSTIC = "gve: expected exactly one argument: --version"
INSTALLATION_DIAGNOSTIC = "gve: installed package metadata is unavailable"


def _installed_version() -> str:
    return metadata.version(DISTRIBUTION_NAME)


def main(argv: Sequence[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments != ["--version"]:
        print(USAGE_DIAGNOSTIC, file=sys.stderr)
        return 2

    try:
        version = _installed_version()
    except Exception:
        print(INSTALLATION_DIAGNOSTIC, file=sys.stderr)
        return 70

    print(f"gve {version}")
    return 0
