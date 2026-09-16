---
functional_set: FS-005
artifact: plan
title: Governed Delete and Move Operations Plan
design_revision: b02a1ac6501cf1a30119e207f6710d7d5bd4b3c0
---

# FS-005 — Plan

## Design binding

This Planning revision consumes Product Design at exact Git revision
`b02a1ac6501cf1a30119e207f6710d7d5bd4b3c0`.

FS-005 extends the accepted FS-004 implementation. Existing Engine execution,
macro registration, authority, exact HEAD guards, dirty-state controls, staged
scope checks, validation, one-commit behavior, publication, verification,
presentation, and conservative recovery remain in force except where this Plan
explicitly extends them.

## Technical intent

Add delete and move as closed product-owned `modify` operations while preserving
the separation between repository-bounded filesystem mutation and governed Git
staging/commit/publication.

The maintained path remains:

```text
caller
  -> closed registered macro contract
  -> product-owned modify orchestration
  -> existing FS-001 Engine
  -> bounded filesystem and Git tasks
  -> stable macro result + observational presentation
```

No second execution engine or generic caller-authored command surface is added.

## Public modify change contract

The public `modify.changes` array retains existing create and modify forms and
adds delete and move.

### Delete

A delete change is:

```json
{
  "operation": "delete",
  "path": "relative/path.txt",
  "expected_sha256": "<64-lowercase-hex>"
}
```

The delete form admits exactly:

```text
operation
path
expected_sha256
```

The path is normalized with the same repository-relative rules used by existing
modify forms.

### Move

A move change is:

```json
{
  "operation": "move",
  "path": "old/path.txt",
  "destination": "new/path.txt",
  "expected_sha256": "<64-lowercase-hex>"
}
```

The move form admits exactly:

```text
operation
path
destination
expected_sha256
```

`path` is the source. `destination` is the target location.

Source and destination must be distinct after normalization.

## Change normalization and collision model

Build shall normalize every path before orchestration.

Each change contributes an affected-path set:

```text
create -> {path}
modify -> {path}
delete -> {path}
move   -> {path, destination}
```

The union of affected paths is used by modify state guards, pending-diff checks,
staging scope, staged-diff checks, commit evidence, recovery scope, and
verification.

The request is invalid if normalized affected paths overlap between changes.

Examples of rejected requests include:

- modifying a path that another change deletes;
- deleting a path that another change moves from;
- creating a path used as another move destination;
- two moves with the same destination;
- moving A to B while another change addresses A or B.

Array order does not define dependency or sequencing semantics.

## Filesystem delete task

The existing bounded file-delete capability shall be the delete mutation
primitive unless Build identifies a contract mismatch requiring the smallest
compatible refinement.

Inputs are:

```text
path
expected_sha256
```

Validation shall:

1. normalize and repository-bound the path;
2. require an existing regular file;
3. require exact SHA-256 equality before mutation;
4. reject directory deletion and repository escape;
5. fail without mutation if any precondition fails.

Execution deletes the file and returns invocation-owned effect evidence
including at least the path and previous SHA-256.

## Filesystem move task

Build shall add a bounded file-move task.

Inputs are:

```text
path
destination
expected_sha256
```

Validation shall:

1. normalize and repository-bound source and destination;
2. require source and destination to differ;
3. require source to be an existing regular file;
4. require source SHA-256 to equal `expected_sha256`;
5. require destination to be absent, including file, directory, or symlink;
6. verify all destination parent resolution remains within the repository;
7. determine which missing destination parent directories would be
   invocation-created;
8. fail without mutation if any precondition fails.

Execution moves the file to destination and creates only required
repository-bounded destination parent directories.

The task shall return effect evidence including at least:

```text
source
destination
sha256
created_parent_paths
```

No Git index mutation occurs inside the filesystem task.

## Pre-mutation evidence

`modify` shall collect sufficient evidence before mutation for both normal
preconditions and bounded recovery.

For delete, this includes the file preimage needed to recreate the file plus its
SHA-256.

