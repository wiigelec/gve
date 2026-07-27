# Specification System Structure

## Status

This document describes the intended structure and contents of the `specs/`
subtree.

It is descriptive and non-authoritative. Accepted GVE specifications, schemas,
manifests, conformance artifacts, and validation rules remain authoritative
until separately governed changes replace them.

## Purpose of `specs/`

The `specs/` subtree is a standalone specification system.

It defines:

- the rules governing the repository;
- the rules governing the maintained product;
- the identities and relationships of specification artifacts;
- the accepted conformance evidence used to evaluate implementations;
- the rules for authoring, organizing, deriving, and validating specifications.

The specification system is intended to exist and validate coherently before
substantial maintained-product implementation begins.

Its intrinsic validation must be self-contained within `specs/`.

The repository validation entry point calls the specification validation entry
point as one part of the complete repository gate.

## Top-Level Structure

The top level of `specs/` contains only the specification-set manifest, the
specification validation entry point, and three functional directories:

```text
specs/
├── GVE-SPECIFICATION-SET.json
├── validate
├── authoritative/
├── derived/
└── validation/
```

No other durable top-level directory is permitted.

All durable paths and filenames are identified by functional responsibility,
authority, domain, or artifact class. They are not named for issues, pull
requests, milestones, implementation phases, migrations, or historical
development sequence.

## `GVE-SPECIFICATION-SET.json`

`GVE-SPECIFICATION-SET.json` is the root manifest for the complete
specification system.

It identifies and binds the artifacts that make up an accepted specification
revision.

The manifest records, as applicable:

- stable artifact identity;
- artifact class;
- functional role;
- repository-relative path;
- governing schema;
- authority relationships;
- deterministic projection relationships;
- conformance relationships;
- canonicalization rules;
- digest algorithms;
- exact content digests.

The manifest does not make validation implementation authoritative merely by
listing or invoking it.

The manifest is the single discovery entry point for accepted specification
authority.

## `validate`

`specs/validate` is the public validation entry point for the specification
system.

It must be executable from the repository and must support intrinsic
specification validation without importing maintained-product implementation
code.

Its responsibilities include:

- validating the specification-set manifest;
- validating authoritative artifacts against their schemas;
- validating semantic relationships and references;
- validating identity and digest bindings;
- validating deterministic derived artifacts;
- validating authoritative conformance artifacts;
- running validator tests required for specification-system confidence.

Repository-target or maintained-product conformance checks may be exposed
through explicit validation modes, but they remain distinct from intrinsic
specification validity.

The repository-level validation script calls `specs/validate` rather than
reimplementing specification validation.

## `authoritative/`

`authoritative/` contains every artifact whose accepted content directly
defines or constrains repository rules, maintained-product behavior,
specification identity, artifact structure, or conformance expectations.

Changing authoritative bytes is presumed to change accepted authority unless
the change is proven to be a path-only or representation-preserving
realignment under separately governed work.

Proposed structure:

```text
authoritative/
├── repository/
├── product/
├── shared/
├── schemas/
└── conformance/
```

### `authoritative/repository/`

Contains specifications governing the repository as a governed product
workspace.

Expected responsibilities include:

- specification-system structure and authoring;
- repository source layout;
- package and module ownership;
- dependency direction;
- artifact placement;
- required validation boundaries;
- repository artifact classification;
- repository conformance obligations.

A specification-system authority belongs here. It defines what may appear
under `specs/`, how artifacts are classified, how they are authored, and how
the specification system validates itself.

### `authoritative/product/`

Contains specifications governing maintained-product behavior.

Expected structure:

```text
product/
└── levels/
    ├── level-0/
    ├── level-1/
    ├── level-2/
    └── level-3/
```

Level and Stage names are permitted only when they are accepted functional
product concepts.

Product specifications define behavior, identities, authority boundaries,
evidence, lifecycle rules, result contracts, plugin contracts, and other
maintained-product semantics.

### `authoritative/shared/`

Contains foundational authority used by both repository and product
specifications.

Expected responsibilities include:

- canonicalization;
- identity frameworks;
- specification revision identity;
- document authority;
- reference semantics;
- shared artifact classification rules.

Shared authority is not owned solely by one product level or one repository
target.

### `authoritative/schemas/`

Contains schemas that constrain authoritative documents and authoritative
conformance artifacts.

Schemas are authoritative artifacts.

They may be grouped by functional owner:

```text
schemas/
├── manifest/
├── repository/
├── product/
├── shared/
└── conformance/
```

Schema validation is necessary but does not replace semantic validation.

### `authoritative/conformance/`

Contains accepted vectors, fixtures, manifests, and exact-byte artifacts that
define conformance expectations.

Artifacts are grouped by durable function, such as:

```text
conformance/
├── identity/
├── repository/
└── product/
    ├── canonical-input/
    ├── invalid-input/
    ├── processing-failure/
    └── authoritative-results/
```

This directory does not contain issue-number or milestone-number namespaces.

Authoritative conformance artifacts are distinct from malformed or synthetic
fixtures used only to test validators.

## `derived/`

