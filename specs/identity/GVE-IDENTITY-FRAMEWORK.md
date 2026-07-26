# GVE Unified Domain-Separated Identity Framework

> This Markdown is a deterministic projection of `GVE-IDENTITY-FRAMEWORK.json`. The JSON is normative.

## Authority

- Governing specification: `GVE-LEVEL-2-DOCUMENT-AUTHORITY`
- Integration state: `repository-integrated`

## Representation

- Syntax: `<family>-<algorithm>:<digest>`
- Digest encoding: `lowercase-hex`

## Identity Families

### `gve-spec-document`

- Semantic domain: `normative-specification-document`
- Domain prefix: `gve/spec-document/v1\0`
- Canonicalization: `gve-canonical-json-v1`
- Digest: `sha256`
- Reference encoding: `by-value`
- Own identity paths: `identity`
- Reference paths: `references`
- Object kind: `object`

### `gve-spec-revision`

- Semantic domain: `governing-specification-set-revision`
- Domain prefix: `gve/spec-revision/v1\0`
- Canonicalization: `gve-canonical-json-v1`
- Digest: `sha256`
- Reference encoding: `identity-plus-value`
- Own identity paths: `identity`
- Reference paths: `(none)`
- Object kind: `unordered-aggregate`

### `gve-governance-composition`

- Semantic domain: `governed-authority-composition`
- Domain prefix: `gve/governance-composition/v1\0`
- Canonicalization: `gve-canonical-json-v1`
- Digest: `sha256`
- Reference encoding: `identity-plus-value`
- Own identity paths: `identity`
- Reference paths: `references`
- Object kind: `ordered-aggregate`

### `gve-effect`

- Semantic domain: `exact-governed-effect`
- Domain prefix: `gve/effect/v1\0`
- Canonicalization: `gve-canonical-json-v1`
- Digest: `sha256`
- Reference encoding: `by-identity`
- Own identity paths: `identity`
- Reference paths: `references`
- Object kind: `object`

### `gve-plan`

- Semantic domain: `accepted-governed-plan`
- Domain prefix: `gve/plan/v1\0`
- Canonicalization: `gve-canonical-json-v1`
- Digest: `sha256`
- Reference encoding: `by-value`
- Own identity paths: `identity`
- Reference paths: `references`
- Object kind: `object`

### `gve-contract`

- Semantic domain: `governed-contract`
- Domain prefix: `gve/contract/v1\0`
- Canonicalization: `gve-canonical-json-v1`
- Digest: `sha256`
- Reference encoding: `identity-plus-value`
- Own identity paths: `identity`
- Reference paths: `references`
- Object kind: `object`

### `gve-production`

- Semantic domain: `governed-production`
- Domain prefix: `gve/production/v1\0`
- Canonicalization: `gve-canonical-json-v1`
- Digest: `sha256`
- Reference encoding: `identity-plus-value`
- Own identity paths: `identity`
- Reference paths: `references`
- Object kind: `object`

### `gve-evidence`

- Semantic domain: `admitted-evidence-record`
- Domain prefix: `gve/evidence/v1\0`
- Canonicalization: `gve-canonical-json-v1`
- Digest: `sha256`
- Reference encoding: `identity-plus-value`
- Own identity paths: `identity`
- Reference paths: `references`
- Object kind: `object`

### `gve-execution-record`

- Semantic domain: `authoritative-governed-execution-record`
- Domain prefix: `gve/execution-record/v1\0`
- Canonicalization: `gve-canonical-json-v1`
- Digest: `sha256`
- Reference encoding: `identity-plus-value`
- Own identity paths: `identity`
- Reference paths: `references`
- Object kind: `object`

### `gve-authoritative-result`

- Semantic domain: `authoritative-governed-result`
- Domain prefix: `gve/authoritative-result/v1\0`
- Canonicalization: `gve-canonical-json-v1`
- Digest: `sha256`
- Reference encoding: `identity-plus-value`
- Own identity paths: `result_identity`
- Reference paths: `references`
- Object kind: `object`

### `gve-finalization`

- Semantic domain: `governed-result-finalization`
- Domain prefix: `gve/finalization/v1\0`
- Canonicalization: `gve-canonical-json-v1`
- Digest: `sha256`
- Reference encoding: `identity-plus-value`
- Own identity paths: `identity`
- Reference paths: `references`
- Object kind: `object`

## Fail-Closed Conditions

