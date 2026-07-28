# Repository Specification Model Scratchpad

## Status

Scratchpad.

This document is non-normative, incomplete, and exploratory. It records ideas
about the role, stability, contents, self-reference, and reusable structure of
repository specifications.

Nothing in this document defines accepted repository layout, development
process, Level semantics, product behavior, or validation requirements.

## Core Idea

Repository specifications are the stable foundation of governed project
development.

Once accepted, they should change rarely.

They are intended to serve as reusable templates for repositories initialized
and governed through GVE.

Repository specifications define the development environment in which a
project's product specifications and maintained implementation are created.

They do not define the product itself.

## Stability

Repository specifications should be designed as durable infrastructure.

They should change only when the general model of governed project development
changes.

Examples of changes that may justify repository-specification revision:

- a change to the normative versus non-normative artifact model;
- a change to specification-system structure;
- a change to repository validation boundaries;
- a change to the development promotion process;
- a change to normative artifact acceptance;
- a change to the fixed Level model;
- a change to repository initialization requirements.

Product feature work should not normally require repository-specification
changes.

Project-specific architectural decisions should not be promoted into reusable
repository authority unless they are genuinely generic.

## Repository Trees

The repository specifications should define the purpose, layout, allowed
contents, and relationships of the primary repository trees.

The principal trees are:

```text
docs/
specs/
src/
```

### `docs/`

`docs/` is non-normative.

It contains thought and planning artifacts that may inform future governed work
but do not define accepted repository or product meaning.

Expected structure:

```text
docs/
âââ scratchpad/
âââ implementation/
```

#### `docs/scratchpad/`

Contains raw, unresolved, exploratory, contradictory, or incomplete thought.

Possible contents:

- questions;
- hypotheses;
- alternatives;
- observations;
- design fragments;
- problem statements;
- rejected or competing ideas;
- preliminary models;
- unknowns requiring clarification.

Scratchpad content is not required to be internally consistent.

It must not be treated as authority.

#### `docs/implementation/`

Contains organized, non-normative implementation plans derived from clarified
scratchpad material.

Possible contents:

- current-state descriptions;
- target-state descriptions;
- boundaries;
- dependencies;
- transition models;
- validation expectations;
- cutover conditions;
- issue candidates;
- risk analysis.

Implementation plans guide issue creation but do not authorize normative
changes by themselves.

### `specs/`

`specs/` is normative.

It contains accepted rules governing:

- repository structure;
- product behavior;
- authority;
- identity;
- conformance;
- validation;
- normative artifact authoring;
- normative artifact relationships.

Expected top-level division:

```text
specs/
âââ repo/
âââ product/
```

#### `specs/repo/`

Contains stable, reusable repository authority.

It defines the repository model and should be portable into initialized target
repositories.

#### `specs/product/`

Contains project-dependent product authority.

Its structure is governed by repository specifications, while its actual
content is determined by the project.

### `src/`

`src/` contains the maintained product implementation.

Its broad layout is governed by repository specifications.

Its actual modules, packages, components, orchestration, and product behavior
are determined by the project and its accepted product specifications.

## Self-Referential Repository Authority

Repository specifications should be self-referential.

They should define both:

1. the repository layout generally; and
2. the layout and allowed contents of `specs/repo/` itself.

This means repository authority should define:

- where repository specifications live;
- how they are divided;
- what document classes are permitted;
- how schemas are organized;
- where conformance artifacts live;
- where derived projections live;
- where validation code and tests live;
- how repository-specification manifests are structured;
- how repository specifications validate themselves;
- how repository-specification changes are accepted.

The repository specification system should comply with the rules it defines.

A small bootstrap may still be necessary to locate the repository manifest and
validation entry point.

The bootstrap should be minimized and explicitly described.

## Product Specification Layout

Repository specifications should define the required shape of product
specifications without defining project-specific product content.

They may define:

