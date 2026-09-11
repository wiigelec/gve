---
functional_set: FS-002
artifact: normative-specification
title: Product Macro Layer and CLI Specification
design_revision: bb72f1d02b67b6722af97ef9cc19e4b2a97ad65b
---

# FS-002 — Normative Specification

Evaluation classifications:

- **M** — mechanical
- **S** — semantic
- **B** — both mechanical and semantic

Purely semantic requirements are active during Planning. Requirements classified
M or B are initially inactive until Build realizes the mechanical implementation
and exact requirement-to-validation-task bindings. Planning may then reactivate
those requirements without changing their identities or normative text.

## Requirements

### FS-002-NR-001 — Exact Design Binding

**Classification: M**

**State: Inactive**

FS-002 Planning shall identify exact consumed Product Design revision
`bb72f1d02b67b6722af97ef9cc19e4b2a97ad65b`.

### FS-002-NR-002 — Macro Layer Purpose

**Classification: S**

FS-002 shall provide product-owned higher-level repository operations above the
accepted FS-001 Engine without replacing the ordinary FS-001 caller-owned
workflow interface.

### FS-002-NR-003 — Single Task Execution Engine

**Classification: B**


All governed task execution initiated by an FS-002 macro shall pass through the
existing FS-001 Engine. FS-002 shall not introduce a second generic task
execution engine.

### FS-002-NR-004 — Product-Owned Macro Orchestration

**Classification: S**

A macro shall be a named GVE product operation whose executable orchestration is
owned by product code rather than supplied by the runtime caller.

### FS-002-NR-005 — No Macro Behavior Language

**Classification: B**

**State: Inactive**

FS-002 shall not expose a generic caller-authored macro behavior language,
including caller-defined tasks, stages, conditions, loops, templates, result
binding operators, or generic continuation rules.

### FS-002-NR-006 — Static Macro Registry

**Classification: B**


The public macro registry shall be product-owned and static at runtime. A caller
shall not install, replace, alias, or define macro identities.

### FS-002-NR-007 — Complete Registration

**Classification: B**

**State: Inactive**

A macro identity shall be registered publicly only when both its complete public
parameter contract and executable product implementation are present. At FS-002
completion the registered macro identities shall be exactly `discover`,
`issue`, `pr`, and `modify`.

### FS-002-NR-008 — Unknown Macro Failure

**Classification: M**


An unknown macro identity shall fail closed before macro execution.

### FS-002-NR-009 — Closed Parameter Contracts

**Classification: B**


Each registered macro shall expose a closed public parameter contract and shall
reject caller parameter shapes or values outside that contract.

### FS-002-NR-010 — Introspection and Runtime Correspondence

**Classification: B**


For every registered macro, the public parameter contract exposed through
introspection and the authoritative runtime validator shall describe the same
accepted public parameter space.

### FS-002-NR-011 — Product-Owned Defaults

**Classification: B**


Macro parameter defaults shall be deterministic product-owned behavior and shall
not depend on caller-supplied executable interpretation.

### FS-002-NR-012 — Native FS-001 Result References

**Classification: B**

**State: Inactive**

When generated task invocations require values from earlier generated
invocations, FS-002 shall use the existing FS-001 `$ref` result-reference
mechanism and shall not introduce a separate macro result-reference language.

### FS-002-NR-013 — Macro Phase Metadata Only

**Classification: S**

Product-owned macro stages or phases shall serve only as presentation and result
grouping metadata around generated FS-001 task invocations and shall not alter
authority, dispatch, fail-fast behavior, or result-reference semantics.

### FS-002-NR-014 — Phase Regrouping Integrity

**Classification: M**


Regrouping Engine task records into macro phases shall preserve generated task
order, task identity, execution status, `not-executed` records, and the
underlying FS-001 task evidence.

### FS-002-NR-015 — Fail-Fast Preservation

**Classification: B**


Macro execution shall preserve FS-001 fail-fast behavior. A macro shall not
convert a governed task failure into successful macro execution merely because a
higher-level operation was requested.

### FS-002-NR-016 — Authority Non-Expansion

**Classification: B**

**State: Inactive**

Macro selection, macro parameters, repository expectations, derived repository
context, and task-result references shall not widen active FS-001 execution
authority.

### FS-002-NR-017 — Context Is Not Authority

**Classification: S**

Repository paths, Git remotes, GitHub repository identities, credentials, or
other execution context discovered from the local repository shall not by
themselves constitute authority to operate on those resources.

### FS-002-NR-018 — Closed Macro Request Envelope

**Classification: M**


The maintained macro request envelope shall use schema version `1`, shall contain
only the fields established by FS-002, and shall reject unknown fields and
unsupported schema versions.

### FS-002-NR-019 — Repository Expectation Guards

**Classification: B**