- `missing-family`
- `unknown-family`
- `missing-domain-prefix`
- `cross-domain-substitution`
- `missing-canonicalization-version`
- `unsupported-canonicalization-version`
- `missing-digest-algorithm`
- `unsupported-digest-algorithm`
- `ambiguous-reference-semantics`
- `implicit-embedded-identity-handling`
- `incomplete-aggregate-membership`
- `self-referential-identity`
- `circular-aggregate-identity`
- `mismatched-identity-family`
- `unverifiable-identity`

## Canonical Normative JSON

```json
{
  "$schema": "../schemas/GVE-IDENTITY-FRAMEWORK.schema.json",
  "aggregate_semantics": {
    "cycle_policy": "reject",
    "incomplete_membership_policy": "reject",
    "required_for_aggregate_kinds": [
      "membership",
      "ordering_significance",
      "duplicate_policy",
      "closure_boundary",
      "member_reference_mode",
      "empty_aggregate_rule",
      "cycle_policy",
      "membership_path",
      "member_identity_path",
      "member_value_path"
    ]
  },
  "authority": {
    "governing_requirement_ids": [
      "L2-DA-REQ-013",
      "L2-DA-REQ-014",
      "L2-DA-REQ-015",
      "L2-DA-REQ-016",
      "L2-DA-REQ-017",
      "L2-DA-REQ-020",
      "L2-DA-REQ-021",
      "L2-DA-REQ-022",
      "L2-DA-REQ-023"
    ],
    "governing_specification": "GVE-LEVEL-2-DOCUMENT-AUTHORITY",
    "integration_state": "repository-integrated",
    "status": "normative-framework-core"
  },
  "canonical_preimage": {
    "canonicalization_version_required": true,
    "construction": "domain-prefix-bytes || canonical-value-bytes",
    "digest_algorithm_required": true,
    "domain_prefix_encoding": "utf-8",
    "domain_prefix_terminator": "nul",
    "family_definition_required": true
  },
  "canonicalization_versions": [
    {
      "array_order": "preserved",
      "encoding": "utf-8",
      "floating_point": "rejected",
      "id": "gve-canonical-json-v1",
      "insignificant_whitespace": "omitted",
      "media_type": "application/json",
      "non_string_object_keys": "rejected",
      "object_member_order": "ascending-unicode-code-point-sequence",
      "surrogate_code_points": "rejected",
      "unicode_normalization": "none"
    }
  ],
  "digest_algorithms": [
    {
      "digest_bits": 256,
      "encoded_length": 64,
      "encoding": "lowercase-hex",
      "id": "sha256"
    }
  ],
  "embedded_identity_rules": {
    "implicit_handling_prohibited": true,
    "per_family_declaration_required": true,
    "permitted_modes": [
      "include",
      "omit-own-identity",
      "canonical-reference"
    ]
  },
  "fail_closed_conditions": [
    "missing-family",
    "unknown-family",
    "missing-domain-prefix",
    "cross-domain-substitution",
    "missing-canonicalization-version",
    "unsupported-canonicalization-version",
    "missing-digest-algorithm",
    "unsupported-digest-algorithm",
    "ambiguous-reference-semantics",
    "implicit-embedded-identity-handling",
    "incomplete-aggregate-membership",
    "self-referential-identity",
    "circular-aggregate-identity",
    "mismatched-identity-family",
    "unverifiable-identity"
  ],
  "fixed_vectors": {
    "canonicalization_version": "gve-canonical-json-v1",
    "digest_algorithm": "sha256",
    "immutable_after_acceptance": true,
    "negative_vectors_required": true,
    "path": "tests/fixtures/issue_76/identity_vectors.json",
    "positive_vectors_required": true
  },
  "framework_invariants": {
    "canonicalization_version_explicit": true,
    "circular_construction_prohibited": true,
    "cross_domain_substitution_prohibited": true,
    "digest_algorithm_explicit": true,
    "domain_prefixes_unique": true,
    "future_families_must_derive_from_framework": true,
    "one_canonical_preimage_per_family": true,
    "one_domain_prefix_per_family": true,
    "one_semantic_domain_per_family": true
  },
  "identity_families": [
    {
      "aggregate": null,
      "canonicalization_version": "gve-canonical-json-v1",
      "digest_algorithm": "sha256",
      "domain_separation_prefix": "gve/spec-document/v1\u0000",
      "id": "gve-spec-document",
      "object_kind": "object",
      "preimage": {
        "aggregate_encoding": null,
        "allowed_reference_family_ids": [],
        "own_identity_paths": [
          "identity"
        ],
        "reference_encoding": "by-value",
        "reference_paths": [
          "references"
        ],
        "value_source": "complete-object",
        "version_bindings": {
          "canonicalization": true,
          "governing_specification_revision": false
        }
      },
      "semantic_domain": "normative-specification-document"
    },
    {
      "aggregate": {
        "closure_boundary": "direct",
        "cycle_policy": "reject",
        "duplicate_policy": "reject",
        "empty_aggregate_rule": "reject",
        "member_family_ids": [
          "gve-spec-document"
        ],
        "member_identity_path": "document_identity",
        "member_reference_mode": "by-identity",
        "member_value_path": null,
        "membership": "every accepted normative specification document exactly once",
        "membership_path": "members",
        "ordering_significance": "unordered"
      },
      "canonicalization_version": "gve-canonical-json-v1",
      "digest_algorithm": "sha256",
      "domain_separation_prefix": "gve/spec-revision/v1\u0000",
      "id": "gve-spec-revision",
      "object_kind": "unordered-aggregate",
      "preimage": {
        "aggregate_encoding": "member-references",
        "allowed_reference_family_ids": [],
        "own_identity_paths": [
          "identity"
        ],
        "reference_encoding": "identity-plus-value",
        "reference_paths": [],
        "value_source": "complete-object",
        "version_bindings": {
          "canonicalization": true,
          "governing_specification_revision": false
        }
      },
      "semantic_domain": "governing-specification-set-revision"
    },
    {
      "aggregate": {
        "closure_boundary": "direct",
        "cycle_policy": "reject",
        "duplicate_policy": "reject",
        "empty_aggregate_rule": "reject",
        "member_family_ids": [
          "gve-contract"
        ],
        "member_identity_path": "identity",
        "member_reference_mode": "identity-plus-value",
        "member_value_path": "value",
        "membership": "every directly composed governed contract in declared order",
        "membership_path": "members",
        "ordering_significance": "ordered"
      },
      "canonicalization_version": "gve-canonical-json-v1",
      "digest_algorithm": "sha256",
      "domain_separation_prefix": "gve/governance-composition/v1\u0000",
      "id": "gve-governance-composition",
      "object_kind": "ordered-aggregate",
      "preimage": {
        "aggregate_encoding": "member-references",
        "allowed_reference_family_ids": [
          "gve-contract"
        ],
        "own_identity_paths": [
          "identity"
        ],
        "reference_encoding": "identity-plus-value",
        "reference_paths": [
          "references"
        ],
        "value_source": "complete-object",
        "version_bindings": {
          "canonicalization": true,
          "governing_specification_revision": false
        }
      },
      "semantic_domain": "governed-authority-composition"
    },
    {
      "aggregate": null,
      "canonicalization_version": "gve-canonical-json-v1",
      "digest_algorithm": "sha256",
      "domain_separation_prefix": "gve/effect/v1\u0000",
      "id": "gve-effect",
      "object_kind": "object",
      "preimage": {
        "aggregate_encoding": null,
        "allowed_reference_family_ids": [
          "gve-contract"
        ],
        "own_identity_paths": [
          "identity"
        ],
        "reference_encoding": "by-identity",
        "reference_paths": [
          "references"
        ],
        "value_source": "complete-object",
        "version_bindings": {
          "canonicalization": true,
          "governing_specification_revision": false
        }
      },
      "semantic_domain": "exact-governed-effect"
    },
    {
      "aggregate": null,
      "canonicalization_version": "gve-canonical-json-v1",
      "digest_algorithm": "sha256",
      "domain_separation_prefix": "gve/plan/v1\u0000",
      "id": "gve-plan",
      "object_kind": "object",
      "preimage": {
        "aggregate_encoding": null,
        "allowed_reference_family_ids": [],
        "own_identity_paths": [
          "identity"
        ],
        "reference_encoding": "by-value",
        "reference_paths": [
          "references"
        ],
        "value_source": "complete-object",
        "version_bindings": {
          "canonicalization": true,
          "governing_specification_revision": false
        }
      },
      "semantic_domain": "accepted-governed-plan"
    },
    {
      "aggregate": null,
      "canonicalization_version": "gve-canonical-json-v1",
      "digest_algorithm": "sha256",
      "domain_separation_prefix": "gve/contract/v1\u0000",
      "id": "gve-contract",
      "object_kind": "object",
      "preimage": {
        "aggregate_encoding": null,
        "allowed_reference_family_ids": [
          "gve-effect"
        ],
        "own_identity_paths": [
          "identity"
        ],
        "reference_encoding": "identity-plus-value",
        "reference_paths": [
          "references"
        ],
        "value_source": "complete-object",
        "version_bindings": {
          "canonicalization": true,
          "governing_specification_revision": false
        }
      },
      "semantic_domain": "governed-contract"
    },
    {
      "aggregate": null,
      "canonicalization_version": "gve-canonical-json-v1",
      "digest_algorithm": "sha256",
      "domain_separation_prefix": "gve/production/v1\u0000",
      "id": "gve-production",
      "object_kind": "object",
      "preimage": {
        "aggregate_encoding": null,
        "allowed_reference_family_ids": [
          "gve-contract"
        ],
        "own_identity_paths": [
          "identity"
        ],
        "reference_encoding": "identity-plus-value",
        "reference_paths": [
          "references"
        ],
        "value_source": "complete-object",
        "version_bindings": {
          "canonicalization": true,
          "governing_specification_revision": false
        }
      },
      "semantic_domain": "governed-production"
    },
    {
      "aggregate": null,
      "canonicalization_version": "gve-canonical-json-v1",
      "digest_algorithm": "sha256",
      "domain_separation_prefix": "gve/evidence/v1\u0000",
      "id": "gve-evidence",
      "object_kind": "object",
      "preimage": {
        "aggregate_encoding": null,
        "allowed_reference_family_ids": [
          "gve-production"
        ],
        "own_identity_paths": [
          "identity"
        ],
        "reference_encoding": "identity-plus-value",
        "reference_paths": [
          "references"
        ],
        "value_source": "complete-object",
        "version_bindings": {
          "canonicalization": true,
          "governing_specification_revision": false
        }
      },
      "semantic_domain": "admitted-evidence-record"
    },
    {
      "aggregate": null,
      "canonicalization_version": "gve-canonical-json-v1",
      "digest_algorithm": "sha256",
      "domain_separation_prefix": "gve/execution-record/v1\u0000",
      "id": "gve-execution-record",
      "object_kind": "object",
      "preimage": {
        "aggregate_encoding": null,
        "allowed_reference_family_ids": [
          "gve-evidence"
        ],
        "own_identity_paths": [
          "identity"
        ],
        "reference_encoding": "identity-plus-value",
        "reference_paths": [
          "references"
        ],
        "value_source": "complete-object",
        "version_bindings": {
          "canonicalization": true,
          "governing_specification_revision": false
        }
      },
      "semantic_domain": "authoritative-governed-execution-record"
    },
    {
      "aggregate": null,
      "canonicalization_version": "gve-canonical-json-v1",
      "digest_algorithm": "sha256",
      "domain_separation_prefix": "gve/authoritative-result/v1\u0000",
      "id": "gve-authoritative-result",
      "object_kind": "object",
      "preimage": {
        "aggregate_encoding": null,
        "allowed_reference_family_ids": [
          "gve-execution-record"
        ],
        "own_identity_paths": [
          "result_identity"
        ],
        "reference_encoding": "identity-plus-value",
        "reference_paths": [
          "references"
        ],
        "value_source": "complete-object",
        "version_bindings": {
          "canonicalization": true,
          "governing_specification_revision": false
        }
      },
      "semantic_domain": "authoritative-governed-result"
    },
    {
      "aggregate": null,
      "canonicalization_version": "gve-canonical-json-v1",
      "digest_algorithm": "sha256",
      "domain_separation_prefix": "gve/finalization/v1\u0000",
      "id": "gve-finalization",
      "object_kind": "object",
      "preimage": {
        "aggregate_encoding": null,
        "allowed_reference_family_ids": [
          "gve-authoritative-result"
        ],
        "own_identity_paths": [
          "identity"
        ],
        "reference_encoding": "identity-plus-value",
        "reference_paths": [
          "references"
        ],
        "value_source": "complete-object",
        "version_bindings": {
          "canonicalization": true,
          "governing_specification_revision": true
        }
      },
      "semantic_domain": "governed-result-finalization"
    }
  ],
  "object_kinds": {
    "per_family_declaration_required": true,
    "permitted_kinds": [
      "object",
      "ordered-aggregate",
      "unordered-aggregate",
      "transitive-closure"
    ]
  },
  "reference_semantics": {
    "ambiguous_reference_prohibited": true,
    "per_family_declaration_required": true,
    "permitted_modes": [
      "by-value",
      "by-identity",
      "identity-plus-value"
    ]
  },
  "repository_integration": {
    "deterministic_markdown_projection_required": true,
    "fixed_vector_validation_required": true,
    "identity_migration_deferred": true,
    "normal_validation_required": true,
    "normative_manifest_binding_required": true
  },
  "representation": {
    "algorithm_separator": "-",
    "digest_encoding": "lowercase-hex",
    "digest_separator": ":",
    "family_pattern": "^gve-[a-z][a-z0-9]*(?:-[a-z0-9]+)*$",
    "syntax": "<family>-<algorithm>:<digest>"
  },
  "schema_version": 1
}
```
