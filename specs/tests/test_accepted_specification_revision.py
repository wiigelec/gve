from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from specs.tooling.revision import build_specification_revision
from specs.tooling.strict_json import load_strict
from specs.tooling.validate import discover_specifications, validate_specification_set


ROOT = Path(__file__).resolve().parents[2]
ACCEPTED_SPECS = ROOT / "specs"


def _accepted_documents(specs_root: Path) -> list[dict]:
    return [
        load_strict(path)
        for path in discover_specifications(specs_root)
    ]


class AcceptedSpecificationRevisionTests(unittest.TestCase):
    def test_accepted_graph_has_one_stable_revision(self) -> None:
        documents = _accepted_documents(ACCEPTED_SPECS)
        first = build_specification_revision(documents)
        second = build_specification_revision(documents)

        self.assertEqual(first, second)
        self.assertEqual(first["algorithm"], "sha256")
        self.assertRegex(first["identity"], r"^[0-9a-f]{64}$")
        self.assertEqual(
            len(first["manifest"]["members"]),
            len(documents),
        )

    def test_normal_validation_returns_accepted_revision(self) -> None:
        documents = _accepted_documents(ACCEPTED_SPECS)
        expected = build_specification_revision(documents)
        actual = validate_specification_set(ACCEPTED_SPECS)

        self.assertEqual(actual, expected)

    def test_reversed_discovery_order_preserves_revision(self) -> None:
        documents = _accepted_documents(ACCEPTED_SPECS)
        forward = build_specification_revision(documents)
        reverse = build_specification_revision(list(reversed(documents)))

        self.assertEqual(forward, reverse)

    def test_every_discovered_normative_document_participates_once(self) -> None:
        documents = _accepted_documents(ACCEPTED_SPECS)
        revision = build_specification_revision(documents)
        expected = sorted(
            document["specification"]["id"]
            for document in documents
        )
        actual = [
            member["id"]
            for member in revision["manifest"]["members"]
        ]

        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), len(set(actual)))

    def test_markdown_projection_change_does_not_change_revision(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        copied_specs = Path(temporary.name) / "specs"
        shutil.copytree(
            ACCEPTED_SPECS,
            copied_specs,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )

        before = build_specification_revision(
            _accepted_documents(copied_specs)
        )
        markdown = sorted((copied_specs / "levels").rglob("*.md"))[0]
        markdown.write_text(
            markdown.read_text(encoding="utf-8")
            + "\nNon-authoritative projection mutation.\n",
            encoding="utf-8",
        )
        after = build_specification_revision(
            _accepted_documents(copied_specs)
        )

        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
