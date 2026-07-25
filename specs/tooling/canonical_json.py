"""GVE canonical JSON serialization for normative revision identities."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from typing import Any


CANONICALIZATION = "gve-canonical-json-v1"
DIGEST_ALGORITHM = "sha256"
IDENTITY_FORMAT = f"{CANONICALIZATION}+{DIGEST_ALGORITHM}:lowercase-hex"
MIN_INTEGER = -(2**63)
MAX_INTEGER = 2**63 - 1


class CanonicalJsonError(ValueError):
    """Raised when a value cannot be serialized by the GVE canonical form."""


def _string(value: str) -> str:
    pieces = ['"']
    escapes = {
        '"': '\\"',
        '\\': '\\\\',
        '\b': '\\b',
        '\t': '\\t',
        '\n': '\\n',
        '\f': '\\f',
        '\r': '\\r',
    }
    for character in value:
        codepoint = ord(character)
        if 0xD800 <= codepoint <= 0xDFFF:
            raise CanonicalJsonError("surrogate code points are not canonicalizable")
        escaped = escapes.get(character)
        if escaped is not None:
            pieces.append(escaped)
        elif codepoint <= 0x1F:
            pieces.append(f"\\u{codepoint:04x}")
        else:
            pieces.append(character)
    pieces.append('"')
    return "".join(pieces)


def _serialize(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int):
        if value < MIN_INTEGER or value > MAX_INTEGER:
            raise CanonicalJsonError(
                "integers must be within the signed 64-bit canonical range"
            )
        return str(value)
    if isinstance(value, float):
        raise CanonicalJsonError("floating-point values are not canonicalizable")
    if isinstance(value, str):
        return _string(value)
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise CanonicalJsonError("object member names must be strings")
        ordered = sorted(value)
        return "{" + ",".join(
            _string(key) + ":" + _serialize(value[key]) for key in ordered
        ) + "}"
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return "[" + ",".join(_serialize(item) for item in value) + "]"
    raise CanonicalJsonError(
        f"unsupported canonical JSON value type: {type(value).__name__}"
    )


def canonical_json(value: Any) -> bytes:
    """Serialize a supported JSON value to exact GVE canonical UTF-8 bytes.

    Objects are ordered by ascending Unicode code point sequence of their member
    names. Arrays retain declared order. Strings are not Unicode-normalized;
    quotation mark, reverse solidus, and controls are escaped deterministically.
    Integers use minimal base-10 form within the signed 64-bit range.
    Floating-point and non-JSON values fail
    closed.
    """
    try:
        return _serialize(value).encode("utf-8")
    except UnicodeEncodeError as exc:
        raise CanonicalJsonError("value is not valid Unicode for UTF-8") from exc


def sha256_identity(value: Any) -> str:
    """Return the lowercase SHA-256 identity of canonical JSON bytes."""
    return hashlib.sha256(canonical_json(value)).hexdigest()
