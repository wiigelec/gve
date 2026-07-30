# Repository Framework Construction Plan

## Status

Implementation planning document.

This document defines the construction sequence for moving the current
`specification-system/` construction state toward the repository framework
described by `docs/overview/PRODUCT-OVERVIEW.md`.

This document is non-normative.

It does not:

- replace accepted normative specifications;
- authorize repository mutations;
- assign final product or repository names;
- declare any construction artifact accepted;
- make the current `specification-system/` tree authoritative;
- authorize removal of the historical executor;
- authorize migration of historical GVE product semantics;
- authorize final identity assignment, sealing, acceptance, or cutover;
- permit multiple independently governable boundaries to be combined merely
  because they appear in the same phase.

Every repository mutation requires its own bounded governing issue, accepted
authority interpretation, exact artifact inventory, isolated Git branch,
validation requirements, and completion evidence.

## Purpose

The current `specification-system/` tree contains useful repository-generic
construction foundations, but it was developed before the product direction was
redefined.

The intended product is now a reusable, Git-native repository framework and
template for moving a high-level idea through:

```text
overview → plan → specifications → product artifacts
```

The framework is designed for collaboration between human maintainers and AI
chatbots. It must preserve durable repository context, support independent
session recovery, define Git-compatible development workflows, and provide a
fixed Level 0 through Level 3 format for product specifications.

The construction plan must therefore preserve reusable generic work while
reordering future construction around the actual framework lifecycle.

## Controlling direction

The product overview establishes these durable goals:

- a reusable repository framework and template;
- Git-native development and exact revision evidence;
- human and AI chatbot collaboration;
- repository-first continuity across independent sessions;
- explicit separation among overview, planning, specifications, product
  artifacts, validation, review, acceptance, merge, release, and maintenance;
- a fixed four-Level product specification template;
- repository-generic behavior separated from hosting-platform profiles;
- future derivation of GVE as a separate product;
- bounded governed transition from the repository's historical direction.

The fixed product specification Levels are:

```text
Level 0 — kernel
Level 1 — primitives
Level 2 — components
Level 3 — orchestrations
```

The framework defines this Level format. The framework repository is not
required to instantiate product-specific Level 0 through Level 3 documents.
Repositories initialized from the framework use the Level format for their
normative product specifications.

## Construction principles

### Existing accepted authority remains controlling

The overview records product direction but is non-normative.

Accepted normative specifications remain controlling until they are explicitly
revised, superseded, retired, or separated through bounded governed work.

The construction tree remains:

```text
specification-system/repo/
```

until a separately governed acceptance and cutover process establishes a final
location and authority role.

### Preserve accepted construction history

The transition must not pretend that earlier work never existed.

Every current construction artifact must be classified as one of:

- retained;
- retained and extended;
- redesigned in place;
- deferred;
- separated into a future product;
- superseded;
- removed only after replacement and acceptance.

### Keep generic mechanics separate from product semantics

Repository-generic behavior must not depend on:

- GVE operation payloads;
- GVE effects;
- GVE execution records;
- GVE authoritative result contracts;
- GVE runtime finalization;
- maintained GVE product code;
- one programming language;
- one build system;
- one hosting provider;
- prior chatbot conversation memory.

### Git-native but platform-separated

The core framework may depend on Git-compatible concepts such as:

- repositories;
- commits;
- trees;
- refs;
- branches;
- tags;
- merge bases;
- ancestry;
- diffs;
- staged, unstaged, untracked, and conflicted state;
- exact-revision validation;
- merge-based integration.

Issues, pull requests, review APIs, labels, branch protection, CI APIs, merge
queues, and release APIs belong to hosting-platform profiles.

GitHub may be the first supported profile.

### Repository-first continuity

Essential development state must be recoverable from durable repository,
Git-compatible, and hosting-platform records.

A chatbot must not require prior conversation history to determine:

- product purpose;
- authority roots;
- active plans;
- governing work;
- accepted base;
- current branch and revision;
- exact mutation boundary;
- validation requirements;
- unresolved questions;
- successor boundaries.

### One bounded issue at a time

Every issue must define:

- one authority interpretation;
- one dependency boundary;
- one bounded artifact inventory;
- exact exclusions;
- exact validation;
- no unrelated cleanup;
- clean accepted-main validation after merge.

