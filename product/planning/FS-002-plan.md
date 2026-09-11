---
functional_set: FS-002
artifact: plan
title: Product Macro Layer and CLI Plan
design_revision: bb72f1d02b67b6722af97ef9cc19e4b2a97ad65b
---

# FS-002 — Plan

## Design binding

This Planning revision consumes Product Design at exact Git revision
`bb72f1d02b67b6722af97ef9cc19e4b2a97ad65b`.

FS-002 extends the accepted FS-001 implementation. The existing Engine, task
registry, authority model, plugin implementations, workflow result semantics,
and native task-result references are preserved unless a concrete defect blocks
the macro surface.

## Technical intent

Build the smallest product-owned composition layer that can provide four stable
higher-level operations without inventing a second execution language.

The runtime path is:

```text
CLI
  -> parse closed macro request
  -> establish/derive repository authority
  -> verify repository expectations
  -> resolve static macro definition
  -> validate macro parameters
  -> Python macro builder constructs staged FS-001 invocations
  -> flatten to ordinary FS-001 workflow
  -> Engine.execute()
  -> regroup workflow task results by product stage metadata
  -> write macro result
```

There is exactly one task execution engine: the existing FS-001 Engine.

## Package structure

Build should add a small set of modules under `product/src/gve/`.

Recommended responsibilities are:

```text
macro.py
  MacroDefinition, MacroRegistry, Stage/plan data structures

macro_request.py
  closed request envelope and common repository expectation parsing

macro_runner.py
  expectation verification, builder invocation, Engine handoff, stage regrouping

macros/
  discover.py
  modify.py
  issue.py
  pr.py

product_macro_registry.py
  static registration of the four product macros
```

Exact internal names remain Build decisions. The important constraint is that
behavior remains ordinary product Python and that the Engine remains the only
generic task interpreter.

No executable macro definitions are loaded from JSON.

A macro is added to the public static registry only in the same Build step that
provides its complete executable implementation and public contract. Build does not
register schema-only or placeholder macros.

## Macro definition model

A macro definition should contain only stable product metadata plus an
implementation callable, conceptually:

```python
MacroDefinition(
    identity="modify",
    parameter_schema=MODIFY_SCHEMA,
    stages=MODIFY_STAGES,
    build=build_modify,
)
```

`parameter_schema` is public introspection data.

`stages` is the stable public stage description when a macro exposes product-owned
stages. Macros without a public stage contract need not provide it.

`build` is authoritative product behavior.

The introspection contract and runtime validator must remain extensionally
equivalent for accepted public parameter values, without requiring runtime schema
interpretation.

Runtime validation may be macro-specific Python code and should not grow into a
general schema-language interpreter.

## Staged macro plan

A builder may return a small typed structure such as:

```text
MacroPlan
  Stage("precheck", "PRECHECK", tasks=[...])
  Stage("mutate", "MUTATE", tasks=[...])
  ...
```

A Stage contains ordinary FS-001 task invocations.

Before Engine execution, the runner flattens stages in order into one ordinary
FS-001 workflow. Invocation IDs are stable within that generated workflow.

After execution, the runner maps the ordered workflow task records back into the
known stage boundaries.

Stages never affect authority, dispatch, failure semantics, or result-reference
resolution.

When Engine fail-fast behavior creates later `not-executed` records, regrouping
retains those records under their originally assigned stages.

## Request contract

Build shall implement the following closed schema-version-1 request envelope:

```json
{
  "schema_version": 1,
  "header": {
    "repository": {
      "identity": "owner/name",
      "branch": "branch-name",
      "head": "0123456789abcdef0123456789abcdef01234567"
    }
  },
  "macro": {
    "name": "discover",
    "parameters": {}
  }
}
```

The top-level object contains exactly `schema_version`, `header`, and `macro`.

`schema_version` is required and must be the JSON integer `1`. Unsupported
versions fail closed.

`header` is required and contains exactly `repository`.

`header.repository` is required and is a closed object whose only admitted fields
are `identity`, `branch`, and `head`. Each repository expectation field is optional
individually. Omission means that property is not guarded by the request. Explicit
`null` is not equivalent to omission and is rejected.

When present:

- `identity` is a non-empty canonical repository identity in `owner/name` form
  derived from a product-supported repository remote identity;
- `branch` is a non-empty branch name and requires exact equality with the
  observed current branch;
- `head` is a 40-character lowercase hexadecimal Git commit identity and requires
  exact equality with the observed local `HEAD`.

A request with an empty `header.repository` object is valid and relies only on
the repository context and active authority established by the CLI.

