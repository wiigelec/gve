from __future__ import annotations

import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = ROOT / "validation/intrinsic/validate_repository_completeness.py"


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "repository_completeness_validator_tests", VALIDATOR_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = load_validator()


def _create_minimal_repo(temp: Path) -> Path:
    spec_root = temp / "specification-system" / "repo"
    shutil.copytree(ROOT, spec_root)

    docs_overview = temp / "docs" / "overview"
    docs_overview.mkdir(parents=True, exist_ok=True)
    (docs_overview / "PRODUCT-OVERVIEW.md").write_text(
        "# Product Overview\n\n## Status\n\nDirectional and non-normative.\n",
        encoding="utf-8",
    )

    docs_plans = temp / "docs" / "plans"
    docs_plans.mkdir(parents=True, exist_ok=True)
    (docs_plans / "REPOSITORY-FRAMEWORK-CONSTRUCTION-PLAN.md").write_text(
        "# Plan\n\n## Status\n\nNon-normative.\n",
        encoding="utf-8",
    )

    return spec_root


class RepositoryCompletenessTests(unittest.TestCase):
    def test_all_completeness_checks_pass(self) -> None:
        VALIDATOR.validate(ROOT)

    def test_missing_overview_dir_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            spec_root = temp / "specification-system" / "repo"
            shutil.copytree(ROOT, spec_root)
            temp.mkdir(parents=True, exist_ok=True)
            with self.assertRaisesRegex(
                VALIDATOR.ValidationFailure,
                "REPO-COMPLETENESS-OVERVIEW-001",
            ):
                VALIDATOR.validate(spec_root)

    def test_overview_missing_non_normative_declaration_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            spec_root = _create_minimal_repo(temp)
            overview_path = temp / "docs" / "overview" / "PRODUCT-OVERVIEW.md"
            overview_path.write_text(
                "# Overview\n\n## Status\n\nNo declaration here.\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                VALIDATOR.ValidationFailure,
                "REPO-COMPLETENESS-OVERVIEW-003",
            ):
                VALIDATOR.validate(spec_root)

    def test_plan_missing_non_normative_declaration_fails(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            spec_root = _create_minimal_repo(temp)
            plan_path = temp / "docs" / "plans" / "REPOSITORY-FRAMEWORK-CONSTRUCTION-PLAN.md"
            plan_path.write_text(
                "# Plan\n\n## Status\n\nNo declaration here.\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                VALIDATOR.ValidationFailure,
                "REPO-COMPLETENESS-PLAN-003",
            ):
                VALIDATOR.validate(spec_root)

    def test_missing_framework_boundary_fails_initialization(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            spec_root = _create_minimal_repo(temp)
            (spec_root / "authoritative/framework-boundary/FRAMEWORK-BOUNDARY.json").unlink()
            with self.assertRaisesRegex(
                VALIDATOR.ValidationFailure,
                "REPO-COMPLETENESS-INIT-001",
            ):
                VALIDATOR.validate(spec_root)

    def test_missing_git_model_fails_release(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            spec_root = _create_minimal_repo(temp)
            (spec_root / "authoritative/git-model/GIT-MODEL.json").unlink()
            with self.assertRaisesRegex(
                VALIDATOR.ValidationFailure,
                "REPO-COMPLETENESS-RELEASE-001",
            ):
                VALIDATOR.validate(spec_root)


if __name__ == "__main__":
    unittest.main()
