---
functional_set: FS-003
artifact: plan
title: Governed Modify Workflow and Terminal Presentation Plan
design_revision: b33bcaefe870fa1e18beaa6518ab6337f7333c65
---

# FS-003 — Plan

## Design binding

This Planning revision consumes Product Design at exact Git revision
`b33bcaefe870fa1e18beaa6518ab6337f7333c65`.

FS-003 extends the accepted FS-002 implementation. The existing Engine, task
registry, authority model, plugins, macro registry, request envelope, native
`$ref` mechanism, and ordered fail-fast task evidence are preserved except where
this Plan explicitly changes the maintained product surface or `modify`
contract.

## Technical intent

Make registered product macros the only maintained runtime execution surface and
upgrade `modify` into a deterministic handoff operation with caller-owned
starting-state assertions, explicit branch intent, stable semantic-review
evidence, and live observational terminal presentation.

The target runtime path is:

```text
CLI
  -> parse closed macro request
  -> establish active authority
  -> validate macro contract
  -> attach optional execution observer
  -> product macro builds internal FS-001 workflow
  -> existing Engine executes registered tasks
  -> observer receives execution/command/stream events
  -> macro-owned result projector derives stable continuation evidence
  -> write authoritative result JSON
  -> emit final terminal summary
```

The observer and result projector do not create a second execution engine.

## Maintained CLI surface

Build shall remove the maintained `execute` subcommand from normal CLI dispatch
and help/introspection.

The maintained commands are exactly:

```text
gve macro --in REQUEST.json --out RESULT.json [--repo PATH]
gve macro-list
gve macro-schema NAME
```

The Python Engine and ordinary FS-001 workflow payload remain available to
product code and mechanical tests as internal implementation machinery.

Removal of `gve execute` is a public product-surface change, not deletion of
FS-001 execution semantics.

## Execution observer and terminal presentation

Build shall introduce the smallest observer/event boundary that can represent
live execution without moving product meaning into printing code.

A suitable conceptual event vocabulary is:

```text
macro-start
phase-start
step-start
task-start
command-start
command-stdout
command-stderr
task-success
task-failure
step-success
step-failure
macro-success
macro-failure
```

Exact internal event names and class layout are Build decisions.

The event mechanism shall satisfy these constraints:

- an observer is optional;
- absence of an observer leaves governed execution results unchanged;
- observers cannot grant authority, alter task parameters, change task order,
  suppress failures, retry tasks, or synthesize success;
- product code identifies meaningful phases/material steps;
- plugins or their command adapters surface exact external command invocation
  and captured streams where an external command actually occurs;
- terminal formatting consumes events/evidence and does not become a task
  interpreter.

The maintained terminal transcript shall provide the semantic presentation
defined by PD-070, including operation identity, phase transitions, announced
material work, exact external commands, OUT/ERR stream lines, explicit PASS/FAIL,
and a final summary.

For `modify`, the terminal shall show a short-status representation before the
product commit. Full staged diff text remains machine evidence and is not dumped
to terminal by default.

The final `modify` summary shall show these labels when the corresponding
evidence is applicable:

```text
Operation
Repository
Branch
Expected HEAD
Observed HEAD
Files Changed
Validation
Commit
Remote HEAD
Result JSON
```

On failed execution, terminal presentation shall identify the failing phase and
task when known, the failure reason, prior successful work, and later work that
was not executed. Presentation of failure evidence shall remain derived from the
authoritative execution result and observer events rather than creating separate
execution meaning.

## Result artifact behavior

`gve macro --out RESULT.json` shall attempt to write the authoritative result for
both success and failed governed execution whenever the destination remains
writable.

The CLI shall distinguish:

```text
governed execution status
result-artifact write status
```

An artifact write failure shall not rewrite a governed failure as success or
erase the in-memory governed result.

Where writing the requested result path fails, the CLI shall report that output
failure clearly in terminal/exit behavior. Exact exit-code allocation remains a
Build decision provided success is never reported for a failed governed
execution or failed required output write.

