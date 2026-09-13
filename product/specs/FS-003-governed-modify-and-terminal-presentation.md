---
functional_set: FS-003
artifact: normative-specification
title: Governed Modify Workflow and Terminal Presentation Specification
design_revision: b33bcaefe870fa1e18beaa6518ab6337f7333c65
---

# FS-003 — Normative Specification

Evaluation classifications:

- **M** — mechanical
- **S** — semantic
- **B** — both mechanical and semantic

Purely semantic requirements are active during Planning. Requirements classified
M or B are initially inactive until Build realizes the mechanical implementation
and exact requirement-to-validation-task bindings. Planning may then reactivate
those requirements without changing their identities or normative text.

## Requirements

### FS-003-NR-001 — Exact Design Binding

**Classification: M**


FS-003 Planning shall identify exact consumed Product Design revision
`b33bcaefe870fa1e18beaa6518ab6337f7333c65`.

### FS-003-NR-002 — Macro-Only Maintained Execution Surface

**Classification: B**


The maintained runtime execution CLI shall expose registered product macros only.
Raw caller-authored FS-001 workflows shall not be accepted through a maintained
CLI command.

### FS-003-NR-003 — Internal FS-001 Preservation

**Classification: S**

FS-003 shall preserve the FS-001 Engine and raw workflow payload as internal
product orchestration mechanisms with their accepted task, authority, reference,
fail-fast, and structured-evidence semantics.

### FS-003-NR-004 — Maintained CLI Commands

**Classification: M**


The maintained commands shall be:

```text
gve macro --in REQUEST.json --out RESULT.json [--repo PATH]
gve macro-list
gve macro-schema NAME
```

A maintained `gve execute` command shall not be exposed.

### FS-003-NR-005 — Observational Presentation

**Classification: B**


Live terminal presentation shall observe governed execution and shall not grant
authority, alter task parameters or ordering, weaken failure, retry tasks, or
become an alternate execution result.

### FS-003-NR-006 — Live Material-Step Presentation

**Classification: B**


Macro terminal execution shall visibly present operation identity, phase
transitions, material-step announcements, applicable exact external commands,
captured non-empty stdout/stderr, explicit PASS/FAIL outcomes, and a final
summary without leaving long validation/publication work silent. The final
`modify` summary shall communicate, when applicable, Operation, Repository,
Branch, Expected HEAD, Observed HEAD, Files Changed, Validation, Commit, Remote
HEAD, and Result JSON.

### FS-003-NR-007 — Observer-Free Semantic Equivalence

**Classification: B**


Attaching or omitting the terminal observer/presenter shall not change governed
task execution semantics or authoritative Engine/macro results.

### FS-003-NR-008 — Authoritative Result Artifact

**Classification: B**


The macro CLI shall attempt to write the authoritative result JSON on successful
and failed governed execution whenever the requested destination remains
writable.

### FS-003-NR-009 — Output Failure Distinction

**Classification: B**


A result-artifact write failure shall be reported distinctly from governed
execution status and shall not convert failed governed execution into success or
erase established execution evidence.

### FS-003-NR-010 — Modify Required Expected HEAD

**Classification: B**


Every `modify` request shall include `expected_head` as an exact lowercase
40-character Git commit identity.

### FS-003-NR-011 — Expected HEAD Before Effects

**Classification: B**


Before any product-requested repository effect, `modify` shall observe local
HEAD and require exact equality with caller-supplied `expected_head`; mismatch
shall fail before mutation.

### FS-003-NR-012 — Explicit Branch Creation Contract

**Classification: B**


`modify` shall create a local branch only when the caller supplies the reviewed
explicit branch-creation request with `create: true` and a valid branch name.

### FS-003-NR-013 — Exact Branch Creation Base

**Classification: B**


A requested new local branch shall be created from exactly `expected_head`,
switched to, and re-verified for both active branch identity and unchanged HEAD
before content mutation.

### FS-003-NR-014 — Existing Requested Branch Fails Closed

**Classification: B**


If caller intent is to create a new local branch and that branch already exists,
`modify` shall fail closed and shall not silently reinterpret the request as use
of the existing branch.

### FS-003-NR-015 — Effective Local Branch

**Classification: S**

The effective local branch shall be the successfully created requested branch
when creation occurs, otherwise the prechecked active local branch.

### FS-003-NR-016 — Effective Publication Branch

**Classification: B**


The effective publication branch shall be the caller-selected `remote_branch`
when explicitly supplied, otherwise the effective local branch.

### FS-003-NR-017 — Origin-Only Publication Authority

**Classification: B**


Publication branch selection may narrow the destination within authorized
`origin` but shall not permit caller selection of another Git remote or otherwise
widen Git authority.

### FS-003-NR-018 — Publication Guard State Model

**Classification: B**


Before mutation/publication, `modify` shall establish the effective publication
branch guard as either its exact observed remote commit identity or verified
remote-branch absence.

### FS-003-NR-019 — Publication Race Recheck

**Classification: B**


Immediately before push, `modify` shall re-observe the effective publication
branch and require exact equality with the previously established existing-OID
or branch-absence guard.

