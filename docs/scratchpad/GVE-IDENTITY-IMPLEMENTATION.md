# Current Normative GVE Identity Implementation

## Status

Non-normative scratchpad.

This document is planning evidence only. It describes the current accepted GVE identity implementation as observed at accepted repository revision:

```text
9f69559e6288462fdff4ca386837c261829e4bb2
```

The accepted normative JSON specification graph remains authoritative. Where this document conflicts with normative JSON, schemas, accepted vectors, or validated repository state, those accepted artifacts control.

## Purpose

GVE already has a repository-integrated identity framework. That framework is not merely a generic SHA-256 convention. It defines a family-qualified representation, canonical JSON, domain-separated preimages, explicit identity families, object and aggregate semantics, verification contexts, fail-closed rejection rules, and repository bindings.

This scratchpad records that functional system so later repository-specification work can preserve accepted behavior rather than rediscover or accidentally redesign it.

## Authority and artifact classes

The current identity system is distributed across several repository artifacts:

| Artifact | Functional role |
|---|---|
| `specs/identity/GVE-IDENTITY-FRAMEWORK.json` | Normative identity framework. |
| `specs/schemas/GVE-IDENTITY-FRAMEWORK.schema.json` | Structural schema for the normative framework. |
| `specs/identity/GVE-IDENTITY-FRAMEWORK.md` | Deterministic human-readable projection. |
| `specs/tests/fixtures/issue_76/identity_vectors.json` | Accepted positive and negative vectors. |
| `specs/SPECIFICATION-SET.json` | Manifest binding for the framework, schema, projection, vectors, and specification revision. |
| `specs/levels/level-2/GVE-LEVEL-2-DOCUMENT-AUTHORITY.json` | Governing normative requirements. |
| `specs/tooling/validate_identity.py` | Repository identity validation entry point. |
| `scripts/validate` | Complete-gate integration. |
| Maintained modules and tests | Derive, verify, and reject identities at governed-operation boundaries. |

Normative JSON controls. Schemas constrain normative structure. Vectors define accepted examples. Markdown is derived. Source and tests implement and verify accepted semantics but do not override normative authority.

## Core representation

A GVE identity has the functional form:

```text
<family>-<algorithm>:<digest>
```

The accepted framework currently uses:

```text
canonicalization: gve-canonical-json-v1
digest algorithm: sha256
digest encoding: lowercase hexadecimal
```

The family qualifier identifies one semantic domain. A raw SHA-256 digest is therefore not equivalent to a GVE identity.

A GVE identity binds:

1. an identity family;
2. a canonicalization version;
3. a digest algorithm;
4. a family-specific domain prefix;
5. a family-defined canonical value;
6. family-specific own-identity, reference, aggregate, version, and verification rules.

## Canonicalization

The accepted canonicalization version is `gve-canonical-json-v1`.

Functionally, it requires:

- UTF-8 JSON;
- object members ordered by ascending Unicode code-point sequence;
- preserved array order;
- omitted insignificant whitespace;
- rejection of floating-point values;
- rejection of surrogate code points;
- rejection of non-string object keys;
- no implicit Unicode normalization.

Canonicalization is explicit and versioned. A family cannot silently substitute another canonicalization rule.

## Domain-separated preimage

The canonical preimage is:

```text
domain-prefix-bytes || canonical-value-bytes
```

The domain prefix is UTF-8 and includes a terminating NUL byte. Each family has one unique domain prefix.

Two identical canonical JSON values therefore produce different identities when used in different semantic domains. Cross-domain substitution is rejected.

## Family declaration model

Each accepted family declares:

- family identifier;
- semantic domain;
- domain-separation prefix;
- canonicalization version;
- digest algorithm;
- canonical value source;
- own-identity paths;
- reference paths;
- reference encoding;
- allowed reference families;
- aggregate encoding, when applicable;
- governing-version bindings;
- verification mode and context source;
- object kind;
- aggregate semantics, when applicable.

Implicit handling is prohibited.

## Own-identity handling

The framework permits family-declared modes:

- `include`
- `omit-own-identity`
- `canonical-reference`

Most current families use `identity` as the own-identity path. `gve-authoritative-result` uses `result_identity`.

The purpose is to avoid circular hashing while keeping the derivation rule explicit and testable.

## Reference semantics

The accepted framework supports three reference modes.

