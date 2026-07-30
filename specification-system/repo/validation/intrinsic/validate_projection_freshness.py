#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

CONSTRUCTION_ROOT = Path(__file__).resolve().parents[2]
if str(CONSTRUCTION_ROOT) not in sys.path:
    sys.path.insert(0, str(CONSTRUCTION_ROOT))

from validation.lib.render_projection import render_document


PROJECTION_MAP: list[tuple[str, str]] = [
    (
        "authoritative/repository-model/REPOSITORY-MODEL.json",
        "derived/markdown/repository-model/REPOSITORY-MODEL.md",
    ),
    (
        "authoritative/framework-boundary/FRAMEWORK-BOUNDARY.json",
        "derived/markdown/framework-boundary/FRAMEWORK-BOUNDARY.md",
    ),
    (
        "authoritative/functional-areas/FUNCTIONAL-AREAS.json",
        "derived/markdown/functional-areas/FUNCTIONAL-AREAS.md",
    ),
    (
        "authoritative/level-model/LEVEL-MODEL.json",
        "derived/markdown/level-model/LEVEL-MODEL.md",
    ),
    (
        "authoritative/specification-system/SPECIFICATION-ARTIFACTS.json",
        "derived/markdown/specification-system/SPECIFICATION-ARTIFACTS.md",
    ),
    (
        "authoritative/specification-system/SPECIFICATION-IDENTITIES.json",
        "derived/markdown/specification-system/SPECIFICATION-IDENTITIES.md",
    ),
]


class ValidationFailure(Exception):
    pass


def validate(root: Path) -> None:
    for source_relative, projection_relative in PROJECTION_MAP:
        source_path = root / source_relative
        projection_path = root / projection_relative

        if not source_path.is_file():
            raise ValidationFailure(
                f"PROJECTION-FRESHNESS-001: source artifact not found: {source_relative}"
            )

        value = json.loads(source_path.read_text(encoding="utf-8"))
        expected = render_document(value, source_relative)

        if not projection_path.is_file():
            raise ValidationFailure(
                f"PROJECTION-FRESHNESS-002: projection not found: {projection_relative}"
            )

        actual = projection_path.read_text(encoding="utf-8")
        if actual != expected:
            raise ValidationFailure(
                f"PROJECTION-FRESHNESS-003: stale projection: {projection_relative} "
                f"(source: {source_relative})"
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate projection freshness for specification-system artifacts"
    )
    parser.add_argument("--root", default=str(CONSTRUCTION_ROOT))
    args = parser.parse_args(argv)
    try:
        validate(Path(args.root))
    except ValidationFailure as exc:
        print(f"projection freshness validation failed: {exc}", file=sys.stderr)
        return 1
    print("projection freshness validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
