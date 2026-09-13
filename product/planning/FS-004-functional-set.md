---
functional_set: FS-004
artifact: functional-set
title: Macro Hardening, Discovery, and Recovery
design_revision: 76d1caf69cc2ebc542116d19ec6d0c8efb5c7b6a
---

# FS-004 — Macro Hardening, Discovery, and Recovery

## Design binding

FS-004 Planning consumes Product Design exactly as published at Git revision:

```text
76d1caf69cc2ebc542116d19ec6d0c8efb5c7b6a
```

The selected new Design scope is:

- `product/design/PD-090-macro-hardening.md`

FS-004 also preserves applicable accepted Design established by PD-001 through
PD-080.

## Functional Set purpose

FS-004 hardens the maintained macro boundary in four related areas:

- compact exact-file patch mutation for `modify`;
- richer bounded read-only repository discovery;
- actionable wrong-repository diagnostics;
- explicit and conservative failure-recovery semantics.

The purpose is to make GVE safer and more efficient for repeated repository
handoff without introducing generic caller-authored execution behavior.

## In scope

FS-004 includes:

- `modify` support for exactly one of complete replacement `content` or bounded
  unified `diff` for each existing-file modification;
- retention of exact expected SHA-256 preconditions for both modification forms;
- patch validation that proves one declared repository-relative target, rejects
  extra file mutations and path escape, and verifies clean applicability before
  mutation;
- preservation of complete-content create behavior and existing complete-content
  modify compatibility;
- `discover` support for one or more folder listings;
- `discover` support for reading multiple UTF-8 files in one macro invocation,
  including complete content and SHA-256 evidence;
- a consolidated `tree-status` discovery concept containing repository/remotes,
  branch/detached state, HEAD, complete porcelain status, staged state, staged
  diff, unstaged diff, and complete tracked-tree diff evidence;
- no implicit reading of untracked file contents by tree-status;
- clear CLI/result distinction among not-a-repository, selected-subdirectory,
  and request repository expectation mismatch cases;
- recovery evidence describing mutation, branch, commit, publication, recovery,
  and residual-state status;
- bounded automatic recovery only after macro-owned worktree mutation and before
  commit, limited to effects of the current invocation;
- preservation of admitted pre-existing dirty work during recovery;
- no automatic history rewrite, reset, amend, revert, force push, or published
  commit deletion;
- ambiguous-publication reporting when normal push may have occurred but exact
  verification cannot establish the expected remote head;
- mechanical validation for contracts, patch boundaries, discovery aggregation,
  repository diagnostics, recovery safety, compatibility, and fail-fast
  preservation.

## Out of scope

FS-004 does not include:

- a caller-authored generic patch executor;
- arbitrary patching of multiple undeclared files;
- binary-file editing;
- automatic semantic merge or conflict resolution;
- implicit reading of all untracked file contents;
- repository auto-discovery that silently switches the selected repository;
- caller-authored tasks, stages, loops, retries, recovery programs, or commands;
- arbitrary shell execution;
- automatic recovery after commit by reset, revert, amend, branch deletion, or
  other history manipulation;
- force push or history rewrite;
- changing accepted issue or pull-request macro meaning except shared diagnostic
  infrastructure needed by FS-004.

## Completion boundary

FS-004 is complete when the feature branch:

- exposes the reviewed compact-patch and expanded-discovery contracts;
- enforces exact-path and stale-state protections for diff modification;
- provides complete tree-status evidence without mutation;
- emits actionable repository-selection failures;
- preserves pre-existing user work during applicable pre-commit recovery;
- never rewrites committed/published history as automatic recovery;
- preserves established Engine fail-fast and ordered task evidence;
- passes canonical repository validation;
- has active mechanical evaluation bindings for every M or B FS-004 normative
  requirement realized by Build; and
- completes Semantic Review against Design revision
  `76d1caf69cc2ebc542116d19ec6d0c8efb5c7b6a`.
