# Product Overview

## Status

Product-direction overview.

This document records the intended outcome and development model for this repository. It is directional and non-normative.

It does not replace accepted normative specifications, authorize repository mutations, or define detailed implementation requirements. Normative behavior remains governed by accepted specifications until those specifications are explicitly revised, superseded, or retired through bounded governed work.

The project name is intentionally unresolved. The historical name GVE may later be used by a separate product derived from this repository framework.

## Product vision

This repository will provide a reusable, Git-native repository framework and template for developing a high-level product idea into a specified, validated, released, and maintainable product.

The framework is designed for collaboration between human maintainers and AI chatbots. It preserves enough durable context in the repository and its Git-compatible development records for an independent AI session to understand the product, recover current work, propose bounded changes, validate results, and continue development without depending on prior conversation history.

The central product-development loop is:

```text
overview → plan → specifications → product artifacts
```

The loop is iterative rather than strictly one-way. Discoveries made during specification, implementation, validation, review, or maintenance may require revisions at an earlier layer.

Changes must be made at the layer that owns the affected decision. Product code must not silently resolve an ambiguity owned by a specification, a specification must not silently invent direction absent from the overview or plan, and a plan must not silently become normative product authority.

## Desired outcome

A repository created from this framework should be capable of progressing from an uncertain high-level idea to a maintained product through explicit, reviewable, and recoverable stages.

The framework should provide:

- a predictable repository structure;
- clear artifact roles and authority boundaries;
- a durable product overview;
- non-normative implementation planning;
- normative repository and product specifications;
- maintained product artifacts;
- schemas and conformance artifacts where appropriate;
- deterministic validation;
- generated and derived artifact handling;
- Git-based change isolation and revision evidence;
- issue- and review-based bounded development;
- independent AI-session recovery;
- explicit acceptance, release, and maintenance boundaries.

The framework itself is not primarily a universal operation-processing runtime.

A governed execution product may later be created as a separate repository derived from this template. Its operation, effect, execution-record, and authoritative-result semantics will belong to that product rather than to the reusable framework.

## Intended users

The framework is intended for:

- human product owners defining outcomes and approving material decisions;
- human developers implementing and validating product behavior;
- AI chatbots performing repository orientation, analysis, planning, implementation support, validation review, and bounded development work;
- reviewers evaluating exact proposed revisions;
- maintainers evolving a released product over time.

The framework should support small projects without requiring unnecessary ceremony while remaining capable of supporting large, long-lived, specification-driven products.

## Development layers

### Overview

The overview records the durable high-level intent of the product.

It describes:

- the problem being addressed;
- intended users;
- desired outcomes;
- important constraints;
- major capabilities;
- explicit non-goals;
- success conditions;
- unresolved product-direction questions.

The overview is directional and non-normative. It provides the basis for planning but does not define exact product behavior.

### Plan

The implementation plan organizes how the intended product will be constructed.

It describes:

- major work areas;
- dependency order;
- construction stages;
- expected artifact families;
- validation strategy;
- transition conditions;
- risks;
- unresolved design decisions.

Plans are non-normative. They coordinate development but cannot override accepted specifications or silently define product behavior.

### Specifications

Specifications define the authoritative contracts for the repository and product.

They may define:

- repository structure;
- artifact roles;
- authority and precedence;
- product concepts;
- interfaces and data contracts;
- required behavior;
- identity and versioning;
- source layout;
- validation;
- conformance;
- generated projections;
- release and maintenance rules.

Candidate specifications remain proposals until accepted through the applicable governed process.

Accepted normative specifications control maintained product artifacts.

### Product artifacts

Product artifacts realize the accepted specifications.

They may include:

- source code;
- libraries;
- command-line tools;
- services;
- schemas;
- configuration;
- templates;
- generators;
- tests;
- conformance artifacts;
- generated documentation;
- packaging;
- release automation;
- repository-maintenance tooling.

