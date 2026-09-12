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

The version-1 maintained `modify.result` fields are:

```text
repository
branch
publication_branch
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

Meanings:

- `repository`: canonical active repository root/identity evidence selected by
  existing macro-result convention;
- `branch`: effective local branch when established;
- `publication_branch`: effective publication branch when established;
- `expected_head`: exact caller value;
- `observed_head`: GVE-observed starting HEAD when established;
- `branch_created`: boolean when the branch outcome is known;
- `files_changed`: stable changed-path evidence when established;
- `validation`: object describing whether canonical validation was requested and
  its known status/evidence;
- `diff`: complete staged diff when successfully captured, otherwise absent;
- `commit`: created commit identity when established, otherwise absent;
- `commit_count`: number of product-created commits known to have occurred;
- `push_mode`: `normal` when publication mode is established;
- `remote_head`: verified/observed effective publication head when established;
- rewrite/force-push and merge indicators: boolean evidence when known.

Planning permits unavailable continuation fields to be omitted rather than
invented. Build shall use one deterministic absence policy consistently and
reflect it in public result tests.

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
