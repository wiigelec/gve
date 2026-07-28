# Repository Identity Implementation Plan

## Status

Implementation planning document.

This document is non-normative. It extends the repository-specification stand-up
plan with a focused implementation path for generic identity authority.

The accepted GVE normative JSON specification graph remains authoritative. This
plan does not redefine the current GVE identity framework, create new accepted
identity families, or authorize changes to maintained runtime behavior.

The plan assumes the temporary construction root:

```text
specification-system/repo/
```

and is designed to dovetail with:

```text
docs/implementation/REPOSITORY-SPECIFICATION-STAND-UP-PLAN.md
docs/scratchpad/GVE-IDENTITY-IMPLEMENTATION.md
```

## Objective

Introduce a portable, repository-generic identity authority that preserves the
mechanical strengths of the current accepted GVE identity framework while
keeping GVE-specific identity families in product authority.

The implementation should produce a layered system:

```text
generic identity mechanism
        â
repository and specification identity profiles
        â
development-process and normative-change profiles
        â
GVE product identity families
```

The generic layer defines how identities work.

Profile layers define which identity families exist for a particular authority
domain.

Product specifications continue to define product-specific identity semantics.

## Design decision

Create a dedicated functional authority area:

```text
specification-system/repo/authoritative/identity/
```

Do not place the complete generic identity mechanism under
`authoritative/specification-system/`.

Identity is broader than specification authoring. It also governs repository
trees, aggregate revisions, development artifacts, normative change, evidence,
execution, results, and finalization.

Do not copy all current GVE identity families into repository authority.

The following current concepts are generic and portable:

- family-qualified identity representation;
- explicit canonicalization versions;
- explicit digest algorithms;
- domain-separated canonical preimages;
- explicit semantic domains;
- own-identity handling;
- reference modes;
- object and aggregate kinds;
- membership and ordering rules;
- duplicate, empty, closure, and cycle policies;
- verification-context rules;
- governing-revision bindings;
- fail-closed identity verification.

The following current GVE families are product-specific and must remain outside
portable repository authority unless separately generalized through accepted
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

## Relationship to the stand-up plan

The repository-specification stand-up plan currently places these concepts in
its foundation sequence:

- repository model;
- specification artifact classes;
- self-reference and bootstrap;
- manifest model;
- functional naming.

This identity plan refines that order:

```text
generic identity kernel
    â
minimal repository vocabulary
    â
specification artifact classes
    â
specification identity profile
    â
self-reference and bootstrap
    â
manifest and revision model
    â
repository identity profile
    â
sealing, projection, conformance, and initialization
```

The generic identity kernel must remain path-independent and
repository-neutral. That allows it to precede the full repository model without
creating a circular dependency.

## Intended directory shape

The stand-up tree should eventually include:

```text
specification-system/
âââ repo/
    âââ REPOSITORY-SPECIFICATION-SET.json
    âââ validate
    âââ authoritative/
    â   âââ identity/
    â   â   âââ IDENTITY-MODEL.json
    â   â   âââ CANONICAL-JSON.json
    â   â   âââ IDENTITY-FAMILY-MODEL.json
    â   â   âââ IDENTITY-VERIFICATION.json
    â   âââ repository-model/
    â   â   âââ REPOSITORY-IDENTITIES.json
    â   âââ specification-system/
    â   â   âââ SPECIFICATION-IDENTITIES.json
    â   âââ development-process/
    â   â   âââ DEVELOPMENT-IDENTITIES.json
    â   âââ normative-change/
    â   â   âââ NORMATIVE-CHANGE-IDENTITIES.json
    â   âââ schemas/
    â   â   âââ identity/
    â   âââ conformance/
    â       âââ identity/
    âââ derived/
    â   âââ markdown/
    â       âââ identity/
    âââ validation/
        âââ lib/
        âââ intrinsic/
        âââ repository/
        âââ tests/
        âââ fixtures/
            âââ identity/
```

Only the first four generic identity artifacts belong in the initial identity
foundation.

The profile artifacts should be added later, after their governing authority
areas define the objects being identified.

## Artifact responsibilities

### `IDENTITY-MODEL.json`

Defines portable identity concepts:

- identity versus identifier;
- family-qualified identity representation;
- semantic-domain ownership;
- identity immutability;
- exact verification;
- domain separation;
- distinction between logical identity, content identity, revision identity,
  and aggregate identity;
