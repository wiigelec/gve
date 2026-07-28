# Validation Scheme Scratchpad

## Status

Scratchpad.

This document is non-normative, incomplete, and intentionally exploratory. It
collects ideas about validation ownership, digest sealing, manifest hierarchy,
and isolated validation workflows for later organization, clarification, and
possible promotion into an implementation plan and normative specifications.

Nothing in this document defines accepted repository behavior, specification
authority, validation semantics, manifest format, or product requirements.

## Core Idea

The repository contains two normative top-level trees:

```text
specs/
src/
```

Each normative tree owns its own validation.

The specification tree is further divided into:

```text
specs/
├── repo/
└── product/
```

Each of those subtrees also owns its own validation.

The validation design should make expensive validation local to the area under
development.

Parent validation should normally verify only that child trees still match the
exact bytes that most recently passed their owned validation suites.

## Intended Validation Hierarchy

```text
repository validation
├── specs digest
└── src digest

specification validation
├── specs/repo digest
└── specs/product digest

specs/repo validation
└── repository-specification validation suite

specs/product validation
└── product-specification validation suite

src validation
└── maintained-product validation suite
```

The hierarchy provides fast validation at parent boundaries and deep validation
at ownership boundaries.

## Possible Repository Shape

```text
repository/
├── REPOSITORY-MANIFEST.json
├── validate
├── specs/
│   ├── SPECIFICATION-MANIFEST.json
│   ├── validate
│   ├── repo/
│   │   ├── validate
│   │   └── validation/
│   └── product/
│       ├── validate
│       └── validation/
└── src/
    ├── validate
    └── validation/
```

Exact filenames and locations remain unresolved.

The important idea is that the manifest storing a child digest lives outside
the child tree whose digest it records.

## Top-Level Repository Validation

The top-level repository validation entry point should be fast.

Its primary responsibility is to validate the exact recorded state of the two
normative trees:

```text
specs/
src/
```

Possible responsibilities:

- validate the repository manifest structure;
- calculate the current canonical digest of `specs/`;
- compare it with the recorded accepted `specs` digest;
- calculate the current canonical digest of `src/`;
- compare it with the recorded accepted `src` digest;
- reject missing, malformed, or duplicate normative-tree bindings;
- report which normative tree changed since its last accepted validation;
- avoid rerunning deep child validation suites.

Possible non-responsibilities:

- running specification semantic validation;
- running source unit or integration tests;
- validating product behavior;
- rewriting accepted digests;
- deciding that changed bytes are valid merely because they can be hashed.

A successful top-level validation would mean:

> The current `specs/` and `src/` trees exactly match the states recorded as
> having passed their owned validation processes.

It would not independently prove those child suites were correctly designed.

## Top-Level Specification Validation

The `specs/validate` entry point should also be fast.

Its primary responsibility is to validate the exact recorded state of:

```text
specs/repo/
specs/product/
```

Possible responsibilities:

- validate the specification manifest structure;
- calculate the current canonical digest of `specs/repo/`;
- compare it with the recorded repository-specification digest;
- calculate the current canonical digest of `specs/product/`;
- compare it with the recorded product-specification digest;
- verify required child bindings are present;
- verify allowed dependency direction between repository and product
  specifications;
- avoid rerunning both deep specification validation suites.

A successful specification-level validation would mean:

> The current repository and product specification subtrees exactly match
> their recorded deeply validated states.

## Repository-Specification Validation

The `specs/repo/validate` entry point owns deep validation of repository-focused
specifications.

Possible responsibilities include:

- specification-system structure;
- repository layout;
- source layout;
- artifact classification;
- functional naming;
- repository dependency direction;
- scratchpad and implementation-plan placement;
- manifest rules;
- repository-generic schemas;
- repository conformance vectors;
- deterministic projections;
- specification-authoring rules;
- validator tests;
- blank-repository initialization requirements.

This validation should be able to run without maintained-product
implementation.

It should be portable with the repository-specification subset installed by
future `gve repo init`.

## Product-Specification Validation

The `specs/product/validate` entry point owns deep validation of product-focused
specifications.

Possible responsibilities include:

- product Level and Stage authority;
- workflows and operations;
- identities;
- plugins;
- diagnostics;
- result contracts;
- product schemas;
- product conformance vectors;
- deterministic product projections;
- semantic hierarchy;
- product-specific validator tests.

Product specification validation may depend on accepted repository
specification rules.

Repository specification validation must not depend on GVE-specific product
authority.

## Source Validation

The `src/validate` entry point owns deep validation of the maintained product.

Possible responsibilities include:

- unit tests;
- integration tests;
- specification conformance tests;
- package tests;
- command-line tests;
- installed-product tests;
- static validation;
- source-layout checks;
- exact diagnostic behavior;
- result and identity behavior.

Source validation may read accepted product and repository specifications.

Source validation should not alter specifications.

## Validation Versus Acceptance

An unresolved design question is whether a validation command should also
write the resulting digest into the parent manifest.

