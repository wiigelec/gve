"""Repository-native maintained-product processing-failure conformance runner."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from gve.cli import run_process


_ACCEPTED_CONTROL = {
    "schema_version": 1,
    "disposition": "processing-failure",
    "failure_stage": "no-op-disposition",
}
CONTROL_DIAGNOSTIC = (
    "gve-processing-failure-conformance: unsupported processor control\n"
)


def _load_control(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-standard JSON constant: {token}")
            ),
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError("unsupported processor control") from exc
    if not isinstance(value, dict) or value != _ACCEPTED_CONTROL:
        raise ValueError("unsupported processor control")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="gve-processing-failure-conformance",
        allow_abbrev=False,
    )
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--processor-control", required=True, type=Path)
    args = parser.parse_args(argv)

    try:
        request_bytes = args.request.read_bytes()
        control = _load_control(args.processor_control)
    except OSError as exc:
        print(
            f"gve-processing-failure-conformance: cannot read input: {exc}",
            file=sys.stderr,
        )
        return 66
    except ValueError:
        sys.stderr.write(CONTROL_DIAGNOSTIC)
        return 64

    outcome = run_process(request_bytes, processor_control=control)
    sys.stdout.buffer.write(outcome.stdout)
    sys.stderr.buffer.write(outcome.stderr)
    return outcome.exit_status


if __name__ == "__main__":
    raise SystemExit(main())
