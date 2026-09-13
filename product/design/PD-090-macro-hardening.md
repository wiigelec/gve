---
doc_id: PD-090
title: Macro Hardening, Discovery, and Recovery
dependencies:
  - PD-050
  - PD-060
  - PD-080
---

# Macro Hardening, Discovery, and Recovery

## Purpose

This document defines the next hardening of the maintained GVE macro surface.
The hardening reduces caller payload size for ordinary edits, makes repository
discovery sufficient to prepare safe mutations, produces actionable repository
selection failures, and makes mutation failure state explicit and recoverable
without silently rewriting history or disturbing unrelated user work.

## Modify patch input

`modify` supports two product-owned representations for modification of an
existing UTF-8 regular file:

- complete replacement `content`;
- a bounded unified `diff`.

A modify change for an existing file selects exactly one representation.

Both representations retain the existing exact-file precondition. The caller
supplies the expected SHA-256 of the file before mutation. A stale digest fails
before that file is changed.

A diff is not a generic patch-programming surface. It is data for one declared
repository-relative file. GVE validates that the patch addresses exactly the
declared file, cannot escape the repository, contains no additional file
mutation, and applies cleanly to the exact expected file state before applying
it.

Create operations continue to use complete content.

This allows a one-character source edit to be represented by a small patch
instead of requiring retransmission of a long file while preserving the
existing stale-state and mutation-scope guards.

## Discover operations

`discover` remains read-only and product-owned.

In addition to the existing repository observations, it provides the following
bounded discovery capabilities.

### List folder

The caller may request one or more repository-relative folders. GVE returns a
deterministically ordered listing for each requested folder.

Folder listing does not follow a path outside the active repository and does
not mutate repository state.

### Read file

The caller may request multiple repository-relative UTF-8 regular files in one
discover request.

Each returned file record contains at least:

- repository-relative path;
- complete content;
- SHA-256 digest.

A failure to read one requested file remains a governed failure and preserves
normal macro fail-fast evidence.

### Tree status

The caller may request a consolidated Git tree-status observation intended to
provide the repository information needed before preparing a mutation.

Tree status includes at least:

- repository root and configured remotes;
- current branch or detached-HEAD indication;
- current HEAD commit when one exists;
- complete porcelain worktree status including untracked paths;
- staged-path state;
- unstaged tracked changes;
- staged changes;
- the complete tracked-tree diff between HEAD and the current worktree/index
  state.

The complete diff is returned as evidence rather than only a summary. Untracked
file contents are not implicitly read by tree status; callers use `read-file`
when their contents are needed.

Tree status is a single product-owned discovery concept even when implemented
using multiple Git observations internally. Callers do not need to reconstruct
its semantic meaning from several unrelated macro invocations.

## Repository selection diagnostics

The maintained CLI distinguishes repository-selection failures from generic
execution failures.

When the selected path is not inside a Git repository, the result identifies
the selected path and states that it is not a Git repository.

When the selected path resolves inside a repository but is not the repository
top level, the result identifies both the selected path and observed top-level
repository path.

When request repository expectations disagree with the selected repository,
the result identifies the mismatched field and includes expected and observed
values.

These diagnostics remain failures. They do not search for, switch to, or infer
a different repository on the caller's behalf.

## Failure and recovery model

Macro execution reports failure state according to the point reached in the
governed operation.

### Failure before mutation

No recovery action is required. GVE reports that no product-owned mutation was
performed.

### Failure after worktree mutation but before commit

GVE may perform bounded automatic recovery only for effects created by the
current macro invocation.

Recovery restores files mutated by the invocation to their pre-mutation state.
It must preserve unrelated pre-existing user work, including dirty paths that
were explicitly admitted by the request.

If the invocation created and switched to a new branch, recovery may return to
the branch that was active before the invocation and remove the newly created
local branch only when doing so cannot discard unrelated user work.

Recovery itself is governed evidence. The macro result distinguishes:

- primary operation failure;
- recovery attempted or not attempted;
- recovery success or failure;
- residual repository state requiring user action.

A recovery failure never converts the primary operation failure to success.

### Failure after commit

After the macro has created its commit, automatic recovery does not reset,
amend, revert, delete, or otherwise rewrite history.

The result preserves the created commit identity and reports publication state.

### Failure during or after publication

GVE never force-pushes as recovery.

If a normal push completed but exact remote verification cannot establish the
expected remote head, the result reports publication as ambiguous and includes
the local commit and every remote-head observation available to the invocation.

The caller decides any subsequent reconciliation in a separate governed
operation.

## Recovery evidence

Applicable macro results expose recovery evidence sufficient to determine:

- whether repository mutation began;
- paths mutated by the invocation;
- whether a branch was created or switched;
- whether a commit was created;
- whether publication was attempted;
- whether publication was verified;
- whether recovery was attempted;
- recovery actions performed;
- recovery status;
- residual conflicts or state requiring user action.

This evidence augments rather than replaces the ordered governed task evidence.

## Authority and scope

Patch input, discovery requests, repository diagnostics, and recovery behavior
do not widen active authority.

Closed repository boundaries remain default-deny.

Automatic recovery may touch only state previously changed by the same macro
invocation and only when the recovery action is proven not to discard unrelated
user work.

## Compatibility

Existing complete-content `modify` requests remain valid.

Existing `discover` observations remain valid.

New discovery capabilities are explicit opt-in requests and do not make default
`discover` unexpectedly return large file contents or full diff text.

No hardening behavior introduces a caller-authored generic task language,
generic patch execution language, history-rewrite authority, or force-push
authority.