- required Level structure;
- required document envelopes;
- required identity and reference rules;
- schema participation;
- conformance artifact placement;
- derived projection rules;
- validation entry points;
- allowed dependency direction;
- manifest participation;
- required Level relationships.

They should not define:

- the particular product's commands;
- the particular product's workflows;
- product-specific components;
- product-specific diagnostics;
- project-specific plugins;
- project-specific data models.

Those belong to `specs/product/`.

## Product Source Layout

Repository specifications should define the structural expectations for
`src/`.

They may define:

- that source is organized according to the fixed Level model;
- allowed dependency direction;
- validation ownership;
- package or module classification;
- separation between implementation layers;
- correspondence between product specifications and source ownership;
- rules for generated versus maintained source.

They should not prescribe the project's actual product modules or component
inventory.

Those are determined by accepted product specifications.

## Development Promotion Process

Repository specifications should define the project-development progression:

```text
scratchpad
    â
implementation plan
    â
normative artifact
```

A more complete model may be:

```text
docs/scratchpad/
    raw and unresolved thought
        â
docs/implementation/
    organized non-normative plan
        â
issue
    bounded governed work
        â
patch
    concrete repository change
        â
pull request
    review and acceptance boundary
        â
normative artifact
    accepted specification or maintained implementation
```

The progression is directional.

Earlier artifacts may explain intent but do not override accepted normative
artifacts.

Not all scratchpad material must be promoted.

Not all implementation plans must produce issues.

Not all issues must produce both specifications and source.

## Normative Artifact Development Process

Repository specifications should define the normative artifact development
process as:

```text
issue
    â
patch
    â
pull request
    â
accepted normative artifact
```

### Issue

The issue defines one bounded responsibility.

It should establish:

- governing authority;
- scope;
- included work;
- excluded work;
- validation expectations;
- acceptance conditions;
- any authorized authority changes.

Issue identifiers are workflow history and must not become permanent artifact
names.

### Patch

The patch is the concrete repository change implementing the issue.

A patch should:

- remain within issue scope;
- preserve unrelated authority and behavior;
- use functional names;
- include required specifications, schemas, conformance evidence, validation,
  and implementation;
- fail closed when authority is ambiguous.

### Pull request

The pull request is the review and repository acceptance boundary.

It should allow reviewers to determine:

- whether the patch conforms to the issue;
- whether normative changes are explicit;
- whether validation evidence is sufficient;
- whether unrelated behavior changed;
- whether permanent artifacts are named by function;
- whether repository and product boundaries remain intact.

Merge acceptance promotes the patch into the repository's maintained normative
state.

## Fixed Level Model

Repository specifications should define a fixed four-Level model.

The Levels are:

```text
Level 0 = kernel
Level 1 = primitives
Level 2 = components
Level 3 = orchestration
```

The Level identities and meanings should not vary by project.

Projects determine the contents within each Level, but not the definitions of
the Levels themselves.

## Level 0: Kernel

Level 0 defines the smallest foundational execution and representation
contract on which all higher Levels depend.

Possible characteristics:

- minimal trusted base;
- canonical core types;
- fundamental error and result forms;
- deterministic representation;
- basic identity or execution kernel;
- no dependency on project components or orchestration;
- stable enough to support all higher layers.

Level 0 should not contain convenience composition, project components, or
workflow policy.

## Level 1: Primitives

Level 1 defines reusable atomic operations and domain primitives built on the
kernel.

Possible characteristics:

- small, focused behavior;
- independently understandable contracts;
- limited composition;
- no project-scale component ownership;
- no orchestration policy;
- dependency only on Level 0.

Examples may include parsing primitives, validation primitives, identity
operations, canonical transforms, or other atomic capabilities.

The exact primitive inventory is project-dependent.

## Level 2: Components

Level 2 defines composed product capabilities with clear ownership and
boundaries.

Possible characteristics:

