# Repository Specification Implementation Plan

## Status

Implementation planning document.

This document is non-normative. It consolidates and supersedes the planning
content previously split between:

```text
docs/implementation/REPOSITORY-SPECIFICATION-STAND-UP-PLAN.md
docs/implementation/REPOSITORY-IDENTITY-IMPLEMENTATION-PLAN.md
```

The accepted GVE normative JSON specification graph remains authoritative.

This plan does not:

- replace the current accepted `specs/` tree;
- make `specification-system/` authoritative;
- redefine the current accepted GVE identity framework;
- authorize runtime behavior changes;
- authorize final manifest sealing or cutover;
- permit broad multi-area implementation in one issue.

The temporary construction root remains:

```text
specification-system/repo/
```

The intended final location remains:

```text
specs/repo/
```

## Objective

Build a complete, self-validating, repository-generic specification system in a
parallel construction tree, then harden and cut it over only after authority,
schemas, conformance, projections, repository validation, identity, bootstrap,
and initialization all close.

The work proceeds through four broad stages:

```text
1. establish complete functional structure
2. replace placeholders with validated construction content
3. harden identity, manifests, projections, conformance, and repository checks
4. accept and cut over the complete subtree
```

The temporary tree must remain explicitly incomplete and non-authoritative until
the final governed cutover.

## Core design principles

### Existing authority remains controlling

During construction:

```text
specs/                       current accepted specification system
specification-system/repo/   replacement repository specifications under construction
```

No construction artifact becomes authoritative merely because it exists,
validates, is reviewed, or is merged.

### Functional names only

Permanent paths and artifact names must describe durable responsibility.

They must not encode:

- issue number;
- milestone;
- implementation phase;
- migration step;
- patch sequence;
- temporary work order.

### Construction and acceptance are separate

Construction artifacts may use temporary functional construction identities and
closed construction envelopes.

They must not claim:

- accepted authority;
- final identity;
- final content digest;
- aggregate revision;
- sealing;
- normative completion.

### Generic mechanisms precede profiles

Cross-cutting mechanisms are defined once.

Domain-specific areas then define profiles against those mechanisms.

For identity:

```text
generic identity mechanism
    |
    v
repository and specification identity profiles
    |
    v
development-process and normative-change profiles
    |
    v
GVE product identity families
```

### Product-independent validation

The repository-specification subtree must not import from maintained GVE product
code.

Its validators must be able to operate independently on:

- the GVE repository;
- a minimal initialized repository;
- a copied portable repository-specification subset.

### One bounded issue at a time

Each issue must have:

- one authority interpretation;
- one bounded artifact inventory;
- one isolated branch;
- exact validation requirements;
- no unrelated cleanup;
- clean accepted-main validation after merge.

## Intended directory shape

```text
specification-system/
`-- repo/
    |-- REPOSITORY-SPECIFICATION-SET.json
    |-- validate
    |-- authoritative/
    |   |-- identity/
    |   |-- repository-model/
    |   |-- specification-system/
    |   |-- development-process/
    |   |-- normative-change/
    |   |-- level-model/
    |   |-- source-layout/
    |   |-- schemas/
    |   `-- conformance/
    |-- derived/
    |   `-- markdown/
    `-- validation/
        |-- lib/
        |-- intrinsic/
        |-- repository/
        |-- tests/
        `-- fixtures/
