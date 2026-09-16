---
doc_id: PD-100
title: Governed Delete and Move Operations
dependencies:
  - PD-050
  - PD-080
  - PD-090
---

# Governed Delete and Move Operations

## Purpose

This document extends the maintained `modify` macro with governed deletion and
move of repository files.

The extension preserves the existing GVE execution model:

- callers select only closed product-owned macro operations;
- exact repository and state guards remain authoritative;
- filesystem mutation remains repository-bounded;
- Git staging, commit, publication, verification, and recovery remain governed;
- unrelated user work is preserved;
- no generic caller-authored filesystem or Git command surface is introduced.

Delete and move are explicit product capabilities rather than aliases for
caller-supplied shell, `git rm`, or `git mv` execution.

## Delete operation

`modify` may accept a delete change for one existing repository-relative regular
file.

A delete change identifies:

```text
operation
path
expected_sha256
```

The operation requires the target to exist as a regular file within the active
repository and requires its current SHA-256 to equal `expected_sha256` before
mutation.

A stale digest, missing target, non-regular target, repository escape, or other
failed precondition fails before that file is deleted.

Deletion is performed by a bounded filesystem task. Git index mutation remains
part of the existing governed commit stage rather than the filesystem task.

## Move operation

`modify` may accept a move change for one existing repository-relative regular
file.

A move change identifies:

```text
operation
path
destination
expected_sha256
```

`path` is the source path and `destination` is the new repository-relative path.

Before mutation GVE shall establish that:

- the source resolves to an existing regular file within the repository;
- the source SHA-256 equals `expected_sha256`;
- the destination remains within the repository;
- source and destination are distinct after normalization;
- the destination does not already exist as a file, directory, or symlink;
- any created destination parent directories remain within the repository.

Move is represented as one product-owned filesystem mutation with explicit
source and destination semantics. It is not exposed as arbitrary rename command
execution.

The filesystem layer shall not stage Git changes. The existing governed commit
stage stages the complete affected path set.

## Affected path model

Create, modify, and delete each contribute one affected repository-relative path.

Move contributes two affected paths:

```text
source
destination
```

The `modify` macro uses the complete normalized affected-path set for applicable
state guards, pending-difference checks, staging scope, staged-difference checks,
commit evidence, recovery scope, and verification.

No two requested changes may produce ambiguous or overlapping normalized
effects. In particular, a request shall reject collisions in which one change
uses a path that another change creates, deletes, modifies, moves from, or moves
to unless a later Functional Set explicitly defines ordered multi-change
semantics for that case.

This keeps one `modify` request declarative rather than making array order a
filesystem programming language.

## Filesystem task semantics

Build shall add only the smallest governed filesystem capabilities needed by the
public operations.

Deletion shall use a bounded file-delete capability with an exact digest
precondition.

Move shall use a bounded file-move capability with an exact source digest
precondition and destination-absence guard.

Filesystem tasks may create missing destination parent directories only as
invocation-owned effects. They return explicit effect evidence sufficient for
normal result reporting and bounded recovery.

Neither capability invokes caller-authored commands or modifies the Git index.

## Git integration

Delete and move continue through the established `modify` commit and publication
pipeline.

The Git layer observes and stages the resulting filesystem state. GVE does not
require `git rm` or `git mv` as mutation primitives.

For delete, the affected path is staged as a deletion.

For move, both source and destination are included in the staging and
verification scope. Git may represent the committed result as a rename or as
delete-plus-add according to normal Git object semantics; GVE does not make
rename detection part of the public contract.

One successful `modify` invocation still creates at most one product commit and
uses only normal non-force publication.

## Pre-mutation evidence

Before delete or move mutation, `modify` captures enough governed evidence to
enforce exact preconditions and support bounded pre-commit recovery.

For delete this includes at least:

- normalized path;
- complete preimage content when recovery requires recreation;
- SHA-256 digest.

For move this includes at least:

- normalized source and destination;
- source SHA-256 digest;
- destination absence;
- destination parent state needed to distinguish invocation-created directories
  from pre-existing directories.

The evidence is invocation-local and does not widen authority.

## Recovery

The accepted FS-004 recovery model remains in force.

If failure occurs after delete or move mutation but before commit, GVE may
automatically recover only effects created by the current invocation.

Delete recovery may recreate the deleted file only when its recorded preimage
and surrounding repository state prove that doing so does not overwrite
unrelated user work.

Move recovery may move the file back from destination to source only when the
destination still matches the invocation-owned moved content, the source remains
absent, and reversing invocation-created parent directories cannot remove
unrelated content.

Recovery removes invocation-created empty destination parent directories only
when they remain empty of unrelated content.

If those safety conditions cannot be proven, recovery fails conservatively and
reports residual state rather than overwriting or deleting unrelated work.

After commit, existing no-history-rewrite recovery rules remain unchanged.

## Public introspection

`gve macro-schema modify` is the authoritative public contract.

After this capability is implemented, the schema shall advertise delete and
move change forms exactly as admitted by runtime validation.

Existing create and modify request forms remain compatible.

No delete or move field is accepted unless it appears in the live public schema.

## Authority and safety

Delete and move do not grant new ambient authority.

All paths remain repository-relative and repository-bounded. Symlink and path
resolution checks continue to prevent repository escape.

Delete cannot remove directories.

Move cannot replace an existing destination.

Neither operation provides recursive deletion, wildcard expansion, arbitrary
filesystem rename, arbitrary Git commands, force push, or history rewrite.

## Compatibility

Existing `modify` create and modify behavior remains unchanged.

Existing callers that do not use delete or move observe no new mutation behavior.

The new operations reuse the accepted Engine, macro orchestration, validation,
commit, publication, verification, presentation, and recovery architecture.