Existing implementation does not become product authority merely because it exists. Product artifacts must be evaluated against accepted specifications.

## Product specification Level template

The framework defines a fixed four-Level format for normative product specifications:

```text
Level 0 — kernel
Level 1 — primitives
Level 2 — components
Level 3 — orchestrations
```

The framework repository defines the meaning, structure, dependency rules, validation requirements, and expected artifact relationships for these Levels.

The framework repository is not required to contain its own product Level 0–3 specification documents. Instead, repositories created from the framework use the Level template to organize their product specifications.

### Level 0 — Kernel

Level 0 defines the product-wide foundations that all higher Levels depend upon.

It may define:

- core terminology;
- universal invariants;
- authority and precedence rules;
- identity and versioning foundations;
- common data constraints;
- error and failure principles;
- lifecycle foundations;
- extension boundaries.

Level 0 must remain minimal and foundational. It must not depend on higher Levels.

### Level 1 — Primitives

Level 1 defines atomic product concepts and contracts built upon the kernel.

It may define:

- entities;
- values;
- records;
- interfaces;
- elementary operations;
- state definitions;
- validation primitives;
- reusable product concepts.

Level 1 may depend on Level 0 but must not depend on Levels 2 or 3.

### Level 2 — Components

Level 2 defines reusable compositions of primitives that provide coherent product responsibilities.

It may define:

- services;
- processors;
- validators;
- adapters;
- repositories;
- subsystems;
- coordinated state machines;
- reusable component contracts.

Level 2 may depend on Levels 0 and 1 but must not depend on Level 3.

### Level 3 — Orchestrations

Level 3 defines complete workflows and externally meaningful product behavior.

It may define:

- end-to-end use cases;
- multi-component workflows;
- user-facing operations;
- lifecycle orchestrations;
- cross-system coordination;
- release or deployment flows;
- complete product interactions.

Level 3 may depend on Levels 0, 1, and 2.

### Level dependency rules

The framework should require dependencies to flow upward through the Level hierarchy:

```text
Level 0 → Level 1 → Level 2 → Level 3
```

Higher Levels may depend on lower Levels. Lower Levels must not depend on higher Levels.

The Level model should also prevent:

- circular dependencies;
- hidden upward dependencies;
- higher Levels redefining lower-Level semantics;
- orchestrations inventing missing primitive behavior;
- implementation artifacts becoming undocumented sources of specification semantics.

Same-Level dependencies may be permitted only when they are explicit, justified, and acyclic.

### Level artifact structure

The framework should define a predictable product-specification layout, such as:

```text
specs/
    levels/
        level-0/
        level-1/
        level-2/
        level-3/
```

The exact subordinate structure may evolve, but the framework should define:

- Level roots;
- artifact naming;
- manifest participation;
- schema requirements;
- cross-reference rules;
- dependency declarations;
- derived projection rules;
- source correspondence;
- conformance participation;
- validation ownership;
- completeness requirements.

A product repository may contain multiple specification artifacts within each Level. The framework should define how those artifacts collectively form the product specification system.

### Relationship to product development

The Level template governs normative product specifications within the broader development lifecycle:

```text
overview
    ↓
plan
    ↓
Level 0 kernel
    ↓
Level 1 primitives
    ↓
Level 2 components
    ↓
Level 3 orchestrations
    ↓
product artifacts
```

The overview establishes product direction. The plan sequences specification and implementation work. The Level specifications define the accepted product contracts. Product artifacts implement those contracts.

The framework should make the Level model available to every initialized product repository without requiring the framework itself to instantiate product-specific Level documents.


## Git-native model

The framework assumes Git commands and Git-compatible development workflows.

The core model may rely on:

- repositories;
- commits;
- branches;
- refs;
- tags;
- object identities;
- merge bases;
- ancestry;
- diffs;
- staged and unstaged state;
- untracked and conflicted paths;
- isolated development branches;
- exact revision validation;
- merge-based integration.

