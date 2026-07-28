# Stage 1 — Installed Product and Version Command

## Purpose

This document defines the implementation requirements and acceptance criteria for Stage 1 of the maintained GVE product.

Stage 1 establishes GVE as an independently installed command-line application.

The objective is to prove that the maintained product can be installed, invoked from a clean command-line environment, and identified by the explicit version defined in the installed package.

Stage 1 does not process instruction payloads, load plugins, execute governed operations, or depend on the GVE source repository at runtime.

---

## Stage Objective

Stage 1 shall provide an installable GVE product with a stable command-line entry point:

```text
gve --version
```

The command shall report the explicit version of the installed GVE package.

The installed command must operate independently of:

- The local GVE source repository
- The current working directory
- Git metadata
- Repository-relative files
- Bootstrap executor code
- Development-only environment configuration
- An editable source checkout

Successful execution from the installed base demonstrates that the maintained product has a valid package boundary and does not accidentally depend on repository state.

---

## Normative Stage 1 Requirements

### S1-REQ-001 — Installable Product

GVE shall be distributed as an installable package.

Installation shall create an executable command named:

```text
gve
```

The installed command shall resolve to code contained in the installed package.

---

### S1-REQ-002 — Installed-Base Execution

The `gve` command shall execute from the installed package base.

Runtime execution shall not require access to the source repository.

The implementation shall not locate, import, or execute maintained-product code by searching for a local repository checkout.

---

### S1-REQ-003 — Repository Independence

After installation, `gve --version` shall function when:

- The current working directory is outside the source repository
- The source repository is absent
- The source repository has been renamed
- The source repository is inaccessible
- The installed package is invoked from a clean shell

Repository contents shall not be part of the runtime version-resolution process.

---

### S1-REQ-004 — Explicit Installed Package Version

The GVE version shall be explicitly defined as part of the installed package.

The reported version shall identify the installed product artifact.

The version shall not be derived at runtime from:

- Git tags
- Git commit identifiers
- `git describe` output
- The source repository
- The current directory
- Environment variables
- Bootstrap executor metadata
- Network services
- Fallback values outside the installed package

The installed package version is the authoritative version source for Stage 1.

---

### S1-REQ-005 — Version Command

The product shall support:

```text
gve --version
```

Successful execution shall write exactly one human-readable version line to standard output.

The required output format is:

```text
gve <version>
```

Example:

```text
gve 0.1.0
```

The command shall terminate with exit status `0`.

---

### S1-REQ-006 — Version Consistency

The version reported by:

```text
gve --version
```

shall equal the version declared by the installed package metadata.

The CLI shall not maintain an independently editable version value that can drift from the installed package version.

There shall be one authoritative package-version definition used during build and installation.

---

### S1-REQ-007 — Clean CLI Invocation

Stage 1 validation shall invoke the installed command from a clean command-line environment.

The validation environment shall not rely on:

- Repository-local `PYTHONPATH`
- Execution from the repository root
- Editable installation
- Shell aliases
- Shell functions
- Repository-local wrappers
- Manually modified import paths

The command located through the installation environment must be the command under test.

---

### S1-REQ-008 — No Source-Tree Fallback

If the installed package is missing, incomplete, or cannot be imported, the command shall fail.

It shall not silently fall back to source code in the current directory or another repository checkout.

A broken installation must remain observable as a broken installation.

---

### S1-REQ-009 — Unsupported Product Behavior

During Stage 1, the product supports only the command-line behavior required to initialize the CLI and report the installed version.

Payload ingestion, plugin resolution, action execution, workflow execution, and result emission are outside Stage 1 scope.

Unsupported invocation shall fail deterministically and shall not attempt governed execution.

---

### S1-REQ-010 — Deterministic Diagnostics

Invalid command-line use shall produce deterministic diagnostics.

Diagnostics shall:

- Be written to standard error
- Avoid tracebacks for ordinary user input errors
- Identify the command-line error
- Return a nonzero exit status

The diagnostic format shall not depend on the source repository or current working directory.

---

## Package Version Authority

### Single Version Source

The package configuration shall contain one authoritative product version.

The implementation may expose that version to runtime code through installed package metadata or generated installed-package data, provided that:

- The value originates from the package’s explicit version declaration
- The installed artifact contains the required version information
- Runtime resolution does not require the source repository
- The CLI and installed package metadata cannot disagree under a valid installation

### Prohibited Version Sources

The following are not authoritative Stage 1 version sources:

```text
Git repository state
Git tags
Git commit hashes
Environment variables
README content
Specification document versions
Bootstrap executor versions
Source-tree constants that are not derived from installed package metadata
```

Specification versions and product-package versions are distinct concepts.

`gve --version` reports the installed maintained-product version, not the version of an individual normative specification document.

---

## Proposed Package Structure

The maintained product should use a dedicated package namespace separate from the historical bootstrap executor.

A representative structure is:

```text
pyproject.toml
src/
    gve/
        __init__.py
        __main__.py
        cli.py
tests/
    stage_1/
        test_version.py
        test_installed_execution.py
```

The exact internal module names may differ, but the maintained product package shall not use the historical bootstrap executor as its runtime entry point.

---

## CLI Entry Point

The package configuration shall install a console entry point equivalent to:

```text
gve = gve.cli:main
```

The entry point shall invoke maintained-product code from the installed package.

The CLI implementation should return integer process status values through a single application entry function.

A representative interface is:

```python
def main(argv: list[str] | None = None) -> int:
    ...
```

The process wrapper shall terminate using the returned status.

---

## Version Resolution

The runtime shall obtain the version associated with the installed `gve` distribution.

The preferred behavior is:

```text
installed package metadata
        ↓
maintained GVE runtime
        ↓
gve --version
```

The runtime shall not inspect the repository to determine the version.

If installed package metadata cannot be resolved, the command shall fail with a deterministic installation-error diagnostic rather than return an invented or fallback version.

---

## Command Behavior

### Successful Version Request

Command:

```text
gve --version
```

Standard output:

```text
gve <installed-package-version>
```

Standard error:

```text
empty
```

Exit status:

```text
0
```

---

### Equivalent Short Option

Stage 1 may support:

```text
gve -V
```

If supported, it shall produce exactly the same version line and exit status as `gve --version`.

Support for `-V` is optional unless separately adopted as a product requirement.

---

### Unsupported Arguments

Example:

```text
gve execute operation.json
```

During Stage 1, this invocation shall not attempt payload processing.

It shall produce a deterministic unsupported-command or argument diagnostic and return a nonzero exit status.

---

### Missing Installation Metadata

If the executable starts but the installed package version cannot be resolved, the command shall:

- Write no successful version line
- Emit a deterministic installation-error diagnostic to standard error
- Return a nonzero exit status
- Avoid deriving a version from repository or environment state

---

## Exit Status Contract

Stage 1 shall define stable exit-status categories.

The initial contract is:

| Exit status | Meaning |
|---:|---|
| `0` | Requested CLI operation completed successfully |
| `2` | Invalid or unsupported command-line invocation |
| `70` | Installed product metadata or internal runtime initialization failure |

Ordinary invalid user input and broken installation state shall not share the same status category.

---

## Installation Validation

Stage 1 shall be validated using a non-editable installation into an isolated environment.

A representative validation sequence is:

```sh
python3 -m venv /tmp/gve-stage-1
/tmp/gve-stage-1/bin/python -m pip install .
cd /tmp
/tmp/gve-stage-1/bin/gve --version
```

The validation shall not set `PYTHONPATH`.

The validation shall not invoke a repository-local script.

The validation shall not use:

```sh
pip install -e .
```

as the authoritative installed-product acceptance test.

Editable installation may be used during development, but it does not satisfy the Stage 1 installed-base requirement.

---

## Built-Artifact Validation

The preferred final acceptance test shall install GVE from a built distribution artifact rather than directly from the repository working tree.

A representative sequence is:

```sh
python3 -m build
python3 -m venv /tmp/gve-stage-1
/tmp/gve-stage-1/bin/python -m pip install dist/gve-<version>-py3-none-any.whl
cd /tmp
/tmp/gve-stage-1/bin/gve --version
```

This test demonstrates that the installed distribution artifact contains everything required to execute the command.

The source repository shall not be needed after the artifact has been built.

---

## Repository-Independence Validation

At least one acceptance test shall prove that the installed product does not require the repository.

A representative test procedure is:

1. Build a GVE distribution artifact.
2. Install the artifact into an isolated environment.
3. Record the expected installed package version.
4. Change to a directory outside the repository.
5. Make the repository unavailable to the test process.
6. Invoke the installed `gve --version`.
7. Verify the exact output and exit status.
8. Verify that runtime modules were loaded from the installed package location.

A stronger test may temporarily rename or remove the source checkout after the package artifact has been built and installed.

---

## Required Tests

### Package Build Tests

Tests shall verify that:

- The package configuration is valid
- A source distribution can be built, if source distributions are supported
- A wheel can be built
- The built artifact contains the maintained-product package
- The built artifact contains the required package metadata

### Package Installation Tests

Tests shall verify that:

- The package installs successfully
- The `gve` executable is created
- The installed package can be imported
- The installed command uses the maintained-product package
- Installation does not require an editable checkout

### Version Tests

Tests shall verify that:

- `gve --version` returns exit status `0`
- Output exactly matches `gve <installed-version>`
- Standard error is empty on success
- The CLI value equals the installed package metadata
- Output is identical from multiple working directories
- The result is not affected by Git state
- The result is not affected by environment variables that attempt to override the version

### Repository Independence Tests

Tests shall verify that:

- Execution succeeds outside the repository
- Execution does not require repository-local `PYTHONPATH`
- Execution does not require Git
- Execution does not require repository files
- Execution does not import from the working directory in place of the installed package
- Execution succeeds after the source repository becomes unavailable

### Failure Tests

Tests shall verify deterministic behavior for:

- Unsupported options
- Unsupported commands
- Malformed invocation
- Unavailable installed version metadata
- Incomplete or broken installation

---

## Validation Assertions

The Stage 1 validation process shall verify all of the following:

```text
resolved executable path
    belongs to the isolated installation

resolved Python package path
    belongs to the isolated installation

reported CLI version
    equals installed distribution metadata

current working directory
    is outside the source repository

source repository
    is not required for execution
```

Validation shall fail if the command imports maintained-product modules from the source checkout.

---

## Stage 1 Non-Goals

Stage 1 does not implement:

- Instruction payload ingestion
- Baseline payload schemas
- Authoritative result emission
- Workflows
- Operations
- Plugin discovery
- Plugin registration
- Action registration
- Authority evaluation
- Effect execution
- Evidence collection
- Filesystem actions
- Bootstrap executor replacement

No Stage 1 code should pretend that these capabilities exist.

---

## Deliverables

Stage 1 shall produce:

1. A maintained-product package structure
2. Package build configuration
3. One explicit installed package version
4. A built distribution artifact
5. An installed `gve` console entry point
6. A `gve --version` implementation
7. Deterministic CLI error handling
8. Isolated installation tests
9. Built-artifact installation tests
10. Repository-independence tests
11. Stage 1 validation documentation

---

## Acceptance Criteria

Stage 1 is complete when all of the following are true:

- GVE builds as an installable package.
- GVE produces a valid installable distribution artifact.
- GVE installs into a clean isolated environment.
- Installation creates a `gve` executable.
- `gve --version` executes from outside the repository.
- The command does not require repository access.
- The command does not require Git.
- The command does not require repository-local environment configuration.
- The command executes from the installed package base.
- The reported version exactly equals the explicit installed package version.
- The CLI does not contain an independent version value that can drift from package metadata.
- Successful output is deterministic.
- Successful execution returns status `0`.
- Invalid invocation returns status `2`.
- Installed metadata or runtime initialization failure returns status `70`.
- Broken installed-version resolution fails without a fallback version.
- Tests prove that runtime code is loaded from the installed package.
- Tests prove that the source repository can be unavailable during execution.
- No payload, workflow, plugin, action, or governed-execution behavior is implemented.

---

## Stage Exit Gate

Stage 1 shall not be declared complete based only on successful execution from the source repository.

The authoritative Stage 1 exit test is execution of the installed `gve` command from a clean environment that has no runtime dependency on the local repository.

The required proof is:

```text
explicit package version
        ↓
package build
        ↓
distribution artifact
        ↓
non-editable installation
        ↓
source repository unavailable
        ↓
clean CLI invocation
        ↓
gve --version
        ↓
exact installed-package version
```

Completion of this gate establishes the permanent installed-product and CLI foundation for Stage 2.
