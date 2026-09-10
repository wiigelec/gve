---
doc_id: PD-020
title: Payload and Orchestration Model
dependencies:
  - PD-001
  - PD-010
---

# Payload and Orchestration Model

## Purpose

This document defines what input JSON means and, equally importantly, what it
does not mean.

## Declarative input

GVE accepts machine-readable JSON that describes task invocation.

The payload may identify a registered task, provide values defined by that
task's parameter model, order multiple task invocations, and refer to permitted
results from prior tasks.

The payload cannot provide replacement task implementations, embed arbitrary
executable source, invent new task identities, pass unrestricted raw transport
arguments around task governance, or widen execution authority.

## Ordered execution

Task order is payload-owned.

Given:

```text
task A
task B
task C
```

GVE attempts those tasks in the declared order subject to engine and task
failure semantics.

This lets a caller construct workflows from reusable governed capabilities
without making each workflow a new GVE executable primitive.

## Workflow task identity

Within one workflow, a task invocation may have a workflow-local identity so
later task parameters can refer to its structured result.

The exact JSON spelling belongs to later schema design, but the semantic model
must support:

```text
invoke task A
  -> produce result A

invoke task B
  parameter derived from result A
```

Workflow-local identities are references to execution evidence, not new
executable capabilities.

## Task-result references

A later task may consume a value produced by an earlier task only when:

- the referenced task has already completed successfully enough to expose that
  result;
- the referenced value exists;
- the consuming task accepts that value type and meaning;
- resolution does not widen the consuming task's authority.

For example:

```text
git.commit
  -> commit SHA

git.push
  -> publish governed branch

git.remote-head
  expected = commit SHA returned by git.commit
```

The caller need not know a future commit SHA before execution.

The concrete reference syntax and type-checking mechanism belong to later Design
refinement or Planning, but the result-flow capability is required product
meaning.

## Workflow example

The operational handoff reference implies a workflow conceptually similar to:

```text
git.repository
git.branch
git.head
git.status
git.remote-head

git.branch-create
git.branch-switch

filesystem.file-modify

execute.script
git.diff-check
git.diff

git.add
git.commit

git.remote-head
git.push
git.remote-head
```

The sequence is reference evidence for the capabilities and ordering GVE must
support. It is not a mandatory built-in pipeline.

## Parameterization

Parameters provide task-specific values, not implementation instructions.

A parameter model should be closed enough that the task retains control over
its behavior.

Conceptually:

```json
{
  "task": "git.push",
  "parameters": {
    "remote": "origin",
    "branch": "design/gve-core-architecture"
  }
}
```

is compatible with this design.

A model that exposes unrestricted raw Git arguments would violate the boundary
because the caller would be defining executable behavior rather than
parameterizing a governed task.

## Authority and payload scope

Execution authority is established outside the payload's ability to enlarge it.

A payload may select only tasks and resource parameters admitted by the active
authority.

Where supported, a payload may narrow the active authority for a task or
workflow. It may not broaden repository, filesystem, remote, GitHub-object,
process, or other authority beyond what GVE has already granted.

## Guards through composition

Exact-state guards may be represented by ordered state tasks with explicit
expectations.

The historical GVE architecture treated repository, branch, HEAD, origin, clean
state, and expected file state as important operation guards.

The task architecture retains that meaning while allowing the caller to compose
guard tasks with mutation tasks.

A failed guard terminates the workflow by default before later governed effects.

## Failure and termination

The default workflow semantic is fail-fast.

When a task fails, later tasks are not executed.

Results from tasks completed before the failure are preserved in workflow
output.

A future continuation or recovery construct, if supported, must be explicitly
designed. A generic caller-controlled `continue_on_error` escape hatch is not
part of the base model.

This default matches the reference development workflow, where guard mismatch,
dirty-state conflict, authority conflict, validation failure, and remote race
must stop later mutation or publication.

## Results as continuation input

A later payload should be based on observed results from prior execution and
current state when those observations are relevant.

The orchestration model must not encourage callers to assume that a requested
effect occurred merely because it was requested.

## No hidden orchestration authority

Task ordering does not expand capability.

A sequence of individually bounded tasks remains bounded by the capabilities
and authority actually available to those tasks.

The engine must not infer additional side effects merely because a familiar
sequence resembles a commit, publication, release, or other higher-level
workflow.

## Future payload evolution

The exact JSON schema belongs to subsequent Design refinement and Planning.

Whatever concrete schema is selected must preserve these semantics:

```text
declarative
ordered
task-addressed
parameterized
result-reference capable
fail-fast by default
non-executable
authority non-expanding
closed against capability invention
```
