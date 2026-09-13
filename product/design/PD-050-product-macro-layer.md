---
doc_id: PD-050
title: Product Macro Layer
dependencies:
  - PD-001
  - PD-010
  - PD-020
  - PD-030
  - PD-040
---

# Product Macro Layer

## Purpose

The product macro layer provides product-owned higher-level repository operations
without creating a second workflow language or execution engine.

A macro is a named GVE operation implemented by GVE. A caller selects the macro
and supplies values admitted by that macro's closed parameter contract. GVE owns
the macro's orchestration.

The runtime relationship is:

```text
macro request
  -> macro-specific parameter validation
  -> product-owned Python macro builder
  -> FS-001 workflow/task invocations
  -> existing Engine
  -> existing governed plugin tasks
  -> macro result
```

The FS-001 engine remains the only task orchestration engine.

## Product-owned orchestration

PD-001 defines the underlying caller-owned FS-001 orchestration model. PD-070
refines the maintained product execution surface so runtime callers do not submit
raw FS-001 workflows through the maintained CLI.

For maintained runtime execution, a caller selects a registered product macro and
GVE owns the orchestration for that fixed named operation. The macro constructs
the internal FS-001 workflow used by the existing Engine.

The FS-001 payload and Engine remain the internal governed orchestration mechanism.
Making raw FS-001 workflow submission internal does not change FS-001 task,
authority, reference, failure, or evidence semantics.

A runtime caller does not provide task order, task identities, conditions, loops,
templates, result-reference expressions, or executable implementation logic.
Those decisions belong to the selected product macro.

## Implementation model

Each macro is implemented in ordinary product Python code.

A macro implementation may validate its parameters, choose among product-defined
paths, repeat product-defined operations over caller data, and construct the
ordered FS-001 task invocations required for that macro.

Those implementation-language features are not exposed as a caller language.

The macro layer shall not define or interpret a generic declarative behavior
language containing constructs such as:

```text
condition expressions
generic for-each constructs
template binding operators
macro-local result-reference syntax
caller-defined stages
caller-defined tasks
generic continuation rules
```

Product behavior belongs in normal product code where it can use direct control
flow and ordinary tests.

## Engine reuse

Macro implementations construct invocations for tasks already registered in the
active product registry and execute them through the existing FS-001 Engine.

A macro must not call filesystem, Git, process, or GitHub transport directly when
the effect is already represented by a governed plugin task.

The Engine continues to own:

- registered task resolution;
- FS-001 task-result reference resolution;
- task parameter validation;
- active authority enforcement;
- ordered fail-fast execution;
- structured task and workflow evidence.

The macro layer does not duplicate those responsibilities.

## Macro registry

The product owns a static macro registry.

Each registered macro definition contains, conceptually:

```text
identity
public parameter description/schema
implementation callable
public stage description when applicable
```

Runtime callers cannot install, replace, alias, or define macros.

Unknown macro identities fail closed before macro execution.

A macro definition is registrable only when its public contract and executable
product implementation are both complete. The registry shall not advertise a
macro identity whose implementation is absent or intentionally placeholder-only.

## Parameter contracts

Each macro exposes a closed parameter contract.

Product code performs authoritative runtime parameter validation. Introspection
may expose a machine-readable schema or equivalent description, but that
description is not an executable macro implementation language.

The product need not implement a general-purpose schema engine merely to support
macro parameters. Macro-specific validation may be direct Python code when that
is simpler and clearer.

Defaults are product-owned and deterministic.

The public parameter description and the authoritative runtime validator must
describe the same accepted parameter space: every value represented as valid by
the public contract must be accepted by runtime validation, and runtime validation
must not accept public parameter shapes outside that contract. This correspondence
does not require a generic schema interpreter.

## Task-result references

Macros reuse the native FS-001 task-result reference mechanism when a generated
task needs a value from a prior generated task.

The macro layer shall not introduce a second result-reference syntax and then
translate it into FS-001 references.

## Stages

A macro may expose stable product-owned stages such as:

```text
PRECHECK
MUTATE
VALIDATE
COMMIT
PUBLISH
VERIFY
```

Stages are presentation and result-grouping metadata around generated task
invocations. They are not executable capabilities and do not alter Engine
semantics.

The Engine need not understand stage meaning.

Stage regrouping preserves every Engine task record, including `not-executed`
records produced after a prior task failure. Each generated invocation remains
associated with its product-owned stage regardless of execution status.

## Failure semantics

Macro execution is fail-fast because its generated FS-001 workflow is fail-fast.

When a governed task fails, later generated tasks are not executed. Earlier task
evidence remains available.

A macro may not weaken active authority or convert a governed failure into
success merely because a higher-level operation was requested.

## Initial product macros

The first macro set is:

```text
discover
modify
issue
pr
```

### discover

`discover` performs bounded governed read-only repository discovery through
explicitly supported filesystem and Git observations. Its public parameter
contract selects only product-defined observations and does not form a generic
query language. `discover` performs no mutation.

### modify

`modify` performs a bounded repository change and publication workflow using
governed tasks. Its product-owned sequence is conceptually:

```text
PRECHECK
  repository/branch/head/worktree and remote-head guards

MUTATE
  filesystem changes for declared paths

VALIDATE
  one canonical repository validation invocation when enabled

COMMIT
  verify the pending difference is contained within the declared mutation path set
  reject patch whitespace errors before staging
  stage declared paths only
  create commit

PUBLISH
  normal guarded push

VERIFY
  confirm remote head equals the created commit
```

The canonical repository validation boundary is `scripts/validate`. The macro
does not enumerate the repository's individual validator implementations.

`modify` does not force-push or rewrite history.

### issue

`issue` maps supported read/create/modify operations to the existing governed
GitHub issue task vocabulary.

### pr

`pr` maps supported read/create/modify operations to the existing governed
GitHub pull-request task vocabulary.

## Authority

Macro requests cannot carry authority grants.

The macro execution surface derives or receives active authority outside the
caller-controlled macro parameter object, then uses the same authority model as
FS-001 task execution.

Macro selection and macro parameters may narrow resource selection. They may not
widen repository, filesystem, Git remote, execute, or GitHub authority.

## Non-goals

The product macro layer is not:

- a general workflow language;
- a user-defined macro system;
- a plugin installation mechanism;
- a replacement for the FS-001 Engine or internal payload model;
- a second task registry;
- a second execution engine;
- a schema language project;
- a generic policy/condition language;
- a transactional rollback system.

If future product requirements need any of those capabilities, they require
separate Product Design rather than incremental expansion of this layer.
