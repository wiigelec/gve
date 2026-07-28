#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

PLACEHOLDER_FIELDS = {
    "construction_identity", "construction_status", "responsibility",
    "normative", "expected_relationships", "unresolved_questions",
}
MODEL_FIELDS = {'unavailable_capabilities', 'domain_separation', 'canonicalization_reference', 'canonical_preimage_declaration', 'construction_status', 'normative', 'subject_categories', 'semantic_identity_representation', 'digest_declaration', 'decision_basis', 'identifier_distinction', 'unresolved_questions', 'construction_identity', 'expected_relationships', 'responsibility'}
FAMILY_FIELDS = {'uniqueness_constraints', 'construction_status', 'normative', 'decision_basis', 'field_constraints', 'conflict_rules', 'unresolved_questions', 'construction_identity', 'family_declaration', 'expected_relationships', 'responsibility'}
CANONICAL_FIELDS = {
    "construction_identity", "construction_status", "responsibility", "normative",
    "canonicalization_version", "decision_basis", "input_domain", "encoding",
    "object_rules", "array_rules", "string_rules", "number_rules",
    "output_rules", "expected_relationships", "unresolved_questions",
}
SCHEMA_FIELDS = {
    "construction_identity", "construction_status", "responsibility", "normative",
    "target_construction_identity", "required_fields", "closed",
    "field_constraints", "forbidden_claim_fields", "expected_relationships",
    "unresolved_questions",
}
FIXTURE_FIELDS = {
    "construction_identity", "construction_status", "responsibility",
    "normative", "cases", "expected_relationships", "unresolved_questions",
}
FIXTURE_CASE_FIELDS = {"name", "expected", "expected_diagnostic", "declarations"}
DECLARATION_FIELDS = {
    "family_construction_identity", "family_name", "semantic_domain",
    "subject_category", "canonicalization_version", "digest_algorithm",
    "digest_encoding", "domain_prefix", "included_preimage_fields",
    "omitted_preimage_fields", "unresolved_capabilities",
}
ARTIFACTS = (
    "authoritative/identity/IDENTITY-MODEL.json",
    "authoritative/identity/CANONICAL-JSON.json",
    "authoritative/identity/IDENTITY-FAMILY-MODEL.json",
    "authoritative/identity/IDENTITY-VERIFICATION.json",
)
SCHEMA_PATH = "authoritative/schemas/identity/CANONICAL-JSON-CONSTRUCTION-SCHEMA.json"
MODEL_SCHEMA_PATH = "authoritative/schemas/identity/IDENTITY-MODEL-CONSTRUCTION-SCHEMA.json"
FAMILY_SCHEMA_PATH = "authoritative/schemas/identity/IDENTITY-FAMILY-CONSTRUCTION-SCHEMA.json"
FIXTURE_PATH = "validation/fixtures/identity/identity-family/IDENTITY-FAMILY-FIXTURES.json"
SUPPORTING_PATHS = (
    "authoritative/schemas/identity/README.md",
    "derived/markdown/identity/README.md",
    "validation/fixtures/identity/README.md",
    SCHEMA_PATH, MODEL_SCHEMA_PATH, FAMILY_SCHEMA_PATH, FIXTURE_PATH,
    "validation/intrinsic/validate_canonical_json.py",
    "validation/tests/test_canonical_json.py",
    "validation/tests/test_identity_family.py",
    "validation/fixtures/identity/canonical-json",
    "validation/fixtures/identity/identity-family",
)
EXPECTED_IDENTITIES = {
    ARTIFACTS[0]: "identity-model-construction",
    ARTIFACTS[1]: "canonical-json-construction",
    ARTIFACTS[2]: "identity-family-model-construction",
    ARTIFACTS[3]: "identity-verification-construction",
    SCHEMA_PATH: "canonical-json-construction-schema",
    MODEL_SCHEMA_PATH: "identity-model-construction-schema",
    FAMILY_SCHEMA_PATH: "identity-family-construction-schema",
    FIXTURE_PATH: "identity-family-fixture-set-construction",
}
FORBIDDEN_CLAIM_KEYS = {
    "accepted", "complete", "completed", "sealed", "final", "digest",
    "content_digest", "content-digest", "revision", "specification_revision",
    "specification-revision", "aggregate_revision", "aggregate-revision",
}
SCHEMA_FORBIDDEN_CLAIM_FIELDS = {
    "accepted", "complete", "completed", "sealed", "final", "digest",
    "content_digest", "revision", "specification_revision", "aggregate_revision",
}
FORBIDDEN_NAME_PARTS = {
    "issue", "pull", "request", "milestone", "phase", "migration",
    "temporary", "temp", "patch", "step", "chronology",
}
IDENTITY = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
FIELD_NAME = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")
MANIFEST_PATH = "REPOSITORY-SPECIFICATION-SET.json"