### Schemas follow semantics

Schemas, fixtures, validators, and conformance artifacts must not invent
unsettled semantic decisions.

A semantic construction boundary must be sufficiently closed before its schema
and validator are treated as durable.

### Construction and acceptance remain distinct

Construction artifacts may be complete enough to validate without being
normative, accepted, sealed, or cut over.

No construction issue may silently assign:

- final semantic identities;
- final aggregate revisions;
- final manifest participation;
- accepted authority;
- sealing;
- release status;
- cutover status.

## Current construction baseline

The current construction set already contains substantive work in:

- repository-neutral path and area vocabulary;
- authority and lifecycle classification;
- containment, ownership, and dependency relationships;
- canonical JSON construction;
- semantic identity construction;
- identity-family declarations;
- reference and aggregate behavior;
- identity verification;
- reusable validation mechanisms;
- generic identity construction conformance;
- specification artifact classes;
- schemas, fixtures, validators, and construction manifest coverage.

The current construction set contains placeholders for:

- development-process authority;
- normative-change authority;
- Level-model authority;
- source-layout authority;
- repository validation;
- general schema and fixture boundaries.

The current construction set does not yet substantively define:

- overview artifacts;
- implementation-plan artifacts;
- framework, template, instance, and product boundaries;
- product artifact roles;
- Git semantics;
- hosting-platform profile mechanics;
- AI-session continuity;
- template initialization;
- release and maintenance;
- framework-to-product derivation.

## Baseline disposition

### Retain as foundational construction

Retain the current generic mechanics for:

- canonical JSON;
- generic semantic identity;
- identity-family declarations;
- identity verification;
- repository path normalization;
- authority and lifecycle classifications;
- containment, ownership, and dependency direction;
- specification artifact classes;
- schema, conformance, validator, fixture, and projection relationships;
- construction manifests;
- repository-local fail-closed validation;
- product-independent validation library behavior.

### Retain but pause further expansion

Pause immediate construction of the specification identity profile.

The profile must not be defined until the revised artifact model determines:

- which framework artifacts require semantic identities;
- which use Git object identities;
- which require both;
- how overview and plan revisions are represented;
- how template versions and instances are represented;
- how release identities are represented;
- how governing revisions interact with bootstrap and manifests.

### Retain and redesign

Retain the current paths but replace placeholder semantics for:

```text
authoritative/development-process/DEVELOPMENT-PROCESS.json
authoritative/normative-change/NORMATIVE-CHANGE.json
authoritative/level-model/LEVEL-MODEL.json
authoritative/source-layout/SOURCE-LAYOUT.json
validation/repository/REPOSITORY-VALIDATION.json
```

### Separate into future GVE product authority

Historical concepts centered on:

- governed runtime operations;
- effects;
- execution records;
- authoritative results;
- runtime finalization;
- GVE-specific product identity families;

must not define the reusable framework.

They may remain temporarily as bootstrap implementation infrastructure and may
later be developed as a separate product instantiated from the framework.

## Intended framework structure

The exact final layout remains separately governed, but the construction model
must eventually support functional areas equivalent to:

```text
docs/
    overview/
    implementation/

specification-system/
    repo/

specs/
    levels/
        level-0/
        level-1/
        level-2/
        level-3/

src/
tests/
schemas/
conformance/
generated/
scripts/
```

The framework repository defines the contracts for this structure.

An initialized product repository contains product-specific overview, plan,
Level specifications, and product artifacts.

## Durable dependency order

The revised durable dependency order is:

```text
1. transition baseline and construction-plan replacement
2. framework, template, instance, and product boundaries
3. development artifact roles
4. repository functional-area model
5. fixed Level 0–3 specification model
6. product artifact roles
7. Git repository and revision model
8. AI-session continuity model
9. generic governed-development model
10. normative-change and acceptance model
11. source correspondence and implementation ownership
12. hosting-platform profile mechanism
13. GitHub hosting profile
14. framework validation architecture
15. template initialization and derivation
16. release and maintenance model
17. identity-profile reassessment
18. manifest and revision model
19. schema and conformance hardening
20. derived projection hardening
21. complete repository validation
22. portable instance validation
23. framework hardening and acceptance
24. framework cutover
25. separate GVE derivation
```

