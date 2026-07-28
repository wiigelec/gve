# GVE Development Model Scratchpad

## Status

Scratchpad.

This document is non-normative, incomplete, and intentionally exploratory. It collects ideas for later organization, elaboration, clarification, rejection, or promotion into implementation planning and normative artifacts.

Nothing in this document defines accepted GVE behavior, repository rules, product semantics, or implementation requirements.

## Core Idea

GVE is both:

- a tool for governed project development; and
- a model for using AI to drive project development from uncertain ideas toward explicit, reviewable, normative results.

The development model is not intended to begin with implementation.

The basic progression is:

```text
scratchpad
    ↓
implementation plan
    ↓
targeted issues
    ↓
normative artifacts
```

Implementation work follows accepted normative artifacts rather than replacing them.

## Repository Meaning

The repository is divided conceptually into non-normative and normative trees.

### Non-normative tree

```text
docs/
├── scratchpad/
└── implementation/
```

#### `docs/scratchpad/`

Contains raw thought, questions, hypotheses, alternatives, observations, contradictions, partial models, and unresolved design ideas.

Scratchpad content may be incomplete, inconsistent, speculative, redundant, later rejected, or later divided into several concerns.

Scratchpad documents do not govern the repository or maintained product. They preserve thought without prematurely converting it into authority.

#### `docs/implementation/`

Contains organized, non-normative implementation plans.

Implementation plans translate clarified scratchpad ideas into objectives, current-state assessments, target states, boundaries, dependencies, transition approaches, validation expectations, and possible issue boundaries.

Implementation plans still do not define accepted repository or product semantics. They are used to generate targeted governing issues and bounded work.

### Normative tree

```text
specs/
src/
```

#### `specs/`

Contains the normative rules governing:

- the repository;
- the maintained product;
- authority;
- identities;
- artifact placement;
- conformance;
- validation;
- accepted behavior.

The specification system should be substantially developed before maintained-product implementation begins.

#### `src/`

Contains the maintained product implementation.

`src/` is normative in the sense that it is the accepted maintained product, but it does not independently define product meaning when it conflicts with accepted specifications.

The intended relationship is:

```text
specs define
src implements
validation proves
```

## Promotion Flow

A thought should not move directly from scratchpad to source code merely because it appears plausible.

```text
docs/scratchpad/
    exploratory thought
        ↓
    clarified concept
        ↓
docs/implementation/
    organized implementation plan
        ↓
GitHub issues
    bounded authority or implementation work
        ↓
specs/
    accepted normative artifact
        ↓
src/
    maintained implementation
```

Not every scratchpad thought is promoted. Not every implementation plan becomes one issue. Not every issue produces source code.

Some issues produce specifications, schemas, conformance vectors, repository rules, validation mechanisms, implementation, derived documentation, cleanup, or realignment.

## Role of Issues

Issues are the governed transition boundary between non-normative planning and normative repository change.

An issue should identify one bounded responsibility and may authorize work to:

- define or revise normative authority;
- add conformance evidence;
- build validation support;
- implement accepted product behavior;
- realign repository structure;
- remove obsolete or nonconforming artifacts.

Issues should be derived from clarified plans rather than raw scratchpad notes.

Issue numbers are historical workflow identifiers. They should not appear in permanent directories, filenames, module names, test names, fixture namespaces, schema names, specification identifiers, or product identities.

Permanent artifacts are named only by durable function, authority, or domain.

## AI Development Role

AI is used throughout the progression, but its role changes by stage.

### Scratchpad stage

AI helps capture raw ideas, identify ambiguity, expose contradictions, compare alternatives, preserve unresolved questions, and avoid premature commitment.

### Implementation-plan stage

AI helps organize ideas, identify functional boundaries, separate generic and repository-specific concerns, define dependencies, identify risks, propose validation and adoption gates, and divide broad work into bounded issue candidates.

### Issue stage

AI helps derive exact scope, identify governing authority, enumerate included and excluded work, create validation expectations, maintain issue isolation, and audit changes against requirements.

### Normative-artifact stage

AI helps author specifications, schemas, conformance vectors, identity rules, repository authorities, and validation contracts.

At this stage, accepted normative artifacts—not AI intent or prior discussion—govern.

### Implementation stage

AI helps implement behavior under accepted specifications.

Implementation must not silently invent semantics missing from authority. Ambiguity should fail closed and return to planning or specification work.

## GVE Repository as Model

The GVE repository should itself demonstrate the development model it enables.

It should model:

- capture of unresolved thought under `docs/scratchpad/`;
- organization under `docs/implementation/`;
- bounded issue creation;
- explicit normative authority under `specs/`;
- maintained implementation under `src/`;
- validation connecting specifications, repository state, and product behavior;
- functional naming without milestone- or issue-derived permanent paths;
- gradual promotion from thought to accepted artifact.

The repository structure is therefore not only implementation organization. It is an example of the governed AI-development process.

## Future Repository Initialization

GVE will initialize blank repositories.

A newly initialized repository should begin by installing the subset of GVE specifications needed to define repository meaning, specification-system structure, artifact classes, naming rules, repository layout, validation boundaries, and the process for adding repository-specific authority.

The target repository receives a dependency-closed subset of GVE's specification corpus.

The installed subset becomes local to the target repository and should validate without depending on the GVE source checkout, network access, GitHub, external schemas, or maintained product code that does not yet exist.

The initialized repository can then use the same progression:

```text
scratchpad
    ↓
implementation plan
    ↓
issues
    ↓
specifications
    ↓
implementation
```

## Generic and Repository-Specific Authority

Future clarification is needed around the boundary between:

- repository-generic authority;
- GVE-repository-specific authority;
- GVE-product-specific authority;
- target-repository-specific authority.

Repository-generic authority is reusable during initialization.

Repository-specific authority defines the particular repository and maintained product.

The generic system should define how repository-specific authority is added without defining that product's meaning in advance.

## Open Questions

- Is `src/` properly described as normative, or as accepted maintained implementation subordinate to normative `specs/`?
- Should issues be considered part of the model but outside the repository artifact taxonomy?
- Which specification artifacts are repository-generic enough to install into every initialized repository?
- How should initialization profiles be represented in the specification-set manifest?
- How is a copied target specification subset given its own revision identity?
- Which validators are generic and which are GVE-specific?
- Should the specification-system authoring rules define the complete scratchpad-to-authority promotion model?
- What evidence is required before a plan is ready to generate issues?
- What evidence is required before issue output becomes accepted normative authority?
- How should unresolved semantic ambiguity be represented and fail closed?
- How should a target repository later upgrade its installed generic specifications?
- Which parts of the development process are product authority and which remain advisory workflow?

## Working Summary

GVE is intended to turn uncertain human and AI thought into governed project development through explicit stages.

```text
docs/scratchpad/       raw, non-normative thought
docs/implementation/   organized, non-normative plans
issues/                bounded governed work
specs/                 accepted repository and product authority
src/                   accepted maintained implementation
```

The flow is directional. Earlier stages may inform later stages, but they do not override accepted normative artifacts.
