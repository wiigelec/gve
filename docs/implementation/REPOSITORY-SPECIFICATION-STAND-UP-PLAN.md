# Repository Specification Stand-Up Plan

## Status

Implementation planning document.

This document is non-normative. It describes how to stand up the replacement
repository-specification system in a parallel construction tree while the
existing `specs/` tree remains authoritative.

The immediate goal is to define the directory structure and create functional
placeholder artifacts. Content will then be added incrementally behind
self-contained validation.

## Objective

Create a complete structural skeleton for the future `specs/repo/` subtree in
the parallel specification-system directory.

The skeleton should make all expected responsibilities visible before their
normative content is written.

The work should proceed in two broad steps:

```text
define structure and placeholders
    ↓
replace placeholders with validated content
```

The temporary tree must not be treated as accepted authority until the final
specification-system cutover.

## Construction Location

Use the parallel construction path:

```text
specification-system/repo/
```

This path mirrors the intended final location:

```text
specs/repo/
```

During construction:

```text
specs/                       current accepted specification system
specification-system/repo/   replacement repo specifications under construction
```

At final cutover, the complete `specification-system/` tree will replace the
existing `specs/` tree.

## Initial Directory Shape

```text
specification-system/
└── repo/
    ├── REPOSITORY-SPECIFICATION-SET.json
    ├── validate
    ├── authoritative/
    │   ├── repository-model/
    │   ├── specification-system/
    │   ├── development-process/
    │   ├── normative-change/
    │   ├── level-model/
    │   ├── source-layout/
    │   ├── schemas/
    │   └── conformance/
    ├── derived/
    │   └── markdown/
    └── validation/
        ├── lib/
        ├── intrinsic/
        ├── repository/
        ├── tests/
        └── fixtures/
```

The exact names may be adjusted while the placeholders are still
non-authoritative, but every path must be functional rather than issue-,
milestone-, phase-, or migration-derived.

## Root Manifest Placeholder

Create:

```text
specification-system/repo/REPOSITORY-SPECIFICATION-SET.json
```

The initial placeholder should identify:

- that this is the repository-specification set;
- that it is under construction;
- the intended manifest schema;
- the expected artifact classes;
- the expected root validation entry point;
- no false claim that placeholder documents are accepted authority.

The placeholder manifest should not contain fabricated final digests.

It may initially contain an explicitly unsealed or incomplete status until the
manifest schema and digest model are defined.

## Validation Entry Point Placeholder

Create:

```text
specification-system/repo/validate
```

The first implementation should validate structure rather than semantics.

Initial checks may include:

- required directories exist;
- required placeholder files exist;
- no issue- or milestone-derived names exist;
- all placeholder files declare their non-authoritative construction status;
- no file imports from the current maintained product;
- no path escapes the temporary repo-specification tree.

As substantive specifications are added, this entry point becomes the complete
deep validation suite for `specs/repo/`.

## Authoritative Placeholder Areas

The `authoritative/` tree represents the eventual repository authority.

During construction, placeholder documents are not authoritative merely
because they are placed there. Each placeholder must explicitly state that it
is incomplete and unaccepted.

### `authoritative/repository-model/`

Purpose:

Define the durable repository model.

Expected eventual contents:

```text
repository-model/
├── REPOSITORY-MODEL.json
└── REPOSITORY-TREES.json
```

Responsibilities:

- define normative and non-normative repository areas;
- define `docs/`, `specs/`, and `src/`;
- define ownership and dependency relationships;
- define repository-generic versus product-specific authority;
- define which repository areas may contain maintained artifacts.

### `authoritative/specification-system/`

Purpose:

Define the rules governing specifications themselves.

Expected eventual contents:

```text
specification-system/
├── SPECIFICATION-SYSTEM.json
├── SPECIFICATION-AUTHORING.json
├── SPECIFICATION-ARTIFACTS.json
└── SPECIFICATION-MANIFEST.json
```

Responsibilities:

- define the layout of `specs/repo/`;
- define the required layout of `specs/product/`;
- define authoritative, derived, and validation artifacts;
- define schemas and conformance artifacts;
- define functional naming;
- define self-reference and bootstrap;
- define manifest participation;
- define how new specification artifacts are authored.

### `authoritative/development-process/`

