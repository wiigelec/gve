from __future__ import annotations

import hashlib
import re
from typing import Any, Iterable, Mapping

from .canonical_json import canonical_json


CORE_AUTHORITY_KIND = "gve-core-specification"
PLUGIN_AUTHORITY_KIND = "gve-plugin-instruction-set"
GOVERNANCE_BINDING_FORMAT = "gve-governance-binding-v1"
IDENTITY_FORMAT = "gve-canonical-json-v1+sha256:lowercase-hex"

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_KINDS = {CORE_AUTHORITY_KIND, PLUGIN_AUTHORITY_KIND}


class GovernanceBindingError(ValueError):
    pass


def _identity(value: Any, location: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise GovernanceBindingError(
            f"{location} must be exactly sixty-four lowercase hexadecimal characters"
        )
    return value


def _authority_component(value: Any, location: str) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise GovernanceBindingError(f"{location} must be an object")
    expected = {"authority_id", "authority_kind", "revision"}
    if set(value) != expected:
        raise GovernanceBindingError(
            f"{location} must contain exactly authority_id, authority_kind, and revision"
        )
    authority_id = value["authority_id"]
    authority_kind = value["authority_kind"]
    if not isinstance(authority_id, str) or not authority_id:
        raise GovernanceBindingError(f"{location}.authority_id must be nonempty")
    if authority_kind not in _ALLOWED_KINDS:
        raise GovernanceBindingError(f"{location}.authority_kind is unknown")
    return {
        "authority_id": authority_id,
        "authority_kind": authority_kind,
        "revision": _identity(value["revision"], f"{location}.revision"),
    }


def canonical_governance_binding(
    core_revision: str,
    plugin_authorities: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    core = {
        "authority_id": "gve-core",
        "authority_kind": CORE_AUTHORITY_KIND,
        "revision": _identity(core_revision, "core_revision"),
    }
    plugins = [
        _authority_component(value, f"plugin_authorities[{index}]")
        for index, value in enumerate(plugin_authorities)
    ]
    if any(item["authority_kind"] != PLUGIN_AUTHORITY_KIND for item in plugins):
        raise GovernanceBindingError(
            "plugin_authorities may contain only plugin instruction-set authorities"
        )
    plugins.sort(key=lambda item: item["authority_id"])
    identities = [item["authority_id"] for item in plugins]
    if len(identities) != len(set(identities)):
        raise GovernanceBindingError("plugin authority identities must be unique")
    return {
        "binding_format": GOVERNANCE_BINDING_FORMAT,
        "identity_format": IDENTITY_FORMAT,
        "authorities": [core, *plugins],
    }


def governance_binding_identity(binding: Mapping[str, Any]) -> str:
    validate_governance_binding(binding)
    return hashlib.sha256(canonical_json(binding)).hexdigest()


def validate_governance_binding(binding: Any) -> None:
    if not isinstance(binding, Mapping):
        raise GovernanceBindingError("governance binding must be an object")
    expected = {"binding_format", "identity_format", "authorities"}
    if set(binding) != expected:
        raise GovernanceBindingError(
            "governance binding must contain exactly binding_format, identity_format, and authorities"
        )
    if binding["binding_format"] != GOVERNANCE_BINDING_FORMAT:
        raise GovernanceBindingError("unsupported governance binding format")
    if binding["identity_format"] != IDENTITY_FORMAT:
        raise GovernanceBindingError("unsupported governance binding identity format")
    authorities = binding["authorities"]
    if not isinstance(authorities, list) or not authorities:
        raise GovernanceBindingError("authorities must be a nonempty array")
    normalized = [
        _authority_component(value, f"authorities[{index}]")
        for index, value in enumerate(authorities)
    ]
    core = [item for item in normalized if item["authority_kind"] == CORE_AUTHORITY_KIND]
    if len(core) != 1 or core[0]["authority_id"] != "gve-core":
        raise GovernanceBindingError(
            "binding must contain exactly one gve-core specification authority"
        )
    plugins = [
        item for item in normalized if item["authority_kind"] == PLUGIN_AUTHORITY_KIND
    ]
    expected_order = [core[0], *sorted(plugins, key=lambda item: item["authority_id"])]
    if normalized != expected_order:
        raise GovernanceBindingError(
            "authorities must contain core first and plugins ordered by authority_id"
        )
    identities = [item["authority_id"] for item in normalized]
    if len(identities) != len(set(identities)):
        raise GovernanceBindingError("authority identities must be unique")


def require_current_authorities(
    binding: Mapping[str, Any],
    current_revisions: Mapping[tuple[str, str], str],
) -> None:
    validate_governance_binding(binding)
    for authority in binding["authorities"]:
        key = (authority["authority_kind"], authority["authority_id"])
        current = current_revisions.get(key)
        if current is None:
            raise GovernanceBindingError(
                f"current authority is missing for {authority['authority_id']}"
            )
        if _identity(current, f"current_revisions[{key!r}]") != authority["revision"]:
            raise GovernanceBindingError(
                f"authority is stale for {authority['authority_id']}"
            )
