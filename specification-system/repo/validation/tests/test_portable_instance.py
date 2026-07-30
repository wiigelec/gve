from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "validation/intrinsic/validate_portable.py"
FIXTURES = ROOT / "validation/fixtures/portable"


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "portable_instance_validator_tests", VALIDATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator()
PortableValidator = VALIDATOR.PortableValidator


class PortableInstanceTests(unittest.TestCase):
    def _assert_valid(self, name: str) -> None:
        v = PortableValidator(FIXTURES / name)
        ok, errors = v.validate()
        if not ok:
            self.fail(f"{name}: expected PASS, got FAIL: {'; '.join(errors)}")

    def _assert_invalid(self, name: str) -> None:
        v = PortableValidator(FIXTURES / name)
        ok, errors = v.validate()
        if ok:
            self.fail(f"{name}: expected FAIL, got PASS")

    def test_minimal_valid(self) -> None:
        self._assert_valid("minimal-valid")

    def test_cli_product(self) -> None:
        self._assert_valid("cli-product")

    def test_library_product(self) -> None:
        self._assert_valid("library-product")

    def test_github_profile(self) -> None:
        self._assert_valid("github-profile")

    def test_copied_subset(self) -> None:
        self._assert_valid("copied-subset")

    def test_with_extensions(self) -> None:
        self._assert_valid("with-extensions")

    def test_missing_overview_fails(self) -> None:
        self._assert_invalid("missing-overview")

    def test_missing_plan_fails(self) -> None:
        self._assert_invalid("missing-plan")

    def test_missing_manifest_fails(self) -> None:
        self._assert_invalid("missing-manifest")


class PortableValidatorDirectTests(unittest.TestCase):
    def test_overview_without_non_normative_fails(self) -> None:
        from pathlib import Path
        import tempfile, shutil
        with tempfile.TemporaryDirectory() as d:
            temp = Path(d)
            (temp / "docs/overview").mkdir(parents=True)
            (temp / "docs/overview/PRODUCT-OVERVIEW.md").write_text(
                "# Overview\n\n## Status\n\nNo declaration.\n"
            )
            (temp / "docs/plans").mkdir(parents=True)
            (temp / "docs/plans/IMPLEMENTATION-PLAN.md").write_text(
                "# Plan\n\n## Status\n\nNon-normative.\n"
            )
            (temp / "specification-system/repo").mkdir(parents=True)
            (temp / "specification-system/repo/REPOSITORY-SPECIFICATION-SET.json").write_text(
                '{"construction_identity": "test"}\n'
            )
            v = PortableValidator(temp)
            ok, errors = v.validate()
            self.assertFalse(ok)
            self.assertTrue(any("PORTABLE-CONTENT-001" in e for e in errors))

    def test_bad_manifest_json_fails(self) -> None:
        from pathlib import Path
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            temp = Path(d)
            (temp / "docs/overview").mkdir(parents=True)
            (temp / "docs/overview/PRODUCT-OVERVIEW.md").write_text(
                "# Overview\n\n## Status\n\nDirectional and non-normative.\n"
            )
            (temp / "docs/plans").mkdir(parents=True)
            (temp / "docs/plans/IMPLEMENTATION-PLAN.md").write_text(
                "# Plan\n\n## Status\n\nNon-normative.\n"
            )
            (temp / "specification-system/repo").mkdir(parents=True)
            (temp / "specification-system/repo/REPOSITORY-SPECIFICATION-SET.json").write_text(
                "not json\n"
            )
            v = PortableValidator(temp)
            ok, errors = v.validate()
            self.assertFalse(ok)
            self.assertTrue(any("PORTABLE-CONTENT-004" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
