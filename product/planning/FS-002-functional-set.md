---
functional_set: FS-002
artifact: functional-set
title: Product Macro Layer and CLI
design_revision: 5c285ef47193e8d52f402259e15edae659460f49
---

# FS-002 — Product Macro Layer and CLI

## Design binding

FS-002 Planning consumes Product Design exactly as accepted at Git revision:

```text
5c285ef47193e8d52f402259e15edae659460f49
```

The selected Design scope is:

- `product/design/PD-001-gve-product-architecture.md`
- `product/design/PD-010-plugin-task-model.md`
- `product/design/PD-020-payload-orchestration-model.md`
- `product/design/PD-030-execution-boundary-model.md`
- `product/design/PD-040-result-model.md`
- `product/design/PD-050-product-macro-layer.md`
- `product/design/PD-060-macro-cli-and-introspection.md`

## Functional Set purpose

FS-002 adds a small product-owned macro layer above the accepted FS-001 Engine.

The public path is:

```text
macro request
  -> macro-specific validation
  -> product-owned Python macro builder
  -> FS-001 workflow
  -> existing Engine
  -> existing governed plugin tasks
  -> staged macro result
```

FS-002 intentionally reuses FS-001 orchestration and task-result semantics rather
than defining a second workflow language.

## In scope

FS-002 includes:

- a static registry for product-owned macros;
- four initial macro identities: `discover`, `modify`, `issue`, and `pr`;
- closed macro request and parameter contracts;
- direct product Python implementations/builders for macro behavior;
- generation of ordinary FS-001 task invocations;
- reuse of native FS-001 `$ref` task-result references;
- product-owned stage metadata used only for presentation/result grouping;
- fail-fast execution through the existing Engine;
- macro result output with ordered stage/task evidence;
- `gve macro --in REQUEST.json --out RESULT.json [--repo PATH]`;
- `gve macro-list`;
- `gve macro-schema NAME`;
- repository-derived execution context and request expectation guards;
- canonical full repository validation through one `scripts/validate` invocation
  inside `modify` when validation is enabled;
- mechanical validation of the public macro contracts and behaviors.

## Out of scope

FS-002 does not include:

- caller-authored macro definitions;
- declarative macro stage/task definitions loaded from JSON;
- a generic macro template/binding language;
- `$macro`, `$item`, `$context`, `$optional`, or macro-specific result-reference
  operators;
- generic conditions, branching, repetition, or continuation constructs exposed
  as a macro language;
- a second workflow/result-reference engine;
- a general-purpose JSON Schema implementation;
- plugin installation or third-party macros;
- transactional rollback;
- force push or history rewrite;
- replacement of the FS-001 execute payload surface;
- rich task-specific console semantics required for correctness.

## Completion boundary

FS-002 is complete when the `fs002` branch contains a working product macro
surface for all four initial macros, preserves FS-001 authority and task
execution semantics, exposes the defined CLI/introspection commands, produces
staged machine-readable macro results, passes canonical repository validation,
and completes Semantic Review against Design revision
`5c285ef47193e8d52f402259e15edae659460f49`.