- prohibition against implicit or cross-domain interpretation;
- relationship among family, algorithm, and digest.

It must not define GVE product families.

### `CANONICAL-JSON.json`

Defines the portable canonical JSON contract:

- accepted media type;
- UTF-8 encoding;
- object-member ordering;
- array-order preservation;
- insignificant whitespace handling;
- accepted number domain;
- surrogate handling;
- object-key restrictions;
- canonicalization versioning;
- deterministic byte production;
- rejection behavior.

The initial construction artifact should map the accepted
`gve-canonical-json-v1` behavior without claiming final normative portability
until the repository-specification system accepts it.

### `IDENTITY-FAMILY-MODEL.json`

Defines the required structure of an identity-family declaration:

- family identifier;
- semantic domain;
- unique domain prefix;
- canonicalization version;
- digest algorithm;
- canonical value source;
- own-identity paths and handling;
- reference paths and reference encoding;
- permitted referenced families;
- object kind;
- aggregate encoding;
- version bindings;
- verification mode;
- verification context source.

It also defines family-level invariants:

- one semantic domain per family;
- one canonical preimage per family;
- one unique domain prefix per family;
- explicit canonicalization;
- explicit digest algorithm;
- no circular construction;
- no ambiguous references;
- no undeclared embedded-identity behavior.

### `IDENTITY-VERIFICATION.json`

Defines portable verification behavior:

- identity parsing;
- expected-family verification;
- embedded-value recomputation;
- caller-supplied verified identity records;
- accepted-state requirements;
- family-conflict rejection;
- duplicate-context rejection;
- missing-context rejection;
- aggregate member verification;
- governing-revision binding;
- deterministic evidence reporting;
- fail-closed error classes.

## Profile responsibilities

### Specification identity profile

Create later:

```text
authoritative/specification-system/SPECIFICATION-IDENTITIES.json
```

Expected responsibilities:

- specification document identity;
- specification-set revision identity;
- manifest identity;
- schema identity;
- projection identity;
- sealed specification-set identity;
- document and set reference rules;
- direct membership closure;
- self-reference handling.

This profile should preserve the accepted distinction between an individual
specification document identity and an aggregate specification-set revision.

### Repository identity profile

Create later:

```text
authoritative/repository-model/REPOSITORY-IDENTITIES.json
```

Expected responsibilities:

- repository-area identity;
- repository-tree identity;
- repository-layout revision;
- maintained-artifact inventory identity;
- repository-conformance result identity;
- path significance;
- ordered versus unordered tree semantics;
- generated versus maintained artifact treatment;
- copy and initialization behavior.

This profile must not be designed before repository-tree membership and path
semantics are defined.

### Development-process identity profile

Create later:

```text
authoritative/development-process/DEVELOPMENT-IDENTITIES.json
```

Expected responsibilities:

- scratchpad and implementation-plan identity only if those artifacts require
  semantic identity;
- candidate plan identity;
- accepted plan identity;
- relationship between mutable planning artifacts and immutable accepted
  revisions;
- attribution and provenance bindings.

### Normative-change identity profile

Create later:

```text
authoritative/normative-change/NORMATIVE-CHANGE-IDENTITIES.json
```

Expected responsibilities:

- work-item identity;
- change-set identity;
- review-proposal identity;
- validation-evidence identity;
- acceptance identity;
- exact revision bindings;
- replay and duplicate rules;
- host-platform identifiers versus portable semantic identities.

GVE-specific plan, contract, effect, production, evidence, execution, result,
and finalization families should remain in GVE product specifications unless a
future generic normative-change model proves they are portable.

## Bootstrap strategy

Identity, manifests, and self-reference create a potential cycle.

The implementation must use staged bootstrap rather than inventing temporary
normative identities.

### Construction bootstrap

Continue using non-cryptographic construction fields:

```text
construction_identity
construction_status
normative: false
```

These are temporary functional identifiers only.

They must not be treated as final identity-family values.

### Candidate identity stage

The generic identity artifacts may define candidate family declarations and
construction vectors.

Candidate identities may appear in test fixtures, but they must be clearly
marked non-authoritative and must not participate in accepted specification-set
membership.

### Specification profile stage

Define specification document and specification revision families using the
generic kernel.

At this stage, identity rules can be validated without sealing the temporary
construction tree.

