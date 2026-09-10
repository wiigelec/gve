---
functional_set: FS-001
artifact: plan
title: Core Governed Repository Execution Plan
design_revision: 8ede712d83a3376911dfb561b0173b7b7fd66cfe
---

# FS-001 — Plan

## Technical intent

FS-001 will implement GVE as a small Python application with a stable engine
boundary and plugin-owned task implementations.

The runtime path is:

```text
JSON document
  -> payload parser / schema validation
  -> workflow model
  -> authority context
  -> task registry
  -> plugin.task dispatch
  -> ordered task execution
  -> task result records
  -> workflow result JSON
```

The engine owns orchestration semantics. Plugins own capability semantics.

## Package structure

Build should use a project-native Python package under `src/` with clear
separation between:

- engine/workflow orchestration;
- payload and result models;
- authority representation;
- task registry;
- plugin implementations for `filesystem`, `git`, `execute`, and `github`;
- CLI entry point.

Exact module and class names are Build decisions unless needed to preserve these
boundaries.

## Payload contract

FS-001 shall define one concrete payload schema version.

The payload shall contain:

- schema version;
- workflow identity;
- ordered task invocations;
- a workflow-local identity for each invocation;
- fully-qualified `plugin.task` identity;
- task-specific parameters;
- optional task-result references where accepted by the consuming parameter;
- optional narrowing authority values where the task contract supports them.

Payload validation occurs before an invocation executes. Unknown top-level
fields, unknown task identities, malformed task parameters, invalid references,
and authority-widening requests fail closed.

The concrete JSON spelling and schema representation may be selected during
Build provided they preserve the normative requirements.

## Task-result references

A task-result reference identifies a value produced by an earlier invocation in
the same workflow.

Reference resolution occurs immediately before the consuming invocation is
validated for execution.

A reference must:

- name an earlier workflow-local invocation identity;
- identify an exposed result value;
- resolve to a value compatible with the receiving parameter;
- never grant authority that the receiving task did not already possess.

Forward references and references to unavailable results are failures.

## Failure model

Execution is sequential and fail-fast.

If an invocation fails, the engine records its failure, stops dispatching later
tasks, preserves all earlier results, marks later invocations as not executed or
otherwise makes their non-execution unambiguous, and returns a failed workflow
result.

FS-001 contains no caller-controlled continuation-after-failure mechanism.

## Authority model

The engine constructs an active authority context outside the payload's ability
to enlarge it.

For FS-001 the authority context is repository-centered. It identifies the
active repository and the capability/resource bounds applicable to the current
execution.

Each plugin interprets that authority for its domain.

Task parameters may narrow an authorized resource selection but may not widen
it. Host filesystem permissions, Git credentials, environment variables,
network reachability, or GitHub credentials are implementation capabilities,
not implicit GVE authority.

## Task registry

The registry maps each supported fully-qualified task identity to exactly one
implementation for the active FS-001 product version.

Unknown task identities fail before execution of that invocation.

The registry is static/product-owned in FS-001. Runtime third-party plugin
loading is out of scope.

## Filesystem plugin

FS-001 shall implement:

```text
filesystem.list
filesystem.file-read
filesystem.file-stat
filesystem.file-hash
filesystem.file-create
filesystem.file-modify
filesystem.file-delete
```

Filesystem task paths are interpreted relative to the active repository unless
the task contract explicitly provides another representation that still resolves
inside the authorized repository scope.

Containment is intrinsic to every filesystem task. Symlink and path
canonicalization handling must prevent a caller-provided path from escaping the
authorized filesystem boundary.

Mutation tasks should support sufficiently explicit expected-state checks to
avoid silently overwriting unrelated work.

## Git plugin

FS-001 shall implement:

```text
git.repository
git.branch
git.head
git.status
git.diff
git.diff-check
git.branch-create
git.branch-switch
git.add
git.commit
git.fetch
git.remote-head
git.push
```

Git tasks expose semantic parameters, not raw argument arrays.

State-oriented tasks may accept an expected value; absent an expectation they
observe and return current state.

`git.push` implements normal non-force publication only.

Git output parsing must preserve the semantics of the underlying format.
In particular, porcelain status handling must preserve fixed-width status
columns rather than stripping leading status characters before interpretation.

## Execute plugin

FS-001 shall implement:

```text
execute.script
```

The selected script and invocation working directory must resolve inside the
active repository.

Arguments are represented structurally and are passed without exposing a generic
shell command string.

GVE does not sandbox or govern the script's own filesystem, Git, network,
credential, or other side effects.

GVE does govern the process-tree runaway envelope. FS-001 shall have finite
configured maxima for:

- wall-clock duration;
- concurrent governed process count;
- total spawned governed process count;
- process-spawn rate or burst.

GVE must own enough of the launched process tree to terminate it when a governed
limit is exceeded. Timeout or process-runaway enforcement failure is reported as
task failure.

Exact numeric defaults and OS-specific monitoring/termination mechanisms are
Build decisions, but they must be finite, testable, and configurable within
GVE-defined maxima.

## GitHub plugin

FS-001 shall implement:

```text
github.issue-read
github.issue-create
github.issue-modify
github.pull-request-read
github.pull-request-create
github.pull-request-modify
```

GitHub tasks use semantic fields rather than generic API requests.

The active authority identifies the GitHub repository scope. Available host
credentials may authenticate an operation but do not enlarge that scope.

Mutation results return stable remote identities and enough observed state for
later invocations or successor workflows.

## Result contract

Every task result shall identify:

- workflow-local invocation identity;
- fully-qualified task identity;
- completion status;
- relevant observations;
- GVE-owned effects;
- task-specific resulting identifiers;
- errors or conflicts when present.

The workflow result shall preserve task-result order, identify overall status,
retain partial results after failure, and make non-executed later tasks
unambiguous.

`execute.script` results concern invocation and runaway-process control only;
they must not claim exhaustive knowledge of script-internal side effects.

## CLI

FS-001 shall provide a local CLI that accepts a payload file and emits the
authoritative workflow result as JSON.

Human-oriented progress or diagnostics may be written separately, but they must
not replace or contradict the JSON result.

A non-successful workflow must produce a process exit status suitable for local
automation.

## Validation strategy

Build owns exact mechanical validation tasks and requirement-to-validation
bindings.

Testing should cover the engine in isolation and each plugin domain with
temporary repositories or controlled fakes where appropriate.

External GitHub mutation tests should not require destructive operations against
unrelated repositories. Build may use mocked/fake transport for deterministic
mechanical tests while preserving semantic task behavior.

Repository-wide `./scripts/validate` remains the canonical mechanical validation
entry point.

## Build sequencing

A practical Build sequence is:

```text
payload/result/authority models
  -> registry + engine
  -> filesystem plugin
  -> git plugin
  -> execute plugin
  -> github plugin
  -> CLI
  -> mechanical validation bindings
  -> end-to-end reference workflow tests
```

This sequence is advisory except where dependencies make the order consequential.