`derived/` contains deterministic, non-authoritative products generated from
authoritative artifacts.

Proposed structure:

```text
derived/
├── markdown/
├── indexes/
└── reports/
```

Initially, committed Markdown projections may be the primary derived content.

Derived artifacts:

- cannot introduce or override authority;
- must be reproducible from authoritative inputs;
- must not be used to resolve conflicts in authoritative content;
- must fail validation when missing, stale, or non-deterministic where they
  are required;
- should mirror authoritative source paths where practical.

Example:

```text
authoritative/product/levels/level-2/GVE-LEVEL-2.json
derived/markdown/product/levels/level-2/GVE-LEVEL-2.md
```

Generated indexes or reports may summarize the specification system, but they
remain non-authoritative.

## `validation/`

`validation/` contains the executable support used to validate, render,
inspect, and exercise the specification system.

Validation code proves or evaluates authority. It does not define authority
through implementation behavior.

Proposed structure:

```text
validation/
├── lib/
├── intrinsic/
├── targets/
├── runners/
├── tests/
└── fixtures/
```

### `validation/lib/`

Contains reusable validation mechanisms, including:

- strict JSON loading;
- canonical JSON processing;
- digest construction;
- specification revision construction;
- schema loading;
- reference resolution;
- deterministic rendering;
- evidence formatting.

### `validation/intrinsic/`

Contains checks that require only the `specs/` subtree.

Expected responsibilities include:

- manifest validation;
- authoritative membership validation;
- schema validation;
- hierarchy and relationship validation;
- identity validation;
- reference closure;
- derived artifact validation;
- authoritative conformance artifact integrity;
- duplicate and undeclared authority rejection.

Intrinsic validation must not import maintained-product code.

### `validation/targets/`

Contains adapters that evaluate external targets against accepted
specifications.

Potential targets include:

- the repository tree;
- repository source layout;
- the maintained source tree;
- an installed product;
- command-line process behavior.

Target adapters read rules and expected evidence from authoritative artifacts.
They do not embed replacement semantics.

### `validation/runners/`

Contains purpose-built executables used to exercise target behavior.

Examples include maintained-product subprocess runners required to reach
closed conformance-only boundaries.

Runners are validation mechanisms, not normative behavior definitions.

### `validation/tests/`

Contains permanent tests for validators, renderers, target adapters, and
runners.

Test modules and methods are named by the invariant they prove.

They are not named after the issue, pull request, milestone, or implementation
phase that introduced them.

### `validation/fixtures/`

Contains synthetic, malformed, incomplete, or adversarial artifacts used only
to test validation behavior.

These fixtures are non-authoritative.

They are grouped by the validation condition they exercise, such as:

```text
fixtures/
├── malformed-manifests/
├── invalid-hierarchies/
├── invalid-identities/
├── invalid-source-layouts/
└── stale-projections/
```

Accepted vectors and exact-byte product fixtures do not belong here; they
belong under `authoritative/conformance/`.

## Dependency Direction

The specification system follows these dependency boundaries:

```text
authoritative  → no dependency on derived or validation
derived        → authoritative
validation     → authoritative and derived
repository     → authoritative repository rules
product        → authoritative product rules
```

Additional constraints:

- authoritative artifacts do not import or depend on validation code;
- derived artifacts do not define authority;
- intrinsic validation does not import maintained-product implementation;
- target validation interacts with the repository or product only through
  explicit adapters or runners;
- maintained-product code does not import specification validation code;
- tests do not become authoritative merely because validation depends on
  them.

## Naming and Ownership

Every durable artifact is named for what it does or governs.

Permitted naming sources include:

- functional responsibility;
- authority domain;
- product concept;
- repository concept;
- artifact class;
- stable conformance behavior.

Durable names must not derive from:

- issue numbers;
- pull-request numbers;
- milestones;
- implementation phases;
- migration sequence;
- temporary development state;
- historical chronology.

Historical identifiers remain appropriate in issue trackers, commit history,
pull requests, and release records, but not in permanent repository paths,
module names, test names, fixture namespaces, schema names, or stable
specification identifiers.

## Authority Boundary

Only artifacts under `authoritative/`, together with the root manifest that
binds them, define accepted specification authority.

Artifacts under `derived/` are reproducible views.

Artifacts under `validation/` are executable proof and evaluation mechanisms.

When these disagree:

1. accepted authoritative content governs;
2. derived content must be regenerated;
3. validation behavior must be corrected;
4. maintained-product behavior must be corrected unless a separately governed
   authority change is accepted.

## Self-Governance

The specification system includes an authoritative specification governing:

- the `specs/` directory structure;
- artifact classes;
- naming;
- ownership;
- authoring structure;
- manifest participation;
- schemas;
- projections;
- conformance artifacts;
- validation boundaries;
- dependency direction.

That specification must comply with the rules it defines and must be included
in the specification-set manifest.

A minimal bootstrap remains necessary to locate:

- `specs/GVE-SPECIFICATION-SET.json`;
- `specs/validate`;
- the authoritative specification-system document.

All other accepted artifacts should be discoverable through the manifest.