### Manifest stage

Define the repository-specification manifest using direct member identities.

The manifest model must state:

- whether the manifest itself is included in the aggregate;
- how its own identity is omitted or canonically referenced;
- whether membership is ordered or unordered;
- how duplicate members are rejected;
- how schemas, projections, vectors, and validators participate;
- how the governing specification revision is derived.

### Acceptance and cutover stage

Only after all authority, schemas, vectors, projections, and validators close
may the tree receive accepted identities and aggregate revisions.

Final sealing must occur as a separate governed hardening and cutover effort.

## Implementation phases

## Phase 0 â Existing construction foundation

Status: established by the current temporary construction manifest and
structural validator.

Identity work in this phase consists only of:

- preserving non-authoritative status;
- preserving exact construction identities;
- recording unresolved final identity and sealing questions;
- preventing fabricated digests and acceptance claims.

No generic identity artifacts are required to be accepted in this phase.

## Phase 1 â Identity construction skeleton

Create the generic identity authority area and placeholders:

```text
authoritative/identity/
âââ IDENTITY-MODEL.json
âââ CANONICAL-JSON.json
âââ IDENTITY-FAMILY-MODEL.json
âââ IDENTITY-VERIFICATION.json
```

Add:

```text
authoritative/schemas/identity/
derived/markdown/identity/
validation/fixtures/identity/
validation/tests/test_identity_construction.py
validation/intrinsic/validate_identity_construction.py
```

Requirements:

- every artifact remains `under-construction`;
- every artifact is explicitly non-normative;
- the root construction manifest declares all identity artifacts;
- artifact identities and paths are functional;
- exact closed field sets are used;
- no final digests or sealing claims are introduced;
- no GVE-specific identity family is copied into generic authority;
- no runtime code depends on the construction artifacts.

Validation should prove:

- required identity artifacts exist;
- construction identities are unique;
- unknown fields fail;
- false normative status fails;
- historical names fail;
- paths remain contained;
- required relationships close;
- duplicated domain prefixes fail;
- ambiguous reference declarations fail;
- incomplete aggregate declarations fail.

## Phase 2 â Generic identity semantic model

Replace the Phase 1 placeholders with substantive, still non-normative
construction content.

Define:

- identity representation;
- canonical JSON behavior;
- digest-algorithm declarations;
- domain-prefix requirements;
- family declarations;
- own-identity handling;
- reference semantics;
- object and aggregate semantics;
- verification contexts;
- fail-closed conditions.

Add temporary construction schemas and positive/negative vectors.

Requirements:

- all semantics map to accepted GVE behavior or are explicitly identified as
  repository-generic design decisions;
- copied GVE behavior and newly generalized behavior are visibly distinguished;
- every generalized rule has evidence;
- unresolved ownership questions remain explicit;
- no accepted GVE family is altered.

## Phase 3 â Reusable validation library

Create reusable mechanisms:

```text
validation/lib/canonical_json.py
validation/lib/identity_family.py
validation/lib/identity_verification.py
validation/lib/identity_evidence.py
```

Responsibilities:

- strict JSON loading;
- canonical JSON byte production;
- family registry loading;
- unique semantic-domain and prefix checks;
- identity derivation;
- identity parsing;
- embedded-value recomputation;
- verified-context handling;
- aggregate validation;
- structured evidence reporting.

The library must remain independent of maintained GVE product code.

The construction tree must not import from `src/gve`.

## Phase 4 â Generic identity conformance

Add construction conformance vectors:

```text
authoritative/conformance/identity/
âââ canonical-json/
âââ domain-separation/
âââ family-definition/
âââ reference-semantics/
âââ aggregate-semantics/
âââ verification-context/
```

Required vector classes:

- canonical JSON success and rejection;
- same value under different domains;
- unknown family;
- duplicated domain prefix;
- own-identity omission;
- by-value reference;
- by-identity reference;
- identity-plus-value mismatch;
- ordered aggregate order change;
- unordered aggregate order invariance;
- duplicate members;
- missing members;
- empty aggregate;
- direct versus transitive closure;
- missing verification context;
- family conflict;
- unaccepted identity;
- duplicate verification record;
- self-reference;
- aggregate cycle.

At this stage vectors are construction vectors, not accepted conformance
authority.

## Phase 5 â Specification identity profile

After specification artifact classes are defined, create:

```text
authoritative/specification-system/SPECIFICATION-IDENTITIES.json
```

Define candidate families for:

- specification document;
- specification-set revision;
- manifest;
- schema;
- projection;
- conformance artifact;
- validation artifact;
- sealed specification set.

Resolve:

- direct membership;
- ordering;
- duplicate handling;
- manifest self-reference;
- projection binding;
- schema binding;
- accepted revision derivation;
- governing-revision verification.

This phase is the prerequisite for a final repository-specification manifest.

## Phase 6 â Self-reference and manifest hardening

Define the final bootstrap model.

Required decisions:

- whether the manifest is a member of its own aggregate;
- whether self-reference uses omission, canonical reference, or an external
  sealing envelope;
- how identity definitions identify themselves;
- how schemas and vectors are bound;
- how derived projections are proved fresh;
- how accepted revision identity is recomputed;
- how a sealed parent manifest binds the repo-specification subtree.

Add hardening checks for:

- stale member identity;
- stale projection;
- incomplete manifest;
- duplicate member;
- circular manifest reference;
- incorrect governing revision;
- unverifiable schema or vector binding.

## Phase 7 â Repository identity profile

After repository-model semantics exist, create:

```text
authoritative/repository-model/REPOSITORY-IDENTITIES.json
```

Define candidate families only after these are settled:

- repository-area membership;
- repository-tree membership;
- path normalization;
- symlink policy;
- generated-artifact policy;
- maintained-artifact policy;
- ordering significance;
- direct versus transitive tree closure;
- initialization and copy semantics.

Do not make filesystem paths identity inputs by default.

Path significance must be an explicit family decision.

## Phase 8 â Development and normative-change profiles

After development-process and normative-change authority exists, define identity
profiles for their portable semantic objects.

Keep host-platform identifiers separate:

```text
GitHub issue number
GitHub pull-request number
Git commit ID
branch name
filesystem path
executor operation_id
```

These may be evidence or implementation identifiers, but they are not portable
semantic identities unless a governing family explicitly includes them.

## Phase 9 â Repository validation and initialization

Extend repository validation to verify:

- generic identity authority;
- identity profiles;
- manifest membership;
- repository tree identities;
- derived projection identities;
- conformance evidence;
- initialization identity preservation;
- dependency-closed copying;
- target manifest derivation;
- standalone identity validation in initialized repositories.

Initialization must explicitly classify each identity as:

- preserved;
- recomputed;
- source-bound;
- target-bound;
- not portable.

## Phase 10 â Hardening and acceptance

Before normative acceptance:

- replace construction envelopes with final schemas;
- close all references;
- freeze accepted vectors;
- verify deterministic projections;
- remove temporary identity exceptions;
- prove no product-specific families leaked into portable authority;
- prove generic validators are independent from GVE runtime code;
- run validation against both the GVE repository and a minimal initialized
  repository;
- recompute all identities from clean source;
- verify exact accepted-main state;
- seal the subtree into its parent manifest.

Acceptance must be a separate governed effort from construction.

## Phase 11 â Cutover

At final cutover:

- the complete `specification-system/` tree replaces the current accepted
  specification tree only through explicit authority;
- generic identity authority becomes normative;
- profile identities become normative;
- accepted vectors become immutable;
- derived projections become reproducible;
- manifests and aggregate revisions become authoritative;
- temporary construction identities and statuses are removed;
- compatibility and migration behavior is explicit.

No cutover is implied by completion of earlier phases.

## Validation architecture

### Intrinsic identity validation

Checks only the repository-specification subtree:

- artifact completeness;
- schema conformance;
- family uniqueness;
- semantic-domain uniqueness;
- domain-prefix uniqueness;
- explicit canonicalization and digest algorithm;
- own-identity declaration;
- reference declaration;
- aggregate completeness;
- cycle rejection;
- reference closure;
- verification-context structure;
- deterministic derivation;
- manifest coverage;
- projection freshness.

### Repository identity validation

Checks an external repository:

- required identity authority exists;
- repository identity profiles match repository structure;
- specification revision matches accepted specification members;
- maintained source and generated artifacts are classified;
- initialization and copying preserve or recompute identities correctly;
- no forbidden identity-bearing path is present;
- all referenced identities are verifiable.

### Evidence reporting

Identity validation should emit structured evidence containing:

