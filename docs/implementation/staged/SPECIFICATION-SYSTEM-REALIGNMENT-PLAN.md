# Specification System Realignment Plan

## Status

Implementation planning document.

This document is non-authoritative. It describes how to construct and adopt the
target specification-system structure without destabilizing the existing
accepted specifications, repository validation, or maintained product.

The intended final structure is described separately in:

```text
docs/SPECIFICATION-SYSTEM-STRUCTURE.md
```

## Objective

Build the replacement specification system in parallel with the existing
`specs/` subtree.

The existing `specs/` subtree remains the accepted specification authority
until the replacement system:

- contains the intended authoritative, derived, and validation structure;
- represents all accepted specification semantics and conformance evidence;
- validates itself independently;
- validates the repository and maintained product where required;
- produces equivalent accepted behavior;
- passes a complete semantic and exact-byte audit;
- is explicitly adopted as the repository's `specs/` subtree.

Only after those conditions are satisfied will the existing `specs/` subtree
be removed and the replacement moved into the authoritative `specs/` path.

## Parallel Construction Directory

The parallel specification system will be constructed under a functional
top-level path:

```text
specification-system/
```

This name describes the artifact's responsibility rather than an issue,
milestone, phase, migration, or temporary sequence.

During construction, the repository contains:

```text
specs/                  # currently accepted specification system
specification-system/   # replacement specification system under construction
```

The replacement directory is not accepted authority merely because it exists
in the repository. Until cutover, the existing `specs/GVE-SPECIFICATION-SET.json`
remains the accepted root manifest.

The replacement tree must contain an explicit status marker or manifest field
showing that it is not yet the accepted repository specification root.

## Intended Replacement Shape

```text
specification-system/
├── GVE-SPECIFICATION-SET.json
├── validate
├── authoritative/
├── derived/
└── validation/
```

At cutover, the complete tree is moved to:

```text
specs/
```

No permanent compatibility shim, duplicate authority tree, or historical copy
remains after acceptance.

## Core Safety Principles

### Existing authority remains stable

Construction of the replacement system must not require incremental mutation
of accepted authority merely to make the replacement tree work.

Changes to the existing `specs/` subtree are limited to separately justified
compatibility or validation work that is necessary to observe, compare, or
verify the replacement.

### One semantic responsibility per change

Each governed change addresses one bounded responsibility, such as:

- defining the specification-system authority;
- creating the replacement manifest model;
- relocating schemas by ownership;
- relocating deterministic projections;
- relocating conformance artifacts by function;
- separating intrinsic validation from target validation;
- removing issue-derived permanent names.

Structural moves must not be combined with unrelated semantic changes.

### No implicit semantic rewrites

Moving an accepted artifact does not authorize changing:

- requirements;
- definitions;
- identities;
- reference semantics;
- schemas;
- exact conformance bytes;
- process mappings;
- diagnostic messages;
- accepted product behavior.

Any semantic defect discovered during realignment is recorded and handled
through separate authority work.

### Functional naming only

New paths, filenames, modules, tests, fixtures, schemas, and stable identifiers
are named only for durable functional responsibility, authority, product
domain, repository domain, or artifact class.

No new durable name may derive from:

- issue numbers;
- pull-request numbers;
- milestones;
- implementation phases;
- migration order;
- temporary chronology;
- historical development sequence.

### Fail closed

The cutover does not occur when:

- artifact classification is ambiguous;
- authority is duplicated;
- accepted vectors cannot be mapped exactly;
- derived output differs unexpectedly;
- intrinsic validation depends on maintained-product code;
- repository or product conformance differs;
- digests or identities cannot be reproduced;
- the replacement manifest does not completely describe the accepted system.

## Work Areas

## Specification-System Authority

Create an authoritative specification that governs the specification system
itself.

It defines:

- the allowed top-level structure;
- artifact classes;
- naming and ownership;
- authoring requirements;
- manifest participation;
- schema ownership;
- projection rules;
- conformance artifact classification;
- validation boundaries;
- dependency direction;
- self-governance and bootstrap rules.

The specification must govern its own path and artifact class.

## Manifest Model

Define a manifest model capable of representing the complete specification
system without one-off integration mechanisms.

The model must distinguish:

- authoritative rule documents;
- authoritative frameworks;
- authoritative schemas;
- authoritative conformance artifacts;
- derived projections;
- validation profiles or entry points where binding is required.

The manifest must remain the sole discovery root for accepted authority.

The replacement manifest must preserve deterministic revision identity and
exact content binding.

## Authoritative Artifact Classification

Classify every current accepted artifact by durable function.

Each artifact must resolve to one of:

- repository authority;
- product authority;
- shared authority;
- authoritative schema;
- authoritative conformance material;
- derived material;
- validation implementation;
- validation test;
- validation-only fixture;
- obsolete or transitional material.

No file is moved solely because of its current directory.

## Repository Authority

Place repository-governing specifications under:

```text
authoritative/repository/
```

This includes authority for:

- the specification system;
- repository source layout;
- repository dependency direction;
- artifact placement and classification;
- repository validation boundaries.

Repository authority must not absorb temporary development-process rules
unless those rules are intentionally part of the GVE repository contract.

## Product Authority

Place maintained-product specifications under:

```text
authoritative/product/
```

The accepted Level hierarchy remains functionally recognizable.

Stage terminology remains only where Stage is an accepted product concept.

## Shared Authority

