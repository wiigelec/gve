from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "product" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from gve.product_macro_registry import product_macro_registry


def _variants(schema):
    assert schema["type"] == "object"
    variants = schema["oneOf"]
    assert len(variants) == 3
    return {v["properties"]["operation"]["enum"][0]: v for v in variants}


def _closed(v, required, props):
    assert v["additionalProperties"] is False
    assert set(v["required"]) == set(required)
    assert set(v["properties"]) == set(props)


def validate_macro_contracts() -> bool:
    macros = product_macro_registry()
    issue = _variants(macros.resolve("issue").parameter_schema)
    assert set(issue) == {"read", "create", "modify"}
    _closed(issue["read"], {"operation", "number"}, {"operation", "number"})
    _closed(issue["create"], {"operation", "title"}, {"operation", "title", "body", "labels"})
    _closed(issue["modify"], {"operation", "number"}, {"operation", "number", "title", "body", "labels", "state"})
    assert {tuple(x["required"]) for x in issue["modify"]["anyOf"]} == {( "title",), ("body",), ("labels",), ("state",)}

    pr = _variants(macros.resolve("pr").parameter_schema)
    assert set(pr) == {"read", "create", "modify"}
    _closed(pr["read"], {"operation", "number"}, {"operation", "number"})
    _closed(pr["create"], {"operation", "title", "base", "head"}, {"operation", "title", "body", "base", "head", "draft"})
    _closed(pr["modify"], {"operation", "number"}, {"operation", "number", "title", "body", "base", "state"})
    assert {tuple(x["required"]) for x in pr["modify"]["anyOf"]} == {( "title",), ("body",), ("base",), ("state",)}

    modify = macros.resolve("modify").parameter_schema
    assert modify["type"] == "object" and modify["additionalProperties"] is False
    variants = {v["properties"]["operation"]["enum"][0]: v for v in modify["properties"]["changes"]["items"]["oneOf"]}
    assert set(variants) == {"create", "modify"}
    _closed(variants["create"], {"operation", "path", "content"}, {"operation", "path", "content"})
    _closed(variants["modify"], {"operation", "path", "content", "expected_sha256"}, {"operation", "path", "content", "expected_sha256"})
    assert modify["properties"]["changes"]["x-gve-unique-path-field-after-normalization"] == "path"
    assert modify["properties"]["allowed_dirty_paths"]["x-gve-unique-after-normalization"] is True
    assert modify["properties"]["remote_branch"]["x-gve-format"] == "git-branch"
    return True
