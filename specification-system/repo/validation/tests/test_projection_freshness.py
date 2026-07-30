from __future__ import annotations

import importlib.util
import json
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "validation/intrinsic/validate_projection_freshness.py"


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "projection_freshness_validator_tests", VALIDATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator()


_PROJECTION_SOURCES: list[str] = [
    p[0] for p in VALIDATOR.PROJECTION_MAP
]
_PROJECTION_TARGETS: list[str] = [
    p[1] for p in VALIDATOR.PROJECTION_MAP
]


class ProjectionFreshnessTests(unittest.TestCase):
    def test_all_projections_exist_and_are_fresh(self) -> None:
        VALIDATOR.validate(ROOT)

    def test_missing_projection_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            copy_root = Path(directory) / "repo"
            shutil.copytree(ROOT, copy_root)
            target = copy_root / _PROJECTION_TARGETS[0]
            target.unlink()
            with self.assertRaisesRegex(
                VALIDATOR.ValidationFailure,
                "PROJECTION-FRESHNESS-002",
            ):
                VALIDATOR.validate(copy_root)

    def test_stale_projection_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            copy_root = Path(directory) / "repo"
            shutil.copytree(ROOT, copy_root)
            target = copy_root / _PROJECTION_TARGETS[0]
            target.write_text("# Stale content\n", encoding="utf-8")
            with self.assertRaisesRegex(
                VALIDATOR.ValidationFailure,
                "PROJECTION-FRESHNESS-003",
            ):
                VALIDATOR.validate(copy_root)

    def test_missing_source_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            copy_root = Path(directory) / "repo"
            shutil.copytree(ROOT, copy_root)
            source = copy_root / _PROJECTION_SOURCES[0]
            source.unlink()
            with self.assertRaisesRegex(
                VALIDATOR.ValidationFailure,
                "PROJECTION-FRESHNESS-001",
            ):
                VALIDATOR.validate(copy_root)

    def test_determinism_all_projections(self) -> None:
        from validation.lib.render_projection import render_document

        for source_rel, proj_rel in VALIDATOR.PROJECTION_MAP:
            source_path = ROOT / source_rel
            proj_path = ROOT / proj_rel
            value = json.loads(source_path.read_text(encoding="utf-8"))
            expected = render_document(value, source_rel)
            actual = proj_path.read_text(encoding="utf-8")
            self.assertEqual(
                expected,
                actual,
                f"projection not fresh: {proj_rel} (regenerate required)",
            )


if __name__ == "__main__":
    unittest.main()