`macro` is required and contains exactly `name` and `parameters`.

`macro.name` is a required non-empty string identifying one registered product
macro. Unknown macro identities fail closed before macro execution.

`macro.parameters` is a required JSON object. Its admitted fields and values are
defined by the selected macro's closed public parameter contract.

Unknown fields at every maintained request-envelope level fail closed. Arrays,
scalars, or `null` are rejected where an object is required.

Remote-head expectations needed for publication are not caller request-envelope
fields. They remain product-owned guards inside `modify` and are observed by the
macro immediately before the mutation/publication points defined by that macro.

The request cannot grant filesystem, Git remote, process, or GitHub authority.

## Repository context

`gve macro` resolves a canonical repository root from `--repo` or current
repository context.

For Git publication, the macro implementation uses the product-supported active
repository remote and branch selection admitted by the macro parameter contract.

For GitHub issue/PR operations, repository identity is derived from the active
repository's supported remote URL form and intersected with active GitHub
authority.

Authority establishment remains outside caller macro parameters.

Repository-derived context does not itself grant authority. The macro CLI must
construct active `Authority` through explicit product policy before execution;
GitHub macros fail closed when matching GitHub repository authority is absent.

## Native result references

Generated FS-001 tasks use the existing FS-001 `$ref` contract directly.

Example conceptual sequence:

```text
commit
  -> result.commit

verify-remote
  expected = {"$ref": "commit.result.commit"}
```

No macro-specific reference syntax or translation layer is added.

## Initial macro behavior

### discover

Goal: bounded read-only repository discovery.

The `discover` public parameter contract is a closed object with one optional
field:

```json
{
  "observations": [
    "repository",
    "branch",
    "head",
    "status",
    "root_entries"
  ]
}
```

When `observations` is omitted, the product-owned default is:

```text
repository
branch
head
status
```

When present, `observations` must be a non-empty array of unique strings chosen
only from the five maintained identities above. Unknown values, duplicates,
non-string values, and an empty array fail closed.

The caller selects which product-defined observations are requested but does not
control task order. Build emits selected observations in this canonical
product-owned order regardless of caller array order:

```text
repository
branch
head
status
root_entries
```

The selected observation identities map exactly to existing governed FS-001
tasks:

```text
repository   -> git.repository {}
branch       -> git.branch {}
head         -> git.head {}
status       -> git.status {"include_untracked": true}
root_entries -> filesystem.list {"path": ".", "recursive": false}
```

`discover` exposes one public stage named `DISCOVER`. Its builder returns one
`MacroPlan` whose selected governed task invocations are all assigned to that
stage. Invocation identities are deterministic product-owned values derived from
the maintained observation identity rather than caller-provided task identities.

The macro performs no mutation and introduces no arbitrary path, recursive-list,
Git argument, task identity, query expression, or generic observation language.

Keep this implementation intentionally small; it is the first proving macro for
the new layer.

### modify

Parameters should cover:

```text
changes
commit_message
remote (default origin)
remote_branch (optional)
validate (default true)
allow_dirty (default false)
allowed_dirty_paths (default empty)
```

Each change contains a repository-relative path, desired content, and optional
expected current digest where supported by the existing filesystem task.

Product-owned stages:

```text
PRECHECK
MUTATE
VALIDATE
COMMIT
PUBLISH
VERIFY
```

PRECHECK:
- require exactly clean status by default;
- when `allow_dirty` is true, permit only exact declared dirty paths using a
  narrow governed status-scope capability;
- observe selected remote head before mutation/publication.

MUTATE:
- generate one governed filesystem change invocation per declared change in
  caller order.

VALIDATE:
- when enabled, generate exactly one governed `execute.script` invocation for
  `scripts/validate`;
- do not enumerate product validation tasks in the macro.

COMMIT:
- produce governed diff/review evidence sufficient to verify declared paths;
- run `git diff --check` through an existing governed capability or the narrowest
  added Git capability required;
- stage only declared mutation paths;
- create one commit with the supplied message.

PUBLISH:
- normal non-force push only;
- guard against the PRECHECK remote-head observation so a remote race fails
  closed.

VERIFY:
- observe selected remote head and require exact equality with the created
  commit.

Build may add the narrowest governed semantic Git observation/review capability
needed to realize reviewed FS-002 behavior when the accepted FS-001 vocabulary
lacks one required operation and the addition is an ordinary implementation
consequence that preserves accepted FS-001 Design. It should prefer extending a
plugin with one bounded semantic capability over expanding the macro layer.

