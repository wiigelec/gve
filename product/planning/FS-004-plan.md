---
functional_set: FS-004
artifact: plan
title: Macro Hardening, Discovery, and Recovery Plan
design_revision: 76d1caf69cc2ebc542116d19ec6d0c8efb5c7b6a
---

# FS-004 — Plan

## Design binding

This Planning revision consumes Product Design at exact Git revision
`76d1caf69cc2ebc542116d19ec6d0c8efb5c7b6a`.

FS-004 extends the accepted FS-003 implementation. Existing Engine execution,
authority, macro registration, fail-fast task records, result references,
publication guards, terminal observation, and complete-content mutation behavior
remain in force except where this Plan explicitly refines them.

## Technical intent

Make routine safe repository edits compact to express while improving the
observation and recovery evidence needed to prepare and diagnose those edits.

The maintained path remains:

```text
caller
  -> closed registered macro contract
  -> product-owned macro orchestration
  -> existing FS-001 Engine
  -> registered governed tasks
  -> stable macro result + observational presentation
```

FS-004 shall not add a second execution engine or generic caller-authored
behavior language.

## Modify change contract

The public `modify.changes` array retains create and modify operations.

### Create

A create change remains:

```json
{
  "operation": "create",
  "path": "relative/path.txt",
  "content": "complete new file content"
}
```

No patch form is added for create.

### Existing-file modify

A modify change requires:

```text
operation
path
expected_sha256
```

and exactly one of:

```text
content
diff
```

A request containing neither or both fails contract validation before macro
execution.

`content` retains accepted complete replacement semantics.

`diff` is a UTF-8 unified patch representation for exactly one declared file.

## Bounded patch governed task

Build shall add the smallest governed task boundary needed to apply one declared
file patch. The task identity is a Build naming decision; its public task
semantics are fixed by this Plan.

Its inputs include exactly:

```text
path
expected_sha256
diff
```

before internal normalization.

Validation occurs before mutation and shall:

1. normalize and authority-check the declared repository-relative path;
2. require the target to be an existing UTF-8 regular file;
3. verify the current SHA-256 equals `expected_sha256`;
4. parse or mechanically inspect the unified patch strongly enough to prove that
   every file header/path refers to exactly the declared path;
5. reject additional file sections;
6. reject absolute paths, parent escape, `/dev/null`, rename/copy semantics, and
   path changes;
7. reject binary patch forms;
8. run a non-mutating apply check against the current repository state;
9. fail without changing the worktree if any check fails.

Execution then applies exactly the already-checked patch and returns normal
effect evidence including the modified path plus previous and resulting
SHA-256 values.

Patch handling shall not expose arbitrary `git apply` options or caller command
construction.

## Modify orchestration integration

`modify` shall map complete-content modifications to the existing filesystem
modify task and diff modifications to the bounded patch task.

All existing `modify` guards continue to apply:

- exact `expected_head`;
- clean worktree by default;
- explicitly scoped tolerated dirty paths;
- no pre-existing staged changes outside declared mutation scope;
- declared path uniqueness after normalization;
- canonical validation when requested;
- pending/staged difference checks;
- one product commit at most;
- normal guarded publication;
- exact remote verification.

The declared mutation path set is independent of content representation.

## Discover public contract

The existing `observations` field and defaults remain compatible.

FS-004 adds explicit opt-in fields:

```text
list_folder
read_file
```

and adds `tree_status` as a supported observation concept.

Exact JSON naming may use snake_case consistently with existing Python/public
schema conventions. Introspection and runtime validation must agree exactly.

### Folder listing

`list_folder` is an array of one or more closed request objects:

```json
{"path": "product/src/gve"}
```

Planning does not expose recursive arbitrary filesystem traversal through this
new convenience surface. Existing lower-level governed capabilities remain
internal implementation choices.

Each requested folder produces one deterministic result record identified by
its normalized requested path. Entries are sorted by repository-relative path
and include at least path and kind.

Duplicate normalized requested folder paths fail contract validation.

### Multi-file read

`read_file` is an object with:

```json
{
  "paths": ["a.txt", "b.txt"]
}
```

Paths must be non-empty, repository-relative, unique after normalization, and
remain inside the repository.

The macro emits one governed file-read task per requested path, preserving
caller path order after validation.

The projected discover result returns file records containing:

```text
path
content
sha256
```