This sequence is a dependency model, not standing authorization.

Repository audits determine whether each boundary is complete and whether the
next incomplete boundary is ready for one bounded governed issue.

## Construction phases

## Phase 0 — Transition baseline

### Objective

Replace the previous construction trajectory with this overview-aligned plan
without changing construction authority or implementation in the same issue.

### Required work

- record the accepted overview as the source of product direction;
- inventory the current `specification-system/` construction state;
- classify all current construction artifacts;
- preserve accepted history;
- pause the previous dependency sequence;
- identify retained generic foundations;
- identify placeholders requiring redesign;
- identify historical GVE product semantics for later separation;
- establish the revised dependency order;
- define transition validation and successor gates.

### Completion criteria

- this plan is present and discoverable;
- the previous plan is explicitly superseded as the active construction plan;
- no normative JSON is changed in the same issue;
- no executor behavior is changed;
- no current construction artifact is removed;
- the complete repository validation gate passes;
- clean accepted-main validation passes after merge.

## Phase 1 — Framework, template, instance, and product boundaries

### Objective

Define the durable object model for the reusable framework and repositories
created from it.

### Required distinctions

- framework source repository;
- distributable repository template;
- initialized product repository;
- product-specific overview;
- product-specific implementation plan;
- product Level specifications;
- product artifacts;
- framework version or revision;
- template provenance;
- instance-local customization;
- future framework update;
- future product derivation.

### Required decisions

- whether the framework source and distributable template are identical;
- which artifacts are copied, generated, selected, or omitted;
- whether template provenance is preserved;
- whether initialized repositories can consume later framework improvements;
- how product-specific profiles are selected;
- how framework and product authority remain separate.

### Exclusions

Do not yet define:

- Git transport mechanics;
- final identities;
- final manifests;
- hosting-platform APIs;
- GVE-specific product behavior.

### Completion criteria

- closed framework/template/instance/product vocabulary;
- no GVE-specific product semantics;
- schema and validator coverage;
- positive and negative fixtures;
- manifest coverage;
- complete repository validation.

## Phase 2 — Development artifact roles

### Objective

Define the non-normative development artifacts that precede product authority.

### Required artifact roles

- product overview;
- implementation plan;
- scratchpad or exploratory record where supported;
- decision record where required;
- governing issue or work-item record;
- detailed scope;
- patch plan;
- unresolved-question record;
- validation evidence reference;
- review evidence reference.

### Overview model

The overview model must define:

- directional and non-normative status;
- intended users and outcomes;
- constraints and non-goals;
- major capabilities;
- success conditions;
- unresolved questions;
- relationship to plans;
- supersession and active-overview discovery;
- prohibition against overriding accepted specifications.

### Plan model

The plan model must define:

- non-normative status;
- work areas;
- dependency order;
- construction phases;
- transition criteria;
- expected artifact families;
- validation strategy;
- risks;
- unresolved design decisions;
- predecessor evidence;
- supersession and active-plan discovery.

### Completion criteria

- overview and plan are distinct artifact roles;
- plans cannot become normative by detail or age;
- overview and plan discovery is deterministic;
- supersession is explicit;
- missing or conflicting active records fail closed;
- schemas, fixtures, validators, and manifest coverage are complete.

## Phase 3 — Repository functional-area model

### Objective

Extend the minimal repository vocabulary into a generic functional layout model.

### Required functional areas

- overview documentation;
- implementation planning;
- repository specifications;
- product specifications;
- maintained product source;
- tests;
- schemas;
- conformance;
- generated artifacts;
- validation;
- repository tooling;
- packaging and release support;
- temporary development state.

### Required semantics

- authority classification;
- lifecycle classification;
- ownership;
- containment;
- dependency direction;
- maintained versus generated treatment;
- functional naming;
- path significance;
- ignored content;
- optional and required areas;
- extension areas;
- product-profile areas.

### Exclusions

Do not prescribe:

- one programming language;
- one build system;
- one packaging system;
- one hosting provider;
- one product source hierarchy.

### Completion criteria

- a minimal initialized repository can be represented;
- a complex product repository can extend the model;
- functional areas remain product-neutral;
- missing required areas and invalid placement fail closed;
- product-specific extensions cannot redefine kernel classifications.

