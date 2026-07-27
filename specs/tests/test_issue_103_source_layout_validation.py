from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from specs.tooling.source_layout import (
    SourceLayoutValidationError,
    validate_source_layout,
)
from specs.tooling.strict_json import load_strict


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
AUTHORITY_PATH = (
    REPOSITORY_ROOT / "specs" / "source-layout" / "GVE-SOURCE-LAYOUT.json"
)


class SourceLayoutValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document = load_strict(AUTHORITY_PATH)

    def test_current_repository_is_completely_classified(self) -> None:
        evidence = validate_source_layout(REPOSITORY_ROOT, self.document)
        self.assertEqual(
            evidence["classified_paths"],
            [
                "src/gve/__init__.py",
                "src/gve/__main__.py",
                "src/gve/cli.py",
                "src/gve/core.py",
                "src/gve/processing_failure.py",
            ],
        )
        self.assertEqual(
            evidence["grandfathered_paths"],
            ["src/gve/processing_failure.py"],
        )

    def _make_repository(self) -> tuple[tempfile.TemporaryDirectory, Path]:
        context = tempfile.TemporaryDirectory()
        self.addCleanup(context.cleanup)
        root = Path(context.name)
        authority = root / "specs" / "source-layout" / "GVE-SOURCE-LAYOUT.json"
        authority.parent.mkdir(parents=True)
        authority.write_text(json.dumps(self.document), encoding="utf-8")
        package = root / "src" / "gve"
        package.mkdir(parents=True)
        for item in self.document["current_tree_classification"]:
            path = root / item["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")
        return context, root

    def test_unclassified_path_is_rejected(self) -> None:
        _context, root = self._make_repository()
        (root / "src/gve/extra.py").write_text("", encoding="utf-8")
        with self.assertRaisesRegex(
            SourceLayoutValidationError,
            "classification mismatch",
        ):
            validate_source_layout(root, self.document)

    def test_stale_classification_is_rejected(self) -> None:
        _context, root = self._make_repository()
        (root / "src/gve/core.py").unlink()
        with self.assertRaisesRegex(
            SourceLayoutValidationError,
            "classification mismatch",
        ):
            validate_source_layout(root, self.document)

    def test_prohibited_ownerless_namespace_is_rejected(self) -> None:
        _context, root = self._make_repository()
        path = root / "src/gve/utils/tool.py"
        path.parent.mkdir(parents=True)
        path.write_text("", encoding="utf-8")
        document = copy.deepcopy(self.document)
        document["current_tree_classification"].append(
            {
                "path": "src/gve/utils/tool.py",
                "functional_responsibility": "invalid ownerless support",
                "placement_class": "installed-product-package",
                "status": "active",
                "relocation_required": False,
                "api_boundary": "maintained-internal",
            }
        )
        with self.assertRaisesRegex(
            SourceLayoutValidationError,
            "ownerless namespace",
        ):
            validate_source_layout(root, document)

    def test_milestone_name_is_rejected(self) -> None:
        _context, root = self._make_repository()
        path = root / "src/gve/stage_2.py"
        path.write_text("", encoding="utf-8")
        document = copy.deepcopy(self.document)
        document["current_tree_classification"].append(
            {
                "path": "src/gve/stage_2.py",
                "functional_responsibility": "invalid chronological module",
                "placement_class": "installed-product-package",
                "status": "active",
                "relocation_required": False,
                "api_boundary": "maintained-internal",
                "root_role": "broad-orchestration",
            }
        )
        with self.assertRaisesRegex(
            SourceLayoutValidationError,
            "prohibited maintained product name",
        ):
            validate_source_layout(root, document)

    def test_invalid_plugin_action_path_is_rejected(self) -> None:
        _context, root = self._make_repository()
        path = root / "src/gve/plugins/example/actions/copy.py"
        path.parent.mkdir(parents=True)
        path.write_text("", encoding="utf-8")
        document = copy.deepcopy(self.document)
        document["current_tree_classification"].append(
            {
                "path": "src/gve/plugins/example/actions/copy.py",
                "functional_responsibility": "invalid action module",
                "placement_class": "installed-product-package",
                "status": "active",
                "relocation_required": False,
                "api_boundary": "maintained-internal",
            }
        )
        with self.assertRaisesRegex(
            SourceLayoutValidationError,
            "invalid plugin action path",
        ):
            validate_source_layout(root, document)

    def test_unauthorized_nested_plugin_namespace_is_rejected(self) -> None:
        _context, root = self._make_repository()
        path = root / "src/gve/plugins/example/internal/worker.py"
        path.parent.mkdir(parents=True)
        path.write_text("", encoding="utf-8")
        document = copy.deepcopy(self.document)
        document["current_tree_classification"].append(
            {
                "path": "src/gve/plugins/example/internal/worker.py",
                "functional_responsibility": "unauthorized nested plugin support",
                "placement_class": "installed-product-package",
                "status": "active",
                "relocation_required": False,
                "api_boundary": "maintained-internal",
            }
        )
        with self.assertRaisesRegex(
            SourceLayoutValidationError,
            "unauthorized nested plugin namespace",
        ):
            validate_source_layout(root, document)

    def test_reserved_dependency_namespace_fails_closed(self) -> None:
        _context, root = self._make_repository()
        path = root / "src/gve/validation/check.py"
        path.parent.mkdir(parents=True)
        path.write_text("", encoding="utf-8")
        document = copy.deepcopy(self.document)
        document["current_tree_classification"].append(
            {
                "path": "src/gve/validation/check.py",
                "functional_responsibility": "future validation functionality",
                "placement_class": "installed-product-package",
                "status": "active",
                "relocation_required": False,
                "api_boundary": "maintained-internal",
            }
        )
        with self.assertRaisesRegex(
            SourceLayoutValidationError,
            "reserved dependency namespace now exists",
        ):
            validate_source_layout(root, document)


    def test_product_import_backflow_is_rejected(self) -> None:
        _context, root = self._make_repository()
        (root / "src/gve/core.py").write_text(
            "import specs.tooling.validate\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(
            SourceLayoutValidationError,
            "forbidden dependency imports",
        ):
            validate_source_layout(root, self.document)

    def test_active_single_feature_root_module_is_rejected(self) -> None:
        _context, root = self._make_repository()
        path = root / "src/gve/single_feature.py"
        path.write_text("", encoding="utf-8")
        document = copy.deepcopy(self.document)
        document["current_tree_classification"].append(
            {
                "path": "src/gve/single_feature.py",
                "functional_responsibility": "narrow single-feature implementation",
                "placement_class": "installed-product-package",
                "status": "active",
                "relocation_required": False,
                "api_boundary": "maintained-internal",
                "root_role": "grandfathered-single-feature",
            }
        )
        with self.assertRaisesRegex(
            SourceLayoutValidationError,
            "prohibited root role",
        ):
            validate_source_layout(root, document)

    def test_root_role_api_boundary_conflict_is_rejected(self) -> None:
        _context, root = self._make_repository()
        document = copy.deepcopy(self.document)
        item = next(
            entry
            for entry in document["current_tree_classification"]
            if entry["path"] == "src/gve/cli.py"
        )
        item["api_boundary"] = "maintained-internal"
        with self.assertRaisesRegex(
            SourceLayoutValidationError,
            "API boundary conflict",
        ):
            validate_source_layout(root, document)


    def test_grandfathered_root_requires_successor(self) -> None:
        _context, root = self._make_repository()
        document = copy.deepcopy(self.document)
        item = next(
            entry
            for entry in document["current_tree_classification"]
            if entry["path"] == "src/gve/processing_failure.py"
        )
        del item["successor_requirement"]
        with self.assertRaisesRegex(
            SourceLayoutValidationError,
            "lacks successor requirement",
        ):
            validate_source_layout(root, document)


if __name__ == "__main__":
    unittest.main()
