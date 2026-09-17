---
functional_set: FS-005
artifact: functional-set
title: Governed Delete and Move Operations
design_revision: b02a1ac6501cf1a30119e207f6710d7d5bd4b3c0
---

# FS-005 — Governed Delete and Move Operations

## Design binding

FS-005 Planning consumes Product Design exactly as published at Git revision:

```text
b02a1ac6501cf1a30119e207f6710d7d5bd4b3c0
```

The selected new Design scope is:

- `product/design/PD-100-governed-delete-and-move.md`

FS-005 also preserves applicable accepted Design established by PD-001 through
PD-090.

## Functional Set purpose

FS-005 extends the maintained `modify` macro with governed file deletion and
move while preserving GVE's existing repository authority, exact-state guards,
commit/publication pipeline, and conservative recovery model.

## In scope

FS-005 includes:

- a public `modify` delete change form for one existing repository-relative
  regular file with exact SHA-256 precondition;
- a public `modify` move change form with explicit source path, destination path,
  and exact source SHA-256 precondition;
- repository-bounded delete and move filesystem task semantics;
- destination-absence enforcement for move;
- source/destination normalization and repository-escape prevention;
- an affected-path model in which move contributes both source and destination;
- rejection of overlapping or ambiguous multi-change path effects;
- Git staging of resulting filesystem state rather than use of `git rm` or
  `git mv` as mutation primitives;
- pre-mutation evidence sufficient for bounded delete/move recovery;
- conservative pre-commit recovery for invocation-owned delete/move effects;
- removal of invocation-created destination parent directories only when safe;
- public `modify` introspection updated so schema and runtime validation agree;
- preservation of existing create/modify request compatibility;
- mechanical validation for contract, mutation, recovery, path-collision,
  authority, and compatibility behavior.

## Out of scope

FS-005 does not include:

- recursive directory deletion;
- wildcard or glob deletion;
- deletion of directories;
- arbitrary filesystem rename;
- arbitrary Git commands;
- caller-authored `git rm` or `git mv` execution;
- overwrite/replace semantics for move destination;
- ordered filesystem-program semantics based on `changes` array position;
- binary-file-specific mutation behavior beyond existing regular-file rules;
- automatic conflict resolution;
- force push or history rewrite;
- automatic post-commit rollback;
- semantic rename guarantees in Git history.

## Completion boundary

FS-005 is complete when the feature branch:

- exposes reviewed delete and move forms through `gve macro-schema modify`;
- enforces stale-state, repository-boundary, destination-absence, and path
  collision guards before mutation;
- uses bounded filesystem delete/move tasks without staging Git internally;
- stages and verifies the complete affected-path set;
- preserves unrelated user work and accepted dirty-state behavior;
- safely recovers invocation-owned pre-commit delete/move effects when provable;
- reports conservative residual state when recovery cannot be proven safe;
- preserves create/modify compatibility;
- passes canonical repository validation;
- has active mechanical evaluation bindings for every M or B FS-005 normative
  requirement realized by Build; and
- completes Semantic Review against Design revision
  `b02a1ac6501cf1a30119e207f6710d7d5bd4b3c0`.