EXPECTED_CANONICAL_CONSTRAINTS = {'canonicalization_version': ['canonical-json-v1'], 'decision_basis': [{'portable_behavior': ['strict-json-and-utf-8-boundary', 'object-member-ordering', 'array-order-preservation', 'deterministic-string-escaping', 'duplicate-member-rejection', 'non-standard-constant-rejection', 'exact-utf-8-output'], 'repository_generic_decisions': ['canonicalization-version-name', 'signed-64-bit-integer-domain', 'no-unicode-normalization']}], 'input_domain': [{'accepted_value_kinds': ['null', 'boolean', 'integer', 'string', 'array', 'object'], 'integer_range': 'signed-64-bit', 'object_member_names': 'string-only'}], 'encoding': [{'input': 'strict-utf-8', 'output': 'utf-8', 'byte_order_mark': 'forbidden', 'unicode_normalization': 'none'}], 'object_rules': [{'member_order': 'ascending-unicode-code-point-sequence', 'source_declaration_order_significant': False, 'duplicate_member_names': 'reject'}], 'array_rules': [{'input_order': 'preserve', 'semantic_sorting': 'outside-canonical-json'}], 'string_rules': [{'quotation_mark': 'escape', 'reverse_solidus': 'escape', 'control_characters': 'deterministic-json-escapes', 'solidus': 'unescaped', 'non_ascii': 'literal-utf-8', 'surrogate_code_points': 'reject'}], 'number_rules': [{'accepted': 'signed-64-bit-integers-only', 'representation': 'minimal-base-10', 'negative_zero': 'not-distinct', 'fractions': 'reject', 'exponents': 'reject', 'non_finite': 'reject'}], 'output_rules': [{'insignificant_whitespace': 'omit', 'trailing_newline': 'forbidden', 'output_boundary': 'exact-canonical-utf-8-bytes'}]}
EXPECTED_MODEL = {'construction_identity': 'identity-model-construction', 'construction_status': 'under-construction', 'responsibility': 'Define the minimum repository-neutral semantic identity construction kernel required to interpret identity-family declarations without defining later reference, aggregate, verification, governing-revision, self-reference, sealing, or acceptance behavior.', 'normative': False, 'decision_basis': {'portable_behavior': ['semantic-identity-distinct-from-implementation-identifier', 'family-qualified-identity', 'explicit-canonicalization-version', 'explicit-digest-algorithm-and-encoding', 'domain-separated-canonical-preimage'], 'repository_generic_decisions': ['closed-family-and-encoded-digest-object-representation', 'object-and-aggregate-subject-categories', 'explicit-included-and-omitted-preimage-fields', 'later-capabilities-unavailable-until-separately-governed']}, 'identifier_distinction': {'semantic_identity': 'family-qualified-content-derived-identity', 'implementation_identifier': 'implementation-local-locator-or-handle', 'equality_rule': 'implementation-identifiers-do-not-determine-semantic-identity-equality', 'preimage_rule': 'implementation-identifiers-are-excluded-unless-a-family-declaration-explicitly-includes-a-semantic-field'}, 'semantic_identity_representation': {'representation_kind': 'closed-object', 'required_components': ['family', 'encoded_digest'], 'final_string_syntax': 'unresolved'}, 'canonicalization_reference': {'supported_versions': ['canonical-json-v1'], 'selection': 'family-declaration-required'}, 'digest_declaration': {'supported_algorithms': ['sha-256'], 'supported_encodings': ['lowercase-hexadecimal'], 'selection': 'family-declaration-required'}, 'domain_separation': {'ownership': 'identity-family', 'prefix_required': True, 'prefix_character_domain': 'printable-ascii', 'prefix_uniqueness': 'repository-specification-construction-set'}, 'subject_categories': ['object', 'aggregate'], 'canonical_preimage_declaration': {'included_fields': 'non-empty-unique-normalized-field-name-array', 'omitted_fields': 'unique-normalized-field-name-array', 'included_and_omitted_fields': 'disjoint'}, 'unavailable_capabilities': ['own-identity-behavior', 'reference-modes', 'reference-encoding', 'aggregate-membership', 'aggregate-ordering', 'aggregate-duplicates', 'aggregate-empty-policy', 'aggregate-closure', 'cycle-handling', 'verification-modes', 'verification-context', 'verification-evidence', 'governing-revision-binding', 'self-reference', 'manifest-bootstrap', 'sealing', 'acceptance'], 'expected_relationships': ['canonical JSON construction boundary', 'identity family construction boundary', 'identity verification construction boundary'], 'unresolved_questions': ['Final accepted semantic identity syntax is not defined.', 'Concrete own-identity, reference, aggregate, verification, governing-revision, self-reference, manifest, sealing, and acceptance behavior remains separately governed.']}
EXPECTED_FAMILY = {'construction_identity': 'identity-family-model-construction', 'construction_status': 'under-construction', 'responsibility': 'Define the closed repository-neutral construction representation and mechanically decidable constraints for identity-family declarations without defining concrete reference, aggregate, verification, self-reference, sealing, or acceptance behavior.', 'normative': False, 'decision_basis': {'portable_behavior': ['family-qualified-semantic-identity', 'explicit-canonicalization-binding', 'explicit-digest-binding', 'domain-separated-preimage', 'fail-closed-family-selection'], 'repository_generic_decisions': ['functional-family-and-semantic-domain-names', 'object-or-aggregate-subject-category', 'construction-set-domain-prefix-uniqueness', 'explicit-included-and-omitted-preimage-fields', 'fixed-unresolved-capabilities']}, 'family_declaration': {'required_fields': ['family_construction_identity', 'family_name', 'semantic_domain', 'subject_category', 'canonicalization_version', 'digest_algorithm', 'digest_encoding', 'domain_prefix', 'included_preimage_fields', 'omitted_preimage_fields', 'unresolved_capabilities'], 'closed': True}, 'field_constraints': {'family_name': 'lowercase-functional-identifier', 'semantic_domain': 'lowercase-functional-identifier', 'subject_category': ['object', 'aggregate'], 'canonicalization_version': ['canonical-json-v1'], 'digest_algorithm': ['sha-256'], 'digest_encoding': ['lowercase-hexadecimal'], 'domain_prefix': 'non-empty-printable-ascii', 'included_preimage_fields': 'non-empty-unique-normalized-field-name-array', 'omitted_preimage_fields': 'non-empty-unique-normalized-field-name-array', 'included_and_omitted_preimage_fields': 'disjoint', 'unresolved_capabilities': ['own-identity-behavior', 'reference-modes', 'reference-encoding', 'aggregate-membership', 'aggregate-ordering', 'aggregate-duplicates', 'aggregate-empty-policy', 'aggregate-closure', 'cycle-handling', 'verification-modes', 'verification-context', 'verification-evidence', 'governing-revision-binding', 'self-reference', 'manifest-bootstrap', 'sealing', 'acceptance'], 'family_construction_identity': 'lowercase-functional-identifier'}, 'uniqueness_constraints': ['family-construction-identity', 'family-name', 'semantic-domain-and-family-name', 'domain-prefix'], 'conflict_rules': ['object-and-aggregate-subject-categories-are-distinct', 'included-and-omitted-preimage-fields-must-not-overlap', 'unknown-canonicalization-version-fails', 'unknown-digest-algorithm-fails', 'unknown-digest-encoding-fails', 'unknown-or-concrete-later-capability-field-fails'], 'expected_relationships': ['identity model construction boundary', 'canonical JSON construction boundary', 'identity verification construction boundary'], 'unresolved_questions': ['No repository or product identity families are declared by this construction model.', 'Concrete own-identity, reference, aggregate, verification, governing-revision, self-reference, manifest, sealing, and acceptance behavior remains separately governed.']}
EXPECTED_MODEL_SCHEMA = {'construction_identity': 'identity-model-construction-schema', 'construction_status': 'under-construction', 'responsibility': 'Constrain the exact construction-only shape of the repository-neutral identity model without claiming final normative schema authority.', 'normative': False, 'target_construction_identity': 'identity-model-construction', 'required_fields': ['construction_identity', 'construction_status', 'responsibility', 'normative', 'decision_basis', 'identifier_distinction', 'semantic_identity_representation', 'canonicalization_reference', 'digest_declaration', 'domain_separation', 'subject_categories', 'canonical_preimage_declaration', 'unavailable_capabilities', 'expected_relationships', 'unresolved_questions'], 'closed': True, 'field_constraints': {'exact_policy': {'construction_identity': 'identity-model-construction', 'construction_status': 'under-construction', 'responsibility': 'Define the minimum repository-neutral semantic identity construction kernel required to interpret identity-family declarations without defining later reference, aggregate, verification, governing-revision, self-reference, sealing, or acceptance behavior.', 'normative': False, 'decision_basis': {'portable_behavior': ['semantic-identity-distinct-from-implementation-identifier', 'family-qualified-identity', 'explicit-canonicalization-version', 'explicit-digest-algorithm-and-encoding', 'domain-separated-canonical-preimage'], 'repository_generic_decisions': ['closed-family-and-encoded-digest-object-representation', 'object-and-aggregate-subject-categories', 'explicit-included-and-omitted-preimage-fields', 'later-capabilities-unavailable-until-separately-governed']}, 'identifier_distinction': {'semantic_identity': 'family-qualified-content-derived-identity', 'implementation_identifier': 'implementation-local-locator-or-handle', 'equality_rule': 'implementation-identifiers-do-not-determine-semantic-identity-equality', 'preimage_rule': 'implementation-identifiers-are-excluded-unless-a-family-declaration-explicitly-includes-a-semantic-field'}, 'semantic_identity_representation': {'representation_kind': 'closed-object', 'required_components': ['family', 'encoded_digest'], 'final_string_syntax': 'unresolved'}, 'canonicalization_reference': {'supported_versions': ['canonical-json-v1'], 'selection': 'family-declaration-required'}, 'digest_declaration': {'supported_algorithms': ['sha-256'], 'supported_encodings': ['lowercase-hexadecimal'], 'selection': 'family-declaration-required'}, 'domain_separation': {'ownership': 'identity-family', 'prefix_required': True, 'prefix_character_domain': 'printable-ascii', 'prefix_uniqueness': 'repository-specification-construction-set'}, 'subject_categories': ['object', 'aggregate'], 'canonical_preimage_declaration': {'included_fields': 'non-empty-unique-normalized-field-name-array', 'omitted_fields': 'unique-normalized-field-name-array', 'included_and_omitted_fields': 'disjoint'}, 'unavailable_capabilities': ['own-identity-behavior', 'reference-modes', 'reference-encoding', 'aggregate-membership', 'aggregate-ordering', 'aggregate-duplicates', 'aggregate-empty-policy', 'aggregate-closure', 'cycle-handling', 'verification-modes', 'verification-context', 'verification-evidence', 'governing-revision-binding', 'self-reference', 'manifest-bootstrap', 'sealing', 'acceptance'], 'expected_relationships': ['canonical JSON construction boundary', 'identity family construction boundary', 'identity verification construction boundary'], 'unresolved_questions': ['Final accepted semantic identity syntax is not defined.', 'Concrete own-identity, reference, aggregate, verification, governing-revision, self-reference, manifest, sealing, and acceptance behavior remains separately governed.']}, 'unknown_fields': 'reject', 'missing_fields': 'reject'}, 'forbidden_claim_fields': ['accepted', 'complete', 'completed', 'sealed', 'final', 'digest', 'content_digest', 'revision', 'specification_revision', 'aggregate_revision'], 'expected_relationships': ['identity model construction boundary', 'identity family construction schema', 'repository specification construction manifest'], 'unresolved_questions': ['Final normative identity-model schema is not defined.', 'Later identity behavior remains separately governed.']}
EXPECTED_FAMILY_SCHEMA = {'construction_identity': 'identity-family-construction-schema', 'construction_status': 'under-construction', 'responsibility': 'Constrain the exact construction-only shape of repository-neutral identity-family declarations without claiming final normative schema authority.', 'normative': False, 'target_construction_identity': 'identity-family-model-construction', 'required_fields': ['construction_identity', 'construction_status', 'responsibility', 'normative', 'decision_basis', 'family_declaration', 'field_constraints', 'uniqueness_constraints', 'conflict_rules', 'expected_relationships', 'unresolved_questions'], 'closed': True, 'field_constraints': {'exact_policy': {'construction_identity': 'identity-family-model-construction', 'construction_status': 'under-construction', 'responsibility': 'Define the closed repository-neutral construction representation and mechanically decidable constraints for identity-family declarations without defining concrete reference, aggregate, verification, self-reference, sealing, or acceptance behavior.', 'normative': False, 'decision_basis': {'portable_behavior': ['family-qualified-semantic-identity', 'explicit-canonicalization-binding', 'explicit-digest-binding', 'domain-separated-preimage', 'fail-closed-family-selection'], 'repository_generic_decisions': ['functional-family-and-semantic-domain-names', 'object-or-aggregate-subject-category', 'construction-set-domain-prefix-uniqueness', 'explicit-included-and-omitted-preimage-fields', 'fixed-unresolved-capabilities']}, 'family_declaration': {'required_fields': ['family_construction_identity', 'family_name', 'semantic_domain', 'subject_category', 'canonicalization_version', 'digest_algorithm', 'digest_encoding', 'domain_prefix', 'included_preimage_fields', 'omitted_preimage_fields', 'unresolved_capabilities'], 'closed': True}, 'field_constraints': {'family_name': 'lowercase-functional-identifier', 'semantic_domain': 'lowercase-functional-identifier', 'subject_category': ['object', 'aggregate'], 'canonicalization_version': ['canonical-json-v1'], 'digest_algorithm': ['sha-256'], 'digest_encoding': ['lowercase-hexadecimal'], 'domain_prefix': 'non-empty-printable-ascii', 'included_preimage_fields': 'non-empty-unique-normalized-field-name-array', 'omitted_preimage_fields': 'non-empty-unique-normalized-field-name-array', 'included_and_omitted_preimage_fields': 'disjoint', 'unresolved_capabilities': ['own-identity-behavior', 'reference-modes', 'reference-encoding', 'aggregate-membership', 'aggregate-ordering', 'aggregate-duplicates', 'aggregate-empty-policy', 'aggregate-closure', 'cycle-handling', 'verification-modes', 'verification-context', 'verification-evidence', 'governing-revision-binding', 'self-reference', 'manifest-bootstrap', 'sealing', 'acceptance'], 'family_construction_identity': 'lowercase-functional-identifier'}, 'uniqueness_constraints': ['family-construction-identity', 'family-name', 'semantic-domain-and-family-name', 'domain-prefix'], 'conflict_rules': ['object-and-aggregate-subject-categories-are-distinct', 'included-and-omitted-preimage-fields-must-not-overlap', 'unknown-canonicalization-version-fails', 'unknown-digest-algorithm-fails', 'unknown-digest-encoding-fails', 'unknown-or-concrete-later-capability-field-fails'], 'expected_relationships': ['identity model construction boundary', 'canonical JSON construction boundary', 'identity verification construction boundary'], 'unresolved_questions': ['No repository or product identity families are declared by this construction model.', 'Concrete own-identity, reference, aggregate, verification, governing-revision, self-reference, manifest, sealing, and acceptance behavior remains separately governed.']}, 'unknown_fields': 'reject', 'missing_fields': 'reject'}, 'forbidden_claim_fields': ['accepted', 'complete', 'completed', 'sealed', 'final', 'digest', 'content_digest', 'revision', 'specification_revision', 'aggregate_revision'], 'expected_relationships': ['identity family construction boundary', 'identity model construction schema', 'repository specification construction manifest'], 'unresolved_questions': ['Final normative identity-family schema is not defined.', 'Concrete family instances and later identity behavior remain separately governed.']}
EXPECTED_FIXTURE_SET = {'construction_identity': 'identity-family-fixture-set-construction', 'construction_status': 'under-construction', 'responsibility': 'Provide repository-neutral positive and negative validator inputs for identity-family declaration construction without defining accepted conformance vectors.', 'normative': False, 'cases': [{'name': 'valid-object-and-aggregate-families', 'expected': 'pass', 'expected_diagnostic': None, 'declarations': [{'family_construction_identity': 'document-family-construction', 'family_name': 'document', 'semantic_domain': 'content', 'subject_category': 'object', 'canonicalization_version': 'canonical-json-v1', 'digest_algorithm': 'sha-256', 'digest_encoding': 'lowercase-hexadecimal', 'domain_prefix': 'repo.identity.document.v1', 'included_preimage_fields': ['body', 'title'], 'omitted_preimage_fields': ['cache_key'], 'unresolved_capabilities': ['own-identity-behavior', 'reference-modes', 'reference-encoding', 'aggregate-membership', 'aggregate-ordering', 'aggregate-duplicates', 'aggregate-empty-policy', 'aggregate-closure', 'cycle-handling', 'verification-modes', 'verification-context', 'verification-evidence', 'governing-revision-binding', 'self-reference', 'manifest-bootstrap', 'sealing', 'acceptance']}, {'family_construction_identity': 'bundle-family-construction', 'family_name': 'bundle', 'semantic_domain': 'collection', 'subject_category': 'aggregate', 'canonicalization_version': 'canonical-json-v1', 'digest_algorithm': 'sha-256', 'digest_encoding': 'lowercase-hexadecimal', 'domain_prefix': 'repo.identity.bundle.v1', 'included_preimage_fields': ['members', 'name'], 'omitted_preimage_fields': ['display_order'], 'unresolved_capabilities': ['own-identity-behavior', 'reference-modes', 'reference-encoding', 'aggregate-membership', 'aggregate-ordering', 'aggregate-duplicates', 'aggregate-empty-policy', 'aggregate-closure', 'cycle-handling', 'verification-modes', 'verification-context', 'verification-evidence', 'governing-revision-binding', 'self-reference', 'manifest-bootstrap', 'sealing', 'acceptance']}]}, {'name': 'unsupported-canonicalization-version', 'expected': 'reject', 'expected_diagnostic': 'REPO-SPEC-IDENTITY-FAMILY-CANONICAL-001', 'declarations': [{'family_construction_identity': 'document-family-construction', 'family_name': 'document', 'semantic_domain': 'content', 'subject_category': 'object', 'canonicalization_version': 'canonical-json-v2', 'digest_algorithm': 'sha-256', 'digest_encoding': 'lowercase-hexadecimal', 'domain_prefix': 'repo.identity.document.v1', 'included_preimage_fields': ['body', 'title'], 'omitted_preimage_fields': ['cache_key'], 'unresolved_capabilities': ['own-identity-behavior', 'reference-modes', 'reference-encoding', 'aggregate-membership', 'aggregate-ordering', 'aggregate-duplicates', 'aggregate-empty-policy', 'aggregate-closure', 'cycle-handling', 'verification-modes', 'verification-context', 'verification-evidence', 'governing-revision-binding', 'self-reference', 'manifest-bootstrap', 'sealing', 'acceptance']}]}, {'name': 'unsupported-digest-algorithm', 'expected': 'reject', 'expected_diagnostic': 'REPO-SPEC-IDENTITY-FAMILY-DIGEST-001', 'declarations': [{'family_construction_identity': 'document-family-construction', 'family_name': 'document', 'semantic_domain': 'content', 'subject_category': 'object', 'canonicalization_version': 'canonical-json-v1', 'digest_algorithm': 'sha-512', 'digest_encoding': 'lowercase-hexadecimal', 'domain_prefix': 'repo.identity.document.v1', 'included_preimage_fields': ['body', 'title'], 'omitted_preimage_fields': ['cache_key'], 'unresolved_capabilities': ['own-identity-behavior', 'reference-modes', 'reference-encoding', 'aggregate-membership', 'aggregate-ordering', 'aggregate-duplicates', 'aggregate-empty-policy', 'aggregate-closure', 'cycle-handling', 'verification-modes', 'verification-context', 'verification-evidence', 'governing-revision-binding', 'self-reference', 'manifest-bootstrap', 'sealing', 'acceptance']}]}, {'name': 'unsupported-digest-encoding', 'expected': 'reject', 'expected_diagnostic': 'REPO-SPEC-IDENTITY-FAMILY-DIGEST-002', 'declarations': [{'family_construction_identity': 'document-family-construction', 'family_name': 'document', 'semantic_domain': 'content', 'subject_category': 'object', 'canonicalization_version': 'canonical-json-v1', 'digest_algorithm': 'sha-256', 'digest_encoding': 'base64', 'domain_prefix': 'repo.identity.document.v1', 'included_preimage_fields': ['body', 'title'], 'omitted_preimage_fields': ['cache_key'], 'unresolved_capabilities': ['own-identity-behavior', 'reference-modes', 'reference-encoding', 'aggregate-membership', 'aggregate-ordering', 'aggregate-duplicates', 'aggregate-empty-policy', 'aggregate-closure', 'cycle-handling', 'verification-modes', 'verification-context', 'verification-evidence', 'governing-revision-binding', 'self-reference', 'manifest-bootstrap', 'sealing', 'acceptance']}]}, {'name': 'malformed-domain-prefix', 'expected': 'reject', 'expected_diagnostic': 'REPO-SPEC-IDENTITY-FAMILY-DOMAIN-001', 'declarations': [{'family_construction_identity': 'document-family-construction', 'family_name': 'document', 'semantic_domain': 'content', 'subject_category': 'object', 'canonicalization_version': 'canonical-json-v1', 'digest_algorithm': 'sha-256', 'digest_encoding': 'lowercase-hexadecimal', 'domain_prefix': 'bad\nprefix', 'included_preimage_fields': ['body', 'title'], 'omitted_preimage_fields': ['cache_key'], 'unresolved_capabilities': ['own-identity-behavior', 'reference-modes', 'reference-encoding', 'aggregate-membership', 'aggregate-ordering', 'aggregate-duplicates', 'aggregate-empty-policy', 'aggregate-closure', 'cycle-handling', 'verification-modes', 'verification-context', 'verification-evidence', 'governing-revision-binding', 'self-reference', 'manifest-bootstrap', 'sealing', 'acceptance']}]}, {'name': 'overlapping-preimage-fields', 'expected': 'reject', 'expected_diagnostic': 'REPO-SPEC-IDENTITY-FAMILY-PREIMAGE-002', 'declarations': [{'family_construction_identity': 'document-family-construction', 'family_name': 'document', 'semantic_domain': 'content', 'subject_category': 'object', 'canonicalization_version': 'canonical-json-v1', 'digest_algorithm': 'sha-256', 'digest_encoding': 'lowercase-hexadecimal', 'domain_prefix': 'repo.identity.document.v1', 'included_preimage_fields': ['body', 'title'], 'omitted_preimage_fields': ['title'], 'unresolved_capabilities': ['own-identity-behavior', 'reference-modes', 'reference-encoding', 'aggregate-membership', 'aggregate-ordering', 'aggregate-duplicates', 'aggregate-empty-policy', 'aggregate-closure', 'cycle-handling', 'verification-modes', 'verification-context', 'verification-evidence', 'governing-revision-binding', 'self-reference', 'manifest-bootstrap', 'sealing', 'acceptance']}]}, {'name': 'duplicate-preimage-fields', 'expected': 'reject', 'expected_diagnostic': 'REPO-SPEC-IDENTITY-FAMILY-PREIMAGE-001', 'declarations': [{'family_construction_identity': 'document-family-construction', 'family_name': 'document', 'semantic_domain': 'content', 'subject_category': 'object', 'canonicalization_version': 'canonical-json-v1', 'digest_algorithm': 'sha-256', 'digest_encoding': 'lowercase-hexadecimal', 'domain_prefix': 'repo.identity.document.v1', 'included_preimage_fields': ['body', 'body'], 'omitted_preimage_fields': ['cache_key'], 'unresolved_capabilities': ['own-identity-behavior', 'reference-modes', 'reference-encoding', 'aggregate-membership', 'aggregate-ordering', 'aggregate-duplicates', 'aggregate-empty-policy', 'aggregate-closure', 'cycle-handling', 'verification-modes', 'verification-context', 'verification-evidence', 'governing-revision-binding', 'self-reference', 'manifest-bootstrap', 'sealing', 'acceptance']}]}, {'name': 'invalid-subject-category', 'expected': 'reject', 'expected_diagnostic': 'REPO-SPEC-IDENTITY-FAMILY-CATEGORY-001', 'declarations': [{'family_construction_identity': 'document-family-construction', 'family_name': 'document', 'semantic_domain': 'content', 'subject_category': 'hybrid', 'canonicalization_version': 'canonical-json-v1', 'digest_algorithm': 'sha-256', 'digest_encoding': 'lowercase-hexadecimal', 'domain_prefix': 'repo.identity.document.v1', 'included_preimage_fields': ['body', 'title'], 'omitted_preimage_fields': ['cache_key'], 'unresolved_capabilities': ['own-identity-behavior', 'reference-modes', 'reference-encoding', 'aggregate-membership', 'aggregate-ordering', 'aggregate-duplicates', 'aggregate-empty-policy', 'aggregate-closure', 'cycle-handling', 'verification-modes', 'verification-context', 'verification-evidence', 'governing-revision-binding', 'self-reference', 'manifest-bootstrap', 'sealing', 'acceptance']}]}, {'name': 'undeclared-later-stage-field', 'expected': 'reject', 'expected_diagnostic': 'REPO-SPEC-IDENTITY-FIELD-001', 'declarations': [{'family_construction_identity': 'document-family-construction', 'family_name': 'document', 'semantic_domain': 'content', 'subject_category': 'object', 'canonicalization_version': 'canonical-json-v1', 'digest_algorithm': 'sha-256', 'digest_encoding': 'lowercase-hexadecimal', 'domain_prefix': 'repo.identity.document.v1', 'included_preimage_fields': ['body', 'title'], 'omitted_preimage_fields': ['cache_key'], 'unresolved_capabilities': ['own-identity-behavior', 'reference-modes', 'reference-encoding', 'aggregate-membership', 'aggregate-ordering', 'aggregate-duplicates', 'aggregate-empty-policy', 'aggregate-closure', 'cycle-handling', 'verification-modes', 'verification-context', 'verification-evidence', 'governing-revision-binding', 'self-reference', 'manifest-bootstrap', 'sealing', 'acceptance'], 'reference_modes': ['direct']}]}, {'name': 'malformed-functional-identifier', 'expected': 'reject', 'expected_diagnostic': 'REPO-SPEC-IDENTITY-FAMILY-NAME-001', 'declarations': [{'family_construction_identity': 'document-family-construction', 'family_name': 'Product Name', 'semantic_domain': 'content', 'subject_category': 'object', 'canonicalization_version': 'canonical-json-v1', 'digest_algorithm': 'sha-256', 'digest_encoding': 'lowercase-hexadecimal', 'domain_prefix': 'repo.identity.document.v1', 'included_preimage_fields': ['body', 'title'], 'omitted_preimage_fields': ['cache_key'], 'unresolved_capabilities': ['own-identity-behavior', 'reference-modes', 'reference-encoding', 'aggregate-membership', 'aggregate-ordering', 'aggregate-duplicates', 'aggregate-empty-policy', 'aggregate-closure', 'cycle-handling', 'verification-modes', 'verification-context', 'verification-evidence', 'governing-revision-binding', 'self-reference', 'manifest-bootstrap', 'sealing', 'acceptance']}]}, {'name': 'duplicate-family-construction-identity', 'expected': 'reject', 'expected_diagnostic': 'REPO-SPEC-IDENTITY-FAMILY-UNIQUE-001', 'declarations': [{'family_construction_identity': 'document-family-construction', 'family_name': 'document', 'semantic_domain': 'content', 'subject_category': 'object', 'canonicalization_version': 'canonical-json-v1', 'digest_algorithm': 'sha-256', 'digest_encoding': 'lowercase-hexadecimal', 'domain_prefix': 'repo.identity.document.v1', 'included_preimage_fields': ['body', 'title'], 'omitted_preimage_fields': ['cache_key'], 'unresolved_capabilities': ['own-identity-behavior', 'reference-modes', 'reference-encoding', 'aggregate-membership', 'aggregate-ordering', 'aggregate-duplicates', 'aggregate-empty-policy', 'aggregate-closure', 'cycle-handling', 'verification-modes', 'verification-context', 'verification-evidence', 'governing-revision-binding', 'self-reference', 'manifest-bootstrap', 'sealing', 'acceptance']}, {'family_construction_identity': 'document-family-construction', 'family_name': 'other-document', 'semantic_domain': 'other-content', 'subject_category': 'object', 'canonicalization_version': 'canonical-json-v1', 'digest_algorithm': 'sha-256', 'digest_encoding': 'lowercase-hexadecimal', 'domain_prefix': 'repo.identity.other-document.v1', 'included_preimage_fields': ['body'], 'omitted_preimage_fields': ['cache_key'], 'unresolved_capabilities': ['own-identity-behavior', 'reference-modes', 'reference-encoding', 'aggregate-membership', 'aggregate-ordering', 'aggregate-duplicates', 'aggregate-empty-policy', 'aggregate-closure', 'cycle-handling', 'verification-modes', 'verification-context', 'verification-evidence', 'governing-revision-binding', 'self-reference', 'manifest-bootstrap', 'sealing', 'acceptance']}]}, {'name': 'duplicate-family-name', 'expected': 'reject', 'expected_diagnostic': 'REPO-SPEC-IDENTITY-FAMILY-UNIQUE-002', 'declarations': [{'family_construction_identity': 'document-family-construction', 'family_name': 'document', 'semantic_domain': 'content', 'subject_category': 'object', 'canonicalization_version': 'canonical-json-v1', 'digest_algorithm': 'sha-256', 'digest_encoding': 'lowercase-hexadecimal', 'domain_prefix': 'repo.identity.document.v1', 'included_preimage_fields': ['body', 'title'], 'omitted_preimage_fields': ['cache_key'], 'unresolved_capabilities': ['own-identity-behavior', 'reference-modes', 'reference-encoding', 'aggregate-membership', 'aggregate-ordering', 'aggregate-duplicates', 'aggregate-empty-policy', 'aggregate-closure', 'cycle-handling', 'verification-modes', 'verification-context', 'verification-evidence', 'governing-revision-binding', 'self-reference', 'manifest-bootstrap', 'sealing', 'acceptance']}, {'family_construction_identity': 'document-family-two-construction', 'family_name': 'document', 'semantic_domain': 'other-content', 'subject_category': 'object', 'canonicalization_version': 'canonical-json-v1', 'digest_algorithm': 'sha-256', 'digest_encoding': 'lowercase-hexadecimal', 'domain_prefix': 'repo.identity.document-two.v1', 'included_preimage_fields': ['body'], 'omitted_preimage_fields': ['cache_key'], 'unresolved_capabilities': ['own-identity-behavior', 'reference-modes', 'reference-encoding', 'aggregate-membership', 'aggregate-ordering', 'aggregate-duplicates', 'aggregate-empty-policy', 'aggregate-closure', 'cycle-handling', 'verification-modes', 'verification-context', 'verification-evidence', 'governing-revision-binding', 'self-reference', 'manifest-bootstrap', 'sealing', 'acceptance']}]}, {'name': 'duplicate-semantic-family', 'expected': 'reject', 'expected_diagnostic': 'REPO-SPEC-IDENTITY-FAMILY-UNIQUE-003', 'declarations': [{'family_construction_identity': 'document-family-construction', 'family_name': 'document', 'semantic_domain': 'content', 'subject_category': 'object', 'canonicalization_version': 'canonical-json-v1', 'digest_algorithm': 'sha-256', 'digest_encoding': 'lowercase-hexadecimal', 'domain_prefix': 'repo.identity.document.v1', 'included_preimage_fields': ['body', 'title'], 'omitted_preimage_fields': ['cache_key'], 'unresolved_capabilities': ['own-identity-behavior', 'reference-modes', 'reference-encoding', 'aggregate-membership', 'aggregate-ordering', 'aggregate-duplicates', 'aggregate-empty-policy', 'aggregate-closure', 'cycle-handling', 'verification-modes', 'verification-context', 'verification-evidence', 'governing-revision-binding', 'self-reference', 'manifest-bootstrap', 'sealing', 'acceptance']}, {'family_construction_identity': 'document-family-three-construction', 'family_name': 'document', 'semantic_domain': 'content', 'subject_category': 'aggregate', 'canonicalization_version': 'canonical-json-v1', 'digest_algorithm': 'sha-256', 'digest_encoding': 'lowercase-hexadecimal', 'domain_prefix': 'repo.identity.document-three.v1', 'included_preimage_fields': ['members'], 'omitted_preimage_fields': ['display_order'], 'unresolved_capabilities': ['own-identity-behavior', 'reference-modes', 'reference-encoding', 'aggregate-membership', 'aggregate-ordering', 'aggregate-duplicates', 'aggregate-empty-policy', 'aggregate-closure', 'cycle-handling', 'verification-modes', 'verification-context', 'verification-evidence', 'governing-revision-binding', 'self-reference', 'manifest-bootstrap', 'sealing', 'acceptance']}]}, {'name': 'duplicate-domain-prefix', 'expected': 'reject', 'expected_diagnostic': 'REPO-SPEC-IDENTITY-FAMILY-UNIQUE-004', 'declarations': [{'family_construction_identity': 'document-family-construction', 'family_name': 'document', 'semantic_domain': 'content', 'subject_category': 'object', 'canonicalization_version': 'canonical-json-v1', 'digest_algorithm': 'sha-256', 'digest_encoding': 'lowercase-hexadecimal', 'domain_prefix': 'repo.identity.document.v1', 'included_preimage_fields': ['body', 'title'], 'omitted_preimage_fields': ['cache_key'], 'unresolved_capabilities': ['own-identity-behavior', 'reference-modes', 'reference-encoding', 'aggregate-membership', 'aggregate-ordering', 'aggregate-duplicates', 'aggregate-empty-policy', 'aggregate-closure', 'cycle-handling', 'verification-modes', 'verification-context', 'verification-evidence', 'governing-revision-binding', 'self-reference', 'manifest-bootstrap', 'sealing', 'acceptance']}, {'family_construction_identity': 'bundle-family-two-construction', 'family_name': 'bundle-two', 'semantic_domain': 'collection-two', 'subject_category': 'aggregate', 'canonicalization_version': 'canonical-json-v1', 'digest_algorithm': 'sha-256', 'digest_encoding': 'lowercase-hexadecimal', 'domain_prefix': 'repo.identity.document.v1', 'included_preimage_fields': ['members'], 'omitted_preimage_fields': ['display_order'], 'unresolved_capabilities': ['own-identity-behavior', 'reference-modes', 'reference-encoding', 'aggregate-membership', 'aggregate-ordering', 'aggregate-duplicates', 'aggregate-empty-policy', 'aggregate-closure', 'cycle-handling', 'verification-modes', 'verification-context', 'verification-evidence', 'governing-revision-binding', 'self-reference', 'manifest-bootstrap', 'sealing', 'acceptance']}]}], 'expected_relationships': ['identity family construction validator', 'identity family construction model', 'repository specification construction manifest'], 'unresolved_questions': ['These fixtures are construction validator inputs and are not accepted conformance vectors.', 'Final accepted identity families and digests remain separately governed.']}
UNRESOLVED_CAPABILITIES = ['own-identity-behavior', 'reference-modes', 'reference-encoding', 'aggregate-membership', 'aggregate-ordering', 'aggregate-duplicates', 'aggregate-empty-policy', 'aggregate-closure', 'cycle-handling', 'verification-modes', 'verification-context', 'verification-evidence', 'governing-revision-binding', 'self-reference', 'manifest-bootstrap', 'sealing', 'acceptance']

