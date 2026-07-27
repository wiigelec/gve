from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
VECTOR_ROOT = REPOSITORY_ROOT / "specs" / "tests" / "fixtures" / "issue_84" / "canonical-success"


class CoreCanonicalSuccessTests(unittest.TestCase):
    def test_package_entry_point_matches_authoritative_vector_exactly(self) -> None:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(SOURCE_ROOT)
        with tempfile.TemporaryDirectory(prefix="gve-core-") as temporary:
            completed = subprocess.run(
                [sys.executable, "-m", "gve"],
                cwd=temporary,
                env=environment,
                input=(VECTOR_ROOT / "input.json").read_bytes(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )

        self.assertEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, (VECTOR_ROOT / "stdout.bin").read_bytes())
        self.assertEqual(completed.stderr, (VECTOR_ROOT / "stderr.bin").read_bytes())
        self.assertEqual(completed.stdout, (VECTOR_ROOT / "result.json").read_bytes())


if __name__ == "__main__":
    unittest.main()
