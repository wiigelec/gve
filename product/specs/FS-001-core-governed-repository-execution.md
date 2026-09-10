---
functional_set: FS-001
artifact: normative-specification
title: Core Governed Repository Execution Specification
design_revision: 6cc46250b8aac3934663be906acd41601791c04f
---

# FS-001 — Normative Specification

Evaluation classifications:

- **M** — mechanical
- **S** — semantic
- **B** — both mechanical and semantic

Purely semantic requirements are active during Planning. Requirements classified M or B are initially inactive until Build realizes the mechanical implementation and exact requirement-to-validation-task bindings, after which Planning may reactivate them without changing their identities or normative text.

This Planning revision supersedes the earlier exact Design binding
`8ede712d83a3376911dfb561b0173b7b7fd66cfe` with `6cc46250b8aac3934663be906acd41601791c04f`. Existing normative requirement text is
preserved; superseded mechanical bindings are made inactive and replacement
requirements receive new identities.

## Requirements

### FS-001-NR-001 — Exact Design Binding

**Classification: M**

**State: Inactive**

FS-001 Planning shall identify exact consumed Product Design revision
`8ede712d83a3376911dfb561b0173b7b7fd66cfe`.

### FS-001-NR-002 — Core Execution Model

**Classification: B**

FS-001 shall realize the Product Design execution model as declarative JSON
input selecting ordered registered `plugin.task` invocations and structured JSON
output reporting their observed execution results.

### FS-001-NR-003 — Closed Task Vocabulary

**Classification: B**

A payload shall invoke only task identities registered by GVE and shall not
define or replace executable task implementations.

### FS-001-NR-004 — Initial Plugin Domains

**Classification: M**

FS-001 shall provide registered plugin namespaces `filesystem`, `git`,
`execute`, and `github`.

### FS-001-NR-005 — Stable Qualified Task Identity

**Classification: B**

Every executable task exposed by FS-001 shall have one fully-qualified
`plugin.task` identity that resolves to exactly one active implementation.

### FS-001-NR-006 — Ordered Execution

**Classification: M**

The engine shall attempt task invocations in declared payload order.

### FS-001-NR-007 — Workflow-Local Invocation Identity

**Classification: M**

Every invocation in a multi-task FS-001 workflow shall be uniquely addressable
within that workflow.

### FS-001-NR-008 — Prior Result References

**Classification: B**

FS-001 shall permit a later invocation parameter to consume an explicitly
exposed compatible result value from an earlier invocation without allowing the
reference to expand execution authority.

### FS-001-NR-009 — Invalid Result Reference Failure

**Classification: M**

A forward, unresolved, unavailable, or incompatible task-result reference shall
fail closed before the consuming task executes.

### FS-001-NR-010 — Fail-Fast Workflow

**Classification: B**

When a task invocation fails, FS-001 shall stop execution of later invocations
by default while preserving results of invocations already attempted.

### FS-001-NR-011 — No Generic Continue-on-Error

**Classification: M**

FS-001 shall not expose a generic caller-controlled continuation-after-failure
mechanism.

### FS-001-NR-012 — Capability and Authority Separation

**Classification: S**

FS-001 shall preserve the distinction between a registered capability and the
authority under which that capability may be exercised.

### FS-001-NR-013 — Authority Non-Expansion

**Classification: B**

Payload values and task-result references may narrow active execution authority
where supported but shall not widen it.

### FS-001-NR-014 — Host Access Non-Authority

**Classification: S**

Filesystem permissions, Git credentials, environment variables, network
reachability, and GitHub credentials available to the host shall not by
themselves constitute GVE execution authority.

### FS-001-NR-015 — Filesystem Task Set

**Classification: M**

FS-001 shall register and implement `filesystem.list`,
`filesystem.file-read`, `filesystem.file-stat`, `filesystem.file-hash`,
`filesystem.file-create`, `filesystem.file-modify`, and
`filesystem.file-delete`.