If realizing a required primitive would change accepted FS-001 product meaning,
authority semantics, capability boundaries, or other consequential Design, Build
shall return upstream rather than defining that change as an implementation
decision.

### issue

Support the minimal read/create/modify operation set using existing governed
GitHub issue tasks.

Macro-specific Python chooses the task sequence for each operation.

No generic discriminator or conditional language is introduced.

### pr

Support the minimal read/create/modify operation set using existing governed
GitHub pull-request tasks.

Macro-specific Python chooses the task sequence for each operation.

## Introspection

`gve macro-list` outputs registered macro names.

`gve macro-schema NAME` outputs only the public parameter contract for the named
macro.

The introspection representation may resemble JSON Schema for familiar tooling,
but only the exact subset emitted by product code is part of FS-002. Runtime
correctness must not depend on implementing arbitrary schema keywords.

## CLI

Add:

```text
gve macro --in REQUEST.json --out RESULT.json [--repo PATH]
gve macro-list
gve macro-schema NAME
```

The macro result file is written on success and, when possible, on request or
execution failure.

The existing FS-001 execute interface remains available and unchanged.

## Installation

Build must provide one repository-supported installation mechanism that exposes
`gve` as a normal shell command outside the source-tree working directory. The
installed command must dispatch into the same product implementation as repository
execution; no installation-specific macro runtime is permitted.

The installation path must be deterministic for repeated development use. A repeat
installation is either idempotent or fails clearly without leaving conflicting
launchers behind.

Validation must exercise the installed command from a working directory outside the
repository and confirm at minimum `gve macro-list`, `gve macro-schema discover`, and
one non-mutating `gve macro` execution once the `discover` macro is available.

Terminal output may display generic macro/stage/task progress and task-provided
streams. Avoid a large switch statement that teaches the CLI the semantics of
each individual plugin task.

## Validation strategy

Validation should target public behavior and architectural boundaries rather than
interpreter internals.

Required validation areas:

- static registry contains exactly the macro identities whose complete public
  contracts and executable implementations are present; at FS-002 completion this
  set is exactly `discover`, `issue`, `pr`, and `modify`;
- request envelope rejects unknown fields and unsupported schema versions;
- each macro accepts valid parameters and rejects invalid parameters;
- introspection matches each public parameter contract;
- builders generate only registered governed task identities;
- generated workflow invocation identities are unique;
- generated native `$ref` values resolve through the existing Engine;
- stage flatten/regroup preserves task order and task result evidence;
- failures remain fail-fast;
- macro requests cannot widen active authority;
- `discover` is read-only;
- `modify` enforces clean/scoped-dirty preconditions, one canonical validation
  invocation, declared-path staging, normal guarded push, and exact remote
  verification;
- `issue` and `pr` map each supported operation to the expected governed GitHub
  behavior;
- CLI commands produce deterministic machine-readable output;
- canonical `scripts/validate` passes.

Tests should assert public contracts and observable task composition. They should
not assert implementation artifacts that exist only to support a generic macro
DSL because no such DSL is part of FS-002.

## Build order

Build proceeds in this order:

1. small macro data structures and empty static registry infrastructure;
2. closed request envelope and direct validation boundary;
3. minimal runner that hands generated workflows to the existing Engine;
4. `discover` as the proving implementation;
5. CLI list/schema/macro execution surfaces;
6. `issue`;
7. `pr`;
8. `modify`;
9. only the narrow plugin primitives proven necessary by the macros;
10. repository-supported installation mechanism and installed-command smoke tests;
11. public-behavior validation and canonical repository validation.

Do not implement all four macros before the `discover` path proves the
architecture.

## Change discipline

Each Build step should remain independently reviewable.

Do not self-host FS-002 development through the unfinished macro layer. Continue
using the established script-transfer handoff until FS-002 has passed its own
Validation and Build Review.

Do not expand scope in response to convenience. A missing generic condition,
loop, template, schema keyword, or presentation feature is not a defect because
those mechanisms are intentionally absent from this Functional Set.

## Completion sequence

Before FS-002 Acceptance:

1. run task-specific validations;
2. run canonical `scripts/validate`;
3. run `git diff --check`;
4. install GVE through the repository-supported installation mechanism;
5. from outside the repository, smoke-test the installed `gve` command, including
   macro introspection and a non-mutating macro execution;
6. confirm the branch contains no unrelated changes;
7. perform Build Review against this Plan;
8. perform Semantic Review against Product Design revision
   `bb72f1d02b67b6722af97ef9cc19e4b2a97ad65b`;
9. only then consider integration into `main`.