One possible model is:

```text
validate
    run the owned validation suite
    on success, calculate the child digest
    write the digest into the parent manifest
```

This is simple and matches the idea that a successful validation records the
validated bytes.

However, this makes validation mutating.

Potential risks:

- validation changes the repository;
- CI validation could create diffs;
- running validation could implicitly accept unintended changes;
- a validator bug could rewrite accepted state;
- review may not clearly distinguish proof from acceptance;
- repeated validation may not be observationally pure.

An alternative model separates validation from sealing:

```text
validate
    read-only
    run the owned validation suite

seal
    run validation
    calculate the child digest
    write the digest into the parent manifest
```

This creates an explicit acceptance boundary.

Possible advantages:

- validation remains read-only;
- CI can run validation safely;
- digest updates are deliberate and reviewable;
- manifest mutation is isolated;
- failed validation cannot change accepted state;
- parent manifests become records of accepted validation rather than caches.

Possible disadvantage:

- development requires an additional command;
- validation and sealing could be run separately unless `seal` always invokes
  validation itself;
- command semantics are more complex.

This distinction needs later clarification and normative treatment.

## Possible Seal Hierarchy

If validation and mutation are separated, the workflow may be:

```text
specs/repo/seal
    runs specs/repo/validate
    writes repo-specification digest to specs manifest

specs/product/seal
    runs specs/product/validate
    writes product-specification digest to specs manifest

specs/seal
    verifies child digests
    writes complete specs digest to repository manifest

src/seal
    runs src/validate
    writes source digest to repository manifest
```

The top-level repository manifest then records:

```text
repository manifest
├── accepted specs digest
└── accepted src digest
```

The specification manifest records:

```text
specification manifest
├── accepted repo-specification digest
└── accepted product-specification digest
```

## Digest Meaning

A recorded digest should have a precise meaning.

Possible meaning:

> These exact subtree bytes successfully passed the complete validation suite
> owned by that subtree and were explicitly accepted into the parent manifest.

The digest should not merely mean:

> These bytes existed when a hash command was run.

The digest is an attestation boundary, not only a change detector.

## Digest Scope

The digest algorithm must be deterministic.

Open details include:

- path normalization;
- file ordering;
- file mode treatment;
- symlink treatment;
- line-ending treatment;
- executable-bit treatment;
- ignored transient files;
- generated caches;
- empty directories;
- manifest canonicalization;
- digest algorithm identity;
- whether filenames and paths are included in the digest;
- whether the validation script itself is inside the hashed subtree.

A likely rule is that the full child tree is hashed, including:

- validation code;
- schemas;
- conformance fixtures;
- derived artifacts;
- manifest fragments owned by the child;
- executable entry points.

The parent manifest storing the child digest must not be inside that child
digest boundary.

## Recursive Digest Avoidance

A child digest cannot include the parent field that stores that digest.

A clean containment model is:

```text
REPOSITORY-MANIFEST.json
    stores digest of specs/
    stores digest of src/

specs/SPECIFICATION-MANIFEST.json
    stores digest of specs/repo/
    stores digest of specs/product/
```

Therefore:

- `specs/repo/` can be hashed completely;
- `specs/product/` can be hashed completely;
- `src/` can be hashed completely;
- `specs/` can be hashed completely because its digest is stored outside it;
- the specification manifest can safely be part of the full `specs/` digest.

## Dirty-State Meaning

A parent digest mismatch should not automatically mean the child tree is
semantically invalid.

It means:

> The child tree no longer matches its last accepted deeply validated state.

Possible status categories:

```text
valid-and-sealed
modified-since-seal
deep-validation-failed
manifest-invalid
digest-unavailable
unsealed
```

This distinction matters during active development.

A subtree under development is expected to be modified and temporarily fail
parent validation until it is deeply validated and resealed.

## Isolation Goal

The main reason for the hierarchy is validation isolation.

When changing only `specs/repo/`, a developer should not need to rerun:

- the complete product-specification suite;
- the complete maintained-product suite;
- unrelated integration tests.

When changing only `src/`, a developer should not need to rerun deep
specification validation if both specification digests remain accepted.

Possible workflows:

### Repository-specification work

```text
edit specs/repo/
run specs/repo deep validation
record accepted specs/repo digest
verify specs child digests
record accepted specs digest
run fast repository digest validation
```

### Product-specification work

```text
edit specs/product/
run specs/product deep validation
record accepted specs/product digest
verify specs child digests
record accepted specs digest
run fast repository digest validation
```

### Source work

```text
edit src/
run src deep validation
record accepted src digest
run fast repository digest validation
```

## Dependency Direction

Possible validation dependency direction:

```text
specs/repo validation
    depends only on repository-specification authority and generic validation
    support

specs/product validation
    may depend on accepted specs/repo authority

src validation
    may depend on accepted specs/repo and specs/product authority

specs top-level validation
    depends only on child digests and specification manifest rules

repository top-level validation
    depends only on specs and src digests and repository manifest rules
```