Purpose:

Define the non-normative-to-normative development progression.

Expected eventual contents:

```text
development-process/
├── DEVELOPMENT-MODEL.json
├── SCRATCHPAD.json
└── IMPLEMENTATION-PLAN.json
```

Responsibilities:

- define `docs/scratchpad/`;
- define `docs/implementation/`;
- define the progression from uncertain thought to organized planning;
- define when material is ready to generate governed issues;
- define that non-normative artifacts cannot override accepted authority.

### `authoritative/normative-change/`

Purpose:

Define how normative repository artifacts are developed and accepted.

Expected eventual contents:

```text
normative-change/
├── ISSUE.json
├── PATCH.json
├── PULL-REQUEST.json
└── ACCEPTANCE.json
```

Responsibilities:

- define bounded issue scope;
- define patch conformance to issue authority;
- define pull-request review responsibility;
- define the acceptance boundary;
- define required validation evidence;
- prohibit issue-derived permanent artifact names.

The eventual authority may use generic concepts rather than require one hosting
platform:

```text
work item
change set
review proposal
acceptance
```

GitHub issue, patch, and pull request may be the GVE implementation of those
generic concepts.

### `authoritative/level-model/`

Purpose:

Define the fixed product Level model that all initialized repositories use.

Expected eventual contents:

```text
level-model/
├── LEVEL-MODEL.json
├── LEVEL-0-KERNEL.json
├── LEVEL-1-PRIMITIVES.json
├── LEVEL-2-COMPONENTS.json
└── LEVEL-3-ORCHESTRATION.json
```

Fixed meanings:

```text
Level 0 = kernel
Level 1 = primitives
Level 2 = components
Level 3 = orchestration
```

Responsibilities:

- define each Level strictly;
- define allowed and forbidden responsibilities;
- define dependency direction;
- define required Level specification fields;
- define required source correspondence;
- define whether empty Levels are permitted;
- define whether direct dependency skipping is permitted.

The project determines the contents of each Level, not the meaning of the
Levels.

### `authoritative/source-layout/`

Purpose:

Define the required structure of maintained product source without defining a
particular product.

Expected eventual contents:

```text
source-layout/
├── SOURCE-LAYOUT.json
└── SOURCE-LEVEL-MAPPING.json
```

Responsibilities:

- define structural expectations for `src/`;
- define correspondence to Level 0–3;
- define allowed dependency direction;
- define maintained versus generated source;
- define source validation ownership;
- avoid prescribing project-specific modules.

### `authoritative/schemas/`

Purpose:

Contain schemas for repository-specification artifacts.

Initial expected structure:

```text
schemas/
├── manifest/
├── repository-model/
├── specification-system/
├── development-process/
├── normative-change/
├── level-model/
├── source-layout/
└── conformance/
```

Schemas should be introduced alongside the authority they constrain.

Placeholder schemas should not pretend to validate incomplete documents.

### `authoritative/conformance/`

Purpose:

Contain accepted repository conformance artifacts.

Initial expected structure:

```text
conformance/
├── repository-layout/
├── specification-layout/
├── development-process/
├── normative-change/
├── level-model/
└── initialization/
```

During early stand-up, these directories may contain README-style placeholders
only.

Accepted vectors should be added only when their expected meaning is defined by
authority.

## Derived Placeholder Area

Create:

```text
specification-system/repo/derived/markdown/
```

The tree should mirror the eventual authoritative structure:

```text
derived/markdown/
├── repository-model/
├── specification-system/
├── development-process/
├── normative-change/
├── level-model/
└── source-layout/
```

No hand-authored Markdown should silently become authoritative.

Early placeholders may explain the intended projection path, but deterministic
rendering should replace them as soon as the authoring model is defined.

## Validation Placeholder Areas

### `validation/lib/`

Reusable mechanisms anticipated for repository-specification validation:

- strict JSON loading;
- canonical tree hashing;
- schema loading;
- manifest loading;
- reference resolution;
- deterministic projection generation;
- functional-name checks;
- evidence reporting.

### `validation/intrinsic/`

Checks that use only `specification-system/repo/`.

Initial checks:

- directory completeness;
- manifest syntax;
- placeholder status declarations;
- duplicate filenames or identities;
- forbidden historical naming;
- path containment.

