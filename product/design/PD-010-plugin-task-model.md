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
shared assumptions and boundaries of that domain.

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
filesystem.paths-verify
```

Mutation tasks must remain within the GVE-authorized filesystem boundary and
must preserve unrelated work. A caller-provided path does not by itself confer
authority to operate outside that boundary.

## Initial Git capability requirements

The reference workflow requires at least:

```text
git.repository
git.branch
git.head
git.status
git.diff
git.diff-check
git.add
git.commit
git.fetch
git.remote-head
git.push
```

These tasks express repository interrogation, exact-state guards, staging,
commit creation, publication race detection, publication, and
post-publication verification.

`git.push` represents GVE-defined normal publication semantics. Arbitrary raw
Git flags are not part of the task's conceptual interface.

History-rewriting publication, if ever supported, is a separate capability and
must not appear as an incidental parameter that weakens normal `git.push`.

## Initial execute capability requirements

The reference workflow requires the ability to invoke repository-owned
generation and validation behavior.

The initial semantic requirement is:

```text
execute.script
```

This capability must remain governed. The task is not conceptually equivalent
to "execute arbitrary caller-supplied source text." It identifies executable
behavior admitted by the execution domain and executes it within that domain's
boundaries.

The exact admission model remains a Design question for refinement and must
preserve the closed-capability invariant established by PD-001.

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

## Task granularity

Tasks should be small enough to compose into different workflows while large
enough to own a meaningful governed capability.

The design should avoid both monolithic workflow tasks that hide independently
meaningful effects and microscopic implementation tasks that expose mechanics
rather than product semantics.

The reference workflow demonstrates useful composition boundaries but does not
make its phase names mandatory task boundaries.

## Shared domain rules

Rules that necessarily apply to every task in a plugin should be owned by the
plugin domain rather than repeated as caller-provided parameters.

Examples include repository-root containment for filesystem tasks and safe Git
command construction for Git tasks.

The caller should not be able to parameterize away a plugin's governing
boundary.

## Extension

New plugins and tasks may extend GVE's capability vocabulary.

Extension changes the executable surface of the product and is therefore a
consequential product decision. New capabilities must be explicitly designed
rather than appearing through generic escape hatches.
