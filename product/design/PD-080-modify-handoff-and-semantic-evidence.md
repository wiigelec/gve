---
doc_id: PD-080
title: Modify Handoff and Semantic Evidence
dependencies:
  - PD-001
  - PD-010
  - PD-020
  - PD-030
  - PD-040
  - PD-050
  - PD-070
---

# Modify Handoff and Semantic Evidence

## Purpose

This document refines the `modify` product macro so a caller can request a
bounded repository mutation against an exact expected repository state and
receive evidence suitable for subsequent semantic review.

The operational reference is `user/script-transfer-handoff.json`.

## Caller-owned intent

The caller owns the requested mutation intent.

Every `modify` request shall provide an exact expected local Git HEAD.

The caller may also explicitly request creation of a development branch and
provide the requested branch name.

The caller does not provide executable task ordering, raw Git commands, shell
fragments, or authority grants.

## Required expected HEAD

Every `modify` request shall contain:

```text
expected_head
```

representing the exact local commit the caller expects before any
product-requested repository mutation begins.

Before mutation, `modify` shall observe local HEAD and require exact equality
with the caller-supplied value.

The macro must not silently replace the caller expectation with whatever HEAD is
observed at execution time.

If local HEAD differs from `expected_head`, the macro fails before mutation.

The expected HEAD continues to serve as the guarded pre-mutation base for later
checks until the product-requested commit is created.

## Explicit branch creation

Branch creation is caller-requested behavior.

The macro shall not create a development branch merely because one is absent.

A request may explicitly select branch creation and provide a branch name.
When branch creation is requested:

1. PRECHECK shall verify the caller's exact `expected_head` before branch
   creation.
2. GVE shall create the requested local branch from exactly `expected_head`.
3. GVE shall switch to the newly created branch.
4. GVE shall verify the active branch equals the requested branch.
5. GVE shall verify HEAD still equals `expected_head` before repository content
   mutation begins.

A caller request to create a branch means create a new branch. If the requested
local branch already exists, creation fails closed rather than silently becoming
"use the existing branch."

Use of an already-existing branch is separate caller intent and must not be
inferred from a failed creation request.

## Modify phases

The product-owned `modify` lifecycle is conceptually:

```text
PRECHECK
BRANCH
MUTATE
VALIDATE
COMMIT
PUBLISH
VERIFY
```

`BRANCH` contains effects only when explicitly requested by the caller.

### PRECHECK

Before mutation, `modify` shall establish or verify applicable evidence for:

- repository identity;
- current branch;
- exact caller-supplied expected HEAD;
- acceptable worktree state;
- acceptable existing staging state;
- exact selected remote publication state used as the publication race guard;
  this is an exact remote commit when the selected remote branch exists, or
  explicit branch absence when publication will create a new remote branch.

Repository expectations are state guards, not authority grants.

### BRANCH

When explicitly requested, create and switch to the requested development branch
from the exact expected HEAD, then re-observe branch and HEAD.

### MUTATE

Mutate only explicitly declared repository-relative paths.

Preserve unrelated user work.

Existing file modifications continue to require exact expected-content evidence
such as the existing SHA-256 guard defined by the macro contract.

### VALIDATE

When validation is enabled, invoke exactly one governed repository-root
`scripts/validate` operation through `execute.script`.

Validation failure stops later commit or publication.

### COMMIT

Before creating the commit, re-check repository, branch, pre-mutation HEAD
relationship, dirty-path scope, and staging scope as required to preserve the
declared mutation boundary.

Before commit, `modify` shall:

- establish that the pending difference is contained within the declared
  mutation path set;
- show a concise short-status change summary in terminal presentation;
- stage only declared mutation paths;
- capture the complete staged diff;
- run the equivalent of `git diff --cached --check`;
- create at most one product-requested commit.

### PUBLISH

Publication shall use an exact previously observed remote-state guard.

For publication to an existing remote branch, the guard is the exact observed
remote commit identity.

For publication that will create a new remote branch, the guard is explicit
remote-branch absence. Immediately before push, the branch must still be absent.
If another actor creates the selected remote branch after PRECHECK, publication
fails closed rather than treating the new remote state as an acceptable target.

Publication shall:

- re-check the selected remote branch state against the applicable exact
  previously observed publication guard;
- use normal non-force push semantics;
- never silently rewrite history.

### VERIFY

After publication, observe the selected remote head and require exact equality
with the commit created by the macro.

Terminal PASS is not emitted before this verification succeeds.

## Semantic-review diff

`modify` shall preserve the complete staged diff that represents the exact
content about to be committed.

The authoritative macro result shall expose this diff through a stable
macro-level result field so a caller or agent can perform semantic validation
without depending on internal generated task identities.

The semantic-review diff is not merely terminal presentation. It is
machine-readable execution evidence.

The staged diff may also remain present in the underlying governed `git.diff`
task record.

If the diff was successfully captured and a later commit, publication, or
verification step fails, the macro result shall retain the captured diff.

If execution fails before the semantic diff is established, the macro shall not
invent one.

## Stable macro-level modify result

In addition to the complete ordered stage/task evidence, the `modify` macro
shall provide stable macro-level continuation evidence when available.

The result model shall be able to communicate at least:

```text
repository
branch
expected_head
observed_head
branch_created
files_changed
validation
diff
commit
commit_count
push_mode
remote_head
history_rewrite_or_force_push_occurred
merge_occurred
```

Exact concrete JSON field spelling belongs to Planning.

The macro-level result is a product-owned projection of underlying governed
evidence. It shall not erase or replace the complete task records.

## Expected and observed state

Caller-provided expected values and GVE-observed values remain distinct.

For example:

```text
expected_head
  = caller assertion

observed_head
  = GVE observation
```

A result shall not imply that the caller asserted the observed value merely
because the assertion matched.

## Change summary

Terminal presentation shall include a concise Git short-status representation of
the mutation before commit.

The machine-readable result shall expose changed-path evidence independently of
that human presentation.

The short-status display and the full staged diff serve different purposes:

```text
short status
  -> rapid human scan

full staged diff
  -> agent/human semantic review
```

## Failure and partial execution

A failed `modify` operation shall preserve useful evidence already established.

A later publication failure does not erase:

- the exact expected and observed starting HEAD;
- branch-creation evidence;
- changed paths;
- validation results;
- staged semantic diff;
- created local commit.

A failed workflow is not equivalent to "nothing happened."

Later not-executed phases remain distinguishable from the phase that failed.

## Handoff continuation

The authoritative result JSON is the continuation artifact for subsequent work.

A caller or agent authorizing successor mutation should inspect relevant observed
result evidence rather than assume that the requested mutation, commit, push, or
verification succeeded.

This preserves the operational principle in
`user/script-transfer-handoff.json`: successor work follows verified results,
not requested outcomes.
