---
functional_set: FS-004
artifact: normative-specification
title: Macro Hardening, Discovery, and Recovery Specification
design_revision: 76d1caf69cc2ebc542116d19ec6d0c8efb5c7b6a
---

# FS-004 — Normative Specification

Evaluation classifications:

- **M** — mechanical
- **S** — semantic
- **B** — both mechanical and semantic

Purely semantic requirements are active during Planning. Requirements classified
M or B are mechanically evaluated through the requirement bindings maintained
for FS-004 and become acceptance-ready only when Build realizes the bound
behavior and canonical Validation passes.

## Requirements

### FS-004-NR-001 — Exact Design Binding

**Classification: M**

FS-004 Planning shall identify exact consumed Product Design revision
`76d1caf69cc2ebc542116d19ec6d0c8efb5c7b6a`.

### FS-004-NR-002 — Existing Modify Compatibility

**Classification: B**

Existing complete-content `modify` requests accepted by FS-003 shall remain
accepted with unchanged complete-replacement meaning.

### FS-004-NR-003 — Exclusive Modify Representation

**Classification: B**

Each existing-file `modify` change shall require `operation`, normalized
repository-relative `path`, exact `expected_sha256`, and exactly one of `content`
or `diff`; both or neither shall fail before macro execution.

### FS-004-NR-004 — Diff Is Bounded Data

**Classification: B**

A caller-supplied `diff` shall be treated only as bounded data for one declared
file and shall not expose caller-selected patch commands, options, tasks,
stages, shell fragments, or generic executable behavior.

### FS-004-NR-005 — Exact Digest Before Patch

**Classification: B**

Before a diff modification changes its target, GVE shall require the target to
be an existing UTF-8 regular file and shall require its current SHA-256 to equal
caller-supplied `expected_sha256`.

### FS-004-NR-006 — Exact Patch Target

**Classification: B**

A diff modification shall address exactly the declared normalized
repository-relative path and shall reject additional file sections, path
changes, absolute paths, repository escape, or `/dev/null` file targets.

### FS-004-NR-007 — Unsupported Patch Forms Rejected

**Classification: B**

Diff modification shall reject rename, copy, delete, binary-patch, and other
patch forms whose meaning is not the reviewed one-existing-file textual
modification contract.

### FS-004-NR-008 — Apply Check Before Mutation

**Classification: B**

A diff modification shall perform a non-mutating applicability check before the
patch is applied, and a non-applicable patch shall fail without changing the
target.

### FS-004-NR-009 — Patch Effect Evidence

**Classification: B**

A successful diff modification shall report the modified path, previous
SHA-256, and resulting SHA-256 through governed task evidence.

### FS-004-NR-010 — Mutation Scope Independent of Representation

**Classification: B**

`modify` declared-path uniqueness, dirty-state guards, staging scope, validation,
difference checks, commit limit, publication guards, and verification shall
apply equivalently whether a modification uses `content` or `diff`.

### FS-004-NR-011 — Discover Default Compatibility

**Classification: B**

Existing `discover` default observations and existing observation requests shall
preserve their accepted FS-003 behavior.

### FS-004-NR-012 — Bounded Folder Listing Contract

**Classification: B**

`discover` shall support explicit one-or-more folder-list requests for
repository-relative directories, reject duplicate normalized request paths, and
return deterministic repository-relative entries including path and kind.

### FS-004-NR-013 — Multi-File Read Contract

**Classification: B**

`discover` shall support one request containing multiple unique normalized
repository-relative UTF-8 regular-file paths and shall return complete content
and SHA-256 evidence for each successfully read file.

### FS-004-NR-014 — Multi-File Read Fail-Fast Preservation

**Classification: B**

Failure of one governed requested file read shall preserve ordinary Engine
fail-fast behavior and shall not be converted into a successful partial
discover result by silently omitting the failed request.

### FS-004-NR-015 — Tree Status Product Concept

**Classification: B**

`discover` shall expose explicit opt-in `tree_status` as one stable product-owned
read-only discovery concept rather than requiring callers to infer its meaning
from unrelated macro invocations.

### FS-004-NR-016 — Tree Status Repository State

**Classification: B**

Tree status shall expose repository root and configured remotes, active branch
or detached state, and current HEAD commit when one exists.

### FS-004-NR-017 — Tree Status Complete Porcelain State

**Classification: B**

Tree status shall expose complete porcelain-derived worktree status including
untracked paths and shall preserve fixed-width Git status semantics during
parsing.

### FS-004-NR-018 — Tree Status Difference Evidence

**Classification: B**

Tree status shall return complete unstaged tracked diff, complete staged diff,
and complete tracked-tree diff between HEAD and the effective tracked
worktree/index state without mutating the real index.

### FS-004-NR-019 — No Implicit Untracked Content Read

**Classification: B**