## Phase 4 — Fixed Level 0–3 specification model

### Objective

Define the fixed product specification format required by the overview.

### Fixed Levels

```text
Level 0 — kernel
Level 1 — primitives
Level 2 — components
Level 3 — orchestrations
```

### Level 0 responsibilities

- core terminology;
- universal invariants;
- authority and precedence;
- identity and versioning foundations;
- common data constraints;
- error and failure principles;
- lifecycle foundations;
- extension boundaries.

### Level 1 responsibilities

- entities;
- values;
- records;
- interfaces;
- elementary operations;
- state definitions;
- validation primitives;
- reusable atomic concepts.

### Level 2 responsibilities

- services;
- processors;
- validators;
- adapters;
- repositories;
- subsystems;
- coordinated state machines;
- reusable component contracts.

### Level 3 responsibilities

- end-to-end use cases;
- multi-component workflows;
- user-facing operations;
- lifecycle orchestrations;
- cross-system coordination;
- release or deployment flows;
- complete product interactions.

### Dependency rules

- Level 0 must not depend on Levels 1–3;
- Level 1 may depend on Level 0 only;
- Level 2 may depend on Levels 0–1;
- Level 3 may depend on Levels 0–2;
- lower Levels must not depend on higher Levels;
- same-Level dependencies must be explicit and acyclic;
- higher Levels must not redefine lower-Level semantics;
- orchestrations must not invent missing primitive behavior;
- implementation artifacts must not become undocumented specification sources.

### Artifact rules

Define:

- Level roots;
- subordinate specification artifacts;
- root manifests;
- naming;
- dependency declarations;
- cross-Level references;
- schema requirements;
- conformance participation;
- derived projections;
- source correspondence;
- validation ownership;
- completeness criteria.

### Framework boundary

The framework defines the Level model.

The framework repository is not required to instantiate product-specific Level
0 through Level 3 documents.

### Completion criteria

- fixed Level inventory is closed;
- dependency validation is fail-closed;
- cycles and upward dependencies are rejected;
- Level artifact placement is deterministic;
- minimal positive and negative product fixtures exist;
- no GVE-specific Level content is introduced.

## Phase 5 — Product artifact roles

### Objective

Define generic roles for maintained product artifacts without prescribing one
product architecture.

### Required classes

- maintained source;
- product test;
- configuration;
- schema;
- template;
- generator;
- generated artifact;
- command-line executable;
- library;
- service;
- package;
- user documentation;
- release automation;
- repository-maintenance tooling.

### Required relationships

- specification implementation;
- source ownership;
- test target;
- generator source;
- generated output;
- packaging membership;
- release participation;
- validation ownership;
- deprecation or replacement where applicable.

### Completion criteria

- product artifacts remain distinct from specifications;
- code cannot silently become normative;
- generated content has deterministic provenance;
- tests do not define semantics unless specifications explicitly assign that role;
- language- and build-system-specific behavior remains profile-defined.

## Phase 6 — Git repository and revision model

### Objective

Define Git-compatible repository state and revision evidence.

### Required concepts

- repository;
- object database;
- commit;
- tree;
- blob;
- ref;
- branch;
- tag;
- default branch;
- remote;
- accepted base;
- merge base;
- ancestry;
- ahead and behind state;
- staged paths;
- unstaged paths;
- untracked paths;
- conflicted paths;
- clean state;
- changed-file inventory;
- diff;
- exact-revision validation;
- integration commit;
- release ref.

### Required distinctions

- Git object identity versus semantic identity;
- branch existence versus authorization;
- commit existence versus acceptance;
- merge versus release;
- local state versus remote orientation;
- exact revision validation versus floating branch validation.

### Completion criteria

- local Git state can be represented deterministically;
- unsafe assumptions about unknown local state fail closed;
- validation evidence binds to exact revisions;
- branch, commit, merge, acceptance, and release remain distinct;
- no GitHub-specific API behavior enters the core model.

## Phase 7 — AI-session continuity model

### Objective

Define repository-first development continuity for independent AI chatbot
sessions.

### Required discovery sequence

1. repository README;
2. active overview;
3. active implementation plan;
4. normative authority roots;
5. governing work item;
6. predecessor evidence;
7. local Git state;
8. current bounded action;
9. mutation boundary;
10. returned evidence and successor decision.