```

The exact contents of each area are introduced incrementally, but every intended
functional responsibility must eventually be visible in the skeleton.

## Root construction manifest

Create and maintain:

```text
specification-system/repo/REPOSITORY-SPECIFICATION-SET.json
```

During construction, the manifest must:

- identify the temporary repository-specification construction set;
- declare explicit under-construction and non-authoritative status;
- identify the root validation entry point;
- declare the complete currently governed construction inventory;
- declare construction artifact classes;
- reject unknown fields;
- reject malformed paths;
- reject undeclared artifacts that claim participation;
- reject missing declared artifacts;
- omit fabricated final digests, sealing, revisions, and acceptance claims.

The construction manifest is not the final normative manifest model.

Every successor issue that adds an artifact family must update the manifest and
validator atomically.

## Validation entry point

Maintain:

```text
specification-system/repo/validate
```

The entry point evolves from structural validation into the complete deep
repository-specification validation suite.

It must remain:

- repository-local;
- deterministic;
- fail-closed;
- independent from maintained GVE product code;
- visibly separate from accepted normative specification validation until
  cutover;
- integrated into `./scripts/validate` without weakening existing checks.

## Authority areas

## `authoritative/identity/`

Purpose:

Define portable identity mechanics that apply across repository,
specification-system, development-process, normative-change, conformance, and
initialization authority.

Initial intended contents:

```text
identity/
|-- IDENTITY-MODEL.json
|-- CANONICAL-JSON.json
|-- IDENTITY-FAMILY-MODEL.json
`-- IDENTITY-VERIFICATION.json
```

Generic responsibilities:

- identity versus identifier;
- family-qualified identity representation;
- explicit canonicalization versions;
- explicit digest algorithms;
- domain-separated canonical preimages;
- semantic domains;
- own-identity handling;
- reference modes;
- object and aggregate kinds;
- membership, ordering, duplicate, empty, closure, and cycle rules;
- verification contexts;
- governing-revision bindings;
- fail-closed rejection;
- self-reference and circularity constraints.

The generic identity area must not define GVE-specific product families.

These remain product-specific unless separately generalized through accepted
normative work:

```text
gve-plan
gve-contract
gve-governance-composition
gve-effect
gve-production
gve-evidence
gve-execution-record
gve-authoritative-result
gve-finalization
```

## `authoritative/repository-model/`

Purpose:

Define the durable repository model.

Expected contents:

```text
repository-model/
|-- REPOSITORY-MODEL.json
|-- REPOSITORY-TREES.json
`-- REPOSITORY-IDENTITIES.json
```

Responsibilities:

- define normative and non-normative repository areas;
- define `docs/`, `specs/`, `src/`, generated areas, and validation areas;
- define ownership and dependency relationships;
- distinguish repository-generic from product-specific authority;
- define maintained versus generated artifacts;
- define tree membership;
- define path significance;
- define repository identity profiles only after tree semantics exist.

## `authoritative/specification-system/`

Purpose:

Define the rules governing specifications themselves.

Expected contents:

```text
specification-system/
|-- SPECIFICATION-SYSTEM.json
|-- SPECIFICATION-AUTHORING.json
|-- SPECIFICATION-ARTIFACTS.json
|-- SPECIFICATION-MANIFEST.json
`-- SPECIFICATION-IDENTITIES.json
```

Responsibilities:

- define `specs/repo/`;
- define required `specs/product/` structure;
- define authoritative, derived, schema, conformance, fixture, and validation
  artifacts;
- define functional naming;
- define authoring;
- define manifest participation;
- define self-reference and bootstrap;
- define specification document and specification revision identity profiles;
- define projection bindings;
- define sealing participation.

## `authoritative/development-process/`

Purpose:

Define the progression from non-normative exploration to governed work.

Expected contents:

```text
development-process/
|-- DEVELOPMENT-MODEL.json
|-- SCRATCHPAD.json
|-- IMPLEMENTATION-PLAN.json
`-- DEVELOPMENT-IDENTITIES.json
```

Responsibilities:

- define `docs/scratchpad/`;
- define `docs/implementation/`;
- define the progression from uncertain thought to organized planning;
- define readiness for governed issue creation;
- define that non-normative documents cannot override accepted authority;
- distinguish mutable planning artifacts from immutable accepted revisions;
- define development identities only where semantic identity is required.

## `authoritative/normative-change/`

Purpose:

Define how normative repository artifacts are developed and accepted.

Expected contents:

```text
normative-change/
|-- ISSUE.json
|-- PATCH.json
|-- PULL-REQUEST.json
|-- ACCEPTANCE.json
`-- NORMATIVE-CHANGE-IDENTITIES.json
```

