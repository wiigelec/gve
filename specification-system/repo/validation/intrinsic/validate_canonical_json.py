#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any


CONSTRUCTION_ROOT = Path(__file__).resolve().parents[2]
if str(CONSTRUCTION_ROOT) not in sys.path:
    sys.path.insert(0, str(CONSTRUCTION_ROOT))

from validation.lib import (  # noqa: E402
    ValidationError as ReusableValidationError,
)
from validation.lib import (  # noqa: E402
    canonical_json_bytes as reusable_canonical_json_bytes,
)


CANONICALIZATION_VERSION = "canonical-json-v1"
MIN_INTEGER = -(2**63)
MAX_INTEGER = 2**63 - 1


class CanonicalJsonFailure(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


def fail(code: str, detail: str) -> None:
    raise CanonicalJsonFailure(code, detail)


def _reject_constant(token: str) -> None:
    fail("REPO-SPEC-CANONICAL-JSON-NON-STANDARD-CONSTANT", token)


def _reject_float(token: str) -> None:
    fail("REPO-SPEC-CANONICAL-JSON-UNSUPPORTED-NUMBER", token)


def _parse_integer(token: str) -> int:
    value = int(token, 10)
    if value < MIN_INTEGER or value > MAX_INTEGER:
        fail("REPO-SPEC-CANONICAL-JSON-UNSUPPORTED-NUMBER", token)
    return value


def _object_from_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            fail("REPO-SPEC-CANONICAL-JSON-DUPLICATE-KEY", key)
        result[key] = value
    return result


def _validate_value(value: Any) -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int) and not isinstance(value, bool):
        if value < MIN_INTEGER or value > MAX_INTEGER:
            fail("REPO-SPEC-CANONICAL-JSON-UNSUPPORTED-NUMBER", str(value))
        return
    if isinstance(value, float):
        fail("REPO-SPEC-CANONICAL-JSON-UNSUPPORTED-NUMBER", repr(value))
    if isinstance(value, str):
        if any(0xD800 <= ord(character) <= 0xDFFF for character in value):
            fail("REPO-SPEC-CANONICAL-JSON-INVALID-UNICODE", "surrogate code point")
        return
    if isinstance(value, list):
        for item in value:
            _validate_value(item)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                fail("REPO-SPEC-CANONICAL-JSON-UNSUPPORTED-VALUE", "non-string object member name")
            _validate_value(key)
            _validate_value(item)
        return
    fail("REPO-SPEC-CANONICAL-JSON-UNSUPPORTED-VALUE", type(value).__name__)


def parse_json_bytes(source: bytes) -> Any:
    try:
        text = source.decode("utf-8")
    except UnicodeDecodeError as exc:
        fail("REPO-SPEC-CANONICAL-JSON-INVALID-UTF8", str(exc))
    if text.startswith("\ufeff"):
        fail("REPO-SPEC-CANONICAL-JSON-INVALID-UTF8", "UTF-8 byte-order mark is forbidden")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_object_from_pairs,
            parse_int=_parse_integer,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except CanonicalJsonFailure:
        raise
    except json.JSONDecodeError as exc:
        fail(
            "REPO-SPEC-CANONICAL-JSON-MALFORMED",
            f"line {exc.lineno} column {exc.colno}: {exc.msg}",
        )
    _validate_value(value)
    return value


def canonical_json_bytes(value: Any) -> bytes:
    _validate_value(value)
    try:
        encoded = reusable_canonical_json_bytes(value, location="canonical-value")
    except ReusableValidationError as exc:
        fail("REPO-SPEC-CANONICAL-JSON-UNSUPPORTED-VALUE", str(exc))
    if encoded.startswith(b"\xef\xbb\xbf") or encoded.endswith(b"\n"):
        fail("REPO-SPEC-CANONICAL-JSON-UNSUPPORTED-VALUE", "serializer violated output boundary")
    return encoded


def canonicalize_bytes(source: bytes) -> bytes:
    return canonical_json_bytes(parse_json_bytes(source))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--canonicalization-version",
        default=CANONICALIZATION_VERSION,
    )
    args = parser.parse_args(argv)

    if args.canonicalization_version != CANONICALIZATION_VERSION:
        print(
            "REPO-SPEC-CANONICAL-JSON-UNSUPPORTED-VERSION: "
            f"{args.canonicalization_version}",
            file=sys.stderr,
        )
        return 1

    try:
        result = canonicalize_bytes(args.input.read_bytes())
    except OSError as exc:
        print(f"REPO-SPEC-CANONICAL-JSON-MALFORMED: {exc}", file=sys.stderr)
        return 1
    except CanonicalJsonFailure as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.output is None:
        sys.stdout.buffer.write(result)
    else:
        try:
            args.output.write_bytes(result)
        except OSError as exc:
            print(f"REPO-SPEC-CANONICAL-JSON-MALFORMED: {exc}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