### FS-001-NR-016 — Filesystem Containment

**Classification: B**

Every FS-001 filesystem task shall interpret paths within its active authorized
filesystem scope and shall reject caller path resolution that escapes that
scope, including escape through path traversal or symlink resolution.

### FS-001-NR-017 — Filesystem Mutation Evidence

**Classification: B**

A filesystem mutation task shall report the path or paths it actually mutated
and enough resulting state to distinguish successful intended mutation from
failure.

### FS-001-NR-018 — Git Task Set

**Classification: M**

FS-001 shall register and implement `git.repository`, `git.branch`, `git.head`,
`git.status`, `git.diff`, `git.diff-check`, `git.branch-create`,
`git.branch-switch`, `git.add`, `git.commit`, `git.fetch`,
`git.remote-head`, and `git.push`.

### FS-001-NR-019 — Git Semantic Interface

**Classification: B**

FS-001 Git tasks shall expose semantic task parameters and shall not provide an
unrestricted raw Git argument forwarding interface.

### FS-001-NR-020 — Git Observation and Assertion

**Classification: B**

A state-oriented Git task shall return its observed state and may fail on an
explicit expected-state mismatch, but shall not infer an unstated expectation.

### FS-001-NR-021 — Normal Push Only

**Classification: B**

`git.push` shall implement normal non-force publication and shall not permit
caller parameters to enable force push or history rewrite.

### FS-001-NR-022 — Git Status Parsing Integrity

**Classification: M**

Any FS-001 parsing of fixed-width Git porcelain status output shall preserve the
status columns before path extraction and shall not remove leading status
characters through whole-line trimming.

### FS-001-NR-023 — Execute Script Scope

**Classification: B**

`execute.script` shall invoke only an existing script whose resolved path is
inside the active repository, and its invocation working directory shall resolve
inside the active repository.

### FS-001-NR-024 — No Caller-Supplied Script Source

**Classification: M**

`execute.script` shall not accept caller-supplied script source as executable
content and shall not expose a generic raw shell command interface.

### FS-001-NR-025 — Structured Execute Arguments

**Classification: M**

`execute.script` arguments shall be represented structurally rather than as an
unrestricted shell command string.

### FS-001-NR-026 — Execute Responsibility Boundary

**Classification: S**

GVE shall not claim to sandbox, govern, enumerate, or verify the executed
script's own filesystem, Git, network, credential, or other script-internal
side effects.

### FS-001-NR-027 — Finite Execute Limits

**Classification: B**

Every `execute.script` invocation shall be subject to finite GVE-defined maxima
for wall-clock runtime, concurrent governed processes, total spawned governed
processes, and process-spawn rate or burst behavior.

### FS-001-NR-028 — Execute Limit Non-Expansion

**Classification: M**

A payload may request stricter execute resource limits when supported but shall
not raise an effective limit above the GVE- or host-granted maximum.

### FS-001-NR-029 — Runaway Process Termination

**Classification: B**

When an execute timeout or governed process-spawn limit is exceeded, GVE shall
attempt termination of the governed launched process tree and shall report
failure if required runaway-process control cannot be completed.

### FS-001-NR-030 — Execute Evidence

**Classification: B**

`execute.script` shall report invocation identity, script identity, working
directory, effective relevant limits, exit status where available, timeout or
process-limit occurrence, process-tree termination outcome when applicable, and
captured stdout/stderr information.

### FS-001-NR-031 — GitHub Task Set

**Classification: M**

FS-001 shall register and implement `github.issue-read`,
`github.issue-create`, `github.issue-modify`, `github.pull-request-read`,
`github.pull-request-create`, and `github.pull-request-modify`.

### FS-001-NR-032 — GitHub Semantic Interface

**Classification: B**

FS-001 GitHub tasks shall expose designed issue and pull-request fields and
shall not expose a generic HTTP or arbitrary GitHub API request interface.

### FS-001-NR-033 — GitHub Repository Authority

**Classification: B**