The fast parent layers should not need to understand deep child semantics.

## Initialization Implications

Future `gve repo init` will copy a subset of repository-focused specifications
and validation support into a blank target repository.

The initialized target should have a working digest hierarchy even before
product specifications or source implementation exist.

Possible initial state:

```text
specs/
├── repo/
├── product/        # absent, empty, or explicitly uninitialized
└── validate

src/                # absent, empty, or explicitly uninitialized
```

Questions include:

- Does the root manifest permit an absent product tree?
- Does it record an empty canonical product digest?
- Does repository initialization create placeholder manifests?
- At what point does `src/` become a normative tree?
- Can the repository validate successfully before product authority exists?
- How are optional normative children represented without ambiguity?

## Trust and Authority Questions

The hierarchy introduces questions about what is actually trusted.

Potential trust anchors:

- root repository manifest;
- specification manifest;
- validation scripts;
- schemas;
- digest algorithm specification;
- accepted Git commit;
- external review and merge process.

A digest proves equality with recorded bytes, not correctness.

Correctness still depends on:

- validation suite quality;
- authority quality;
- review;
- explicit acceptance;
- deterministic tooling;
- protection against validator self-approval.

The system should not imply stronger proof than it provides.

## Validator Self-Modification

If validation code is inside the tree it validates, changing the validator
changes the tree digest.

That is probably desirable.

However, a modified validator might approve invalid content and then seal
itself.

Possible mitigations to explore:

- parent-level validation rules for child validator structure;
- immutable bootstrap validation logic;
- review requirements;
- cross-validation;
- known validator identity bindings;
- restricted sealing operations;
- CI comparison with trusted validation entry points;
- acceptance through governed issues and pull requests.

This cannot be solved by hashing alone.

## Manifest Mutation Questions

If sealing writes parent manifests, the write operation should be deterministic.

Possible requirements:

- fail without mutation if validation fails;
- write only the owned digest field;
- preserve unrelated manifest bytes or regenerate canonically;
- report old and new digests;
- reject a dirty or malformed parent manifest;
- reject unexpected sibling changes;
- avoid timestamps in normative content unless required;
- avoid environment-dependent values;
- produce a reviewable diff;
- verify the written manifest after mutation.

## Full Validation

Although ordinary workflows should be isolated, the repository may still need
a complete validation mode.

Possible command:

```text
./validate --deep
```

or:

```text
./validate-all
```

It could run:

1. `specs/repo` deep validation;
2. `specs/product` deep validation;
3. `specs` digest validation;
4. `src` deep validation;
5. top-level repository digest validation;
6. repository cleanliness checks.

Possible uses:

- release preparation;
- major cutovers;
- validator changes;
- manifest-format changes;
- specification-system changes;
- CI scheduled audits;
- confidence checks after broad refactoring.

The existence of full validation should not force every local change to pay its
cost.

## Naming

Permanent validation artifacts should be named by function.

Possible names:

```text
validate
seal
manifest.json
repository-manifest.json
specification-manifest.json
digest.py
canonical_tree.py
```

Avoid permanent names derived from:

- issue numbers;
- milestones;
- phases;
- migrations;
- temporary transition order.

## Open Questions

- Should `validate` ever mutate, or must validation and sealing be separate?
- What exactly constitutes acceptance of a newly written digest?
- Is the root manifest authoritative, normative implementation state, or an
  integrity index?
- Should manifests be JSON, another canonical format, or specification-defined
  artifacts?
- Are validation scripts part of normative trees?
- Should validation test code be included in subtree digests?
- How are platform-dependent files and executable modes handled?
- Should digests cover derived artifacts?
- Should generated Markdown be sealed with authority or regenerated on demand?
- How does product validation prove it used the accepted repository
  specifications?
- How does source validation prove it used the accepted product
  specifications?
- Can a stale but digest-matching child be semantically superseded by another
  manifest?
- How are optional or not-yet-created normative trees represented?
- What prevents a modified validator from approving itself?
- Should sealing be allowed only from a clean Git worktree?
- Should sealing require an expected prior digest?
- Should a seal record validation evidence in addition to a SHA?
- Is a single SHA enough, or should the parent bind algorithm, tree format,
  validation profile, and evidence identity?
- When is full deep validation mandatory despite normal isolation?
- Which parts of this scheme are repository-generic and copied by
  `gve repo init`?
- Which parts are specific to the GVE repository and product?

## Working Summary

The proposed direction is a layered validation system:

```text
deep child validation
    ↓
accepted child digest
    ↓
fast parent digest validation
```

The intended hierarchy is:

```text
repository
├── specs
│   ├── repo
│   └── product
└── src
```

Each deep validation suite is isolated to its ownership boundary.

Parent validation checks whether child bytes remain equal to their last
accepted deeply validated states.

The major unresolved design question is whether successful validation itself
updates parent manifests or whether a separate explicit sealing operation owns
that mutation.