Later checks:

- schema conformance;
- semantic relationships;
- reference closure;
- deterministic projections;
- self-reference;
- Level model coherence;
- manifest completeness;
- digest and identity bindings.

### `validation/repository/`

Checks an external repository against repository authority.

Initial target:

- the GVE repository construction environment.

Future target:

- a blank repository initialized with the portable repo-specification subset.

Expected responsibilities:

- required repository trees;
- normative and non-normative placement;
- source and specification layout;
- validation entry points;
- forbidden paths;
- functional naming;
- initialization completeness.

### `validation/tests/`

Tests for the validators and renderers.

Test names should describe invariants.

Examples:

```text
test_repository_model_validation.py
test_specification_layout_validation.py
test_level_model_validation.py
test_functional_naming.py
test_manifest_coverage.py
```

### `validation/fixtures/`

Synthetic invalid inputs used only to test validators.

Initial structure:

```text
fixtures/
├── missing-required-path/
├── invalid-artifact-class/
├── invalid-level-dependency/
├── historical-name/
├── unresolved-reference/
└── stale-projection/
```

These are not accepted conformance vectors.

## Placeholder File Requirements

Every placeholder should contain:

- functional title;
- construction status;
- intended responsibility;
- expected inputs or relationships;
- known unresolved questions;
- explicit statement that it is non-authoritative until accepted;
- no invented normative requirements.

A minimal JSON placeholder may use a temporary construction envelope such as:

```json
{
  "status": "under-construction",
  "identity": "REPOSITORY-MODEL",
  "responsibility": "Define the durable repository tree model.",
  "normative": false,
  "unresolved": []
}
```

This envelope is only a construction device unless separately accepted as part
of the final authoring model.

## Content Development Order

After the skeleton exists, content should be added according to dependency.

### Foundation

First define:

- repository model;
- specification artifact classes;
- self-reference and bootstrap;
- manifest model;
- functional naming.

These concepts determine how every other document is authored and placed.

### Repository development process

Then define:

- scratchpad;
- implementation plan;
- issue;
- patch;
- pull request;
- acceptance.

These define how future normative work is governed.

### Fixed Level model

Then define:

- Level 0 kernel;
- Level 1 primitives;
- Level 2 components;
- Level 3 orchestration;
- Level dependency rules;
- required Level specification structure.

### Product structure contracts

Then define:

- required `specs/product/` layout;
- required `src/` layout;
- project-defined content boundaries;
- product and source validation ownership.

### Conformance and initialization

Then define:

- repository-layout conformance;
- specification-layout conformance;
- blank-repository initialization;
- portable artifact selection;
- dependency-closed copying;
- target manifest creation;
- standalone validation after copying.

This is an authoring order, not permission to combine all work into one issue
or patch.

## Skeleton Completion Criteria

The initial structural stand-up is complete when:

- every intended functional directory exists;
- every expected authority area has a placeholder;
- the root manifest placeholder identifies all expected artifact classes;
- `validate` can detect missing or malformed skeleton elements;
- no placeholder asserts accepted authority;
- no issue- or milestone-derived permanent name exists;
- no placeholder depends on current GVE product implementation;
- the structure clearly separates repository authority, schemas, conformance,
  derived projections, and validation implementation;
- the structure can be reviewed before substantive normative content is added.

## Content Completion Criteria

The repo-specification system is substantively complete only when:

- placeholders have been replaced by authored normative artifacts;
- every normative artifact has a governing schema;
- all references close;
- all required derived projections reproduce;
- conformance artifacts are authority-backed;
- repository validation passes against a minimal initialized repository;
- repository validation passes against the GVE repository;
- the fixed Level model is complete;
- the development and normative-change processes are explicit;
- the tree is self-referential and validates its own layout;
- the complete subtree can be sealed into its parent specification manifest.

## Explicit Non-Goals of the Initial Stand-Up

The initial skeleton should not:

- replace the current `specs/` tree;
- change current GVE product authority;
- change maintained product behavior;
- invent final specification identities;
- invent final schemas merely to make placeholders pass;
- create accepted conformance vectors before requirements exist;
- implement the final digest-sealing model;
- combine structural stand-up with semantic migration;
- claim that empty placeholder directories constitute valid authority.