Responsibilities:

- bounded issue scope;
- patch conformance;
- review responsibility;
- validation evidence;
- acceptance boundary;
- exact revision binding;
- replay and duplicate rules;
- distinction between portable semantic identity and host-platform identifiers.

Portable concepts may use:

```text
work item
change set
review proposal
acceptance
```

GitHub issue, commit, branch, and pull-request identifiers remain implementation
or evidence identifiers unless an accepted identity family explicitly governs
them.

## `authoritative/level-model/`

Purpose:

Define the fixed Level model.

Expected contents:

```text
level-model/
|-- LEVEL-MODEL.json
|-- LEVEL-0-KERNEL.json
|-- LEVEL-1-PRIMITIVES.json
|-- LEVEL-2-COMPONENTS.json
`-- LEVEL-3-ORCHESTRATION.json
```

Fixed meanings:

```text
Level 0 = kernel
Level 1 = primitives
Level 2 = components
Level 3 = orchestration
```

Responsibilities:

- strict Level meanings;
- allowed and forbidden responsibilities;
- dependency direction;
- required Level fields;
- source correspondence;
- empty-Level policy;
- dependency-skipping policy.

The project determines Level contents, not Level meanings.

## `authoritative/source-layout/`

Purpose:

Define required maintained source structure without defining a particular
product.

Expected contents:

```text
source-layout/
|-- SOURCE-LAYOUT.json
`-- SOURCE-LEVEL-MAPPING.json
```

Responsibilities:

- structural expectations for `src/`;
- correspondence to Levels 0 through 3;
- dependency direction;
- maintained versus generated source;
- validation ownership;
- product-independent layout requirements.

## `authoritative/schemas/`

Purpose:

Contain schemas for repository-specification artifacts.

Expected structure:

```text
schemas/
|-- identity/
|-- manifest/
|-- repository-model/
|-- specification-system/
|-- development-process/
|-- normative-change/
|-- level-model/
|-- source-layout/
`-- conformance/
```

Schemas must be introduced alongside the authority they constrain.

Construction schemas must not pretend to be final normative schemas.

## `authoritative/conformance/`

Purpose:

Contain authority-backed conformance artifacts.

Expected structure:

```text
conformance/
|-- identity/
|-- repository-layout/
|-- specification-layout/
|-- development-process/
|-- normative-change/
|-- level-model/
`-- initialization/
```

Early construction vectors remain non-authoritative.

Accepted vectors become immutable only after their governing semantics are
accepted.

## Derived area

Create:

```text
specification-system/repo/derived/markdown/
```

It should eventually mirror:

```text
identity/
repository-model/
specification-system/
development-process/
normative-change/
level-model/
source-layout/
```

Rules:

- hand-authored Markdown must not silently become authority;
- early README-style construction markers are permitted;
- deterministic rendering replaces hand-authored explanation once authoring
  semantics exist;
- stale projections must fail validation;
- projection identity and source binding must be explicit before hardening.

## Validation architecture

## `validation/lib/`

Reusable mechanisms:

```text
strict_json.py
canonical_json.py
schema_loading.py
manifest_loading.py
reference_resolution.py
identity_family.py
identity_verification.py
tree_hashing.py
projection_generation.py
functional_naming.py
evidence_reporting.py
```

Libraries should be extracted only when behavior is stable enough to justify
reuse.

Do not perform broad refactoring merely to create the directory.

## `validation/intrinsic/`

Checks using only `specification-system/repo/`.

Initial checks:

- directory completeness;
- manifest syntax;
- construction status;
- exact fields;
- duplicate functional identities;
- forbidden historical naming;
- path containment;
- no symlink escape;
- no maintained-product imports.

Later checks:

