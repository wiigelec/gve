---
functional_set: FS-005
artifact: normative-specification
title: Governed Delete and Move Operations Specification
design_revision: b02a1ac6501cf1a30119e207f6710d7d5bd4b3c0
---

# FS-005 — Normative Specification

Evaluation classifications:

- **M** — mechanical
- **S** — semantic
- **B** — both mechanical and semantic

Purely semantic requirements are evaluated during Semantic Review. Requirements
classified M or B are mechanically evaluated through the requirement bindings
maintained for FS-005 and become acceptance-ready only when Build realizes the
bound behavior and canonical Validation passes.

## Requirements

### FS-005-NR-001 — Exact Design Binding

**Classification: M**

FS-005 Planning shall identify exact consumed Product Design revision
`b02a1ac6501cf1a30119e207f6710d7d5bd4b3c0`.

### FS-005-NR-002 — Governed Delete Request Form

**Classification: B**

The public `modify` macro shall expose a closed delete change form requiring
`operation: delete`, one normalized repository-relative `path`, and exact
lowercase `expected_sha256`, with no caller-selected task, command, shell, Git,
or recovery language.

### FS-005-NR-003 — Governed Move Request Form

**Classification: B**

The public `modify` macro shall expose a closed move change form requiring
`operation: move`, normalized repository-relative source `path`, normalized
repository-relative `destination`, and exact lowercase source
`expected_sha256`, with no caller-selected task, command, shell, Git, or
recovery language.

### FS-005-NR-004 — Repository-Bounded Regular-File Delete

**Classification: B**

Delete shall operate only on an existing regular file inside the authorized
repository and shall reject directories, symbolic links, path escape, and other
non-regular targets.

### FS-005-NR-005 — Exact Delete State Guard

**Classification: B**

Before delete mutates its target, GVE shall require the target's current
SHA-256 to equal caller-supplied `expected_sha256`; stale state shall fail
without deleting the file.

### FS-005-NR-006 — Repository-Bounded Move Source

**Classification: B**

Move shall operate only on an existing regular-file source inside the
authorized repository and shall reject symbolic links, directories, source
escape, destination escape, and a normalized destination equal to the source.

### FS-005-NR-007 — Exact Move State and Destination-Absence Guards

**Classification: B**

Before move mutates repository state, GVE shall require the source's current
SHA-256 to equal caller-supplied `expected_sha256` and shall require the
destination to be absent as a file, directory, symbolic link, or broken
symbolic link.

### FS-005-NR-008 — Regular-File Move Does Not Require Text Decoding

**Classification: B**

Move precondition and recovery evidence shall not require UTF-8 decoding of the
source; a regular-file move shall remain valid for arbitrary file bytes under
the same regular-file and digest rules.

### FS-005-NR-009 — Complete Affected-Path Set

**Classification: B**

For each request, the macro shall derive one complete normalized affected-path
set in which create, modify, and delete contribute their path and move
contributes both source and destination.

### FS-005-NR-010 — Affected-Path Collision Rejection

**Classification: B**

The complete normalized affected-path set shall contain no duplicate or
overlapping requested path identity; move source/destination self-collision and
destination collision with any other requested path shall fail before mutation.

### FS-005-NR-011 — Affected-Path Pipeline Consistency

**Classification: B**

Dirty-state guards, index snapshot, pending-difference checks, Git staging,
staged-scope verification, committed-difference evidence, and publication shall
use the complete affected-path set rather than only move sources.

### FS-005-NR-012 — Filesystem Mutation Precedes Git Staging

**Classification: B**

Delete and move mutation primitives shall change only bounded filesystem state;
they shall not invoke `git rm`, `git mv`, stage the index internally, or expose
caller-selected Git mutation behavior. Git staging shall remain a later
product-owned macro step.

### FS-005-NR-013 — Delete Recovery Preimage Evidence

**Classification: B**

Before a recoverable delete, GVE shall retain exact invocation-local evidence
sufficient to recreate the deleted file byte-for-byte, including its normalized
path, complete byte-preserving preimage content, and SHA-256.

### FS-005-NR-014 — Move Recovery Evidence

**Classification: B**

Before or during a recoverable move, GVE shall retain bounded invocation-local
evidence sufficient to identify source, destination, exact moved-content
SHA-256, destination absence, and destination parent directories created by the
invocation.

### FS-005-NR-015 — Conservative Delete Recovery

**Classification: B**

Before commit, automatic delete recovery may recreate a deleted file only when
the target remains absent and exact restoration can be proven; recovery shall
not overwrite unrelated or later-created content.

### FS-005-NR-016 — Conservative Move Recovery

**Classification: B**

Before commit, automatic move recovery may move content back only when the
destination remains the invocation-owned regular file with the expected digest
and the source remains absent. Invocation-created destination parents may be
removed only when they remain safely empty.

### FS-005-NR-017 — Unsafe Recovery Reports Residual State

**Classification: B**

If exact delete or move recovery cannot be proven safe, recovery shall stop
rather than guess, preserve the primary macro failure, and report residual
state without overwriting unrelated work.

### FS-005-NR-018 — Existing Modify Compatibility

**Classification: B**

Existing accepted create, complete-content modify, and diff-modify request
forms and their governed commit/publication semantics shall remain accepted
without semantic narrowing caused by delete or move support.

### FS-005-NR-019 — Modify Introspection Correspondence

**Classification: B**

`gve macro-schema modify` and authoritative runtime validation shall describe
the same closed request space containing create, content-modify, diff-modify,
delete, and move forms.

### FS-005-NR-020 — Canonical Mechanical Validation

**Classification: M**

The completed FS-005 Build shall pass repository-wide `scripts/validate` under
the product's existing hard execution ceilings.

### FS-005-NR-021 — Requirement Evaluation Binding

**Classification: M**

Every active FS-005 requirement classified M or B shall have exact applicable
mechanical-validation task bindings before FS-005 is ready for Semantic Review.

### FS-005-NR-022 — Authority and Engine Preservation

**Classification: S**

FS-005 shall preserve accepted repository authority, exact-state guard,
fail-fast Engine, ordered structured evidence, one-commit normal-publication,
and no-force/no-history-rewrite boundaries; delete and move shall not create an
alternate execution architecture.
