from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping
import re

from .errors import PayloadError


_REPOSITORY_IDENTITY = re.compile(r"^[^/\s]+/[^/\s]+$")
_HEAD = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class RepositoryExpectations:
    identity: str | None = None
    branch: str | None = None
    head: str | None = None


@dataclass(frozen=True)
class MacroRequest:
    schema_version: int
    repository: RepositoryExpectations
    macro_name: str
    parameters: Mapping[str, object]


def _object(value: object, field: str) -> dict:
    if not isinstance(value, dict):
        raise PayloadError(f"{field} must be an object")
    return value


def _closed(obj: dict, expected: set[str], field: str) -> None:
    observed = set(obj)
    if observed != expected:
        missing = sorted(expected - observed)
        extra = sorted(observed - expected)
        raise PayloadError(
            f"{field} has invalid fields",
            details={"field": field, "missing": missing, "extra": extra},
        )


def _optional_string(
    obj: dict,
    name: str,
    field: str,
    *,
    pattern: re.Pattern[str] | None = None,
) -> str | None:
    if name not in obj:
        return None
    value = obj[name]
    if not isinstance(value, str) or not value:
        raise PayloadError(f"{field}.{name} must be a non-empty string when present")
    if pattern is not None and pattern.fullmatch(value) is None:
        raise PayloadError(f"{field}.{name} has invalid format")
    return value


def parse_macro_request(value: object) -> MacroRequest:
    request = _object(value, "request")
    _closed(request, {"schema_version", "header", "macro"}, "request")

    schema_version = request["schema_version"]
    if type(schema_version) is not int or schema_version != 1:
        raise PayloadError("request.schema_version must be integer 1")

    header = _object(request["header"], "request.header")
    _closed(header, {"repository"}, "request.header")

    repository = _object(header["repository"], "request.header.repository")
    extra_repository = set(repository) - {"identity", "branch", "head"}
    if extra_repository:
        raise PayloadError(
            "request.header.repository has invalid fields",
            details={
                "field": "request.header.repository",
                "missing": [],
                "extra": sorted(extra_repository),
            },
        )

    expectations = RepositoryExpectations(
        identity=_optional_string(
            repository,
            "identity",
            "request.header.repository",
            pattern=_REPOSITORY_IDENTITY,
        ),
        branch=_optional_string(repository, "branch", "request.header.repository"),
        head=_optional_string(
            repository,
            "head",
            "request.header.repository",
            pattern=_HEAD,
        ),
    )

    macro = _object(request["macro"], "request.macro")
    _closed(macro, {"name", "parameters"}, "request.macro")

    name = macro["name"]
    if not isinstance(name, str) or not name:
        raise PayloadError("request.macro.name must be a non-empty string")

    parameters = _object(macro["parameters"], "request.macro.parameters")

    return MacroRequest(
        schema_version=1,
        repository=expectations,
        macro_name=name,
        parameters=MappingProxyType(dict(parameters)),
    )