### By value

The referenced value participates directly in the canonical input.

### By identity

Only the referenced identity participates in the canonical input. The caller must supply authoritative verification context proving that the identity exists, belongs to the expected family, and is accepted.

### Identity plus value

Both the referenced identity and embedded value participate. The implementation recomputes the referenced identity from the embedded value and rejects a mismatch.

Ambiguous reference handling is prohibited.

## Object and aggregate kinds

The framework supports:

- `object`
- `ordered-aggregate`
- `unordered-aggregate`

Aggregate families must define:

- membership;
- ordering significance;
- duplicate policy;
- closure boundary;
- member reference mode;
- empty-aggregate rule;
- cycle policy;
- membership path;
- member identity path;
- member value path;
- member verification mode.

The accepted v1 aggregate closure boundary is direct. Aggregate identity does not silently imply transitive closure.

## Verification contexts

Two major patterns are used.

### Embedded-value recomputation

The identified value contains both a referenced identity and enough embedded value to recompute it. The implementation recomputes the reference under the declared family and rejects mismatches.

### Caller-supplied verified identity set

The canonical input contains an identity reference without the full referenced value. The caller supplies records containing:

```text
identity
family_id
accepted
```

That context is external to the canonical preimage.

The implementation rejects missing context, missing identities, unknown families, family conflicts, unaccepted identities, and duplicate context records.

## Current accepted identity families

### `gve-spec-document`

- **Semantic domain:** normative specification document.
- **Kind:** object.
- **Input:** complete object.
- **References:** by value.
- **Verification:** no separate external identity verification.
- **Purpose:** identifies one normative specification document.

### `gve-spec-revision`

- **Semantic domain:** governing specification-set revision.
- **Kind:** unordered aggregate.
- **Members:** every accepted normative specification document exactly once.
- **Member family:** `gve-spec-document`.
- **Ordering:** insignificant.
- **Duplicates:** rejected.
- **Closure:** direct.
- **Member references:** by identity.
- **Verification:** caller-supplied verified identity set.
- **Purpose:** identifies the accepted normative specification graph as a complete set of verified document identities.

### `gve-governance-composition`

- **Semantic domain:** governed authority composition.
- **Kind:** ordered aggregate.
- **Members:** directly composed governed contracts in declared order.
- **Member family:** `gve-contract`.
- **Reference mode:** identity plus value.
- **Verification:** embedded-value recomputation.
- **Purpose:** identifies an ordered composition of governed contracts.

### `gve-effect`

- **Semantic domain:** exact governed effect.
- **Kind:** object.
- **Allowed reference family:** `gve-contract`.
- **Reference mode:** by identity.
- **Verification:** caller-supplied verified identity set.
- **Purpose:** identifies the exact governed effect authorized by verified contracts.

### `gve-plan`

- **Semantic domain:** accepted governed plan.
- **Kind:** object.
- **Reference mode:** by value.
- **Verification:** no separate external identity verification.
- **Purpose:** identifies an accepted governed plan without circular dependence on a later contract.

### `gve-contract`

- **Semantic domain:** governed contract.
- **Kind:** object.
- **Allowed reference family:** `gve-effect`.
- **Reference mode:** identity plus value.
- **Verification:** embedded-value recomputation.
- **Purpose:** binds a contract to the exact effects it authorizes.

### `gve-production`

- **Semantic domain:** governed production.
- **Kind:** object.
- **Allowed reference family:** `gve-contract`.
- **Reference mode:** identity plus value.
- **Verification:** embedded-value recomputation.
- **Purpose:** identifies governed production bound to verified contracts.

### `gve-evidence`

- **Semantic domain:** admitted evidence record.
- **Kind:** object.
- **Allowed reference family:** `gve-production`.
- **Reference mode:** identity plus value.
- **Verification:** embedded-value recomputation.
- **Purpose:** binds evidence to the governed production from which it arose.

### `gve-execution-record`

- **Semantic domain:** authoritative governed execution record.
- **Kind:** object.
- **Allowed reference family:** `gve-evidence`.
- **Reference mode:** identity plus value.
- **Verification:** embedded-value recomputation.
- **Purpose:** identifies an execution record and binds it to admitted evidence.

### `gve-authoritative-result`