## Modify public parameter contract

FS-003 revises the closed `modify` parameter object.

The maintained fields are:

```text
changes
commit_message
expected_head
branch (optional)
remote_branch (optional)
validate (default true)
allow_dirty (default false)
allowed_dirty_paths (default empty)
```

### `expected_head`

`expected_head` is required for every `modify` request.

It is exactly one lowercase 40-character Git commit identity.

Before any product-requested repository effect, `modify` shall observe local
`HEAD` and require exact equality with `expected_head`.

A missing, malformed, or mismatched `expected_head` fails before mutation.

The existing request-envelope `header.repository.head` remains an independent
common repository expectation when supplied. Planning does not silently alias
that header field to the required macro parameter. If both are supplied, both
guards must be satisfied.

### `branch`

`branch` is optional.

When present it is a closed object:

```json
{
  "create": true,
  "name": "dev/feature-x"
}
```

The object contains exactly `create` and `name`.

`create` must be JSON boolean `true`; `false` is rejected because omission
already means no branch-creation request and accepting `false` would add no
distinct product intent.

`name` is a non-empty branch name admitted by the existing governed Git branch
semantics.

When `branch` is omitted, no local branch is created and the effective local
branch is the prechecked active branch.

When supplied:

1. PRECHECK verifies exact `expected_head`;
2. the requested local branch must not already exist;
3. GVE creates the branch from exactly `expected_head`;
4. GVE switches to it;
5. GVE verifies the active branch equals `name`;
6. GVE verifies HEAD still equals `expected_head`;
7. only then may MUTATE begin.

### Effective publication branch

The effective publication branch is:

```text
remote_branch
  when explicitly supplied

otherwise
  effective local branch
```

`remote_branch`, when present, remains a non-empty branch name within authorized
`origin`.

Cross-name publication is therefore supported explicitly:

```text
local:  dev/feature-x
remote: review/feature-x
```

The request cannot select another remote; the maintained remote is `origin`.

## Modify stages

The stable `modify` stage identities become:

```text
PRECHECK
BRANCH
MUTATE
VALIDATE
COMMIT
PUBLISH
VERIFY
```

`BRANCH` contains generated task records only when branch creation was requested.
If no branch work is required, the stage remains valid metadata and may contain
no task records.

## Required governed Git capabilities

Build shall realize FS-003 through bounded semantic Git capabilities.

If existing plugin vocabulary is insufficient, Build may add the narrowest
registered tasks required for:

- create a named local branch from an exact expected commit;
- switch to a named local branch;
- assert/observe local branch existence or absence where needed;
- observe remote branch state as either exact commit identity or absence;
- expose concise short-status evidence without losing fixed-width status
  columns;
- capture complete staged diff;
- perform cached diff whitespace checking;
- normal push from the effective local branch to the effective publication
  branch.

No task may accept arbitrary Git argv, arbitrary shell fragments, force options,
or unconstrained remote names.

## PRECHECK behavior

PRECHECK shall establish:

- repository identity;
- current local branch;
- local HEAD exactly equal to `expected_head`;
- accepted worktree/dirty scope under the existing FS-002 contract;
- accepted staging scope;
- effective local branch intent;
- effective publication branch;
- publication remote state.

Publication remote state is represented as exactly one of:

```text
existing(branch, commit_oid)
absent(branch)
```

That state is retained as the publication race guard.

For a cross-name publication destination, the guard applies to the effective
publication branch, not the local branch name.

## BRANCH behavior

When branch creation is requested, BRANCH performs only the reviewed creation,
switch, branch verification, and HEAD verification sequence.

A pre-existing requested branch fails closed.

The macro does not silently reinterpret create intent as use-existing intent.

## MUTATE and VALIDATE behavior

MUTATE preserves the accepted FS-002 change contract and caller change order.

Only declared repository-relative change paths may be mutated.

When validation is enabled, VALIDATE emits exactly one governed
`execute.script` for repository-root `scripts/validate`.

No alternate validation command is caller-selectable.