class ValidationFailure(Exception):
    pass

def fail(code: str, detail: str) -> None:
    raise ValidationFailure(f"{code}: {detail}")

def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate object member {key}")
        result[key] = value
    return result

def strict_json(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
        value = json.loads(
            raw,
            object_pairs_hook=_unique_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(
                ValueError(f"non-standard JSON constant {token}")
            ),
        )
    except UnicodeDecodeError:
        fail("REPO-SPEC-IDENTITY-JSON-001", f"{path}: invalid UTF-8")
    except OSError as exc:
        fail("REPO-SPEC-IDENTITY-PATH-001", f"{path}: {exc}")
    except (json.JSONDecodeError, ValueError) as exc:
        fail("REPO-SPEC-IDENTITY-JSON-001", f"{path}: {exc}")
    if not isinstance(value, dict):
        fail("REPO-SPEC-IDENTITY-JSON-002", f"{path}: top level must be an object")
    return value

def exact_fields(value: dict[str, Any], fields: set[str], label: str) -> None:
    unknown = sorted(set(value) - fields)
    missing = sorted(fields - set(value))
    if unknown:
        fail("REPO-SPEC-IDENTITY-FIELD-001", f"{label}: unknown fields: {', '.join(unknown)}")
    if missing:
        fail("REPO-SPEC-IDENTITY-FIELD-002", f"{label}: missing fields: {', '.join(missing)}")

def string_list(value: Any, label: str, *, nonempty: bool = True) -> list[str]:
    if not isinstance(value, list) or (nonempty and not value):
        fail("REPO-SPEC-IDENTITY-TYPE-001", f"{label}: must be an array with required entries")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        fail("REPO-SPEC-IDENTITY-TYPE-001", f"{label}: entries must be non-empty strings")
    return list(value)

def validate_identity(value: Any, label: str) -> str:
    if not isinstance(value, str) or not IDENTITY.fullmatch(value):
        fail("REPO-SPEC-IDENTITY-IDENTITY-001", f"{label}: invalid construction identity")
    if set(value.split("-")) & FORBIDDEN_NAME_PARTS:
        fail("REPO-SPEC-IDENTITY-NAME-001", f"{label}: work-derived identity parts are forbidden")
    return value

def contained_path(root: Path, value: Any, label: str) -> Path:
    if not isinstance(value, str) or not value:
        fail("REPO-SPEC-IDENTITY-PATH-003", f"{label}: must be a non-empty relative path")
    pure = PurePosixPath(value)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        fail("REPO-SPEC-IDENTITY-PATH-003", f"{label}: path is not normalized and relative")
    target = root.joinpath(*pure.parts)
    try:
        target.resolve(strict=False).relative_to(root.resolve())
    except ValueError:
        fail("REPO-SPEC-IDENTITY-PATH-002", f"{label}: path escapes construction root")
    current = root
    for part in pure.parts:
        current = current / part
        if current.is_symlink():
            fail("REPO-SPEC-IDENTITY-PATH-002", f"{label}: symlink is forbidden")
    return target

def validate_common(value: dict[str, Any], label: str) -> str:
    if set(value) & FORBIDDEN_CLAIM_KEYS:
        fail("REPO-SPEC-IDENTITY-CLAIM-001", f"{label}: forbidden final-authority fields")
    identity = validate_identity(value["construction_identity"], f"{label}.construction_identity")
    if value["construction_status"] != "under-construction":
        fail("REPO-SPEC-IDENTITY-STATUS-001", f"{label}: status must be under-construction")
    if value["normative"] is not False:
        fail("REPO-SPEC-IDENTITY-STATUS-002", f"{label}: normative must be false")
    if not isinstance(value["responsibility"], str) or not value["responsibility"].strip():
        fail("REPO-SPEC-IDENTITY-TYPE-001", f"{label}.responsibility must be non-empty")
    string_list(value["expected_relationships"], f"{label}.expected_relationships")
    string_list(value["unresolved_questions"], f"{label}.unresolved_questions")
    return identity

def validate_exact_policy(value: dict[str, Any], expected: dict[str, Any], fields: set[str], label: str, code: str) -> None:
    exact_fields(value, fields, label)
    validate_common(value, label)
    if value != expected:
        fail(code, f"{label}: construction claims do not match policy")

def validate_canonical(value: dict[str, Any], label: str) -> None:
    exact_fields(value, CANONICAL_FIELDS, label)
    validate_common(value, label)
    actual = {field: value[field] for field in EXPECTED_CANONICAL_CONSTRAINTS}
    expected = {field: allowed[0] for field, allowed in EXPECTED_CANONICAL_CONSTRAINTS.items()}
    if actual != expected:
        fail("REPO-SPEC-IDENTITY-CANONICAL-001", f"{label}: canonical construction claims do not match policy")

def validate_schema(value: dict[str, Any], label: str) -> None:
    exact_fields(value, SCHEMA_FIELDS, label)
    validate_common(value, label)
    if value["target_construction_identity"] != "canonical-json-construction":
        fail("REPO-SPEC-IDENTITY-SCHEMA-001", f"{label}: invalid schema target")
    required_fields = value["required_fields"]
    if (
        not isinstance(required_fields, list)
        or len(required_fields) != len(CANONICAL_FIELDS)
        or set(required_fields) != CANONICAL_FIELDS
    ):
        fail("REPO-SPEC-IDENTITY-SCHEMA-001", f"{label}: required fields do not match model")
    if value["closed"] is not True:
        fail("REPO-SPEC-IDENTITY-SCHEMA-001", f"{label}: schema must be closed")
    if value["field_constraints"] != EXPECTED_CANONICAL_CONSTRAINTS:
        fail("REPO-SPEC-IDENTITY-SCHEMA-001", f"{label}: field constraints do not match model")
    forbidden = value["forbidden_claim_fields"]
    if (
        not isinstance(forbidden, list)
        or len(forbidden) != len(SCHEMA_FORBIDDEN_CLAIM_FIELDS)
        or set(forbidden) != SCHEMA_FORBIDDEN_CLAIM_FIELDS
    ):
        fail("REPO-SPEC-IDENTITY-SCHEMA-001", f"{label}: forbidden claim fields do not match policy")

def validate_exact_schema(value: dict[str, Any], expected: dict[str, Any], label: str) -> None:
    exact_fields(value, SCHEMA_FIELDS, label)
    validate_common(value, label)
    if value != expected:
        fail("REPO-SPEC-IDENTITY-SCHEMA-001", f"{label}: construction schema claims do not match policy")

def _functional(value: Any, label: str) -> str:
    if not isinstance(value, str) or not IDENTITY.fullmatch(value):
        fail("REPO-SPEC-IDENTITY-FAMILY-NAME-001", f"{label}: invalid lowercase functional identifier")
    return value

def _preimage_fields(value: Any, label: str) -> list[str]:
    fields = string_list(value, label)
    if len(fields) != len(set(fields)):
        fail("REPO-SPEC-IDENTITY-FAMILY-PREIMAGE-001", f"{label}: duplicate field names")
    if any(not FIELD_NAME.fullmatch(field) for field in fields):
        fail("REPO-SPEC-IDENTITY-FAMILY-PREIMAGE-001", f"{label}: malformed field name")
    return fields

def validate_family_declarations(declarations: Any, label: str) -> None:
    if not isinstance(declarations, list) or not declarations:
        fail("REPO-SPEC-IDENTITY-FAMILY-TYPE-001", f"{label}: non-empty declarations array required")
    identities: set[str] = set()
    names: set[str] = set()
    semantic: set[tuple[str, str]] = set()
    prefixes: set[str] = set()
    for index, declaration in enumerate(declarations):
        item_label = f"{label}[{index}]"
        if not isinstance(declaration, dict):
            fail("REPO-SPEC-IDENTITY-FAMILY-TYPE-001", f"{item_label}: declaration must be an object")
        exact_fields(declaration, DECLARATION_FIELDS, item_label)
        construction_identity = _functional(
            declaration["family_construction_identity"],
            f"{item_label}.family_construction_identity",
        )
        family_name = _functional(declaration["family_name"], f"{item_label}.family_name")
        semantic_domain = _functional(declaration["semantic_domain"], f"{item_label}.semantic_domain")
        if declaration["subject_category"] not in {"object", "aggregate"}:
            fail("REPO-SPEC-IDENTITY-FAMILY-CATEGORY-001", f"{item_label}: unsupported subject category")
        if declaration["canonicalization_version"] != "canonical-json-v1":
            fail("REPO-SPEC-IDENTITY-FAMILY-CANONICAL-001", f"{item_label}: unsupported canonicalization version")
        if declaration["digest_algorithm"] != "sha-256":
            fail("REPO-SPEC-IDENTITY-FAMILY-DIGEST-001", f"{item_label}: unsupported digest algorithm")
        if declaration["digest_encoding"] != "lowercase-hexadecimal":
            fail("REPO-SPEC-IDENTITY-FAMILY-DIGEST-002", f"{item_label}: unsupported digest encoding")
        prefix = declaration["domain_prefix"]
        if (
            not isinstance(prefix, str)
            or not prefix
            or any(ord(character) < 0x20 or ord(character) > 0x7E for character in prefix)
        ):
            fail("REPO-SPEC-IDENTITY-FAMILY-DOMAIN-001", f"{item_label}: malformed domain prefix")
        included = _preimage_fields(
            declaration["included_preimage_fields"],
            f"{item_label}.included_preimage_fields",
        )
        omitted = _preimage_fields(
            declaration["omitted_preimage_fields"],
            f"{item_label}.omitted_preimage_fields",
        )
        if set(included) & set(omitted):
            fail("REPO-SPEC-IDENTITY-FAMILY-PREIMAGE-002", f"{item_label}: included and omitted fields overlap")
        if declaration["unresolved_capabilities"] != UNRESOLVED_CAPABILITIES:
            fail("REPO-SPEC-IDENTITY-FAMILY-LATER-001", f"{item_label}: unresolved capabilities do not match policy")
        if construction_identity in identities:
            fail("REPO-SPEC-IDENTITY-FAMILY-UNIQUE-001", f"{item_label}: duplicate construction identity")
        semantic_key = (semantic_domain, family_name)
        if semantic_key in semantic:
            fail("REPO-SPEC-IDENTITY-FAMILY-UNIQUE-003", f"{item_label}: duplicate semantic family declaration")
        if family_name in names:
            fail("REPO-SPEC-IDENTITY-FAMILY-UNIQUE-002", f"{item_label}: duplicate family name")
        if prefix in prefixes:
            fail("REPO-SPEC-IDENTITY-FAMILY-UNIQUE-004", f"{item_label}: duplicate domain prefix")
        identities.add(construction_identity)
        names.add(family_name)
        semantic.add(semantic_key)
        prefixes.add(prefix)

def validate_fixture_set(value: dict[str, Any], label: str) -> None:
    exact_fields(value, FIXTURE_FIELDS, label)
    validate_common(value, label)
    cases = value["cases"]
    if not isinstance(cases, list) or not cases:
        fail("REPO-SPEC-IDENTITY-FIXTURE-001", f"{label}: non-empty cases array required")
    names: set[str] = set()
    for index, case in enumerate(cases):
        case_label = f"{label}.cases[{index}]"
        if not isinstance(case, dict):
            fail("REPO-SPEC-IDENTITY-FIXTURE-001", f"{case_label}: case must be an object")
        exact_fields(case, FIXTURE_CASE_FIELDS, case_label)
        name = _functional(case["name"], f"{case_label}.name")
        if name in names:
            fail("REPO-SPEC-IDENTITY-FIXTURE-001", f"{case_label}: duplicate case name")
        names.add(name)
        expected = case["expected"]
        diagnostic = case["expected_diagnostic"]
        if expected == "pass":
            if diagnostic is not None:
                fail("REPO-SPEC-IDENTITY-FIXTURE-001", f"{case_label}: passing case diagnostic must be null")
            validate_family_declarations(case["declarations"], f"{case_label}.declarations")
        elif expected == "reject":
            if not isinstance(diagnostic, str) or not diagnostic.startswith("REPO-SPEC-IDENTITY-"):
                fail("REPO-SPEC-IDENTITY-FIXTURE-001", f"{case_label}: rejected case diagnostic required")
            try:
                validate_family_declarations(case["declarations"], f"{case_label}.declarations")
            except ValidationFailure as exc:
                if not str(exc).startswith(diagnostic + ":"):
                    fail("REPO-SPEC-IDENTITY-FIXTURE-001", f"{case_label}: unexpected diagnostic {exc}")
            else:
                fail("REPO-SPEC-IDENTITY-FIXTURE-001", f"{case_label}: rejected case unexpectedly passed")
        else:
            fail("REPO-SPEC-IDENTITY-FIXTURE-001", f"{case_label}: expected must be pass or reject")
    if value != EXPECTED_FIXTURE_SET:
        fail("REPO-SPEC-IDENTITY-FIXTURE-001", f"{label}: fixture set does not match governed inventory")

def validate_manifest(root: Path) -> None:
    manifest = strict_json(root / MANIFEST_PATH)
    paths = manifest.get("artifact_paths")
    if not isinstance(paths, list) or not paths or len(paths) != len(set(paths)):
        fail("REPO-SPEC-IDENTITY-MANIFEST-002", "manifest paths are malformed or duplicate")
    declared = set(paths)
    for relative in (*ARTIFACTS, SCHEMA_PATH, MODEL_SCHEMA_PATH, FAMILY_SCHEMA_PATH, FIXTURE_PATH):
        if paths.count(relative) != 1:
            fail("REPO-SPEC-IDENTITY-MANIFEST-001", f"{relative}: must participate exactly once")
    for index, relative in enumerate(paths):
        target = contained_path(root, relative, f"manifest.artifact_paths[{index}]")
        if (
            relative.startswith("authoritative/identity/")
            or relative.startswith("authoritative/schemas/identity/")
            or relative == FIXTURE_PATH
        ) and not target.is_file():
            fail("REPO-SPEC-IDENTITY-MANIFEST-003", f"{relative}: declared identity artifact is missing")
    participating = set()
    for directory in (
        root / "authoritative/identity",
        root / "authoritative/schemas/identity",
        root / "validation/fixtures/identity/identity-family",
    ):
        for path in sorted(directory.glob("*.json")):
            if "construction_identity" in strict_json(path):
                participating.add(path.relative_to(root).as_posix())
    if participating - declared:
        fail("REPO-SPEC-IDENTITY-MANIFEST-004", "undeclared identity construction participants")

def validate(root: Path) -> None:
    identities = set()
    observed = {}
    for relative in (*ARTIFACTS, *SUPPORTING_PATHS):
        if not contained_path(root, relative, relative).exists():
            fail("REPO-SPEC-IDENTITY-PATH-001", f"{relative}: required path is missing")
    for relative in ARTIFACTS:
        value = strict_json(root / relative)
        if relative == ARTIFACTS[0]:
            validate_exact_policy(value, EXPECTED_MODEL, MODEL_FIELDS, relative, "REPO-SPEC-IDENTITY-MODEL-001")
        elif relative == ARTIFACTS[1]:
            validate_canonical(value, relative)
        elif relative == ARTIFACTS[2]:
            validate_exact_policy(value, EXPECTED_FAMILY, FAMILY_FIELDS, relative, "REPO-SPEC-IDENTITY-FAMILY-001")
        else:
            exact_fields(value, PLACEHOLDER_FIELDS, relative)
            validate_common(value, relative)
        identity = value["construction_identity"]
        if identity in identities:
            fail("REPO-SPEC-IDENTITY-IDENTITY-003", f"{relative}: duplicate construction identity")
        identities.add(identity)
        observed[relative] = identity
    canonical_schema = strict_json(root / SCHEMA_PATH)
    validate_schema(canonical_schema, SCHEMA_PATH)
    observed[SCHEMA_PATH] = canonical_schema["construction_identity"]
    model_schema = strict_json(root / MODEL_SCHEMA_PATH)
    validate_exact_schema(model_schema, EXPECTED_MODEL_SCHEMA, MODEL_SCHEMA_PATH)
    observed[MODEL_SCHEMA_PATH] = model_schema["construction_identity"]
    family_schema = strict_json(root / FAMILY_SCHEMA_PATH)
    validate_exact_schema(family_schema, EXPECTED_FAMILY_SCHEMA, FAMILY_SCHEMA_PATH)
    observed[FAMILY_SCHEMA_PATH] = family_schema["construction_identity"]
    fixture_set = strict_json(root / FIXTURE_PATH)
    validate_fixture_set(fixture_set, FIXTURE_PATH)
    observed[FIXTURE_PATH] = fixture_set["construction_identity"]
    for relative, expected in EXPECTED_IDENTITIES.items():
        if observed.get(relative) != expected:
            fail("REPO-SPEC-IDENTITY-IDENTITY-002", f"{relative}: unexpected construction identity")
    validate_manifest(root)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args(argv)
    try:
        validate(args.root)
    except (ValidationFailure, OSError, UnicodeDecodeError, SyntaxError) as exc:
        print(f"identity construction validation failed: {exc}", file=sys.stderr)
        return 1
    print("identity construction validation passed")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
