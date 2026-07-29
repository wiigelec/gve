from __future__ import annotations

from typing import Any

from .contracts import ValidationError


_MIN_INTEGER = -(2**63)
_MAX_INTEGER = 2**63 - 1


def _escape_string(value: str, *, location: str) -> str:
    pieces: list[str] = ['"']
    for character in value:
        codepoint = ord(character)
        if 0xD800 <= codepoint <= 0xDFFF:
            raise ValidationError(f"{location}: surrogate code point is forbidden")
        if character == '"':
            pieces.append(r'\"')
        elif character == "\\":
            pieces.append(r"\\")
        elif character == "\b":
            pieces.append(r"\b")
        elif character == "\f":
            pieces.append(r"\f")
        elif character == "\n":
            pieces.append(r"\n")
        elif character == "\r":
            pieces.append(r"\r")
        elif character == "\t":
            pieces.append(r"\t")
        elif codepoint < 0x20:
            pieces.append(f"\\u{codepoint:04x}")
        else:
            pieces.append(character)
    pieces.append('"')
    return "".join(pieces)


def _canonical_text(value: Any, *, location: str) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, int) and not isinstance(value, bool):
        if value < _MIN_INTEGER or value > _MAX_INTEGER:
            raise ValidationError(f"{location}: integer is outside signed-64-bit range")
        return str(value)
    if isinstance(value, float):
        raise ValidationError(f"{location}: fractions and exponents are forbidden")
    if isinstance(value, str):
        return _escape_string(value, location=location)
    if isinstance(value, list):
        return "[" + ",".join(
            _canonical_text(item, location=f"{location}[{index}]")
            for index, item in enumerate(value)
        ) + "]"
    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise ValidationError(f"{location}: object member names must be strings")
        members = []
        for key in sorted(value):
            rendered_key = _escape_string(key, location=f"{location}.<member-name>")
            rendered_value = _canonical_text(
                value[key], location=f"{location}.{key}"
            )
            members.append(f"{rendered_key}:{rendered_value}")
        return "{" + ",".join(members) + "}"
    raise ValidationError(
        f"{location}: unsupported canonical JSON value type {type(value).__name__}"
    )


def canonical_json_bytes(value: Any, *, location: str = "value") -> bytes:
    return _canonical_text(value, location=location).encode("utf-8")