- schema conformance;
- semantic relationships;
- reference closure;
- identity-family uniqueness;
- domain-prefix uniqueness;
- canonicalization;
- aggregate semantics;
- deterministic projections;
- self-reference;
- Level coherence;
- manifest completeness;
- digest and identity bindings;
- sealing readiness.

## `validation/repository/`

Checks an external repository against repository authority.

Targets:

- the GVE repository;
- a minimal initialized repository;
- a repository receiving a copied portable specification subset.

Responsibilities:

- required trees;
- normative and non-normative placement;
- source and specification layout;
- validation entry points;
- forbidden paths;
- functional naming;
- identity profiles;
- manifest membership;
- initialization completeness;
- standalone validation.

## `validation/tests/`

Tests must describe invariants.

Expected families include:

```text
test_repository_model_validation.py
test_specification_layout_validation.py
test_identity_construction.py
test_canonical_json.py
test_identity_family.py
test_identity_references.py
test_identity_aggregates.py
test_identity_verification.py
test_level_model_validation.py
test_functional_naming.py
test_manifest_coverage.py
test_projection_freshness.py
test_initialization.py
```

## `validation/fixtures/`

Synthetic invalid inputs used only to test validators.

Expected structure:

```text
fixtures/
|-- identity/
|-- missing-required-path/
|-- invalid-artifact-class/
|-- invalid-level-dependency/
|-- historical-name/
|-- unresolved-reference/
`-- stale-projection/
```

Fixtures are not accepted conformance vectors.

## Construction placeholder requirements

Every placeholder must contain:

- functional construction identity;
- construction status;
- intended responsibility;
- expected inputs or relationships;
- unresolved questions;
- explicit non-authoritative status;
- no invented normative requirements.

A temporary construction envelope may be used, but it remains a construction
device until separately accepted.

## Identity architecture

## Generic identity kernel

The generic identity kernel defines how identities work.

It must remain:

- path-independent unless a family explicitly chooses path inputs;
- repository-neutral;
- product-neutral;
- independent from GVE runtime code;
- domain-separated;
- versioned;
- deterministic;
- fail-closed.

Initial artifacts:

```text
IDENTITY-MODEL.json
CANONICAL-JSON.json
IDENTITY-FAMILY-MODEL.json
IDENTITY-VERIFICATION.json
```

## Identity profiles

Profiles define which families exist for a domain.

### Specification profile

Expected candidate identities:

- specification document;
- specification-set revision;
- manifest;
- schema;
- projection;
- conformance artifact;
- validation artifact;
- sealed specification set.

### Repository profile

Expected candidate identities:

- repository area;
- repository tree;
- repository-layout revision;
- maintained-artifact inventory;
- repository-conformance result.

These must not be defined before path and tree semantics are settled.

### Development profile

Expected candidate identities:

- candidate plan;
- accepted plan;
- immutable planning revision;
- provenance and attribution bindings.

### Normative-change profile

Expected candidate identities:

- work item;
- change set;
- review proposal;
- validation evidence;
- acceptance.

GVE product families remain under product authority.

## Identity bootstrap

Identity, manifests, and self-reference create a potential cycle.

Use staged bootstrap.

### Construction stage

Use only temporary functional construction identities.

Do not treat them as final cryptographic identities.

### Candidate identity stage

Permit candidate family declarations and test vectors.

Do not add them to accepted specification-set membership.

### Specification identity stage

Define specification document and specification revision profiles against the
generic kernel.

### Manifest stage

Define direct member identity participation and explicit self-reference
handling.

Required decisions:

- whether the manifest is a member of its own aggregate;
- own-identity omission or canonical-reference behavior;
- ordered versus unordered membership;
- duplicate rejection;
- schema, vector, projection, and validator participation;
- governing revision derivation.

### Acceptance stage

Only after all authority, schemas, vectors, projections, and validators close may
the tree receive accepted identities and aggregate revisions.

### Cutover stage

Final sealing occurs as a separate governed hardening and cutover effort.

## Content development order

The authoritative implementation order is:

```text
1. construction foundation
2. complete functional skeleton
3. generic identity construction skeleton
4. generic identity semantic model
5. minimal repository vocabulary
6. specification artifact classes
7. reusable validation mechanisms
8. specification identity profile
9. self-reference and bootstrap
10. manifest and revision model
11. repository model and repository identity profile
12. development-process authority
13. normative-change authority
14. fixed Level model
15. source-layout contracts
16. conformance
17. derived projection hardening
18. repository validation
19. initialization and portable copying
20. hardening, acceptance, and cutover
```

This order refines the earlier stand-up sequence by making the generic identity
kernel explicit before identity-dependent manifest and sealing work.

## Implementation phases

## Phase 0 — Construction foundation

Status: established.

Current responsibilities:

- temporary manifest;
- executable validation entry point;
- representative repository-model placeholder;
- representative specification-artifact placeholder;
- structural validator;
- permanent structural tests;
- complete-gate integration;
- no normative authority claim.

## Phase 1 — Planning integrity and complete skeleton

Goals:

- reconcile all planning documents into this plan;
- correct encoding defects;
- create every intended functional directory;
- create one functional placeholder for every expected authority area;
- extend the manifest to cover the complete skeleton;
- extend structural validation for complete directory and placeholder coverage;
- preserve non-authoritative status.

Do not add substantive semantics in this phase.

## Phase 2 — Generic identity construction skeleton

Create:

```text
authoritative/identity/
|-- IDENTITY-MODEL.json
|-- CANONICAL-JSON.json
|-- IDENTITY-FAMILY-MODEL.json
`-- IDENTITY-VERIFICATION.json

authoritative/schemas/identity/
derived/markdown/identity/
validation/fixtures/identity/
validation/intrinsic/validate_identity_construction.py
validation/tests/test_identity_construction.py
```

