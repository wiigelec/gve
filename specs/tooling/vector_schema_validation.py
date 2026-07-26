"""Schema loading helpers for Issue 84 vector tooling."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_ROOT = ROOT / "specs/schemas"


def schema_validator(schema_name: str) -> Draft202012Validator:
    schema_path = SCHEMA_ROOT / schema_name
    schema = json.loads(schema_path.read_text())
    return Draft202012Validator(schema)