Git records exact repository states and transitions. It does not by itself establish semantic correctness, review, acceptance, or product authority.

For example:

- a commit identifies an exact tree;
- a branch identifies a line of proposed work;
- a diff provides a review surface;
- a merge records integration;
- a tag names a revision;
- a CI run records selected checks against an exact revision.

Those facts remain distinct from whether the change satisfies the overview, plan, specifications, governing issue, review requirements, or acceptance criteria.

## Hosting-platform boundary

The reusable core should remain Git-compatible rather than treating one hosting provider as universal repository authority.

Hosting-platform capabilities may be defined through explicit profiles, including:

- issues;
- pull requests or merge requests;
- review comments;
- labels;
- protected branches;
- continuous-integration APIs;
- merge queues;
- release records.

GitHub may be the first fully supported platform profile.

Platform-specific behavior must remain distinguishable from Git-generic repository behavior.

## Human and AI collaboration

### Human responsibilities

Human maintainers retain responsibility for:

- choosing product direction;
- approving material scope and semantic decisions;
- deciding which findings become governed work;
- resolving product tradeoffs;
- performing environment-specific validation where required;
- reviewing proposed changes;
- accepting exact revisions;
- merging and releasing completed work.

### AI chatbot responsibilities

AI chatbots may:

- discover repository purpose and authority;
- read the overview, plans, specifications, and governing records;
- inspect Git and hosting-platform state;
- identify contradictions, missing decisions, and incomplete boundaries;
- propose bounded issues;
- create or refine implementation plans;
- generate reviewable repository mutations;
- evaluate validation and execution evidence;
- audit changes against governing scope and specifications;
- continue work across independent sessions.

An AI chatbot must report missing or conflicting authority rather than silently selecting a convenient interpretation.

## Repository-first continuity

The repository and its durable development records are the continuity mechanism.

Essential information must not exist only in a chatbot conversation.

Durable records should preserve:

- product intent;
- authority roots;
- planning status;
- governing issues;
- scope and exclusions;
- dependencies;
- accepted bases;
- intended branches;
- implementation decisions;
- validation requirements;
- exact revision evidence;
- unresolved questions;
- successor boundaries.

A new AI session should be able to recover the smallest sufficient development context without reading the entire repository or relying on prior model memory.

## Session discovery

A new development session should be able to follow a predictable discovery path:

1. Read the repository README.
2. Read this product overview.
3. Read the current implementation plan.
4. Discover the normative specification roots and authority hierarchy.
5. Inspect the current governing issue and its durable planning records.
6. Inspect relevant prerequisites and accepted predecessor evidence.
7. Interrogate the actual local Git state.
8. Identify the next bounded action.
9. Perform only authorized mutations.
10. Review returned evidence before continuing.

The repository should make each step mechanically discoverable where practical.

## Bounded development workflow

A normal bounded change should use a Git-compatible workflow:

1. Establish a governing issue.
2. Record detailed scope and an ordered patch plan.
3. Identify the accepted default-branch base.
4. Create an isolated working branch.
5. Apply one coherent patch at a time.
6. Inspect the changed-file inventory and diff.
7. Run focused and complete validation.
8. Commit only the bounded paths.
9. Repeat the patch-and-validation loop as required.
10. Validate the exact proposed branch head.
11. Push and create a review proposal.
12. Require exact-head CI and semantic review.
13. Explicitly accept the exact revision.
14. Merge the accepted revision.
15. Validate the resulting default-branch revision.
16. Close the governing issue only after its completion gate is satisfied.

The exact tooling may evolve, but the separation among planning, mutation, validation, review, acceptance, merge, and closure must remain visible.

## Validation model

The framework should provide stable repository-local validation entry points.

Validation should eventually cover:

- repository structure;
- artifact placement;
- specification structure;
- schemas;
- references;
- manifests;
- identity rules where applicable;
- conformance artifacts;
- source layout;
- generated artifacts;
- projection freshness;
- product tests;
- packaging;
- text and diff hygiene.

