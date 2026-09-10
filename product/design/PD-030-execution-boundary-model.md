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

Executable authority resides in GVE plugin tasks.

A payload is a request to exercise those capabilities. Possession or generation
of a payload does not create a new executable capability.

This is particularly important for AI-generated workflows. An AI may construct
JSON that composes approved tasks, but the JSON must not become a carrier for
arbitrary Python, shell, Git, filesystem, or remote-API behavior.

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

## Git boundary

Git tasks expose semantic repository operations rather than arbitrary Git
command execution.

Repository identity, branch state, exact HEAD, worktree state, remote state,
staging scope, commit creation, and publication are independently observable or
executable capabilities.

Normal publication must not silently become history rewrite because of
caller-supplied raw flags.

## Execute boundary

The execute domain has the greatest potential to bypass other boundaries.

`execute.script` therefore means governed execution of admitted executable
behavior, not unrestricted evaluation of caller-provided program text.

If executable behavior can itself mutate repository or external state, the
design must account for those effects rather than assuming the filesystem and
Git plugins remain the only possible sources of mutation.

The exact execution-admission and containment model remains an explicit Design
question for refinement.

## GitHub boundary

GitHub tasks expose selected issue and pull-request semantics.

A caller may provide values such as issue identity, title, body, labels, base,
head, or other fields specifically designed for a task.

The caller must not gain a generic HTTP or GitHub API escape hatch through those
parameters.

## Fail-closed behavior

Boundary violations are execution failures.

Examples include unknown task identity, invalid parameter, path outside
permitted scope, expected Git state mismatch, unacceptable worktree conflict,
remote-state race, unauthorized mutation, failed validation where continuation
depends on it, or unsupported remote object mutation.

A failure must not be weakened automatically so that a workflow can continue.

## Observability

A governed capability must provide enough evidence for a caller to understand
the observed state and outcome relevant to that task.

Observability is part of boundary enforcement because silent behavior makes it
difficult to distinguish authorized effects from unintended effects.

## Reference handoff

The script-transfer handoff requires exact repository checks, preservation of
unrelated work, no force push by default, task-specific validation, canonical
validation, exact remote verification, and structured failure evidence.

Those requirements are useful validation scenarios for this boundary model.

The maintained product should achieve them through GVE-owned tasks rather than
through AI-generated executable handoff code.
