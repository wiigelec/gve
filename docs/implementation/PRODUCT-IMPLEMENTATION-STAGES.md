# Product Implementation Stages

## Purpose

This document defines the staged implementation strategy for the maintained GVE product.

The objective is to build the product incrementally while continuously validating the architecture against the normative specifications. Each stage produces a usable, testable product while minimizing architectural rework.

The implementation stages are intentionally independent of the historical bootstrap executor. The bootstrap executor exists only to support governed development of the specifications and repository. It is not the maintained product and does not determine the implementation sequence described here.

---

# Guiding Principles

## Specification First

Normative specifications remain the authoritative source for product behavior.

Implementation validates the specifications rather than defining them.

## Vertical Development

Each stage produces a functioning vertical slice of the product instead of partially implementing many unrelated subsystems.

## Stable Foundations

Each completed stage becomes part of the permanent product.

Temporary scaffolding should be avoided whenever practical.

## Incremental Semantic Commitment

The implementation should depend only on semantic concepts that are sufficiently specified for the current stage.

Unresolved semantic questions should not block unrelated implementation work.

---

# Stage 1 — Product Installation

## Objective

Establish the maintained product as an installable application with a stable command-line interface.

No governed operations are processed during this stage.

## Scope

Implement:

- Package layout
- Installation
- Executable CLI
- Runtime initialization
- Diagnostic framework
- Version display

The product shall expose:

```text
gve --version
```

The displayed version shall be derived strictly from the system environment.

The implementation shall not derive its version from:

- Git metadata
- Repository contents
- Package metadata
- Embedded constants
- Bootstrap artifacts

## Acceptance Criteria

The product:

- Installs successfully.
- Launches successfully.
- Reports its version.
- Produces deterministic diagnostics.
- Exits with well-defined status codes.

---

# Stage 2 — Baseline Payload Processing

## Objective

Establish the complete request/result pipeline without executing external effects.

## Scope

Implement:

- Payload ingestion
- Structural validation
- Schema validation
- Identity derivation
- Baseline evaluation
- Result generation

No plugins execute during this stage.

No external mutations occur during this stage.

The purpose is to prove the application lifecycle:

```text
request
    ↓
parse
    ↓
validate
    ↓
evaluate
    ↓
result
```

## Acceptance Criteria

The product shall:

- Accept valid baseline payloads.
- Reject invalid payloads.
- Emit deterministic baseline results.
- Distinguish successful ingestion from successful execution.
- Produce stable diagnostics.

---

# Stage 3 — Filesystem Plugin

## Objective

Prove the complete plugin execution pipeline using a single read-only action.

## Scope

Implement the first maintained plugin:

```text
filesystem
```

with exactly one supported action:

```text
list-dir
```

No mutation actions are implemented.

The complete execution path becomes:

```text
request
    ↓
core validation
    ↓
plugin resolution
    ↓
action validation
    ↓
authorization
    ↓
execution
    ↓
observation
    ↓
result
```

The filesystem plugin exists to validate the plugin architecture rather than to provide broad filesystem capability.

## Acceptance Criteria

The product shall:

- Resolve the filesystem plugin.
- Validate plugin contracts.
- Validate action contracts.
- Execute `list-dir`.
- Observe the resulting directory contents.
- Emit deterministic result evidence.
- Reject unsupported plugins.
- Reject unsupported actions.

---

# Stage 4 — Architecture Hardening

## Objective

Complete the architectural hardening required before unrestricted implementation.

This stage intentionally precedes broad plugin development.

## Scope

Complete and validate:

- Authority model
- Execution semantics
- Effect-state semantics
- Observation model
- Evidence model
- Plugin lifecycle
- Plugin identity
- Action identity
- Replay handling
- Failure handling
- Diagnostic taxonomy
- Compatibility rules
- Conformance requirements

This stage should eliminate architectural uncertainty before significant implementation investment occurs.

## Acceptance Criteria

The core execution architecture is considered stable.

Independent developers should be able to implement plugins and actions without modifying the core architecture or inventing execution policy.

The execution pipeline should be considered complete and extensible.

---

# Stage 5 — Unrestricted Product Development

## Objective

Expand the maintained product using the hardened architecture.

## Scope

Implement additional plugins and actions according to the normative specifications.

Future work may include:

- Additional filesystem actions
- Git integration
- Workflow execution
- Publication
- External system integration
- Additional maintained plugins

No architectural redesign should be required during this stage.

Changes should primarily consist of new capabilities implemented within the established framework.

---

# Stage Exit Criteria

A stage is complete when:

- Its objectives have been achieved.
- All acceptance criteria pass.
- Its implementation is adequately tested.
- Required specification support exists.
- Subsequent stages do not require redesign of the completed work.

Stages should not be considered complete solely because code exists.

---

# Development Philosophy

Implementation should proceed only as quickly as the specifications support.

The goal is not to maximize implementation speed.

The goal is to construct a product whose architecture emerges directly from the normative specification set while minimizing future redesign.

Each completed stage should increase confidence that the maintained GVE product can be expanded through additional plugins and actions without requiring changes to the core execution architecture.

The implementation plan intentionally separates product evolution from specification evolution. Specifications define the required behavior. The implementation stages define a practical sequence for realizing that behavior in a maintained product.