## COMMIT behavior and semantic evidence

Before commit, `modify` shall:

1. re-check repository, effective local branch, guarded pre-commit HEAD
   relationship, dirty scope, and staging scope;
2. establish pending-change containment within the declared mutation path set;
3. obtain governed short-status evidence for terminal presentation;
4. stage only declared mutation paths;
5. capture the complete staged diff;
6. run the equivalent of `git diff --cached --check`;
7. create at most one product-requested commit.

The staged diff captured in step 5 is the stable semantic-review diff.

If a later step fails, that captured diff remains available in the macro-level
result.

## PUBLISH and VERIFY behavior

Immediately before push, PUBLISH shall re-observe the effective publication
branch and require exact equality with the PRECHECK guard:

- an existing branch must still resolve to the exact guarded commit;
- an absent branch must still be absent.

Any mismatch fails before push.

Publication uses normal non-force semantics only.

After push, VERIFY observes the effective publication branch and requires exact
equality with the commit created by `modify`.

## Stable modify macro-level result

The macro runner shall support a product-owned result projection hook rather
than hard-coding `modify` task identities into generic runner semantics.

Conceptually:

```text
MacroDefinition
  ...
  project_result(plan, engine_result, repository_context) -> object
```

Exact API shape is a Build decision.

The `modify` authoritative result shall retain existing top-level macro status,
stages, and task evidence and add stable macro-level continuation evidence under
a `result` object.

The version-1 maintained `modify.result` object has a fixed public key set:

```json
{
  "repository": {
    "root": "/canonical/repository/root",
    "identity": "owner/name"
  },
  "branch": "dev/feature-x",
  "publication_branch": "dev/feature-x",
  "expected_head": "0123456789abcdef0123456789abcdef01234567",
  "observed_head": "0123456789abcdef0123456789abcdef01234567",
  "branch_created": true,
  "files_changed": ["path/a", "path/b"],
  "validation": {
    "requested": true,
    "status": "success"
  },
  "diff": "diff --git ...",
  "commit": "89abcdef0123456789abcdef0123456789abcdef",
  "commit_count": 1,
  "push_mode": "normal",
  "remote_head": "89abcdef0123456789abcdef0123456789abcdef",
  "history_rewrite_or_force_push_occurred": false,
  "merge_occurred": false
}
```

All keys above are always present once a valid `modify` request has entered macro
execution and a macro result can be constructed.

The single version-1 unavailable-evidence representation is JSON `null`.
A field whose evidence has not yet been established is `null`; Build shall not
omit that key or substitute a guessed value.

Field meanings and concrete types are:

- `repository` is always an object with fixed keys `root` and `identity`;
  `root` is the canonical absolute active repository root when established,
  otherwise `null`; `identity` is canonical `owner/name` when established,
  otherwise `null`;
- `branch` is the effective local branch string when established, otherwise
  `null`;
- `publication_branch` is the effective publication branch string when
  established, otherwise `null`;
- `expected_head` is the exact caller-supplied 40-character commit identity and
  is non-null for a valid `modify` request;
- `observed_head` is the exact GVE-observed starting HEAD when established,
  otherwise `null`;
- `branch_created` is `true` when the requested branch was successfully created,
  `false` when branch creation was not requested and that fact is established,
  and `null` before the branch-creation outcome is established;
- `files_changed` is an array of repository-relative changed-path strings when
  changed-path evidence is established, otherwise `null`;
- `validation` is always an object with fixed keys `requested` and `status`;
  `requested` is the boolean value derived from the validated request and
  `status` is exactly `not-requested`, `not-executed`, `success`, or `failed`;
- `diff` is the complete staged diff string when successfully captured,
  otherwise `null`;
- `commit` is the created commit identity when established, otherwise `null`;
- `commit_count` is an integer and is exactly `0` until the product creates its
  commit, then exactly `1`;
- `push_mode` is always the string `normal` for a valid `modify` request because
  FS-003 admits no other publication mode;