Requirements:

- all artifacts remain under construction;
- all artifacts remain non-normative;
- root manifest coverage is atomic;
- exact closed fields;
- unique construction identities;
- no final digests;
- no sealing;
- no product families;
- no runtime imports.

## Phase 3 — Generic identity semantic model

Define:

- identity representation;
- canonical JSON;
- digest declarations;
- domain separation;
- family structure;
- own-identity handling;
- reference semantics;
- object and aggregate semantics;
- verification context;
- governing-revision binding;
- fail-closed conditions.

Requirements:

- map accepted GVE behavior where portable;
- distinguish copied accepted behavior from new repository-generic decisions;
- preserve unresolved questions;
- do not alter accepted GVE families.

## Phase 4 — Reusable validation library

Create reusable strict JSON, canonicalization, identity, reference, aggregate,
and evidence mechanisms.

Requirements:

- no imports from `src/gve`;
- behavior-preserving extraction;
- focused tests;
- deterministic diagnostics;
- no broad unrelated refactoring.

## Phase 5 — Generic identity construction conformance

Add positive and negative construction vectors for:

- canonical JSON;
- domain separation;
- family definitions;
- own-identity behavior;
- reference modes;
- ordered aggregates;
- unordered aggregates;
- duplicate rejection;
- empty aggregates;
- direct closure;
- verification context;
- family conflicts;
- unaccepted identities;
- self-reference;
- cycles.

These are still construction vectors.

## Phase 6 — Minimal repository vocabulary

Define the minimum repository model needed by later profiles:

- repository areas;
- authority classification;
- maintained/generated distinction;
- tree membership vocabulary;
- ownership;
- dependency direction;
- path normalization.

Do not yet define final repository identities.

## Phase 7 — Specification artifact classes

Define:

- authoritative artifact;
- derived artifact;
- schema;
- conformance artifact;
- validation implementation;
- fixture;
- manifest participant;
- projection relationship;
- authoring relationship.

This phase is a prerequisite for the specification identity profile.

## Phase 8 — Specification identity profile

Create:

```text
authoritative/specification-system/SPECIFICATION-IDENTITIES.json
```

