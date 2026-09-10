---
functional_set: FS-001
artifact: functional-set
title: Core Governed Repository Execution
design_revision: 8ede712d83a3376911dfb561b0173b7b7fd66cfe
---

# FS-001 — Core Governed Repository Execution

## Design binding

FS-001 Planning consumes Product Design exactly as accepted at Git revision:

```text
8ede712d83a3376911dfb561b0173b7b7fd66cfe
```

The selected Design scope is:

- `product/design/PD-001-gve-product-architecture.md`
- `product/design/PD-010-plugin-task-model.md`
- `product/design/PD-020-payload-orchestration-model.md`
- `product/design/PD-030-execution-boundary-model.md`
- `product/design/PD-040-result-model.md`

## Functional Set purpose

FS-001 realizes the first complete usable GVE execution path for repository
development workflows.

The Functional Set is intentionally large enough to exercise the complete
product architecture end to end:

```text
JSON payload
  -> engine
  -> registered plugin.task invocations
  -> ordered governed execution
  -> JSON workflow result
```

FS-001 includes the initial plugin domains required by Product Design:

```text
filesystem
git
execute
github
```

and enough tasks from those domains to express the reference development
workflow represented by `user/script-transfer-handoff.json`.

## In scope

FS-001 includes:

- a concrete versioned JSON payload contract;
- ordered workflow execution;
- workflow-local invocation identities;
- references from later task parameters to earlier task results;
- default fail-fast behavior;
- active execution authority that a payload may narrow but not widen;
- plugin registration and exact `plugin.task` resolution;
- structured task and workflow JSON results;
- the initial filesystem task set;
- the initial Git task set;
- `execute.script` with repository-local script selection and bounded
  process-tree runaway protection;
- the initial GitHub issue and pull-request task set;
- command-line invocation suitable for local repository workflows;
- mechanical validation sufficient to enforce FS-001's mechanically decidable
  normative requirements.

## Out of scope

FS-001 does not include:

- arbitrary caller-supplied executable source;
- generic shell execution;
- generic Git argument forwarding;
- generic GitHub HTTP/API requests;
- force push or history-rewrite publication;
- workflow continuation after failure;
- loops, branching, parallel task execution, or a general workflow language;
- script sandboxing or policing of script-internal side effects;
- generalized support for non-repository execution;
- plugin installation or third-party plugin distribution;
- compatibility guarantees for payload versions that do not yet exist.

## Completion boundary

FS-001 is complete when the repository contains a working implementation that
can accept a valid FS-001 payload, execute the selected registered tasks in
order under the FS-001 authority and failure model, return structured JSON
evidence, mechanically satisfy all applicable mechanical requirements, and
semantically preserve the selected Product Design.

The `fs1` branch is the development branch for the complete FS-001 lifecycle
through Planning, Build, Validation, Build Review, and Acceptance. Acceptance is
intentional integration of the satisfactory `fs1` candidate into `main`.
