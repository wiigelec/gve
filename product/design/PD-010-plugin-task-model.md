---
doc_id: PD-010
title: Plugin and Task Model
dependencies:
  - PD-001
---

# Plugin and Task Model

## Purpose

This document defines the semantic relationship between GVE plugins and tasks.

## Plugin model

A plugin is a capability-domain owner.

A plugin groups related tasks under a stable namespace and establishes the
shared assumptions, authority interpretation, and boundaries of that domain.

The initial required plugin domains are:

```text
filesystem
git
execute
github
```

Plugin namespaces are semantically meaningful. They are not merely packaging
conventions.

## Task identity

A task has a stable fully-qualified identity:

```text
plugin.task
```

Examples:

```text
filesystem.file-modify
git.branch
execute.script
github.pull-request-create
```

The fully-qualified identity resolves to exactly one GVE-owned implementation
for the active product version.

The payload may refer to the identity. It may not redefine the identity's
meaning.

## Task ownership

A task owns all semantics necessary to make its capability governed.

At the Design level this includes accepted parameter meaning, required
observations and preconditions, allowed effects, boundary enforcement, success
and failure meaning, and evidence returned to the caller.

Implementation details remain Planning and Build concerns unless they have
consequential product meaning.

## Observation and assertion

State-oriented tasks may both observe and assert when those behaviors are two
forms of the same semantic capability.

For example, `git.head` may return the observed local HEAD when no expectation is
provided, or fail when an explicitly supplied expected HEAD does not match the
observation.

The task still returns the observation in either case when safely available.

This avoids duplicating the task vocabulary solely to distinguish "get" from
"assert" while keeping assertion behavior explicit in the task parameter model.

A state task must not infer an unstated expected value.

## Initial filesystem capability requirements

The reference development workflow requires the filesystem domain to support at
least:

```text
filesystem.list
filesystem.file-read
filesystem.file-stat
filesystem.file-hash
filesystem.file-create
filesystem.file-modify
filesystem.file-delete
```

Mutation tasks must remain within the GVE-authorized filesystem boundary and
must preserve unrelated work. A caller-provided path does not by itself confer
authority to operate outside that boundary.

Authorized-path containment is a mandatory filesystem-plugin invariant, not an
optional task that a workflow author must remember to invoke.

Filesystem mutation tasks must produce enough evidence to identify the paths and
resulting state they actually affected.

## Initial Git capability requirements

The reference workflow requires at least:

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

These tasks express repository interrogation, exact-state guards, branch
lifecycle, staging, commit creation, publication race detection, publication,
and post-publication verification.

`git.branch` observes or asserts the current branch. Branch creation and branch
switching are distinct effects and therefore use distinct tasks.

`git.push` represents GVE-defined normal publication semantics. Arbitrary raw
Git flags are not part of the task's conceptual interface.

History-rewriting publication, if ever supported, is a separate capability and
must not appear as an incidental parameter that weakens normal `git.push`.

Git tasks must preserve repository identity and authority boundaries defined by
the active execution context.

## Initial execute capability requirements

The reference workflow requires the ability to invoke repository-owned
generation and validation behavior.

The initial semantic requirement is:

```text
execute.script
```

`execute.script` invokes an existing script located inside the active repository.
The task does not accept caller-supplied script source as executable content.

The script path must resolve inside the active repository. The working directory
for the invocation must also resolve inside the active repository.

GVE governs invocation and protects the host against runaway process-tree
behavior. It does not govern, sandbox, interpret, or take responsibility for the
script's own filesystem, Git, network, credential, or other side effects. Those
effects have the same responsibility boundary as running the same repository
script manually.

All execute tasks are intrinsically resource-bounded. The execute plugin must
govern, at minimum:

```text
wall-clock duration
maximum concurrent governed processes
maximum total spawned governed processes
process-spawn rate or burst behavior
process-tree ownership
termination of the governed process tree
repository-local script selection
repository-local working directory
structured argument passing
stdout and stderr capture
exit status
```

Exact numeric limits are configuration or Planning concerns, but the existence
of finite limits is Product Design.

A payload may request stricter limits when supported. It may not raise an
execution limit above the maximum granted by GVE execution authority or host
policy.

Timeout, process-limit exhaustion, or inability to terminate the governed
process tree is a governed failure and must be represented in JSON output.

The design intent is conservative host behavior. GVE must not permit unbounded
process trees or process storms that can destabilize the host or trigger
reasonable host protection controls.

## Initial GitHub capability requirements

GitHub issues and pull requests are required development workflow objects.

The initial semantic requirements are:

```text
github.issue-read
github.issue-create
github.issue-modify

github.pull-request-read
github.pull-request-create
github.pull-request-modify
```

GitHub tasks expose governed semantic fields rather than arbitrary API request
construction.

Read tasks are first-class because current issue or pull-request state may be a
precondition for later mutation.

GitHub authority includes the repository and remote-object scope against which a
task may operate. Credentials present on the host do not automatically enlarge
that authority.

## Task granularity

Tasks should be small enough to compose into different workflows while large
enough to own a meaningful governed capability.

The design should avoid both monolithic workflow tasks that hide independently
meaningful effects and microscopic implementation tasks that expose mechanics
rather than product semantics.

The reference workflow demonstrates useful composition boundaries but does not
make its phase names mandatory task boundaries.

## Mandatory plugin invariants

A rule that must hold for every invocation in a plugin domain is enforced by the
plugin or task implementation rather than represented as an optional workflow
step.

Examples include:

- filesystem path containment;
- safe Git argument construction;
- normal non-force semantics of `git.push`;
- GitHub API surface restriction;
- execute-process resource ceilings;
- repository-local script selection for `execute.script`.

A payload cannot parameterize away a mandatory plugin invariant.

## Extension

New plugins and tasks may extend GVE's capability vocabulary.

Extension changes the executable surface of the product and is therefore a
consequential product decision. New capabilities must be explicitly designed
rather than appearing through generic escape hatches.