Tree status may report untracked paths but shall not implicitly read or return
their file contents.

### FS-004-NR-020 — Discover Stable Projection

**Classification: B**

New folder-list, multi-file-read, and tree-status results shall be available
through stable macro-level discover projection without erasing or reordering
underlying governed task evidence.

### FS-004-NR-021 — Introspection Correspondence

**Classification: B**

`gve macro-schema discover`, `gve macro-schema modify`, and authoritative runtime
validation shall describe the same revised closed parameter spaces.

### FS-004-NR-022 — Non-Repository Diagnostic

**Classification: B**

When the selected resolved path is not a Git repository, macro CLI failure shall
identify that selected path and state that it is not a Git repository.

### FS-004-NR-023 — Non-Top-Level Diagnostic

**Classification: B**

When the selected path is inside a Git repository but is not its top level,
macro CLI failure shall identify both the selected path and observed repository
top level and shall not silently switch repositories.

### FS-004-NR-024 — Repository Expectation Evidence

**Classification: B**

Repository identity, branch, or head expectation mismatch shall remain
fail-closed and shall provide structured `field`, `expected`, and `observed`
evidence.

### FS-004-NR-025 — Recovery Trigger Boundary

**Classification: B**

Automatic recovery shall be considered only after failed macro execution that
produced invocation-owned worktree or branch effects, before any product commit,
and only when recovery can be bounded to proven effects of that invocation.

### FS-004-NR-026 — No-Mutation Recovery State

**Classification: B**

Failure before product-owned mutation shall report recovery as not required.

### FS-004-NR-027 — Recoverable Pre-Mutation Capture

**Classification: B**

Before recoverable mutation, `modify` shall retain sufficient invocation-local
evidence to restore each macro-owned existing-file modification exactly, identify
each macro-created path as previously absent, and record original/created branch
state when branch creation is requested.

### FS-004-NR-028 — Worktree Recovery Scope

**Classification: B**

Eligible automatic worktree recovery shall affect only paths proven to have
been changed by the current invocation and shall preserve unrelated and admitted
pre-existing user work.

### FS-004-NR-029 — Unsafe Recovery Fails Closed

**Classification: B**

If safe attribution or exact restoration cannot be proven, recovery shall stop
rather than guess, preserve the primary macro failure, and report residual state.

### FS-004-NR-030 — Created Branch Recovery

**Classification: B**

Before commit, a branch created by the failed invocation may be removed only
after successful worktree recovery, return to the exact original branch, and
verification that the created branch still has no independent commit; no
pre-existing branch may be deleted.

### FS-004-NR-031 — No Automatic Post-Commit History Rewrite

**Classification: B**

After the product commit exists, automatic recovery shall not reset, amend,
revert, delete committed history, force push, or delete the published remote
branch.

### FS-004-NR-032 — Publication State Evidence

**Classification: B**

Modify result evidence shall distinguish publication not attempted,
attempted-unverified, and verified states and shall retain applicable local
commit, remote-head-before, and remote-head-after observations.

### FS-004-NR-033 — Recovery Result Evidence

**Classification: B**

The stable `modify` result shall directly expose mutation-started state, mutated
paths, branch effect, commit-created state, publication attempted/verified state,
and a recovery object distinguishing at least not-required, not-attempted,
success, partial, and failed states with actions and residual state.

### FS-004-NR-034 — Recovery Does Not Synthesize Success

**Classification: B**

Recovery success or failure shall never convert the primary failed macro
operation into overall success, and original ordered failure evidence shall be
retained.

### FS-004-NR-035 — Existing Engine Preservation

**Classification: S**

FS-004 shall preserve the accepted FS-001 Engine, authority, result-reference,
fail-fast, and ordered structured-evidence semantics.

### FS-004-NR-036 — Authority Non-Expansion

**Classification: S**

Diff data, discovery requests, repository diagnostics, projected evidence, and
recovery policy shall not widen active authority.

### FS-004-NR-037 — No Generic Recovery Language

**Classification: B**

If recovery requires additional governed execution after primary failure, its
selection and task sequence shall be product-owned, use the existing Engine and
registered tasks, and shall not expose caller-programmable recovery behavior.

### FS-004-NR-038 — Canonical Mechanical Validation

**Classification: M**

The completed FS-004 Build shall pass repository-wide `scripts/validate`.

### FS-004-NR-039 — Requirement Evaluation Binding

**Classification: M**

Every FS-004 requirement classified M or B shall have exact applicable
mechanical-validation task bindings before FS-004 is ready for Semantic Review.

### FS-004-NR-040 — Closed Architectural Boundaries

**Classification: B**

FS-004 Build shall preserve repository architectural boundaries and shall prefer
the smallest implementation surfaces necessary to realize the reviewed Design
and Planning without introducing an alternate execution architecture.