Define candidate identity families for specification artifacts and aggregate
revisions.

Resolve:

- direct membership;
- ordering;
- duplicates;
- schema binding;
- projection binding;
- conformance binding;
- governing revision;
- verification context.

## Phase 9 — Self-reference and bootstrap

Resolve:

- manifest self-participation;
- identity-definition self-identification;
- own-identity omission;
- canonical references;
- external sealing envelopes;
- bootstrap ordering;
- circularity rejection.

Add negative tests for every prohibited cycle.

## Phase 10 — Manifest and revision model

Define the final candidate manifest model.

Requirements:

- complete inventory;
- exact classes;
- identity participation;
- revision derivation;
- schema binding;
- projection binding;
- vector binding;
- validator binding;
- duplicate rejection;
- stale member rejection;
- incomplete membership rejection.

## Phase 11 — Repository model and identity profile

Complete:

```text
REPOSITORY-MODEL.json
REPOSITORY-TREES.json
REPOSITORY-IDENTITIES.json
```

Resolve:

- path significance;
- ordering;
- direct versus transitive closure;
- maintained/generated treatment;
- symlinks;
- repository copy semantics;
- tree identity;
- layout revision identity.

## Phase 12 — Development-process authority

Define scratchpad, implementation plan, progression, readiness, provenance, and
development identities where required.

## Phase 13 — Normative-change authority

Define work items, change sets, review proposals, acceptance, validation
evidence, exact revision binding, replay rules, and portable identity profiles.

## Phase 14 — Fixed Level model

Define Level 0 through Level 3 and all dependency and source correspondence
rules.

## Phase 15 — Source-layout contracts

Define maintained source structure, Level mapping, generated source treatment,
and source validation ownership.

## Phase 16 — Schemas and conformance hardening

Replace construction schemas and vectors with final candidate schemas and
authority-backed conformance artifacts.

Freeze vectors only at acceptance.

## Phase 17 — Derived projection hardening

Implement deterministic projection generation.

Validate:

- source binding;
- projection identity;
- freshness;
- reproducibility;
- no hand-authored authority drift.

## Phase 18 — Repository validation

Validate:

- GVE repository;
- minimal initialized repository;
- portable copied subset;
- repository trees;
- specification layout;
- identity profiles;
- manifests;
- source layout;
- Levels;
- conformance;
- projections.

## Phase 19 — Initialization and copying

Define:

- blank-repository initialization;
- portable artifact selection;
- dependency-closed copying;
- target manifest creation;
- target-bound identities;
- source-bound identities;
- preserved identities;
- recomputed identities;
- standalone validation.

## Phase 20 — Hardening and acceptance

Before acceptance:

- close all references;
- replace temporary envelopes;
- freeze accepted vectors;
- remove construction exceptions;
- verify deterministic projections;
- verify every identity recomputes;
- verify no product-specific authority leaked into generic repo authority;
- validate GVE and minimal initialized repositories;
- validate clean accepted-main;
- seal the subtree into its parent manifest.

## Phase 21 — Cutover

At cutover:

- the complete repository-specification subtree becomes accepted authority;
- temporary construction status is removed;
- final schemas govern all normative artifacts;
- manifests and aggregate revisions become authoritative;
- projections become reproducible derived artifacts;
- conformance vectors become immutable;
- repository validation becomes the accepted validation path;
- the old authority is replaced only through explicit governed acceptance.

## Identity validation requirements

Identity validation should eventually emit structured evidence containing:

- family;
- semantic domain;
- canonicalization version;
- digest algorithm;
- domain prefix identifier;
- canonical input classification;
- supplied identity;
- computed identity;
- verification mode;
- verification-context summary;
- aggregate membership summary;
- governing revision;
- deterministic diagnostic code;
- pass/fail status.

Large or sensitive canonical values should not be emitted by default.

## Hardening principles

### One source for generic mechanics

Canonicalization, family structure, reference modes, aggregate rules, and
verification context are defined once under identity authority.