Macro request repository expectations shall act only as state guards and shall
fail closed on applicable repository identity, branch, or local-HEAD mismatch.
They shall not grant execution authority.

### FS-002-NR-020 — Discover Read-Only Behavior

**Classification: B**


`discover` shall perform only bounded product-supported repository discovery
through governed observation tasks and shall produce no repository mutation.

### FS-002-NR-021 — Modify Declared Mutation Scope

**Classification: B**

**State: Inactive**

`modify` shall mutate only the declared repository-relative change paths, shall
preserve unrelated work, and shall stage only the declared mutation path set.

### FS-002-NR-022 — Modify Worktree Guard

**Classification: B**

**State: Inactive**

`modify` shall require a clean worktree by default. When scoped dirty-state
operation is explicitly enabled, only the exact dirty paths admitted by the
macro contract may be tolerated; conflicting dirty state shall fail closed
before mutation.

### FS-002-NR-023 — Modify Canonical Validation

**Classification: B**

**State: Inactive**

When validation is enabled, `modify` shall invoke exactly one governed
`execute.script` operation for the repository-root `scripts/validate` entry
point and shall not enumerate repository validator implementations itself.

### FS-002-NR-024 — Modify Difference Guard

**Classification: B**

**State: Inactive**

Before commit, `modify` shall produce governed difference evidence sufficient to
verify that the pending commit is contained within the declared mutation path
set and shall reject patch whitespace errors.

### FS-002-NR-025 — Modify Commit Behavior

**Classification: B**

**State: Inactive**

`modify` shall create at most one product-requested commit for its declared
mutation after successful applicable preconditions and validation, and that
commit shall contain only the declared mutation path set.

### FS-002-NR-026 — Modify Guarded Normal Publication

**Classification: B**

**State: Inactive**

`modify` publication shall use normal non-force push semantics and shall fail
closed when the selected remote head no longer matches the remote state observed
for the publication guard.

### FS-002-NR-027 — Modify Publication Verification

**Classification: B**

**State: Inactive**

After successful publication, `modify` shall observe the selected remote head and
require exact equality with the commit created by the macro.

### FS-002-NR-028 — Issue Macro Boundary

**Classification: B**

**State: Inactive**

`issue` shall support only the product-defined issue read, create, and modify
operations and shall realize those operations through existing governed GitHub
issue tasks rather than arbitrary GitHub API requests.

### FS-002-NR-029 — Pull Request Macro Boundary

**Classification: B**

**State: Inactive**

`pr` shall support only the product-defined pull-request read, create, and
modify operations and shall realize those operations through existing governed
GitHub pull-request tasks rather than arbitrary GitHub API requests.

### FS-002-NR-030 — Macro CLI Surface

**Classification: M**


FS-002 shall provide the maintained commands:

```text
gve macro --in REQUEST.json --out RESULT.json [--repo PATH]
gve macro-list
gve macro-schema NAME
```

The existing FS-001 `gve execute` surface shall remain available.

### FS-002-NR-031 — Machine-Readable Macro Result

**Classification: B**


Macro execution shall produce an authoritative machine-readable result
identifying at least the macro identity, overall status, ordered macro phase
grouping, ordered governed task results, and applicable failure evidence. The
result shall be written on success and, when possible, on request or execution
failure.

### FS-002-NR-032 — Contract-Only Introspection

**Classification: B**


`gve macro-list` and `gve macro-schema NAME` shall expose public macro identity
and contract information only. Introspection shall not expose macro
implementation source, internal workflow templates, credentials, or executable
behavior definitions.

### FS-002-NR-033 — Generic Presentation Boundary

**Classification: S**

Human terminal presentation may observe generic macro, phase, task, status,
stream, and evidence information, but execution correctness shall not depend on
task-specific presentation semantics.

### FS-002-NR-034 — Normal Command Installation

**Classification: B**

**State: Inactive**

FS-002 shall provide one repository-supported installation mechanism that makes
the maintained `gve` command usable from outside the source-tree working
directory while dispatching to the same product implementation used by
repository execution.

### FS-002-NR-035 — Deterministic Reinstallation

**Classification: M**

**State: Inactive**

Repeating the supported installation procedure shall either be idempotent or
shall fail with a clear actionable result without silently creating conflicting
launchers.

### FS-002-NR-036 — Installed Command Verification

**Classification: M**

**State: Inactive**

Mechanical Validation shall exercise the installed command from a working
directory outside the repository and shall verify at least `gve macro-list`,
`gve macro-schema discover`, and one non-mutating `gve macro` execution after
`discover` is available.

### FS-002-NR-037 — FS-001 Semantic Preservation

**Classification: S**

FS-002 shall preserve the accepted FS-001 capability, authority, workflow,
failure, and structured task-result semantics except where a separately
identified defect requires an explicit upstream product decision.