### Required behavior

- smallest sufficient context recovery;
- deterministic authority discovery;
- explicit conflict reporting;
- no dependence on prior conversation memory;
- no inference of unknown local state from remote state;
- exact artifact and mutation boundaries;
- evidence-driven continuation;
- durable unresolved questions;
- durable successor boundaries;
- human decision points.

### Completion criteria

- a fresh chatbot session can orient from repository records;
- conflicting authority is reported rather than silently resolved;
- missing governing work blocks mutation;
- unknown local state blocks unsafe local operations;
- successor actions derive from observed results.

## Phase 8 — Generic governed-development model

### Objective

Define the portable development workflow independently of one hosting platform.

### Required lifecycle

```text
idea
overview
plan
candidate specification
accepted specification
product artifact
validation
review
acceptance
integration
release
maintenance
```

### Required bounded-work stages

- governing work item;
- detailed scope;
- ordered patch plan;
- accepted base;
- isolated branch;
- coherent patch;
- focused validation;
- complete validation;
- commit;
- exact-head validation;
- publication;
- review proposal;
- semantic review;
- acceptance;
- integration;
- accepted-main validation;
- closure.

### Completion criteria

- every stage has a distinct role;
- validation is not review;
- review is not acceptance;
- acceptance is not integration;
- integration is not release;
- issue closure is not successor authorization;
- incomplete evidence fails closed.

## Phase 9 — Normative-change and acceptance model

### Objective

Define how candidate normative authority becomes accepted authority.

### Required concepts

- normative change proposal;
- exact candidate revision;
- authority interpretation;
- change set;
- review evidence;
- validation evidence;
- acceptance decision;
- accepted revision;
- supersession;
- withdrawal;
- rejection;
- replay or reproducibility requirements;
- post-merge accepted-main verification.

### Required safeguards

- exact revision binding;
- no floating-branch acceptance;
- no acceptance without required evidence;
- no self-acceptance by validation alone;
- no silent authority replacement;
- no closure before accepted-main completion gate.

## Phase 10 — Source correspondence and implementation ownership

### Objective

Define how product specifications correspond to maintained implementation.

### Required semantics

- Level-to-source correspondence;
- source ownership;
- maintained versus generated source;
- specification coverage;
- implementation status;
- test ownership;
- validator ownership;
- product-defined source layouts;
- language and build profiles;
- generated source treatment;
- partial implementation;
- intentionally unimplemented specification behavior.

### Completion criteria

- source correspondence is explicit;
- no universal language-specific layout is imposed;
- missing required correspondence fails;
- generated source remains traceable;
- product profiles can extend without redefining generic rules.

## Phase 11 — Hosting-platform profile mechanism

### Objective

Define how platform-specific development behavior extends the Git-generic core.

### Required profile capabilities

- work items;
- review proposals;
- comments;
- reviews;
- labels;
- branch protection;
- CI checks;
- merge queues;
- releases;
- platform identity;
- API evidence references.

### Required rules

- profiles must declare which generic concepts they implement;
- profiles may not redefine Git semantics;
- missing platform capabilities must have explicit fallback behavior;
- evidence must bind to exact repository revisions;
- profile-specific identifiers are not automatically semantic identities.

## Phase 12 — GitHub hosting profile

### Objective

Define the first supported hosting-platform profile.

### Expected mappings

- issue → governing work item;
- issue comments → detailed scope and patch plan records;
- pull request → review proposal;
- review comments and submissions → review evidence;
- checks and workflow runs → CI evidence;
- merge result → integration evidence;
- GitHub release → release record where used.

### Completion criteria

- GitHub behavior remains profile-specific;
- exact commit and PR head binding is explicit;
- branch protection and CI evidence are represented;
- repository-generic behavior remains portable.

## Phase 13 — Framework validation architecture

### Objective

Expand validation from construction-tree checks into complete framework
validation.

### Required validation families

- overview discovery;
- plan discovery;
- repository functional layout;
- Level structure and dependency direction;
- specification artifact classes;
- product artifact roles;
- Git state and revision evidence;
- AI-session continuity requirements;
- governed-development records;
- normative-change evidence;
- source correspondence;
- profile declarations;
- generated artifact freshness;
- initialization completeness;
- release structure.

