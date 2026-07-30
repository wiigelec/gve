#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


class ValidationFailure(Exception):
    pass


ValidationResult = tuple[bool, list[str]]


class PortableValidator:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.errors: list[str] = []

    def _err(self, code: str, message: str) -> None:
        self.errors.append(f"{code}: {message}")

    def _check_path(self, *parts: str) -> Path | None:
        path = self.root.joinpath(*parts)
        if not path.exists():
            self._err("PORTABLE-PATH-001", f"required path not found: {'/'.join(parts)}")
            return None
        return path

    def _check_file(self, *parts: str) -> str | None:
        path = self._check_path(*parts)
        if path is None:
            return None
        if not path.is_file():
            self._err("PORTABLE-PATH-002", f"required file not found: {'/'.join(parts)}")
            return None
        return path.read_text(encoding="utf-8")

    def _has_non_normative(self, text: str) -> bool:
        return bool(re.search(r"(?i)non[- ]normative", text))

    def validate(self) -> ValidationResult:
        self.errors = []

        self._check_directory("docs")
        self._check_directory("docs", "overview")
        self._check_directory("docs", "plans")

        overview_text = self._check_file("docs", "overview", "PRODUCT-OVERVIEW.md")
        plan_text = self._check_file("docs", "plans", "IMPLEMENTATION-PLAN.md")
        spec_root = self._check_path("specification-system", "repo")
        manifest_path = (
            self.root / "specification-system" / "repo" / "REPOSITORY-SPECIFICATION-SET.json"
            if spec_root
            else None
        )

        if overview_text is not None and not self._has_non_normative(overview_text):
            self._err(
                "PORTABLE-CONTENT-001",
                "docs/overview/PRODUCT-OVERVIEW.md must declare non-normative status",
            )

        if plan_text is not None and not self._has_non_normative(plan_text):
            self._err(
                "PORTABLE-CONTENT-002",
                "docs/plans/IMPLEMENTATION-PLAN.md must declare non-normative status",
            )

        if manifest_path is not None and manifest_path.is_file():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                if not isinstance(manifest.get("construction_identity"), str):
                    self._err(
                        "PORTABLE-CONTENT-003",
                        "specification-system/repo/REPOSITORY-SPECIFICATION-SET.json "
                        "must have construction_identity",
                    )
            except (json.JSONDecodeError, ValueError, OSError) as exc:
                self._err(
                    "PORTABLE-CONTENT-004",
                    f"specification-system/repo/REPOSITORY-SPECIFICATION-SET.json: {exc}",
                )
        elif manifest_path is not None:
            self._err(
                "PORTABLE-PATH-002",
                "required file not found: specification-system/repo/REPOSITORY-SPECIFICATION-SET.json",
            )

        return (len(self.errors) == 0, self.errors)

    def _check_directory(self, *parts: str) -> Path | None:
        path = self.root.joinpath(*parts)
        if not path.is_dir():
            self._err("PORTABLE-PATH-001", f"required directory not found: {'/'.join(parts)}")
            return None
        return path


def validate(root: Path) -> None:
    validator = PortableValidator(root)
    ok, errors = validator.validate()
    if not ok:
        raise ValidationFailure("; ".join(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a repository against framework-level requirements"
    )
    parser.add_argument("root", type=Path, help="Path to the target repository")
    args = parser.parse_args(argv)
    try:
        validate(args.root)
    except ValidationFailure as exc:
        print(f"portable instance validation failed: {exc}", file=sys.stderr)
        return 1
    print(f"portable instance validation passed: {args.root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
