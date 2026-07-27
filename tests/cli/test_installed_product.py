from __future__ import annotations

import contextlib
import io
import os
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPOSITORY_ROOT / "src"
EXPECTED_VERSION = "0.1.0"


def _run(
    command: list[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class InstalledProductTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory(prefix="gve-stage-1-")
        cls.root = Path(cls.temporary.name)
        cls.build_source = cls.root / "build-source"
        cls.wheelhouse = cls.root / "wheelhouse"
        cls.environment = cls.root / "environment"
        cls.cwd_one = cls.root / "cwd-one"
        cls.cwd_two = cls.root / "cwd-two"

        cls.build_source.mkdir()
        shutil.copy2(REPOSITORY_ROOT / "pyproject.toml", cls.build_source / "pyproject.toml")
        shutil.copytree(SOURCE_ROOT / "gve", cls.build_source / "src" / "gve")
        cls.wheelhouse.mkdir()
        cls.cwd_one.mkdir()
        cls.cwd_two.mkdir()

        build_environment = os.environ.copy()
        build_environment.pop("PYTHONPATH", None)
        build_environment.pop("PYTHONHOME", None)
        build_environment["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
        completed = _run(
            [
                sys.executable,
                "-m",
                "pip",
                "wheel",
                "--no-deps",
                "--no-build-isolation",
                "--wheel-dir",
                str(cls.wheelhouse),
                str(cls.build_source),
            ],
            cwd=cls.root,
            env=build_environment,
        )
        if completed.returncode != 0:
            raise AssertionError(
                "wheel build failed\n"
                f"stdout:\n{completed.stdout}\n"
                f"stderr:\n{completed.stderr}"
            )

        wheels = sorted(cls.wheelhouse.glob("gve-*.whl"))
        if len(wheels) != 1:
            raise AssertionError(f"expected one GVE wheel, found: {wheels}")
        cls.wheel = wheels[0]

        completed = _run(
            [sys.executable, "-m", "venv", str(cls.environment)],
            cwd=cls.root,
        )
        if completed.returncode != 0:
            raise AssertionError(
                "virtual environment creation failed\n"
                f"stdout:\n{completed.stdout}\n"
                f"stderr:\n{completed.stderr}"
            )

        scripts = "Scripts" if os.name == "nt" else "bin"
        cls.environment_python = cls.environment / scripts / (
            "python.exe" if os.name == "nt" else "python"
        )
        cls.gve = cls.environment / scripts / ("gve.exe" if os.name == "nt" else "gve")

        install_environment = os.environ.copy()
        install_environment.pop("PYTHONPATH", None)
        install_environment.pop("PYTHONHOME", None)
        install_environment["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
        completed = _run(
            [
                str(cls.environment_python),
                "-m",
                "pip",
                "install",
                "--no-deps",
                str(cls.wheel),
            ],
            cwd=cls.root,
            env=install_environment,
        )
        if completed.returncode != 0:
            raise AssertionError(
                "wheel installation failed\n"
                f"stdout:\n{completed.stdout}\n"
                f"stderr:\n{completed.stderr}"
            )

        shutil.rmtree(cls.build_source)

        cls.clean_environment = os.environ.copy()
        cls.clean_environment.pop("PYTHONPATH", None)
        cls.clean_environment.pop("PYTHONHOME", None)
        cls.clean_environment["GVE_VERSION"] = "999.999.999"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def invoke(self, *arguments: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return _run(
            [str(self.gve), *arguments],
            cwd=cwd or self.cwd_one,
            env=self.clean_environment,
        )

    def test_wheel_and_console_script_exist(self) -> None:
        self.assertTrue(self.wheel.is_file())
        self.assertTrue(self.gve.is_file())

    def test_version_matches_installed_metadata_exactly(self) -> None:
        metadata_result = _run(
            [
                str(self.environment_python),
                "-c",
                "import importlib.metadata as m; print(m.version('gve'))",
            ],
            cwd=self.cwd_one,
            env=self.clean_environment,
        )
        self.assertEqual(metadata_result.returncode, 0, metadata_result.stderr)
        self.assertEqual(metadata_result.stdout, EXPECTED_VERSION + "\n")
        self.assertEqual(metadata_result.stderr, "")

        command_result = self.invoke("--version")
        self.assertEqual(command_result.returncode, 0)
        self.assertEqual(command_result.stdout, f"gve {EXPECTED_VERSION}\n")
        self.assertEqual(command_result.stderr, "")

    def test_version_is_repository_independent_from_multiple_directories(self) -> None:
        first = self.invoke("--version", cwd=self.cwd_one)
        second = self.invoke("--version", cwd=self.cwd_two)
        self.assertEqual(first.returncode, 0)
        self.assertEqual(second.returncode, 0)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(first.stderr, "")
        self.assertEqual(second.stderr, "")
        self.assertFalse(self.build_source.exists())

    def test_import_origin_is_the_isolated_installation(self) -> None:
        completed = _run(
            [
                str(self.environment_python),
                "-c",
                "import pathlib, gve; print(pathlib.Path(gve.__file__).resolve())",
            ],
            cwd=self.cwd_one,
            env=self.clean_environment,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        imported = Path(completed.stdout.strip())
        self.assertTrue(imported.is_file())
        self.assertTrue(imported.is_relative_to(self.environment.resolve()))
        self.assertFalse(imported.is_relative_to(REPOSITORY_ROOT.resolve()))

    def test_unsupported_and_malformed_invocations_return_usage_status(self) -> None:
        for arguments in ((), ("execute", "operation.json"), ("--unknown",)):
            with self.subTest(arguments=arguments):
                completed = self.invoke(*arguments)
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(completed.stdout, "")
                self.assertEqual(
                    completed.stderr,
                    "gve: expected exactly one argument: --version\n",
                )
                self.assertNotIn("Traceback", completed.stderr)

    def test_missing_installed_metadata_returns_initialization_status(self) -> None:
        purelib_result = _run(
            [
                str(self.environment_python),
                "-c",
                "import sysconfig; print(sysconfig.get_paths()['purelib'])",
            ],
            cwd=self.cwd_one,
            env=self.clean_environment,
        )
        self.assertEqual(purelib_result.returncode, 0, purelib_result.stderr)
        purelib = Path(purelib_result.stdout.strip())
        metadata_directories = sorted(purelib.glob("gve-*.dist-info"))
        self.assertEqual(len(metadata_directories), 1)
        metadata_directory = metadata_directories[0]
        hidden_metadata = metadata_directory.with_name(metadata_directory.name + ".missing")
        metadata_directory.rename(hidden_metadata)
        try:
            completed = self.invoke("--version")
        finally:
            hidden_metadata.rename(metadata_directory)

        self.assertEqual(completed.returncode, 70)
        self.assertEqual(completed.stdout, "")
        self.assertEqual(
            completed.stderr,
            "gve: installed package metadata is unavailable\n",
        )
        self.assertNotIn("Traceback", completed.stderr)


class CliUnitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sys.path.insert(0, str(SOURCE_ROOT))

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            sys.path.remove(str(SOURCE_ROOT))
        except ValueError:
            pass

    def test_metadata_resolution_failure_has_no_fallback(self) -> None:
        from gve import cli

        stdout = io.StringIO()
        stderr = io.StringIO()
        with (
            mock.patch.object(
                cli.metadata,
                "version",
                side_effect=cli.metadata.PackageNotFoundError("gve"),
            ),
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(stderr),
        ):
            status = cli.main(["--version"])

        self.assertEqual(status, 70)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(
            stderr.getvalue(),
            "gve: installed package metadata is unavailable\n",
        )


if __name__ == "__main__":
    unittest.main()