### Validation principles

- deterministic;
- repository-local where practical;
- fail-closed;
- product-independent;
- exact-revision aware;
- structured diagnostics;
- no semantic product-leakage heuristics;
- no weakening of existing checks.

## Phase 14 — Template initialization and derivation

### Objective

Define creation of an initialized product repository from the framework.

### Required inputs

- product name or temporary identifier;
- initial overview;
- initial implementation plan;
- selected profiles;
- Level-root initialization choice;
- source and build profile choice where applicable;
- hosting-platform profile choice where applicable.

### Required outputs

- repository structure;
- overview;
- plan;
- product specification Level roots;
- validation entry points;
- initial manifests;
- framework provenance;
- selected-profile declarations;
- standalone validation capability.

### Required copy semantics

- copied artifacts;
- generated artifacts;
- selected optional artifacts;
- source-bound identities;
- target-bound identities;
- preserved identities;
- recomputed identities;
- dependency closure.

### Completion criteria

- a minimal initialized repository validates independently;
- the initialized repository does not depend on maintained framework source;
- product-specific content remains separate from framework authority;
- the Level template is available without requiring framework product Levels.

## Phase 15 — Release and maintenance model

### Objective

Define the lifecycle from accepted implementation to maintained product.

### Required concepts

- release candidate;
- release revision;
- release tag or ref;
- package;
- version;
- compatibility;
- migration;
- maintenance branch;
- patch release;
- deprecation;
- end of life;
- framework update;
- template-instance migration.

### Required distinctions

- acceptance versus release;
- merge versus release;
- source revision versus package identity;
- framework version versus product version;
- template provenance versus product authority.

## Phase 16 — Identity-profile reassessment

### Objective

Determine which framework and product artifacts require semantic identity after
the complete artifact and lifecycle model is known.

### Required decisions

- specification document identities;
- specification-set revisions;
- overview revision identities, if any;
- plan revision identities, if any;
- template revision identities;
- initialized instance identities;
- repository-layout revision identities;
- validation evidence identities;
- release identities;
- package identities;
- generated artifact identities;
- governing revision bindings;
- Git identity bindings.

### Required constraints

- no raw-digest fallback;
- Git object identities remain distinct;
- paths are inputs only when explicitly declared;
- family declarations remain closed;
- bootstrap and self-reference remain separately resolved.

## Phase 17 — Manifest and revision model

### Objective

Define final candidate manifests and aggregate revisions.

### Required capabilities

- complete inventory;
- exact artifact classes;
- identity participation;
- revision derivation;
- schema binding;
- projection binding;
- conformance binding;
- validator binding;
- duplicate rejection;
- stale member rejection;
- incomplete membership rejection;
- explicit self-reference handling;
- template and product manifest separation.

## Phase 18 — Schema and conformance hardening

### Objective

Replace construction schemas and vectors with candidate authority-backed schemas
and conformance artifacts.

### Required work

- close every authority artifact;
- remove placeholder-only envelopes;
- ensure schemas match accepted semantics;
- add positive and negative vectors;
- distinguish fixtures from conformance artifacts;
- preserve repository portability;
- freeze vectors only at acceptance.

## Phase 19 — Derived projection hardening

### Objective

Define and validate deterministic derived artifacts.

### Required properties

- identified source;
- declared generator;
- deterministic output;
- source binding;
- reproducibility;
- freshness;
- projection identity where required;
- no hand-authored authority drift.

## Phase 20 — Complete repository validation

### Objective

Validate the full framework source repository.

### Required coverage

- overview and plan;
- construction authority;
- repository functional areas;
- Level model;
- Git model;
- AI-session continuity;
- development workflow;
- normative change;
- product artifact roles;
- source correspondence;
- platform profiles;
- manifests;
- schemas;
- conformance;
- projections;
- release and maintenance rules.

## Phase 21 — Portable instance validation

### Objective

Validate the framework against repositories other than its own source tree.

### Required targets

- minimal initialized repository;
- representative command-line product;
- representative library product;
- repository using the GitHub profile;
- copied portable framework subset;
- repository with valid optional extensions;
- intentionally invalid repositories for every fail-closed boundary.

