---
doc_id: PD-040
title: Result and Evidence Model
dependencies:
  - PD-001
  - PD-010
  - PD-020
  - PD-030
---

# Result and Evidence Model

## Purpose

GVE returns machine-readable JSON evidence for governed execution.

The output side of the product model is:

```text
plugin.task
  -> JSON out
```

## Task result

Each task returns a structured result whose meaning is owned by GVE.

At minimum, the result model must be able to communicate task identity,
workflow-local invocation identity where present, completion status, relevant
observations, effects performed, resulting state identifiers where applicable,
and errors or conflicts.

Different task domains may add task-specific evidence.

Examples include file hashes, repository HEADs, changed paths, commit IDs,
remote branch state, process exit status, process-limit failures, issue numbers,
and pull-request numbers.

## Addressable result values

A task result may expose specifically addressable values for use by later tasks
in the same workflow.

Result addressing must be unambiguous and limited to earlier task invocations.

A reference resolves an observed value; it does not confer new authority.

If a reference cannot be resolved, is incompatible with the consuming
parameter, or depends on a task that did not produce the required successful
result, the consuming task must not execute.

The exact JSON reference syntax belongs to later schema work.

## Workflow result

For a payload containing multiple tasks, the engine aggregates task results in
execution order.

The workflow result records enough information to determine what payload
execution was attempted, which tasks ran, which task failed if any, which tasks
were not run because execution terminated, what effects occurred before
termination, and what final observations were established.

The workflow result must not erase partial execution merely because a later task
failed.

## Evidence versus assertion

Result JSON is produced from GVE observations.

The caller does not supply authoritative output facts such as successful
publication, resulting commit identity, resulting file hash, process outcome, or
remote object identity.

Expected values may appear as task inputs or guards, but observed values belong
to results.

## Failure

Failure is a first-class result.

When possible, failure output should preserve the task that failed, the reason
for failure, observations established before failure, effects already
completed, conflicts or races, resource-limit violations, and the safest known
execution-boundary state.

A failed workflow is not equivalent to "nothing happened."

Because the default workflow model is fail-fast, the aggregate result should
also distinguish tasks that failed from later tasks that were never attempted.

## Execute evidence

Execute-task results should make process behavior inspectable enough to explain
normal completion or governed termination.

Where relevant this includes:

```text
admitted executable identity
effective timeout
effective process ceilings
exit status
timeout occurrence
process-limit occurrence
termination outcome
captured stdout/stderr metadata or content
```

The result must not claim successful containment when the governed process tree
could not be terminated as required.

## Publication evidence

The historical GVE and the reference handoff both distinguish local commit,
successful push invocation, and verified remote state.

The new result model should preserve this distinction.

A publication workflow can therefore report separate evidence for:

```text
local commit created
push attempted
push completed
remote head observed
remote head matched expected published commit
```

This avoids treating transport success as proof of repository state.

## GitHub evidence

GitHub mutation tasks should return stable identities and observed resulting
state sufficient for later workflows to reference the created or modified
object.

For example:

```text
github.issue-create
  -> issue number / URL / observed state

github.pull-request-create
  -> pull-request number / URL / observed state
```

Exact result fields remain a later schema decision.

## Continuation

Returned evidence is the bridge to subsequent work.

A caller constructing successor JSON should rely on actual results and current
state when those facts govern the next operation.

This preserves a useful principle from `gvev0`: successor work follows observed
execution evidence rather than assumed execution success.

## Serialization

JSON is the required machine-readable result representation for the maintained
product.

Human-readable presentation may be layered over the result, but must not become
a competing authority for execution outcome.
