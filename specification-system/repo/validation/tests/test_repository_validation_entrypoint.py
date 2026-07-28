from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[2]


class RepositoryValidationEntrypointTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "repo"
        shutil.copytree(SOURCE_ROOT, self.root, symlinks=True)
        self.validate = self.root / "validate"
        self.tests = self.root / "validation/tests"
        intrinsic = self.root / "validation/intrinsic/validate_skeleton.py"
        intrinsic.write_text(
            "#!/usr/bin/env python3\n"
            "print('repository-specification construction validation passed')\n",
            encoding="utf-8",
        )
        for path in self.tests.glob("test_*.py"):
            path.unlink()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_test(self, name: str, body: str) -> None:
        (self.tests / name).write_text(body, encoding="utf-8")

    def run_validate(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [str(self.validate), *arguments],
            cwd=self.root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=120,
        )

    def test_complete_discovery_reports_nonzero_test_count(self) -> None:
        self.write_test(
            "test_entrypoint_pass.py",
            "import unittest\n\n"
            "class EntrypointPass(unittest.TestCase):\n"
            "    def test_pass(self):\n"
            "        self.assertTrue(True)\n",
        )
        result = self.run_validate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(
            "python3 -m unittest discover -s specification-system/repo/validation/tests -p 'test_*.py'",
            result.stdout,
        )
        self.assertIn(
            "repository-specification validate: complete unit-test discovery passed (1 tests)",
            result.stdout,
        )
        self.assertIn("Ran 1 test", result.stderr)
        self.assertIn("OK", result.stderr)

    def test_failing_discovered_test_causes_failure(self) -> None:
        self.write_test(
            "test_entrypoint_failure.py",
            "import unittest\n\n"
            "class EntrypointFailure(unittest.TestCase):\n"
            "    def test_failure(self):\n"
            "        self.fail('intentional entrypoint regression failure')\n",
        )
        result = self.run_validate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("intentional entrypoint regression failure", result.stderr)

    def test_zero_test_discovery_causes_failure(self) -> None:
        result = self.run_validate()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Ran 0 tests", result.stderr)
        self.assertIn("unit-test discovery ran zero tests", result.stderr)
        self.assertNotIn(
            "complete unit-test discovery passed",
            result.stdout,
        )

    def test_filename_argument_is_rejected(self) -> None:
        result = self.run_validate("missing-test-file.py")
        self.assertEqual(result.returncode, 2)
        self.assertIn("arguments are not supported", result.stderr)


if __name__ == "__main__":
    unittest.main()