## Phase 22 — Framework hardening and acceptance

### Required work

- close all references;
- replace temporary envelopes;
- remove construction exceptions;
- freeze accepted vectors;
- verify deterministic projections;
- verify all required identities;
- verify no GVE product semantics leaked into generic authority;
- validate framework and initialized repositories;
- validate exact candidate revision;
- complete semantic review;
- record acceptance;
- validate clean accepted-main after merge.

## Phase 23 — Framework cutover

### Objective

Make the completed repository framework the accepted product authority.

### Required work

- remove temporary construction status;
- establish final authoritative locations;
- activate final schemas;
- activate manifests and revisions;
- activate deterministic projections;
- activate accepted conformance vectors;
- activate repository validation;
- preserve historical authority and transition records;
- separately authorize naming and repository renaming where desired.

## Phase 24 — Separate GVE derivation

### Objective

Use the accepted framework to initialize and develop GVE as a separate product.

### Required sequence

```text
framework template
    ↓
GVE product overview
    ↓
GVE implementation plan
    ↓
GVE Level 0 kernel
    ↓
GVE Level 1 primitives
    ↓
GVE Level 2 components
    ↓
GVE Level 3 orchestrations
    ↓
GVE product artifacts
```

GVE-specific operation, effect, execution-record, authoritative-result, and
finalization semantics belong only to that product.

## Cross-cutting validation requirements

Every bounded issue affecting `specification-system/repo/` must verify:

- construction status remains accurate;
- manifest inventory is updated atomically;
- artifact classes are declared;
- schemas reject unknown fields;
- paths are normalized;
- references close within the issue boundary;
- product leakage review is completed;
- no maintained GVE runtime import is introduced;
- no third-party runtime dependency is introduced without explicit authority;
- focused tests pass;
- complete construction validation passes;
- repository-wide validation passes;
- `git diff --check` passes;
- clean accepted-main validation passes after merge.

## Audit gates

Before proposing each successor issue, audit:

1. whether every prerequisite boundary is accepted;
2. whether accepted-main validation is clean;
3. whether the target boundary is the earliest incomplete dependency;
4. whether unresolved decisions prevent bounded implementation;
5. whether one issue can close the boundary without combining independent work;
6. whether artifact, schema, fixture, validator, manifest, and test updates can be
   atomic;
7. whether product leakage has been reviewed;
8. whether the issue can state exact exclusions.

## Completion criteria for the framework construction system

The framework construction system is substantively complete when:

- the overview is discoverable;
- the active implementation plan is discoverable;
- framework, template, instance, and product roles are explicit;
- repository functional areas are explicit;
- the Level 0–3 product specification format is complete;
- product artifact roles are complete;
- Git semantics are explicit;
- hosting-platform profiles are separated;
- AI-session continuity is explicit;
- development and normative-change workflows are explicit;
- source correspondence is explicit;
- initialization produces standalone-valid product repositories;
- release and maintenance are explicit;
- schemas and conformance are authority-backed;
- projections reproduce;
- identities and manifests close;
- repository validation passes on all required targets;
- no GVE-specific product semantics define the reusable framework.

## Acceptance criteria

The framework may be accepted only when:

- all construction exceptions are removed;
- final schemas govern all normative artifacts;
- accepted vectors are frozen;
- required identities and revisions recompute;
- projections reproduce;
- reference closure passes;
- framework validation passes;
- minimal initialized repository validation passes;
- representative product repository validation passes;
- GitHub-profile validation passes where applicable;
- initialization produces a standalone-valid target;
- no product-specific semantics leak into portable authority;
- the exact candidate revision passes complete validation;
- semantic review accepts the exact candidate revision;
- clean accepted-main validation passes after merge;
- cutover is separately authorized.

## Explicit non-goals

This plan does not authorize:

- selecting the final project name;
- renaming the repository;
- changing accepted GVE product semantics;
- deleting the historical executor;
- moving historical GVE specifications;
- creating the future GVE repository;
- requiring the framework repository to contain product Level documents;
- requiring one programming language;
- requiring one build system;
- requiring one hosting provider;
- treating Git commits as semantic acceptance;
- allowing AI chatbots to self-authorize work;
- allowing validation to substitute for review;
- combining construction and cutover;
- weakening existing validation.
