from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from specs.tooling.validate_identity import (
    IdentityIntegrationError,
    validate_repository_identity,
)


ROOT = Path(__file__).resolve().parents[1]


class Issue76RepositoryIntegrationTests(unittest.TestCase):
    def test_repository_identity_integration_passes(self) -> None:
        validate_repository_identity(ROOT)

    def test_manifest_binding_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = json.loads(
                (ROOT / "GVE-SPECIFICATION-SET.json").read_text(encoding="utf-8")
            )
            manifest.pop("identity_framework")
            (root / "GVE-SPECIFICATION-SET.json").write_text(
                json.dumps(manifest),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                IdentityIntegrationError,
                "lacks identity_framework binding",
            ):
                validate_repository_identity(root)


if __name__ == "__main__":
    unittest.main()
