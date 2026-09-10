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
task's parameter model, and order multiple task invocations.

The payload cannot provide replacement task implementations, embed arbitrary
executable source, invent new task identities, or pass unrestricted raw
transport arguments around task governance.

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

## Workflow example

The operational handoff reference implies a workflow conceptually similar to:

```text
git.repository
git.branch
git.head
git.status
git.remote-head

filesystem.file-modify
filesystem.paths-verify

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

## Guards through composition

Exact-state guards may be represented by ordered interrogating or asserting
tasks.

The historical GVE architecture treated repository, branch, HEAD, origin, clean
state, and expected file state as important operation guards.

The task architecture retains that meaning while allowing the caller to compose
guard tasks with mutation tasks.

A failed guard prevents later governed effects according to workflow failure
semantics.

## Results as continuation input

A later payload should be based on observed results from prior execution and
current state when those observations are relevant.

The orchestration model must not encourage callers to assume that a requested
effect occurred merely because it was requested.

## No hidden orchestration authority

Task ordering does not expand capability.

A sequence of individually bounded tasks remains bounded by the capabilities
actually invoked.

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
non-executable
closed against capability invention
```