No read succeeds by silently omitting another failed requested file; ordinary
Engine fail-fast evidence remains authoritative.

### Tree status

`tree_status` is a product-owned consolidated observation.

Build should realize it as one dedicated read-only governed Git task unless an
equally bounded implementation preserves one stable result contract without
forcing callers to reconstruct semantics.

The result contains at least:

```text
repository:
  root
  remotes
branch
detached
head
status:
  clean
  entries
staged:
  entries
diff:
  unstaged
  staged
  tracked_tree
```

`status.entries` uses complete porcelain-derived records and includes untracked
paths when present.

`diff.unstaged` is complete tracked working-tree versus index diff text.

`diff.staged` is complete index versus HEAD diff text.

`diff.tracked_tree` is complete HEAD versus effective tracked worktree/index
state. Build may obtain this through a temporary-index or equivalent read-only
mechanism, but the operation must not mutate the real index.

For an unborn HEAD, detached HEAD, or other supported Git edge state, result
fields use explicit null/boolean state rather than guessing a branch identity.

Tree status does not include untracked file contents.

## Discover result projection

`discover` shall provide stable macro-level projection for newly added
convenience observations so callers do not have to inspect internal task IDs.

The projection preserves underlying task records and includes requested
observation data keyed or ordered deterministically.

Large complete content and diff evidence remains machine-readable result data;
terminal presentation may summarize it rather than printing it in full.

## Repository-selection diagnostics

CLI repository context establishment shall produce structured, actionable
failures.

At minimum distinguish:

### Selected path is not a Git repository

Result message identifies the selected resolved path.

### Selected path is inside a Git repository but not top level

Result details contain:

```text
selected
observed_top_level
```

GVE fails rather than silently replacing the requested repository.

### Request expectation mismatch

Existing repository identity, branch, and head request guards remain fail-closed.

Their error details contain:

```text
field
expected
observed
```

Presentation may make these friendlier, but the structured evidence is
authoritative.

## Recovery trigger boundary

Automatic recovery is considered only when all of the following are true:

- governed macro execution has failed;
- the current invocation produced worktree or branch effects;
- no product commit has been created;
- recovery can be bounded to effects proven to belong to this invocation.

A failure before any mutation returns recovery state `not-required`.

A failure at or after product commit returns recovery state `not-attempted` with
reason `commit-created` or a more specific later-state reason.

## Pre-mutation recovery capture

Before the first recoverable effect, `modify` shall retain enough invocation-
local evidence to restore macro-owned state without touching unrelated work.

For each declared existing-file modification this includes either:

- complete pre-mutation bytes/content already read under the exact digest guard;
  or
- another bounded restoration mechanism proven to restore exactly that file.

For a create operation, recovery records that the path did not exist before the
macro-owned create.

For requested branch creation, recovery records the original active branch and
the created branch identity.

Recovery evidence is invocation-local and is not caller-authored behavior.

## Worktree recovery

When recovery is eligible:

- a macro-created file may be removed only if it is still attributable to the
  failed invocation and doing so cannot remove unrelated subsequent work;
- a macro-modified file may be restored only to the captured pre-mutation state;
- recovery shall not alter paths outside the declared macro mutation set;
- recovery shall not modify admitted dirty paths unless that same path was also
  a declared macro mutation and its exact pre-mutation state was captured;
- if safe attribution cannot be established, recovery stops and reports residual
  state instead of guessing.

Recovery actions shall themselves be represented as governed execution evidence
or an equivalently authoritative product-owned recovery record tied to the
failed invocation.

## Branch recovery

If the macro created and switched to a new local branch before failure and no
commit was created, recovery may:

1. verify the worktree is safe for branch switching after file recovery;
2. switch back to the exact original branch;
3. verify the created branch still points at the original expected head and has
   no independent commits;
4. delete only that created local branch.

If any proof fails, branch cleanup is skipped and residual state is reported.

No branch that pre-existed the invocation may be deleted.

## Post-commit behavior

Once `modify-commit` succeeds, automatic rollback is forbidden.

Recovery shall not automatically perform:

```text
git reset
git commit --amend
git revert
git branch -D
force push
remote branch deletion
```

The macro-level result retains the created commit and continuation evidence.

## Publication ambiguity

Publication remains normal non-force push guarded by the previously observed
remote head.

If push transport reports failure, or push succeeds but VERIFY cannot establish
the expected remote head, projected result evidence includes:

```text
publication_attempted
publication_verified
local_commit
remote_head_before
remote_head_after (when observable)
publication_state
```

`publication_state` distinguishes at least:

```text
not-attempted
attempted-unverified
verified
```

No automatic force push or remote rewrite occurs.

## Recovery result projection

`modify` macro-level projection adds a stable recovery object:

```json
{
  "mutation_started": false,
  "mutated_paths": [],
  "branch_effect": null,
  "commit_created": false,
  "publication_attempted": false,
  "publication_verified": false,
  "recovery": {
    "state": "not-required",
    "actions": [],
    "residual_state": []
  }
}
```

Exact representation may be expanded by Build, but these semantic distinctions
must remain directly machine-readable.

Applicable recovery states include at least:

```text
not-required
not-attempted
success
partial
failed
```

A recovery result never changes macro overall status from failure to success.

## Failure preservation

The existing Engine fail-fast task behavior remains unchanged.

If recovery requires additional governed actions after a failed primary Engine
workflow, Build may introduce a product-owned recovery execution pass, but it
must:

- use the existing Engine and registered tasks;
- be selected only by product-owned `modify` recovery policy;
- never be caller programmable;
- preserve the original failure as primary;
- record recovery task evidence separately and in order;
- never synthesize success for the failed macro.

This is not a second generic task engine.

## Mechanical validation plan

Build validation shall cover at least:

### Modify contract

- complete-content modify remains accepted;
- diff-only modify is accepted;
- both content and diff are rejected;
- neither content nor diff is rejected;
- malformed digest/path/diff is rejected;
- duplicate normalized paths are rejected.

### Patch safety

- one-line change succeeds;
- stale SHA-256 fails before mutation;
- wrong target path in patch fails before mutation;
- multi-file patch fails before mutation;
- path escape fails;
- rename/copy/delete/binary patch forms fail;
- non-applicable patch fails without changing the target;
- successful patch reports previous/result digest.

### Discover

- existing defaults remain unchanged;
- multiple folder listings preserve deterministic order;
- duplicate normalized folder requests fail;
- multiple file reads return content and digest;
- failed file read preserves fail-fast evidence;
- tree status reports branch/HEAD/status/staged/unstaged/tracked-tree diff;
- untracked paths appear in status but their contents are not implicitly read;
- tree-status task has no mutation effects.

### Repository diagnostics

- non-repository path produces the dedicated failure and selected-path detail;
- repository subdirectory produces selected and top-level detail;
- identity/branch/head expectation mismatches retain expected/observed evidence.

### Recovery

- failure before mutation reports not-required;
- failure after created file removes only that macro-created file when safe;
- failure after modified file restores exact pre-mutation content when safe;
- admitted unrelated dirty work survives recovery byte-for-byte;
- unsafe attribution causes residual-state reporting rather than destructive
  cleanup;
- created branch can be safely returned/deleted only under the planned guards;
- pre-existing branch is never deleted;
- failure after commit never resets/reverts/amends/deletes history;
- publication ambiguity retains local and remote evidence;
- recovery failure keeps overall macro failure.

### Compatibility and boundaries

- existing complete-content modify integration continues to pass;
- existing discover default task composition remains compatible;
- macro introspection matches runtime contracts;
- no caller-authored tasks or generic patch options are exposed;
- canonical `scripts/validate` passes.

## Build surfaces

Expected implementation surfaces include:

```text
product/src/gve/macros/modify.py
product/src/gve/macros/discover.py
product/src/gve/plugins/filesystem.py and/or a narrowly scoped patch task
product/src/gve/plugins/git.py
product/src/gve/macro_runner.py
product/src/gve/cli.py
product/src/gve/presenter.py only if diagnostic/recovery presentation requires it
product/validation/macro_modify.py
product/validation/macro_discover.py
product/validation/filesystem.py
product/validation/git.py
product/validation/cli.py
product/validation/macro_integration.py as applicable
product/specs/FS-004-*.md
product/validation/requirement-evaluation.json
```

Build shall prefer the smallest implementation preserving existing task and
macro semantics.

## Planning completion

Planning is ready for Build when:

- FS-004 normative requirements are derived from this Plan and PD-090;
- each requirement has an evaluation classification;
- M/B requirements have exact planned validation bindings before acceptance;
- no unresolved semantic decision is delegated to implementation behavior.