- `remote_head` is the latest established observed effective-publication-branch
  commit identity after publication/verification evidence is available,
  otherwise `null`;
- `history_rewrite_or_force_push_occurred` is always boolean and remains `false`;
- `merge_occurred` is always boolean and remains `false`.

The fixed shape does not authorize invention of evidence. `null` explicitly
means that the corresponding observation or effect has not been established.

The result projection never removes stage/task records.

## Failure and evidence retention

A failed `modify` result shall preserve every stable macro-level evidence value
already established.

In particular:

- failure after staged diff capture retains `diff`;
- failure after commit retains `commit` and `commit_count`;
- failure after branch creation retains branch evidence;
- publication failure retains pre-publication evidence;
- later not-executed stage/task records remain present under existing macro
  fail-fast semantics.

The projector must derive evidence only from actual caller assertions, repository
observations, successful governed task results, and established product context.
It must not synthesize an outcome that was not observed.

## Introspection correspondence

`gve macro-schema modify` shall describe exactly the revised closed parameter
contract, including required `expected_head` and optional `branch`.

Runtime validation shall accept exactly the same public parameter space.

The public schema shall not expose internal task identities, event implementation
details, or generated workflow structure.

## Validation construction

Build shall add or revise product validation tasks covering at least:

- absence of maintained `gve execute` CLI dispatch/help;
- continued internal Engine/FS-001 execution regression coverage;
- observer-disabled semantic equivalence;
- terminal phase/step/command/stream/PASS/FAIL presentation;
- exact final `modify` summary labels for applicable evidence;
- failed transcript identification of failing phase/task, failure reason, prior
  successful work, and later not-executed work;
- result JSON on governed failure when writable;
- explicit artifact-write failure behavior;
- required/malformed/mismatched `expected_head`;
- no effects before expected-HEAD validation;
- omitted branch creation;
- successful explicit branch creation from exact HEAD;
- requested-branch-already-exists failure;
- same-name default publication;
- explicit cross-name publication;
- existing-remote exact-OID race guard;
- new-remote verified-absence race guard;
- remote race before push;
- short-status fixed-width preservation;
- full staged diff in stable macro result;
- diff preservation after later failure;
- commit evidence preservation after later publication failure;
- exact verified remote head after normal push;
- introspection/runtime contract correspondence;
- complete underlying stage/task evidence retention.

Build shall bind every M or B FS-003 normative requirement to exact mechanical
validation tasks in the product Requirement Evaluation Manifest.

## Build sequence

A practical Build order is:

```text
1. CLI public-surface restriction
2. observer/event plumbing with no semantic change
3. terminal presenter
4. modify parameter/schema revision
5. bounded branch/remote-state Git capabilities
6. modify PRECHECK + BRANCH changes
7. short-status + staged-diff evidence path
8. result-projector hook and modify stable result
9. publication/verification guard updates
10. result-artifact failure handling
11. validation and requirement bindings
12. canonical validation + Semantic Review
```

Steps may be combined when a smaller coherent patch is clearer, but Build shall
not bypass the reviewed boundaries.

## Build stop conditions

Build returns upstream rather than inventing semantics if implementation reveals
a need for:

- automatic branch creation not requested by the caller;
- branch reuse semantics beyond the reviewed create-only request;
- arbitrary remote selection;
- force push/history rewrite;
- caller-controlled Git argv or shell fragments;
- a second workflow/event behavior language;
- semantic diff interpretation by GVE;
- a change to accepted authority semantics;
- a materially different result-field meaning or publication race model.

## Completion evidence

A Build candidate is ready for Semantic Review when:

- every FS-003 M/B requirement is active and mechanically bound;
- `scripts/validate` passes;
- the staged/committed implementation diff is reviewable;
- public CLI/introspection behavior matches Planning;
- failure-path evidence has been exercised;
- normal publication behavior has been exercised without force/history rewrite;
- the candidate can be compared directly against Design revision
  `b33bcaefe870fa1e18beaa6518ab6337f7333c65` and this Planning revision.