GitHub task execution shall remain within the GitHub repository scope granted by
the active GVE authority regardless of broader capability of the host
credentials.

### FS-001-NR-034 — GitHub Mutation Evidence

**Classification: B**

A successful GitHub mutation task shall return the stable remote object identity
and observed resulting state needed for later governed work.

### FS-001-NR-035 — Task Result Contract

**Classification: B**

Every attempted task shall return structured result data sufficient to identify
the invocation, task identity, completion status, relevant observations,
GVE-owned effects, resulting identifiers where applicable, and errors or
conflicts when present.

### FS-001-NR-036 — Workflow Result Contract

**Classification: B**

A multi-task workflow result shall preserve invocation order, overall status,
results already produced before failure, and unambiguous indication of later
tasks that were not executed.

### FS-001-NR-037 — Evidence Ownership

**Classification: S**

Observed outcome facts belong to GVE-produced results; caller expectations shall
not be represented as authoritative evidence that an effect occurred.

### FS-001-NR-038 — Publication Evidence Separation

**Classification: B**

Git publication results shall permit callers to distinguish local commit
creation, push attempt/completion, observed remote state, and exact remote-state
verification.

### FS-001-NR-039 — JSON Result Authority

**Classification: B**

The authoritative FS-001 execution result shall be machine-readable JSON.
Human-oriented output may supplement but shall not contradict or replace it.

### FS-001-NR-040 — CLI Execution

**Classification: M**

FS-001 shall provide a local command-line entry point that accepts a payload
file and emits the authoritative workflow result.

### FS-001-NR-041 — CLI Failure Status

**Classification: M**

The FS-001 CLI shall return a non-success process exit status when the workflow
result is unsuccessful or the payload cannot be executed.

### FS-001-NR-042 — Static Product-Owned Registry

**Classification: B**

FS-001 task registration shall be product-owned and shall not permit a payload
to install, load, or define arbitrary runtime plugins.

### FS-001-NR-043 — Reference Workflow Expressibility

**Classification: S**

The FS-001 capability set shall be sufficient to express the repository
development operations represented by `user/script-transfer-handoff.json`
without requiring caller-supplied executable implementation logic.

### FS-001-NR-044 — Build Implementation Freedom

**Classification: S**

Build may make ordinary implementation choices not fixed by this Plan when
those choices preserve Product Design, FS-001 scope, and all active normative
requirements.

### FS-001-NR-045 — Mechanical Enforcement Ownership

**Classification: S**

Build shall construct the exact mechanical validation tasks and requirement
bindings for mechanically decidable FS-001 obligations; Planning classification
alone shall not be treated as an implementation of validation.

### FS-001-NR-046 — Validation Gate

**Classification: M**

All active mechanically evaluated FS-001 requirements shall have applicable
mechanical enforcement and all required repository Validation shall pass before
FS-001 is eligible for Acceptance.

### FS-001-NR-047 — Semantic Review Gate

**Classification: S**

FS-001 Semantic Review shall find no unresolved material discrepancy between the
candidate implementation, complete FS-001 Planning result, and selected Product
Design before Acceptance.

### FS-001-NR-048 — Acceptance

**Classification: S**

FS-001 Acceptance shall be represented by intentional integration of the
satisfactory `fs1` development candidate into `main`.

### FS-001-NR-049 — Revised Exact Design Binding

**Classification: M**

This FS-001 Planning revision shall identify exact consumed Product Design
revision `6cc46250b8aac3934663be906acd41601791c04f`.

### FS-001-NR-050 — Execute Host Portability

**Classification: B**

`execute.script` shall preserve its governed invocation, finite process-control,
runaway-tree termination, and result-capture contract on both native Linux and
Cygwin hosts. Process accounting used for total-spawned-process or spawn-rate
enforcement shall not rely on a mechanism that can miss short-lived governed
descendants. If required process supervision cannot be established on a
supported host, the task shall fail closed before launching the selected script.
