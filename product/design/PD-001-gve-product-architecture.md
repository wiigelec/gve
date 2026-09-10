---
doc_id: PD-001
title: GVE Product Architecture
dependencies: []
---

# GVE Product Architecture

## Purpose

GVE is a governed task execution engine for repository development work.

Its primary product model is:

```text
JSON in
  -> plugin.task
  -> JSON out
```

A caller supplies declarative JSON describing one or more ordered task
invocations. GVE resolves each invocation to a task implemented by an installed
plugin, validates the task parameters, executes the governed capability, and
returns structured JSON evidence.

GVE exists to make repository automation composable without allowing the caller
to invent new executable behavior.

## Product identity

GVE owns executable repository capabilities.

The caller owns orchestration.

A payload may select a capability that GVE already implements, place that
capability in an ordered workflow, and provide values allowed by that task's
parameter contract. The payload does not define how the capability works.

The distinction is fundamental:

```text
payload
  selects and parameterizes

GVE
  defines and executes
```

This keeps executable authority inside GVE rather than in AI-generated scripts,
shell fragments, raw Git argument lists, or arbitrary API requests.

## Core concepts

### Engine

The engine accepts and validates payloads, resolves task identities, dispatches
tasks, applies workflow failure semantics, resolves permitted task-result
references, collects task results, and emits the workflow result.

The engine is not itself a filesystem, Git, process-execution, or GitHub
implementation. Those capabilities are supplied through plugins.

### Plugin

A plugin owns a capability domain.

Initial product requirements establish these core domains:

- `filesystem`
- `git`
- `execute`
- `github`

A plugin provides a namespace for governed tasks and may establish domain-wide
rules shared by those tasks.

### Task

A task is the atomic executable capability exposed by GVE.

A task owns its identity, accepted parameters, semantic behavior, preconditions,
boundary enforcement, permitted effects, success and failure meaning, and
structured result.

Examples include:

```text
filesystem.file-modify
git.status
git.push
execute.script
github.issue-create
```

### Payload

A payload is a declarative composition of task invocations.

It may order tasks, supply task parameters, and refer to results produced by
prior tasks where the consuming task permits that value.

It may not define executable implementation logic or extend the task vocabulary.

### Result

Every task produces structured machine-readable evidence. The engine aggregates
task results into a workflow result.

Results describe what GVE observed and what GVE did. A caller does not get to
declare execution successful merely by requesting success.

### Capability

Capability describes what GVE knows how to do.

The registered plugin-task vocabulary is the set of executable capabilities
implemented by the active GVE product.

### Authority

Authority describes where, to what resources, and within what limits an
available capability may be exercised for a particular execution.

Capability and authority are separate concepts.

A registered task does not imply unrestricted permission to use that task
against every repository, path, remote, process, issue, or pull request
accessible to the host.

Effective permission is the intersection of:

```text
registered capability
  + execution authority
  + task parameters
```

A payload may narrow an already granted authority when a task permits it. A
payload may not widen authority.

## Capability boundary

The set of registered `plugin.task` identities is GVE's executable capability
boundary.

If no task exists for an effect, a payload cannot request that effect.

A plugin task must not expose an escape hatch that recreates arbitrary execution
inside an otherwise bounded interface. Generic raw shell execution, arbitrary
Python source, unrestricted Git argument forwarding, unrestricted filesystem
paths, and arbitrary remote API requests would defeat this boundary.

The product therefore favors semantic operations over transport-level escape
hatches.

For example, `git.push` means the governed publication behavior defined by GVE.
It does not mean "execute an arbitrary git command beginning with push."

Likewise, `github.issue-modify` means the governed issue fields supported by
that task. It does not mean "perform an arbitrary HTTP request against GitHub."

## Composition

GVE workflows are compositions of tasks rather than hard-coded lifecycle
pipelines.

One payload may describe:

```text
git.repository
git.branch
git.head
git.branch-create
git.branch-switch
filesystem.file-modify
execute.script
git.diff-check
git.add
git.commit
git.remote-head
git.push
git.remote-head
```

Another may be read-only:

```text
git.repository
git.status
git.diff
filesystem.list
filesystem.file-read
```

The engine need not assign product meaning to labels such as PRECHECK, MUTATE,
VALIDATE, COMMIT, PUBLISH, or VERIFY. Those are useful workflow groupings, but
the executable semantics reside in the tasks themselves.

## Reference architecture relationship

The historical `gvev0` repository is architectural reference material.

Its useful concepts include exact repository guards, narrow authorization,
explicit expected effects, separation of local commit from remote publication,
structured execution evidence, and continuation from observed results rather
than assumed outcomes.

The new GVE does not inherit the historical monolithic operation-type and
executor-version model as product identity. Those ideas are decomposed into
plugin-owned tasks composed by declarative JSON.

## Reference workflow relationship

`user/script-transfer-handoff.json` is an operational reference workflow used to
identify capabilities that GVE must be able to express.

The handoff transport itself is not GVE's product interface.

The maintained GVE interface is JSON payload input, governed plugin-task
execution, and JSON result output.

## Design invariants

The governing invariants for the product are:

> The caller may compose approved executable capabilities, but may not create
> executable capabilities.

> The caller may narrow granted execution authority, but may not widen it.

All later Product Design, Planning, implementation, and validation should
preserve those boundaries.