- **Semantic domain:** authoritative governed result.
- **Kind:** object.
- **Own-identity field:** `result_identity`.
- **Allowed reference family:** `gve-execution-record`.
- **Reference mode:** identity plus value.
- **Verification:** embedded-value recomputation.
- **Purpose:** identifies an authoritative result while avoiding self-reference.

### `gve-finalization`

- **Semantic domain:** governed result finalization.
- **Kind:** object.
- **Allowed reference family:** `gve-authoritative-result`.
- **Reference mode:** identity plus value.
- **Verification:** embedded-value recomputation.
- **Governing revision binding:** exact `gve-spec-revision` supplied through verification context.
- **Purpose:** binds finalization to both the authoritative result and the exact governing specification revision.

## Functional lifecycle

A conforming derivation or verification follows this sequence:

1. Select the applicable accepted family.
2. Validate family existence and applicability.
3. Resolve canonicalization, digest, and governing-revision bindings.
4. Build the family-defined canonical value.
5. Handle own-identity paths explicitly.
6. Resolve references using the declared reference mode.
7. Validate aggregate membership, order, duplicates, emptiness, closure, and cycles.
8. Canonicalize under `gve-canonical-json-v1`.
9. Prepend the family-specific domain prefix.
10. Compute SHA-256 and encode lowercase hexadecimal.
11. Format the family-qualified identity.
12. Compare with the supplied or embedded identity.
13. Reject any missing, ambiguous, circular, cross-domain, unsupported, or unverifiable condition.

## Important non-equivalences

### Functional names are not cryptographic identities

Names such as `GVE-IDENTITY-FRAMEWORK`, requirement IDs, repository paths, and filenames are functional identifiers or locations.

### Content digests are not automatically GVE identities

A `content_sha256` value binds content under a manifest rule. It is not automatically the same as a family-qualified GVE identity.

### Paths are not automatically identity inputs

A path matters only when a family explicitly includes it in the canonical input or a governing manifest binds it separately.

### Git identities are not GVE semantic identities

Git commit IDs, tree IDs, blob IDs, branches, issue numbers, PR numbers, and filenames are not GVE family identities unless accepted authority explicitly makes them inputs.

### Operation IDs are operational identifiers

Executor `operation_id` values must not be treated as normative family identities merely because they are unique strings.

### Direct closure is not transitive closure

The accepted v1 aggregate boundary is direct.

### Document identity differs from specification revision identity

`gve-spec-document` identifies one normative document value. `gve-spec-revision` identifies the accepted set of verified document identities.

## Fail-closed conditions

The framework rejects at least:

- missing or unknown families;
- missing or non-unique domain prefixes;
- cross-domain substitution;
- missing or unsupported canonicalization versions;
- missing or unsupported digest algorithms;
- ambiguous references;
- implicit own-identity handling;
- incomplete aggregate membership;
- self-reference;
- circular aggregate identity;
- mismatched family;
- missing or unverifiable identity;
- missing verification context;
- unaccepted references;
- duplicate verification records;
- forbidden aggregate duplicates or cycles.

Identity uncertainty is an error, not permission to fall back to a raw digest or best-effort interpretation.

## Repository integration

The accepted framework requires:

- normative manifest binding;
- deterministic Markdown projection;
- normal repository validation;
- fixed positive and negative vectors;
- immutable accepted vectors;
- explicit handling of identity migration.

The current framework records identity migration as deferred. Older artifacts therefore are not silently rewritten without separate authority.

## Maintained implementation responsibilities

### Canonical JSON

- enforce the accepted JSON value domain;
- produce deterministic bytes;
- reject unsupported values.

### Family registry

- load accepted family definitions;
- reject unknown families;
- validate unique semantic domains and domain prefixes;
- expose family-specific rules.

### Identity derivation

- construct the canonical value;
- apply own-identity handling;
- apply reference encoding;
- prepend domain separation;
- digest and format.

### Identity verification

- validate representation;
- verify the expected family;
- recompute embedded references;
- consume verified identity context for by-identity references;
- verify exact governing specification revision where required.

### Aggregate validation

- enforce membership and order;
- reject duplicates and cycles;
- enforce direct closure;
- verify each member identity under the declared mode.

### Repository validation

- validate the framework against its schema;
- validate manifest bindings and stored hashes;
- validate deterministic projection;
- run fixed vectors;
- validate specification revision identity;
- reject stale or inconsistent identity evidence.