- family;
- semantic domain;
- canonicalization version;
- digest algorithm;
- domain prefix identifier;
- canonical input classification;
- computed identity;
- supplied identity;
- verification mode;
- verification-context summary;
- aggregate membership summary;
- governing revision;
- pass/fail status;
- deterministic diagnostic code.

Sensitive or excessively large canonical values should not be emitted by
default.

## Hardening principles

### One source of generic mechanics

Canonicalization, family declaration, reference modes, aggregate rules, and
verification contexts must be defined once in generic identity authority.

Profiles must reference those mechanics rather than restate them.

### No product leakage

Portable repository authority must not depend on GVE product modules, operation
types, or product-specific family names.

### No implicit identity behavior

Every family must declare:

- what is identified;
- what is omitted;
- what is referenced;
- how references are encoded;
- whether order matters;
- what closure means;
- what context is required.

### No raw-digest fallback

A missing or unknown family is an error.

A plain digest must never be silently interpreted as a semantic identity.

### No path-default assumption

Paths are not identity inputs unless the family explicitly declares them.

### No automatic transitive closure

The default aggregate closure remains direct unless a family explicitly
requires transitive closure and defines cycle behavior.

### No circular acceptance

Construction identities, candidate identities, accepted identities, aggregate
revisions, and sealing identities must remain distinct stages.

## Issue boundaries

Each phase should be implemented through one or more bounded issues.

A single issue should not combine:

- generic identity mechanics;
- specification profile design;
- repository profile design;
- manifest bootstrap;
- sealing;
- initialization;
- product-family migration;
- final cutover.

Recommended issue sequence:

1. establish identity construction skeleton;
2. define canonical JSON construction model;
3. define identity-family construction model;
4. define verification and aggregate construction model;
5. create reusable identity validation library;
6. add generic construction vectors;
7. define specification identity profile;
8. define self-reference and manifest bootstrap;
9. harden manifest and revision validation;
10. define repository identity profile;
11. define development and normative-change profiles;
12. define initialization identity behavior;
13. perform identity hardening;
14. perform normative acceptance and cutover.

## Completion criteria

### Identity skeleton complete

- every intended generic identity directory exists;
- every generic identity artifact has a functional placeholder;
- the construction manifest covers all identity artifacts;
- intrinsic validation detects missing or malformed identity skeleton elements;
- no artifact claims normative acceptance;
- no GVE-specific family is presented as portable authority.

### Generic identity content complete

- canonicalization is explicit;
- domain separation is explicit;
- family structure is complete;
- own-identity handling is explicit;
- reference modes are complete;
- aggregate rules are complete;
- verification contexts are complete;
- all generic vectors pass;
- all references close;
- projections reproduce;
- generic validators are product-independent.

### Profile complete

- specification identities are defined;
- repository identities are defined;
- development and normative-change identities are defined where required;
- every profile derives from generic identity authority;
- no profile duplicates generic mechanics;
- manifest and revision identities are deterministic.

### Hardening complete

- bootstrap and self-reference are non-circular;
- accepted vectors are frozen;
- stale projections and stale identities fail;
- initialization behavior is explicit;
- repository validation passes on GVE and a minimal initialized repository;
- all accepted identities recompute;
- the subtree can be sealed into its parent manifest.

## Explicit non-goals

This plan does not authorize:

- changing current accepted GVE identity semantics;
- migrating existing GVE identities;
- adding new GVE product families;
- replacing current validation tooling immediately;
- treating temporary construction artifacts as normative;
- making Git or GitHub identifiers portable semantic identities;
- making every repository path identity-bearing;
- combining identity construction with final repository-specification cutover.

## Immediate next step

The next bounded implementation should establish only the identity construction
skeleton and extend the temporary construction manifest and validator.

It should create:

```text
authoritative/identity/
âââ IDENTITY-MODEL.json
âââ CANONICAL-JSON.json
âââ IDENTITY-FAMILY-MODEL.json
âââ IDENTITY-VERIFICATION.json

authoritative/schemas/identity/
derived/markdown/identity/
validation/fixtures/identity/
validation/intrinsic/validate_identity_construction.py
validation/tests/test_identity_construction.py
```

All artifacts should remain non-normative and under construction.

That step gives future repository-specification hardening a stable identity
boundary without prematurely defining specification, repository, governance, or
product identity families.
