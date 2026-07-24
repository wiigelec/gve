from __future__ import annotations

import json
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
README = REPOSITORY_ROOT / "README.md"
LEVEL_2_JSON = REPOSITORY_ROOT / "specs/levels/level-2/GVE-LEVEL-2.json"
LEVEL_3_JSON = REPOSITORY_ROOT / "specs/levels/level-3/GVE-LEVEL-3.json"


class AuthorityDiscoveryMigrationTests(unittest.TestCase):
    def test_deleted_root_level_documents_are_absent_from_current_authority(self) -> None:
        self.assertFalse((REPOSITORY_ROOT / "LEVEL_2.md").exists())
        self.assertFalse((REPOSITORY_ROOT / "LEVEL_3.md").exists())

        readme = README.read_text(encoding="utf-8")
        self.assertNotIn("LEVEL_2.md", readme)
        self.assertNotIn("LEVEL_3.md", readme)
        self.assertIn("specs/levels/level-0", readme)
        self.assertIn("specs/levels/level-3", readme)
        self.assertIn("through", readme)

    def test_normative_roots_contain_no_legacy_document_references(self) -> None:
        level_2_text = LEVEL_2_JSON.read_text(encoding="utf-8")
        level_3_text = LEVEL_3_JSON.read_text(encoding="utf-8")

        self.assertNotIn("LEVEL_2.md", level_2_text)
        self.assertNotIn("LEVEL_3.md", level_3_text)
        self.assertNotIn("TRANSITIONAL-LEVEL-2-MATERIAL", level_2_text)
        self.assertNotIn("HISTORICAL-LEVEL-3-MATERIAL", level_3_text)

        level_2 = json.loads(level_2_text)
        level_3 = json.loads(level_3_text)
        self.assertNotIn(
            "historical",
            " ".join(level_2["scope"]["includes"]).lower(),
        )
        self.assertNotIn(
            "historical",
            " ".join(level_3["scope"]["includes"]).lower(),
        )


if __name__ == "__main__":
    unittest.main()