### FS-003-NR-020 — Normal Non-Force Publication

**Classification: B**


`modify` shall publish using normal non-force semantics only and shall not
rewrite history or silently introduce force behavior.

### FS-003-NR-021 — Exact Remote Verification

**Classification: B**


After publication, `modify` shall observe the effective publication branch and
require exact equality with the commit created by the macro before reporting
successful terminal PASS.

### FS-003-NR-022 — Modify Stage Model

**Classification: S**

The maintained `modify` stages shall be PRECHECK, BRANCH, MUTATE, VALIDATE,
COMMIT, PUBLISH, and VERIFY, and stage metadata shall not alter Engine semantics.

### FS-003-NR-023 — Declared Mutation Preservation

**Classification: B**


FS-003 shall preserve the accepted FS-002 requirement that `modify` mutates only
declared repository-relative change paths, preserves unrelated work, and stages
only the declared mutation path set.

### FS-003-NR-024 — Canonical Validation Preservation

**Classification: B**


When validation is enabled, `modify` shall invoke exactly one governed
repository-root `scripts/validate` operation and shall not substitute a
caller-selected command.

### FS-003-NR-025 — Concise Short-Status Evidence

**Classification: B**


Before the product commit, `modify` terminal presentation shall show governed
Git short-status evidence preserving the fixed-width status semantics needed to
distinguish staged, unstaged, renamed, copied, deleted, and untracked states.

### FS-003-NR-026 — Complete Staged Diff Capture

**Classification: B**


Before commit, `modify` shall capture the complete staged diff representing the
exact content to be committed.

### FS-003-NR-027 — Cached Difference Check

**Classification: B**


Before commit, `modify` shall reject patch whitespace errors through the
governed equivalent of `git diff --cached --check`.

### FS-003-NR-028 — Stable Macro-Level Modify Result

**Classification: B**


The authoritative `modify` result shall expose stable macro-level continuation
evidence independently of generated task identities while retaining complete
ordered stage/task evidence. Once a valid `modify` request has entered macro
execution and a macro result can be constructed, the version-1 `result` object
shall use the fixed key set and concrete value shapes defined by the FS-003 Plan.

### FS-003-NR-029 — Stable Modify Result Fields

**Classification: B**


Stable `modify` continuation evidence shall use the Plan-defined fixed public
keys and concrete types for repository, effective local branch, effective
publication branch, caller `expected_head`, observed starting HEAD,
branch-creation outcome, changed paths, validation evidence, staged diff,
created commit, commit count, push mode, observed/verified remote head,
force/history-rewrite evidence, and merge evidence. Unestablished observational
or effect evidence shall be represented by JSON `null` exactly where the Plan
defines nullability rather than by key omission or guessed values.

### FS-003-NR-030 — Evidence Non-Invention

**Classification: B**


A macro-level result shall derive continuation evidence only from actual caller
assertions, established product context, repository observations, and successful
governed task results; unavailable evidence shall not be invented.

### FS-003-NR-031 — Partial Failure Evidence Retention

**Classification: B**


A failed `modify` result shall retain stable continuation evidence already
established, including staged diff after capture and commit evidence after commit,
even when later publication or verification fails.

### FS-003-NR-032 — Underlying Task Evidence Retention

**Classification: B**


Stable macro-level result projection shall not erase, reorder, or replace the
complete generated stage/task records, including later `not-executed` records.

### FS-003-NR-033 — Modify Introspection Correspondence

**Classification: B**


`gve macro-schema modify` and authoritative runtime validation shall describe the
same revised closed parameter space, including required `expected_head` and the
optional explicit branch-creation request.

### FS-003-NR-034 — No Arbitrary Execution Escape Hatch

**Classification: B**


FS-003 shall not add caller-controlled raw Git argv, shell fragments, arbitrary
remote selection, caller-defined tasks, caller-defined stages, force options, or
generic event/workflow behavior.

### FS-003-NR-035 — Existing Macro Semantic Preservation

**Classification: S**

`discover`, `issue`, and `pr` shall preserve their accepted FS-002 semantics
except for shared terminal/result infrastructure that is semantically
observational.

### FS-003-NR-036 — FS-002 Authority Preservation

**Classification: S**

FS-003 shall preserve accepted FS-002/FS-001 authority non-expansion semantics;
expected-state assertions, branch names, publication branch selection, terminal
presentation, and result projection shall not grant authority.

### FS-003-NR-037 — Canonical Mechanical Validation

**Classification: M**


The completed FS-003 Build shall pass repository-wide `scripts/validate`.

### FS-003-NR-038 — Requirement Evaluation Binding

**Classification: M**


Build shall bind every FS-003 requirement classified M or B to exact applicable
mechanical validation tasks before FS-003 is ready for Semantic Review.

### FS-003-NR-039 — Failed Transcript Evidence

**Classification: B**


On failed macro execution, terminal presentation shall distinguish the failing
phase and task when known, the relevant failure reason, prior successful work,
and later work that was not executed, without changing authoritative execution
meaning.