Place authority shared by repository and product specifications under:

```text
authoritative/shared/
```

Likely shared responsibilities include:

- identity framework;
- canonicalization;
- specification revision identity;
- document authority;
- shared reference semantics.

Special-case manifest bindings should be eliminated where the general artifact
model can represent the same relationship.

## Schema Realignment

Move schemas under:

```text
authoritative/schemas/
```

Group schemas by functional owner rather than keeping one undifferentiated
registry.

Every schema move must update:

- authoritative references;
- manifest bindings;
- validation lookup;
- tests;
- deterministic projections where paths are rendered.

Schema bytes remain unchanged unless separately governed semantic work is
required.

## Conformance Realignment

Move accepted vectors, fixtures, manifests, and exact-byte artifacts under:

```text
authoritative/conformance/
```

Group them by durable behavior or authority.

Examples include:

- identity vectors;
- canonical input vectors;
- invalid-input results;
- processing-failure results;
- authoritative result envelopes;
- repository-layout examples where they are accepted conformance authority.

Issue-derived namespaces are removed.

Validation-only malformed artifacts move instead to:

```text
validation/fixtures/
```

## Derived Artifact Realignment

Move deterministic non-authoritative output under:

```text
derived/
```

Markdown projections should mirror their authoritative source paths.

The replacement validation system must prove that every committed projection
is exactly reproducible from accepted authoritative input.

Derived artifacts must never participate in semantic conflict resolution.

## Validation Architecture

Create a self-contained validation system under:

```text
validation/
```

It is divided into:

```text
validation/
├── lib/
├── intrinsic/
├── targets/
├── runners/
├── tests/
└── fixtures/
```

### Intrinsic validation

Intrinsic validation uses only the replacement specification tree.

It validates:

- manifest structure and coverage;
- authoritative artifacts;
- schemas;
- semantic hierarchy;
- identity and digest bindings;
- reference closure;
- deterministic projections;
- authoritative conformance integrity;
- duplicate and undeclared authority rejection.

It must not import maintained-product code.

### Target validation

Target validation evaluates external systems against accepted authority.

Targets may include:

- repository structure;
- maintained source layout;
- installed product behavior;
- command-line process behavior.

Target adapters read expected rules and evidence from authoritative artifacts.

### Validation tests

Validation tests prove the validators, renderers, adapters, and runners.

Test names and fixture paths are functional rather than historical.

## Validation Entry Point

The replacement tree provides:

```text
specification-system/validate
```

Before cutover, this validates the replacement tree explicitly.

After cutover, it becomes:

```text
specs/validate
```

The final repository validation entry point calls:

```text
./specs/validate
```

The specification validation script owns specification-system validation.
The repository validation script orchestrates the complete repository gate and
does not duplicate specification-validation logic.

## Parallel Comparison

While both trees exist, validation must compare the accepted system and the
replacement system.

Comparison includes:

- complete artifact inventory;
- stable specification identities;
- semantic definitions and requirements;
- document relationships;
- schema behavior;
- conformance vector bytes;
- deterministic projection content;
- revision identity inputs;
- repository conformance results;
- maintained-product conformance results;
- validation exit statuses and evidence classes.

Path changes are expected.

Semantic and exact-byte changes are not expected unless explicitly authorized.

## Adoption Gate

The replacement system may become authoritative only when all of the following
are true:

- every accepted current artifact has an explicit disposition;
- every replacement authoritative artifact is manifest-bound;
- no authority exists only in validation code or tests;
- no issue-derived or milestone-derived durable name remains;
- intrinsic replacement validation passes;
- replacement derived artifacts reproduce deterministically;
- repository target validation passes;
- maintained-product target validation passes;
- accepted conformance vectors remain exact;
- specification identities and revision effects are understood;
- the complete replacement diff is semantically audited;
- no unresolved duplicate or conflicting authority exists;
- repository validation can call the replacement validation entry point;
- rollback remains possible before the final cutover commit is accepted.

## Cutover

The cutover is one bounded repository realignment.

Immediately before cutover:

```text
specs/
specification-system/
```

The cutover performs:

1. remove the existing `specs/` subtree;
2. move `specification-system/` to `specs/`;
3. update repository references to the final `specs/` paths;
4. run `./specs/validate`;
5. run complete repository validation;
6. verify no path references the construction location;
7. verify no duplicate specification authority remains.

Immediately after cutover:

```text
specs/
├── GVE-SPECIFICATION-SET.json
├── validate
├── authoritative/
├── derived/
└── validation/
```

The repository must not retain:

- a backup specification directory;
- a compatibility copy;
- duplicate manifests;
- a redirect from the old tree;
- historical issue-derived artifact paths;
- references to `specification-system/`.

Repository history remains the rollback and audit record.

## Rollback Boundary

Before cutover acceptance, rollback consists of removing the parallel
`specification-system/` work while leaving the existing `specs/` authority
unchanged.

After cutover acceptance, rollback requires reverting the complete cutover
revision. It must not be performed by recreating a partial hybrid tree.

## Completion Condition

The realignment is complete when:

- `specs/` has the accepted target structure;
- the manifest describes the complete specification system;
- authority, derived output, and validation implementation are visibly
  separated;
- intrinsic specification validation is self-contained;
- repository validation calls `./specs/validate`;
- repository and maintained-product conformance remain accepted;
- no durable artifact is named for an issue, milestone, phase, or migration;
- the parallel construction directory no longer exists.
