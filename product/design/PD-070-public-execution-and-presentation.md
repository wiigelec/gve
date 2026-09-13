---
doc_id: PD-070
title: Public Execution Surface and Terminal Presentation
dependencies:
  - PD-050
  - PD-060
---

# Public Execution Surface and Terminal Presentation

## Purpose

This document refines the maintained GVE execution surface and the human-facing
terminal presentation used when registered product macros execute.

## Public execution boundary

The maintained command-line execution surface exposes registered product macros
only.

The maintained execution commands are:

```text
gve macro --in REQUEST.json --out RESULT.json [--repo PATH]
gve macro-list
gve macro-schema NAME
```

The FS-001 raw workflow payload and Engine remain internal product mechanisms
used by registered product macros. They are not a maintained public CLI surface.

A runtime caller may select a registered macro and provide values admitted by
that macro's closed parameter contract. A runtime caller may not submit an
arbitrary FS-001 task sequence through the maintained CLI.

This refines the earlier separation described by PD-060. The maintained public
boundary is now:

```text
runtime caller
  -> registered product macro
  -> product-owned orchestration
  -> internal FS-001 Engine
  -> registered governed tasks
```

## Internal FS-001 preservation

Making FS-001 internal to the maintained CLI does not change its execution
semantics.

Registered macros continue to use the existing Engine for:

- exact registered-task resolution;
- task parameter validation;
- task-result reference resolution;
- authority enforcement;
- ordered fail-fast execution;
- structured task and workflow evidence.

No second execution engine is introduced.

## Terminal presentation

Macro execution shall provide human-readable terminal presentation in addition
to the authoritative machine-readable result file.

Terminal presentation is observational. It does not grant authority, alter task
ordering, weaken failures, redefine task meaning, or become an alternate source
of execution truth.

The authoritative execution result remains the JSON result written by the macro
command.

The macro CLI shall attempt to write the authoritative result JSON for both
successful and failed governed execution whenever the requested result
destination remains writable.

A governed execution failure and an output-artifact write failure are distinct.
Failure to write the result artifact must not erase or reinterpret the governed
execution result, and the CLI shall report the output failure explicitly.

## Handoff-style execution transcript

The maintained terminal presentation shall support a verbose execution
transcript modeled on the operational behavior in
`user/script-transfer-handoff.json`.

A macro execution transcript shall provide:

```text
GVE <macro>: START|PASS|FAILED
[<NN>/<TOTAL>] <PHASE> <description>
PASS|FAIL <concise detail>
$ <exact external command>
OUT | <captured stdout line>
ERR | <captured stderr line>
===== <PHASE> =====
```

Exact decoration may evolve, but the semantic presentation shall preserve:

- operation identity before mutation;
- visible phase transitions;
- announcement of each material step before execution;
- exact external commands before invocation when a governed task invokes an
  external command;
- captured non-empty stdout and stderr;
- explicit PASS or FAIL for each announced material step;
- visible progress during validation, commit, publication, and verification;
- immediate failure presentation after the failing step;
- a concise final summary;
- the path of the authoritative result JSON.

A long-running governed operation shall not remain silent merely because its
authoritative result is written later.

## Phase presentation

Product-owned macro phases remain presentation and grouping metadata.

For `modify`, the maintained presentation may include:

```text
PRECHECK
BRANCH
MUTATE
VALIDATE
COMMIT
PUBLISH
VERIFY
```

A phase with no generated tasks may be omitted from the transcript or shown as
having no requested work. Phase presentation does not alter Engine semantics.

## Git change summary

When `modify` has produced repository mutations and before the product-requested
commit is created, terminal presentation shall show a concise Git change summary
equivalent in meaning to:

```text
git status --short
```

The summary is presentation of governed repository-state evidence. It does not
create a generic raw Git execution surface.

The summary shall preserve Git's fixed-width short-status meaning so that staged,
unstaged, renamed, copied, deleted, and untracked states remain distinguishable.

## Final summary

The final `modify` terminal summary shall communicate, when applicable:

```text
Operation
Repository
Branch
Expected HEAD
Observed HEAD
Files Changed
Validation
Commit
Remote HEAD
Result JSON
```

Additional concise evidence may be shown when useful.

A successful terminal PASS shall not be emitted until all product-required
publication and exact remote verification steps have succeeded.

## Failure presentation

A failed macro shall retain the same fail-fast meaning as the underlying Engine.

Terminal presentation shall distinguish:

- the failing phase and task;
- the relevant failure reason;
- prior successful work;
- later work that was not executed;
- the result JSON location when the result could be written.

Presentation must not convert a governed failure into success.

## Presentation implementation boundary

The product may use an execution-observer or event mechanism so terminal
presentation can announce and display work while it occurs.

Presentation logic should not be embedded as product meaning inside individual
task implementations merely to print terminal text.

When no terminal observer is attached, governed execution remains semantically
identical.
