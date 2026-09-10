---
doc_id: PD-030
title: Execution Boundary Model
dependencies:
  - PD-001
  - PD-010
  - PD-020
---

# Execution Boundary Model

## Purpose

This document establishes where executable authority resides and how GVE keeps a
caller inside approved capabilities.

## Authority location

Executable capability resides in GVE plugin tasks.

Execution authority is a separate constraint describing where and under what
limits those capabilities may be exercised.

A payload is a request to exercise registered capabilities within existing
authority. Possession or generation of a payload does not create a new
capability or enlarge authority.

This is particularly important for AI-generated workflows. An AI may construct
JSON that composes approved tasks, but the JSON must not become a carrier for
arbitrary Python, shell, Git, filesystem, remote-API, or process behavior.

## Effective execution boundary

A task invocation is permitted only where all three layers agree:

```text
registered capability
        intersect
active execution authority
        intersect
validated task parameters
        =
permitted invocation
```

A payload may narrow execution where the task model permits. It may not enlarge
the active execution authority.

Host credentials, filesystem permissions, Git credentials, environment
variables, or network reachability do not themselves constitute GVE authority.

## Closed executable surface

GVE dispatches only registered `plugin.task` identities.

Unknown tasks fail closed. Parameters that do not conform to a task's accepted
semantic model fail closed.

A plugin task must not expose parameters whose practical effect is to bypass its
governance.

## Filesystem boundary

Filesystem tasks operate inside a GVE-governed filesystem scope.

Containment, path interpretation, symlink behavior, mutation rules, and
preservation of unrelated work are task/plugin responsibilities.

The payload may identify a target allowed by that scope but cannot redefine the
scope itself merely by supplying a path.

Path containment applies intrinsically to every filesystem task. It is not an
optional verification step.

## Git boundary

Git tasks expose semantic repository operations rather than arbitrary Git
command execution.

Repository identity, branch state, exact HEAD, worktree state, remote state,
branch creation, branch switching, staging scope, commit creation, and
publication are independently observable or executable capabilities.

Normal publication must not silently become history rewrite because of
caller-supplied raw flags.

Git authority constrains which repository, refs, remotes, and publication
effects are admitted for an execution.

## Execute boundary

`execute.script` provides controlled invocation of an existing repository-local
script.

The script path must resolve inside the active repository. The working directory
used for the invocation must also resolve inside the active repository. These
requirements govern which script GVE may launch and the context from which GVE
launches it.

GVE's responsibility ends at the invocation boundary except for runaway
process-tree control and execution-result capture.

GVE does not sandbox, constrain, interpret, or take responsibility for the
script's own filesystem, Git, network, credential, or other side effects. A
repository script invoked through GVE has the same responsibility boundary as
that script when intentionally run manually by the user.

The execute plugin must establish ownership of the launched process tree and
apply finite resource limits for the life of the task.

At minimum, the governed execution envelope includes:

```text
finite wall-clock timeout
finite maximum concurrent process count
finite maximum total spawned process count
bounded process-spawn rate or burst
governed process-tree ownership
termination of the governed process tree on limit violation
repository-local script selection
repository-local working directory
structured argument passing
stdout and stderr capture
exit-status observation
```

The exact numeric ceilings may vary by configuration or authority, but an
execute task may never be unbounded.

The effective limit for any parameterizable resource is no broader than the
GVE- or host-granted maximum.

Conceptually:

```text
GVE/host maximum
        intersect
payload-requested limit
        =
effective limit
```

A caller may request a stricter timeout or process ceiling when supported. It
may not raise the ceiling.

Timeout, process-limit exhaustion, spawn-limit exhaustion, or failure to
terminate the governed process tree is a governed task failure.

The process-tree limits exist to protect host stability and to prevent GVE from
unintentionally exhibiting uncontrolled process-spawning patterns that
reasonable endpoint or malware protection systems may treat as hostile.

The execute plugin does not infer script-side effects into filesystem, Git, or
GitHub authority. If a script performs such effects, they are effects of the
script itself and are outside GVE's governance responsibility.

## GitHub boundary

GitHub tasks expose selected issue and pull-request semantics.

A caller may provide values such as issue identity, title, body, labels, base,
head, or other fields specifically designed for a task.

The caller must not gain a generic HTTP or GitHub API escape hatch through those
parameters.

GitHub authority constrains which repository and remote objects may be read or
mutated. Credentials available to the host do not enlarge that authority.

## Fail-closed behavior

Boundary violations are execution failures.

Examples include unknown task identity, invalid parameter, path outside
permitted scope, expected Git state mismatch, unacceptable worktree conflict,
remote-state race, unauthorized mutation, failed validation where continuation
depends on it, process-resource exhaustion, or unsupported remote object
mutation.

A failure terminates later workflow execution by default.

A failure must not be weakened automatically so that a workflow can continue.

## Observability

A governed capability must provide enough evidence for a caller to understand
the observed state and outcome relevant to that task.

Observability is part of boundary enforcement because silent behavior makes it
difficult to distinguish authorized effects from unintended effects.

For `execute.script`, GVE reports invocation and process-control observations.
It does not claim to report or verify all effects caused internally by the
script.

## Reference handoff

The script-transfer handoff requires exact repository checks, preservation of
unrelated work, no force push by default, task-specific validation, canonical
validation, exact remote verification, and structured failure evidence.

Those requirements are useful validation scenarios for this boundary model.

The maintained product should achieve them through GVE-owned tasks rather than
through AI-generated executable handoff code.