### Governed-operation integration

- derive and verify plan, contract, effect, production, evidence, execution, result, and finalization identities at the appropriate boundary;
- prevent duplicate or replayed identities where accepted semantics require it;
- keep operational IDs separate from normative semantic identities.

## Repository-specification implications

The temporary repository-specification system must not invent an independent identity scheme.

Future work must preserve:

- family-qualified identities;
- domain separation;
- explicit canonicalization versions;
- explicit digest algorithms;
- explicit own-identity handling;
- explicit reference modes;
- object and aggregate distinctions;
- direct closure semantics;
- verification-context boundaries;
- governing specification-revision bindings;
- fail-closed circularity and ambiguity rules.

Identity ownership in the future repository-specification tree remains unresolved. It may become a dedicated identity authority, or it may remain under specification-system authority with explicit cross-family references. The choice must be governed and cannot be inferred merely from the current path `specs/identity/`.

The following later artifacts should not become substantive until that mapping is resolved:

- repository manifest model;
- specification authoring model;
- self-reference and bootstrap model;
- sealing and aggregate revision model;
- normative-change identity rules;
- initialization and copying identity preservation;
- repository conformance evidence;
- deterministic projection identity and freshness rules.

## Open questions

### Mapping questions answerable from current authority

- Which family definitions are portable repository semantics?
- Which are GVE-product-specific?
- Which maintained modules consume each family?
- Which older artifacts remain outside the unified framework because migration is deferred?
- Which checks are family-semantic checks versus repository-integration checks?

### Genuine future normative questions

- Should repository artifacts have a dedicated family?
- Should repository trees be ordered or unordered aggregates?
- Are paths canonical inputs, contextual metadata, or both?
- How are initialized copies related to source repository identities?
- Which identities survive portable copying?
- Does final repository sealing use direct or transitive closure?
- How are derived projections identified and bound to authoritative sources?
- How does the future repository manifest identify itself without circular construction?
- Which families belong to portable repository authority versus GVE product authority?

### Non-semantic implementation cleanup questions

- Can family loading and validation be consolidated without changing semantics?
- Can repository validation emit one structured identity-evidence report?
- Can vector diagnostics be localized while preserving exact pass/fail behavior?
- Can consumers share one derivation API without weakening family-specific rules?

## Evidence map

| Functional statement | Primary evidence |
|---|---|
| Family-qualified representation | `specs/identity/GVE-IDENTITY-FRAMEWORK.json` |
| Canonical JSON rules | `specs/identity/GVE-IDENTITY-FRAMEWORK.json` |
| Domain-separated preimage | `specs/identity/GVE-IDENTITY-FRAMEWORK.json` |
| Own-identity and reference modes | `specs/identity/GVE-IDENTITY-FRAMEWORK.json` |
| Object and aggregate kinds | `specs/identity/GVE-IDENTITY-FRAMEWORK.json` |
| Accepted family inventory | `specs/identity/GVE-IDENTITY-FRAMEWORK.json` |
| Fixed positive and negative behavior | `specs/tests/fixtures/issue_76/identity_vectors.json` |
| Framework structural constraints | `specs/schemas/GVE-IDENTITY-FRAMEWORK.schema.json` |
| Governing requirements | `specs/levels/level-2/GVE-LEVEL-2-DOCUMENT-AUTHORITY.json` |
| Specification-set participation | `specs/SPECIFICATION-SET.json` |
| Human-readable projection | `specs/identity/GVE-IDENTITY-FRAMEWORK.md` |
| Identity repository validation | `specs/tooling/validate_identity.py` |
| Complete-gate integration | `scripts/validate` |
| Governed-operation consumers | maintained modules under `src/gve/` and `src/scf_governed_executor/` |
| Behavioral tests | identity-related tests under `specs/tests/`, `tests/core/`, and `tests/governed_executor/` |

## Promotion boundary

This scratchpad does not authorize:

- a new family;
- changed canonical inputs;
- changed canonicalization;
- a new digest algorithm;
- changed closure semantics;
- changed verification context;
- identity migration;
- repository-specification ownership;
- manifest or sealing changes;
- runtime changes.

Any such work requires accepted authority interpretation, bounded governed scope, exact evidence, schemas, vectors, implementation changes where required, and clean accepted-main validation.