Validation establishes only the properties it is designed to check. A passing validation result is not semantic review or acceptance.

Validation evidence should identify the exact repository state or Git revision tested.

## Authority model

The framework must keep these roles distinct:

```text
idea
overview
plan
candidate specification
accepted normative specification
product artifact
validation evidence
review
acceptance
merge
release
```

No role silently substitutes for another.

In particular:

- an overview is not a specification;
- a plan is not product authority;
- code is not authority merely because it works;
- tests do not define semantics unless accepted specifications assign them that role;
- validation is not review;
- review is not acceptance;
- acceptance is not merge;
- merge is not release;
- completion of one issue does not authorize unrelated successor work.

## Generated and derived artifacts

The framework may support deterministic generated or derived artifacts, including Markdown projections, schemas, indexes, manifests, and documentation.

Every generated artifact should have:

- an identified source;
- a declared generator or derivation rule;
- deterministic output;
- reproducibility checks;
- freshness validation;
- a clear statement that it does not independently override its source authority.

Hand editing a generated projection must not silently revise normative authority.

## Portability

A completed framework should be usable to initialize more than one product repository.

Portable behavior should not depend on:

- the historical GVE product;
- GVE-specific identity families;
- GVE operation or result contracts;
- maintained GVE runtime modules;
- one product’s source structure;
- one hosting provider’s APIs;
- prior chatbot conversations.

Repository-generic mechanisms must be separable from product-specific profiles.

## Relationship to GVE

GVE is a potential future product derived from this framework.

A future GVE repository may define:

- governed operation descriptions;
- operation dispatch;
- effects;
- execution records;
- authoritative results;
- validation;
- repository and remote mutations;
- publication;
- failure and recovery behavior.

Those concepts will be governed by the future GVE product’s own overview, plan, specifications, implementation, and acceptance records.

The current historical executor may remain temporarily in this repository as bootstrap development infrastructure while the framework transition is governed. Its existence does not define the desired reusable product outcome.

## Transition principles

The repository currently contains accepted specifications and implementation created for an earlier GVE product direction.

The transition to this framework must:

- preserve accepted history;
- avoid pretending that earlier authority never existed;
- identify which artifacts remain reusable;
- identify which artifacts belong only to the future GVE product;
- identify which artifacts require revision or supersession;
- preserve working bootstrap development infrastructure until a replacement is accepted;
- avoid product leakage into repository-generic authority;
- use bounded governed issues;
- keep the repository valid throughout the transition;
- avoid combining product redefinition, renaming, authority replacement, implementation removal, and final cutover into one change.

This overview establishes direction only. Detailed transition sequencing belongs in the revised implementation plan.

## Success conditions

The framework succeeds when a repository initialized from it can:

- begin from a high-level product idea;
- record a useful overview;
- produce a dependency-aware implementation plan;
- develop and accept normative specifications;
- implement conforming product artifacts;
- validate repository and product state deterministically;
- support bounded Git-based development;
- support independent AI chatbot sessions;
- preserve durable authority and decision context;
- distinguish generic framework behavior from product-specific behavior;
- release and maintain exact product revisions;
- evolve through reviewable governed changes.

The framework should ultimately be capable of being used to construct GVE as a separate product without importing GVE-specific semantics into the template itself.

## Explicit non-goals

This overview does not define:

- the final project name;
- the final repository layout;
- final specification schemas;
- final identity families;
- final manifest or sealing behavior;
- a universal product architecture;
- one mandatory programming language;
- one mandatory build system;
- one mandatory hosting platform;
- automatic acceptance by AI;
- replacement of human product judgment;
- immediate removal of the bootstrap executor;
- immediate migration of existing GVE specifications;
- the future GVE product contract;
- final framework cutover.

Those decisions require the revised implementation plan and separately governed issues.