Profiles reference them.

### No product leakage

Portable repository authority must not depend on GVE operation types, runtime
modules, or GVE-specific family names.

### No implicit identity behavior

Every family declares:

- what is identified;
- what is omitted;
- what is referenced;
- how references are encoded;
- whether order matters;
- what closure means;
- what verification context is required.

### No raw-digest fallback

A raw digest is not silently treated as a semantic identity.

Missing or unknown family is an error.

### No automatic path significance

Paths are identity inputs only when explicitly declared.

### No automatic transitive closure

Aggregate closure is direct unless a family explicitly defines transitive
closure and cycle handling.

### No circular acceptance

Construction identity, candidate identity, accepted identity, aggregate
revision, and sealing identity remain distinct stages.

## Issue sequencing

Recommended issue order:

1. reconcile plan and complete directory skeleton;
2. establish generic identity construction skeleton;
3. define canonical JSON construction model;
4. define identity-family construction model;
5. define verification and aggregate construction model;
6. create reusable validation library;
7. add generic identity construction vectors;
8. define minimal repository vocabulary;
9. define specification artifact classes;
10. define specification identity profile;
11. define self-reference and bootstrap;
12. define manifest and revision model;
13. complete repository model;
14. define repository identity profile;
15. define development-process authority;
16. define normative-change authority;
17. define fixed Level model;
18. define source layout;
19. harden schemas and conformance;
20. implement deterministic projections;
21. implement repository validation;
22. define initialization and copying;
23. perform hardening and acceptance;
24. perform final cutover.

A single issue must not combine multiple independent authority families merely
because they appear in the same phase.

## Skeleton completion criteria

The structural skeleton is complete when:

- every intended functional directory exists;
- every authority area has a placeholder;
- the manifest declares every construction artifact class;
- validation detects missing or malformed skeleton elements;
- no placeholder asserts accepted authority;
- no work-derived permanent name exists;
- no placeholder depends on maintained GVE product code;
- authority, schemas, conformance, projections, and validation are visibly
  separated;
- the structure is reviewable before substantive content is added.

## Identity construction completion criteria

Generic identity construction is complete when:

- all four generic identity artifacts exist;
- canonicalization is explicit;
- domain separation is explicit;
- family structure is complete;
- own-identity handling is explicit;
- reference modes are complete;
- aggregate rules are complete;
- verification context is complete;
- all generic construction vectors pass;
- all references close;
- generic validators are product-independent;
- no GVE-specific family is represented as generic authority.

## Content completion criteria

The repository-specification system is substantively complete when:

- placeholders are replaced by authored candidate normative artifacts;
- every candidate normative artifact has a schema;
- all references close;
- all derived projections reproduce;
- all identity profiles derive from generic identity authority;
- conformance is authority-backed;
- repository validation passes against GVE;
- repository validation passes against a minimal initialized repository;
- the fixed Level model is complete;
- development and normative-change processes are explicit;
- initialization and portable copying are explicit;
- the tree validates its own structure;
- the subtree can be sealed into its parent manifest.

## Acceptance criteria

The repository-specification system may be accepted only when:

- all construction exceptions are removed;
- final schemas govern all normative artifacts;
- accepted vectors are frozen;
- identities and revisions recompute;
- projections reproduce;
- reference closure passes;
- repository validation passes on all required targets;
- initialization produces a standalone-valid target;
- no product-specific semantics leak into portable authority;
- the exact final revision passes complete validation;
- clean accepted-main validation passes after merge;
- cutover is separately authorized.

## Explicit non-goals

This plan does not authorize:

- changing current accepted GVE identity semantics;
- migrating existing GVE identities without separate authority;
- adding new GVE product identity families;
- treating temporary construction artifacts as normative;
- making Git or GitHub identifiers portable semantic identities;
- making every repository path identity-bearing;
- using hand-authored Markdown as authority;
- broad validator refactoring without bounded need;
- combining construction and cutover;
- weakening existing accepted validation.