- composition of Level 0 and Level 1 behavior;
- cohesive functional responsibilities;
- stateful or multi-step behavior where required;
- explicit inputs, outputs, failures, and identities;
- independently testable product components;
- no repository-wide orchestration policy;
- dependency only on Levels 0 and 1.

The exact component inventory is project-dependent.

## Level 3: Orchestration

Level 3 defines coordination of components into product workflows.

Possible characteristics:

- ordering and coordination;
- lifecycle control;
- workflow policy;
- cross-component sequencing;
- command or application-level behavior;
- external execution surfaces;
- dependency on lower Levels;
- no lower Level dependency on Level 3.

The exact orchestration workflows are project-dependent.

## Level Dependency Direction

The Level model should enforce strict downward dependency:

```text
Level 3 â Levels 2, 1, 0
Level 2 â Levels 1, 0
Level 1 â Level 0
Level 0 â no higher Level
```

Forbidden dependencies include:

```text
Level 0 â Level 1, 2, or 3
Level 1 â Level 2 or 3
Level 2 â Level 3
```

Questions remain about whether direct dependency skipping is allowed or whether
each Level should depend only on the immediately lower Level.

## Level Specification Requirements

Repository specifications should define strict required sections or fields for
every Level specification.

Possible required concepts:

- Level identity;
- fixed Level definition;
- purpose;
- allowed responsibilities;
- forbidden responsibilities;
- dependency rules;
- artifact classes;
- implementation correspondence;
- conformance requirements;
- failure boundaries;
- identity rules;
- relationship to adjacent Levels;
- required validation evidence.

The fixed Level definitions should be reusable across projects.

Project product specifications should populate the project-specific artifacts
and requirements within those fixed definitions.

## Repository Initialization

Future `gve repo init` should copy the repository-focused specification subset
into a blank target repository.

That subset should establish:

- `docs/`, `specs/`, and `src/`;
- normative and non-normative classification;
- scratchpad and implementation planning;
- issue-to-patch-to-PR normative development;
- fixed Level 0â3 definitions;
- specification authoring;
- validation boundaries;
- repository manifests and digest relationships;
- the process for adding project-specific product specifications.

The copied repository specification system should validate without requiring
product specifications or maintained source to exist yet, unless empty or
uninitialized product and source states are explicitly required.

## Open Questions

- Should `src/` be called normative, or should only `specs/` be normative while
  `src/` is the accepted maintained implementation?
- Which repository rules are truly reusable across all GVE-initialized
  repositories?
- How much of GitHub issue and pull-request workflow belongs in normative
  repository specifications?
- Must the normative artifact workflow support non-GitHub issue and review
  systems?
- Is merge the only acceptance event, or is a separate sealing or manifest
  update required?
- Should repository specifications define branch or commit requirements?
- Should Level definitions apply equally to specifications and source?
- Are schemas and validation tools assigned to Levels?
- Can a project omit a Level when it has no content at that layer?
- Is direct Level 3 to Level 0 dependency allowed?
- Is Level 0 a product kernel, a repository kernel, or both?
- Should repository-generic Level definitions use GVE-prefixed identities?
- How are fixed Level definitions versioned without destabilizing all derived
  repositories?
- How does an initialized repository adopt later repository-specification
  revisions?
- How is self-reference validated without circular authority?
- Which parts of `specs/repo/` are bootstrap authority and which are ordinary
  manifest members?

## Working Summary

Repository specifications are intended to be the durable, reusable foundation
for GVE-driven project development.

They define:

```text
non-normative thought and planning
    docs/scratchpad/
    docs/implementation/

normative repository and product authority
    specs/repo/
    specs/product/

maintained product implementation
    src/
```

They also define the two principal development flows:

```text
scratchpad â implementation plan â normative artifact
```

and:

```text
issue â patch â pull request â accepted normative artifact
```

They establish a fixed product-layer model:

```text
Level 0 = kernel
Level 1 = primitives
Level 2 = components
Level 3 = orchestration
```

The repository specifications define the stable framework. Each project defines
its own product specifications and source contents within that framework.
