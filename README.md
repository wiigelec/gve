# Three-Point GVE Migration Plan

## 1. Consolidate the Governed Executor Inside SCF

### Objective

Prepare the current governed executor for extraction without intentionally changing its runtime behavior, operation contracts, schemas, terminal statuses, or compatibility behavior.

### Scope

Consolidate all executor-owned code and resources into a clearly bounded subtree within SCF. This phase is organizational and extraction-oriented, not corrective.

The consolidation should identify and gather:

* `src/scf_governed_executor/**`;
* executor launchers and bootstrap scripts;
* operation and result schemas;
* executor-specific tests and fixtures;
* executor validation profiles;
* executor documentation;
* compatibility and legacy execution paths;
* package version information;
* Git and GitHub publication support;
* self-update and session-initialization support;
* any SCF files imported or read directly by the executor.

### Required work

1. Produce a complete extraction manifest listing every executor-owned file.
2. Identify all dependencies on the SCF repository layout, root directory, documentation, schemas, scripts, and validation infrastructure.
3. Separate executor-owned functionality from SCF policy and workflow documentation.
4. Convert hard-coded repository-relative resource paths into one clearly defined resource-resolution layer.
5. Preserve the current Python package name, `scf_governed_executor`, for the initial extraction.
6. Record the exact baseline:

   * source commit;
   * executor version;
   * schema hashes;
   * supported operation routes;
   * legacy compatibility behavior;
   * test totals;
   * current audit findings.
7. Add characterization tests where needed to prove that extraction does not alter observable behavior.

### Constraints

This phase must not repair known audit findings unless a change is strictly necessary to make extraction possible.

In particular, it should not yet change:

* executor or schema version semantics;
* terminal-status names;
* operation types;
* timeout behavior;
* result-writing behavior;
* redaction behavior;
* Git hook policy;
* command environment policy;
* mutation and recovery semantics.

### Completion criteria

This phase is complete when:

* every GVE-owned file is identified;
* no hidden SCF dependency remains undocumented;
* all executor tests pass;
* the executor boundary can be moved without discovering new required SCF source files;
* the consolidation baseline is committed and tagged or otherwise recorded immutably.

---

## 2. Extract GVE Into an Independent Repository

### Objective

Create the standalone GVE repository as the sole canonical home of the governed executor while preserving the behavior of the consolidated SCF baseline.

### Repository structure

The initial standalone repository should contain:

```text
gve/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/
│   └── scf_governed_executor/
├── schemas/
├── tests/
├── docs/
├── scripts/
│   └── governed-execute
└── .github/
    └── workflows/
```

The repository may be named `gve` or `governed-executor`, while the initial Python import namespace remains `scf_governed_executor`.

### Required work

1. Create the new repository using a history-preserving split where practical.
2. Import the complete extraction manifest from Phase 1.
3. Add minimal standalone packaging:

   * `pyproject.toml`;
   * supported Python version;
   * console entry point;
   * package-data configuration;
   * schema and resource installation;
   * test dependencies;
   * build configuration.
4. Replace SCF source-tree launcher assumptions with an installed package entry point.
5. Preserve the existing command-line behavior and operation-file interface.
6. Reproduce all current executor tests in the standalone repository.
7. Add installation tests that:

   * build a wheel;
   * install it into a clean environment;
   * invoke the installed CLI;
   * run representative governed operations;
   * verify equivalent result artifacts.
8. Establish the initial standalone release or immutable baseline tag.
9. Record the relationship between:

   * the last in-tree SCF commit;
   * the first canonical GVE commit;
   * the initial standalone release.
10. Import the second-audit findings into the GVE issue tracker without repairing them as part of extraction.

### Compatibility baseline

The initial GVE release must preserve:

* current executor version behavior;
* current schemas;
* current terminal statuses;
* current dispatch behavior;
* current legacy compatibility;
* current result formats;
* current mutation classification;
* current publication behavior;
* current known defects.

Only mechanical changes needed for independent packaging, path resolution, installation, and repository ownership should be included.

### Completion criteria

This phase is complete when:

* GVE builds and installs independently;
* GVE tests pass without an SCF checkout;
* the installed executor produces behavior equivalent to the consolidated SCF baseline;
* schemas and package resources resolve from the GVE installation;
* the GVE repository is declared canonical;
* the initial GVE release or commit is immutable and identifiable;
* all known audit findings exist as GVE issues.

---

## 3. Refactor SCF to Consume the External GVE

### Objective

Remove the active in-tree governed executor from SCF and make SCF depend on a pinned, verified revision of the external GVE repository.

### Dependency model

The final dependency direction must be:

```text
SCF ──depends on──> GVE
GVE ──does not depend on──> SCF source
```

SCF may provide policy, operation descriptions, validation profiles, and integration configuration, but the executor implementation must come from the external GVE repository.

### Required work

1. Select the initial GVE dependency mechanism:

   * preferably a pinned release artifact;
   * alternatively an exact Git commit;
   * or a pinned Git submodule when the source tree must remain visible.
2. Record in SCF:

   * GVE repository location;
   * exact release, tag, or commit;
   * expected package version;
   * artifact or checkout digest;
   * compatible schema baseline;
   * installation or clone procedure.
3. Add a minimal SCF bootstrap process that:

   * retrieves the exact authorized GVE revision;
   * verifies its identity or digest;
   * installs it into an isolated environment;
   * invokes the external `governed-execute` entry point.
4. Replace direct imports from the in-tree executor with invocation of the installed external GVE.
5. Move SCF-specific policy out of GVE where necessary and retain it in SCF as:

   * operation templates;
   * authorization policy;
   * validation profile selection;
   * repository-specific paths;
   * workflow documentation;
   * compatibility requirements.
6. Add cross-repository integration tests covering:

   * SCF operation generation;
   * GVE operation acceptance;
   * governed validation;
   * local mutation;
   * Git publication;
   * result artifact consumption;
   * legacy or recovery paths still required by SCF.
7. Run parity tests comparing:

   * the final in-tree executor baseline;
   * the pinned external GVE release.
8. Remove the active in-tree implementation after external integration passes.
9. Retain only the minimum migration or bootstrap adapter needed by SCF.
10. Document GVE upgrade and rollback procedures.

### Upgrade policy

SCF must never track an unpinned GVE branch.

Every GVE upgrade should be an explicit governed SCF change that records:

* old GVE revision;
* new GVE revision;
* compatibility changes;
* schema changes;
* required SCF updates;
* test evidence;
* rollback revision.

### Completion criteria

The migration is complete when:

* SCF uses only the external GVE implementation;
* the GVE revision is pinned and verified;
* SCF no longer contains a second active executor copy;
* SCF integration tests pass against the external package;
* the old and new execution paths produce equivalent baseline behavior;
* installation, upgrade, and rollback procedures are documented;
* all future executor repairs occur in the GVE repository;
* SCF changes only when required to consume a new GVE release or contract.

# Overall sequencing

The three phases must occur in order:

```text
Consolidate in SCF
        ↓
Extract unchanged into GVE
        ↓
Refactor SCF to consume external GVE
```

Repairs identified by the second audit begin only after the standalone GVE repository is canonical and SCF is either using the extracted baseline or has a stable migration branch targeting it.