For move, this includes:

- source SHA-256;
- destination absence;
- destination parent state sufficient to distinguish pre-existing directories
  from invocation-created directories.

Existing index snapshots and staged-state guards continue to apply to the full
affected-path set.

## Mutation orchestration

Mutation tasks are selected by operation:

```text
create -> filesystem.file-create
modify(content) -> filesystem.file-modify
modify(diff) -> filesystem.file-patch
delete -> filesystem.file-delete
move -> filesystem.file-move
```

Task ordering follows declared change order only as execution order. That order
does not create semantic dependencies because path-collision validation forbids
overlapping effects.

## Git commit integration

The existing commit stage remains authoritative.

`git.add` receives the complete affected-path set.

For delete, staging the deleted path records removal.

For move, staging both source and destination records the resulting tree state.

GVE does not require or expose `git rm` or `git mv`.

Git's later rename detection is not part of the public GVE contract.

Existing safeguards continue to require:

- expected branch/head state;
- scoped dirty state;
- no unrelated staged changes;
- pending difference in the declared affected scope;
- staged scope restricted to affected paths;
- clean diff-check;
- at most one commit;
- normal non-force push;
- exact remote-head verification.

## Recovery integration

The accepted FS-004 recovery boundary remains in force.

### Delete recovery

Before commit, recovery may recreate a deleted file from the recorded preimage
only when:

- the path is still absent;
- restoring it cannot overwrite unrelated state;
- recorded invocation evidence is sufficient to prove the restoration.

If proof fails, recovery reports residual state instead of overwriting.

### Move recovery

Before commit, recovery may reverse a move only when:

- destination still exists as the invocation-owned regular file;
- destination content still matches the expected invocation-owned digest;
- source remains absent;
- reversing the move cannot overwrite unrelated state.

Invocation-created destination parent directories may be removed after reversal
only when they remain empty of unrelated content.

Recovery actions and failures remain explicit task/result evidence.

No automatic reset, amend, revert, force push, or post-commit history rewrite is
introduced.

## Public schema and runtime agreement

`PARAMETER_SCHEMA`, runtime validation, macro orchestration, tests, and
`gve macro-schema modify` shall admit the same four operation families:

```text
create
modify
delete
move
```

Unknown fields remain rejected.

Existing create and modify forms remain backward-compatible.

## Mechanical validation

Build shall add focused mechanical coverage for at least:

- delete schema acceptance and unknown-field rejection;
- move schema acceptance and unknown-field rejection;
- stale delete digest rejection;
- stale move digest rejection;
- missing delete source;
- missing move source;
- destination already exists as file;
- destination already exists as directory;
- destination symlink rejection;
- source/destination equality after normalization;
- repository escape attempts;
- delete of non-regular target;
- affected-path collision rejection;
- move staging scope including source and destination;
- successful delete commit;
- successful move commit;
- delete recovery after pre-commit failure;
- move recovery after pre-commit failure;
- conservative recovery refusal when state changed after mutation;
- invocation-created parent cleanup;
- preservation of pre-existing destination parent directories;
- preservation of allowed unrelated dirty work;
- create/modify regression compatibility;
- public schema/runtime agreement.

Repository-wide canonical validation remains the acceptance gate.

## Build touchpoints

Expected Build touchpoints include:

```text
product/src/gve/macros/modify.py
product/src/gve/plugins/filesystem.py
product/validation/**
product/specs/**
```

Exact test/spec filenames are Build decisions subject to repository conventions.

Planning does not require changes to Git task semantics unless Build discovers an
existing task cannot stage or verify deleted/moved paths correctly. Any such
change shall be the smallest compatible extension and remain within this
Functional Set.

## Specification and evaluation

Build shall create the FS-005 normative specification and bind each mechanically
testable or boundary requirement to active validation evidence following the
accepted repository validation-manifest conventions.

Semantic Review shall compare the completed Build against PD-100 at exact design
revision `b02a1ac6501cf1a30119e207f6710d7d5bd4b3c0` and this Planning revision.
