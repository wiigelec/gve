---
functional_set: FS-003
artifact: functional-set
title: Governed Modify Workflow and Terminal Presentation
design_revision: b33bcaefe870fa1e18beaa6518ab6337f7333c65
---

# FS-003 — Governed Modify Workflow and Terminal Presentation

## Design binding

FS-003 Planning consumes Product Design exactly as accepted at Git revision:

```text
b33bcaefe870fa1e18beaa6518ab6337f7333c65
```

The selected Design scope is:

- `product/design/PD-001-gve-product-architecture.md`
- `product/design/PD-010-plugin-task-model.md`
- `product/design/PD-020-payload-orchestration-model.md`
- `product/design/PD-030-execution-boundary-model.md`
- `product/design/PD-040-result-model.md`
- `product/design/PD-050-product-macro-layer.md`
- `product/design/PD-060-macro-cli-and-introspection.md`
- `product/design/PD-070-public-execution-and-presentation.md`
- `product/design/PD-080-modify-handoff-and-semantic-evidence.md`

## Functional Set purpose

FS-003 tightens the maintained GVE product boundary around registered macros and
makes `modify` suitable for governed repository handoff and semantic review.

The maintained execution path is:

```text
runtime caller
  -> registered product macro
  -> product-owned orchestration
  -> internal FS-001 workflow
  -> existing Engine
  -> registered governed tasks
  -> stable macro result + observational terminal transcript
```

FS-003 preserves the accepted FS-001 Engine semantics while removing raw
caller-authored FS-001 workflow execution from the maintained CLI.

## In scope

FS-003 includes:

- removal of `gve execute` from the maintained public CLI surface;
- preservation of raw FS-001 workflow execution as internal product machinery;
- retained public commands `gve macro`, `gve macro-list`, and
  `gve macro-schema`;
- live observational terminal presentation for macro execution;
- product-owned execution events or equivalent observer hooks sufficient to show
  phases, material steps, external commands, captured streams, and PASS/FAIL
  outcomes without changing execution semantics;
- authoritative result JSON on success and, when possible, governed failure;
- distinct reporting of execution failure versus result-artifact write failure;
- mandatory caller-supplied `expected_head` for every `modify` request;
- explicit caller-requested local branch creation from exactly `expected_head`;
- fail-closed behavior when a requested new local branch already exists;
- deterministic effective-local-branch and effective-publication-branch
  selection;
- optional explicit cross-name publication within authorized `origin`;
- exact existing-remote-head or remote-branch-absence publication race guards;
- a `BRANCH` presentation/result stage for caller-requested branch creation;
- concise governed Git short-status presentation before commit;
- complete staged diff capture before commit;
- stable macro-level `modify` continuation evidence, including the staged diff;
- preservation of established macro-level evidence after later commit,
  publication, or verification failure;
- exact remote-head verification after normal non-force publication;
- mechanical validation for the revised CLI, `modify` contract, result
  projection, observer/presentation behavior, and publication guards.

## Out of scope

FS-003 does not include:

- a second task execution engine;
- restoration of a maintained raw FS-001 caller workflow surface;
- caller-defined tasks, stages, commands, workflow logic, or authority grants;
- a generic event scripting or presentation language;
- arbitrary shell or Git command execution;
- arbitrary Git remote selection;
- force push, history rewrite, or merge behavior;
- automatic development-branch creation when the caller did not request it;
- silently using an existing local branch when branch creation was requested;
- transactional rollback;
- semantic interpretation of the staged diff by GVE itself;
- removal of complete stage/task evidence in favor of the macro-level result;
- changes to `discover`, `issue`, or `pr` semantics beyond shared terminal/result
  infrastructure required by FS-003.

## Completion boundary

FS-003 is complete when the `fs003` branch:

- exposes only registered macros through the maintained execution CLI;
- implements the reviewed `modify` expected-HEAD, branch, publication, diff,
  and continuation-evidence semantics;
- provides live observational terminal output without changing governed
  execution meaning;
- writes authoritative macro result JSON on successful execution and on failed
  governed execution whenever the requested destination remains writable;
- passes canonical repository validation;
- has active mechanical evaluation bindings for every M or B FS-003 normative
  requirement realized by Build; and
- completes Semantic Review against Design revision
  `b33bcaefe870fa1e18beaa6518ab6337f7333c65`.
