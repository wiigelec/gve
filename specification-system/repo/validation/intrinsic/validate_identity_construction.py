#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

CONSTRUCTION_ROOT = Path(__file__).resolve().parents[2]
if str(CONSTRUCTION_ROOT) not in sys.path:
    sys.path.insert(0, str(CONSTRUCTION_ROOT))

from validation.intrinsic.identity_behavior_adapter import (  # noqa: E402
    build_behavior_registry as reusable_build_behavior_registry,
)
from validation.intrinsic.identity_behavior_adapter import (  # noqa: E402
    evaluate_behavior as reusable_evaluate_behavior,
)

PLACEHOLDER_FIELDS = {
    "construction_identity", "construction_status", "responsibility",
    "normative", "expected_relationships", "unresolved_questions",
}
MODEL_FIELDS = {'unresolved_questions', 'verification_boundary', 'aggregate_model', 'canonical_preimage_declaration', 'construction_status', 'canonicalization_reference', 'unavailable_capabilities', 'digest_declaration', 'expected_relationships', 'object_kinds', 'decision_basis', 'reference_model', 'normative', 'responsibility', 'domain_separation', 'semantic_identity_representation', 'identifier_distinction', 'construction_identity'}
FAMILY_FIELDS = {'conflict_rules', 'unresolved_questions', 'family_declaration', 'construction_status', 'expected_relationships', 'decision_basis', 'field_constraints', 'normative', 'responsibility', 'uniqueness_constraints', 'construction_identity'}
VERIFICATION_FIELDS = {'construction_evidence', 'unresolved_questions', 'aggregate_verification', 'construction_status', 'construction_sequence', 'verification_request', 'reference_verification', 'verification_context', 'own_identity_verification', 'expected_relationships', 'decision_basis', 'rejection_classes', 'normative', 'responsibility', 'verification_result', 'construction_identity'}
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
VERIFICATION_SCHEMA_PATH = "authoritative/schemas/identity/IDENTITY-VERIFICATION-CONSTRUCTION-SCHEMA.json"
FIXTURE_PATH = "validation/fixtures/identity/identity-family/IDENTITY-FAMILY-FIXTURES.json"
BEHAVIOR_FIXTURE_PATH = "validation/fixtures/identity/identity-behavior/IDENTITY-BEHAVIOR-FIXTURES.json"
SUPPORTING_PATHS = (
    "authoritative/schemas/identity/README.md",
    "derived/markdown/identity/README.md",
    "validation/fixtures/identity/README.md",
    SCHEMA_PATH, MODEL_SCHEMA_PATH, FAMILY_SCHEMA_PATH, VERIFICATION_SCHEMA_PATH, FIXTURE_PATH, BEHAVIOR_FIXTURE_PATH,
    "validation/intrinsic/validate_canonical_json.py",
    "validation/tests/test_canonical_json.py",
    "validation/tests/test_identity_family.py",
    "validation/fixtures/identity/canonical-json",
    "validation/fixtures/identity/identity-family",
    "validation/fixtures/identity/identity-behavior",
)
EXPECTED_IDENTITIES = {
    ARTIFACTS[0]: "identity-model-construction",
    ARTIFACTS[1]: "canonical-json-construction",
    ARTIFACTS[2]: "identity-family-model-construction",
    ARTIFACTS[3]: "identity-verification-construction",
    SCHEMA_PATH: "canonical-json-construction-schema",
    MODEL_SCHEMA_PATH: "identity-model-construction-schema",
    FAMILY_SCHEMA_PATH: "identity-family-construction-schema",
    VERIFICATION_SCHEMA_PATH: "identity-verification-construction-schema",
    FIXTURE_PATH: "identity-family-fixture-set-construction",
    BEHAVIOR_FIXTURE_PATH: "identity-behavior-fixture-set-construction",
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
EXPECTED_MODEL = {'construction_identity': 'identity-model-construction', 'construction_status': 'under-construction', 'responsibility': 'Define the repository-neutral semantic identity construction kernel, including explicit own-identity, reference, aggregate, cycle, and verification boundaries without defining repository profiles, manifest bootstrap, sealing, or acceptance behavior.', 'normative': False, 'decision_basis': {'portable_behavior': ['semantic-identity-distinct-from-implementation-identifier', 'family-qualified-identity', 'explicit-canonicalization-version', 'explicit-digest-algorithm-and-encoding', 'domain-separated-canonical-preimage', 'explicit-own-identity-handling', 'family-qualified-reference-verification', 'ordered-and-unordered-aggregate-construction', 'direct-aggregate-closure', 'fail-closed-cycle-and-ambiguity-rejection'], 'repository_generic_decisions': ['closed-family-and-encoded-digest-object-representation', 'object-ordered-aggregate-and-unordered-aggregate-kinds', 'designated-own-identity-field-omission', 'identity-only-and-identity-plus-value-reference-values', 'unordered-members-sorted-by-semantic-identity', 'construction-only-verification-evidence']}, 'identifier_distinction': {'semantic_identity': 'family-qualified-content-derived-identity', 'implementation_identifier': 'implementation-local-locator-or-handle', 'equality_rule': 'implementation-identifiers-do-not-determine-semantic-identity-equality', 'preimage_rule': 'implementation-identifiers-are-excluded-unless-a-family-declaration-explicitly-includes-a-semantic-field'}, 'semantic_identity_representation': {'representation_kind': 'closed-object', 'required_components': ['family', 'encoded_digest'], 'family_qualification_required': True, 'encoded_digest_constraint': 'sixty-four-lowercase-hexadecimal-characters', 'final_string_syntax': 'unresolved'}, 'canonicalization_reference': {'supported_versions': ['canonical-json-v1'], 'selection': 'family-declaration-required'}, 'digest_declaration': {'supported_algorithms': ['sha-256'], 'supported_encodings': ['lowercase-hexadecimal'], 'selection': 'family-declaration-required'}, 'domain_separation': {'ownership': 'identity-family', 'prefix_required': True, 'prefix_character_domain': 'printable-ascii', 'prefix_terminator': 'nul', 'prefix_uniqueness': 'repository-specification-construction-set'}, 'object_kinds': ['object', 'ordered-aggregate', 'unordered-aggregate'], 'canonical_preimage_declaration': {'included_fields': 'non-empty-unique-normalized-field-name-array', 'omitted_fields': 'unique-normalized-field-name-array', 'included_and_omitted_fields': 'disjoint', 'own_identity_rule': 'omit-designated-own-identity-field', 'domain_prefix_application': 'domain-prefix-bytes-followed-by-canonical-value-bytes'}, 'reference_model': {'permitted_modes': ['by-identity', 'identity-plus-value'], 'family_qualification_required': True, 'identity_only_context': 'caller-supplied-verified-identity-set', 'identity_plus_value_context': 'embedded-value-recomputation', 'unsupported_or_ambiguous_reference': 'reject'}, 'aggregate_model': {'ordering_modes': ['ordered', 'unordered'], 'ordered_rule': 'preserve-declared-order', 'unordered_rule': 'sort-ascending-by-member-semantic-identity', 'duplicate_policy': 'reject', 'empty_policy': 'family-declaration-required', 'closure_boundary': 'direct', 'transitive_closure': 'unavailable', 'self_membership': 'reject', 'cycle_policy': 'reject'}, 'verification_boundary': {'supplied_identity_comparison': 'exact-family-and-digest-match', 'reference_verification': 'family-specific-and-fail-closed', 'aggregate_verification': 'all-direct-members-required', 'evidence_scope': 'construction-computation-only'}, 'unavailable_capabilities': ['governing-revision-binding', 'manifest-bootstrap', 'sealing', 'acceptance'], 'expected_relationships': ['canonical JSON construction boundary', 'identity family construction boundary', 'identity verification construction boundary'], 'unresolved_questions': ['Final accepted semantic identity string syntax is not defined.', 'Governing revision, manifest bootstrap, sealing, and acceptance behavior remains separately governed.']}
EXPECTED_FAMILY = {'construction_identity': 'identity-family-model-construction', 'construction_status': 'under-construction', 'responsibility': 'Define the closed repository-neutral construction representation and mechanically decidable constraints for identity-family declarations, including own-identity, reference, aggregate, and verification behavior without defining repository profiles, bootstrap, sealing, or acceptance.', 'normative': False, 'decision_basis': {'portable_behavior': ['family-qualified-semantic-identity', 'explicit-canonicalization-binding', 'explicit-digest-binding', 'domain-separated-preimage', 'explicit-own-identity-mode', 'explicit-reference-mode', 'explicit-aggregate-semantics', 'explicit-verification-mode', 'fail-closed-family-selection'], 'repository_generic_decisions': ['functional-family-and-semantic-domain-names', 'closed-object-kind-declaration', 'designated-own-identity-field-omission', 'identity-only-or-identity-plus-value-references', 'unordered-member-semantic-identity-sort', 'fixed-unavailable-later-capabilities']}, 'family_declaration': {'required_fields': ['family_construction_identity', 'family_name', 'semantic_domain', 'object_kind', 'canonicalization_version', 'digest_algorithm', 'digest_encoding', 'domain_prefix', 'included_preimage_fields', 'omitted_preimage_fields', 'own_identity', 'references', 'aggregate', 'verification', 'unavailable_capabilities'], 'closed': True}, 'field_constraints': {'family_name': 'lowercase-functional-identifier', 'semantic_domain': 'lowercase-functional-identifier', 'object_kind': ['object', 'ordered-aggregate', 'unordered-aggregate'], 'canonicalization_version': ['canonical-json-v1'], 'digest_algorithm': ['sha-256'], 'digest_encoding': ['lowercase-hexadecimal'], 'domain_prefix': 'non-empty-printable-ascii-with-implicit-nul-terminator', 'included_preimage_fields': 'non-empty-unique-normalized-field-name-array', 'omitted_preimage_fields': 'unique-normalized-field-name-array', 'included_and_omitted_preimage_fields': 'disjoint', 'own_identity': {'required_fields': ['mode', 'field'], 'closed': True, 'mode': ['omit-own-identity'], 'field': 'normalized-field-name'}, 'references': {'required_fields': ['mode', 'identity_field', 'value_field', 'allowed_family_names'], 'closed': True, 'mode': ['none', 'by-identity', 'identity-plus-value'], 'identity_field': 'normalized-field-name-or-null', 'value_field': 'normalized-field-name-or-null', 'allowed_family_names': 'unique-lowercase-functional-identifier-array'}, 'aggregate': {'required_fields': ['membership_field', 'member_family_names', 'ordering', 'duplicate_policy', 'empty_policy', 'closure_boundary', 'cycle_policy'], 'closed': True, 'non_aggregate_value': None, 'ordering': ['ordered', 'unordered'], 'duplicate_policy': ['reject'], 'empty_policy': ['allow', 'reject'], 'closure_boundary': ['direct'], 'cycle_policy': ['reject']}, 'verification': {'required_fields': ['mode', 'context_source'], 'closed': True, 'mode': ['none', 'verified-identity-set', 'embedded-value-recomputation'], 'context_source': ['none', 'caller-supplied', 'embedded-value']}, 'unavailable_capabilities': ['governing-revision-binding', 'manifest-bootstrap', 'sealing', 'acceptance'], 'family_construction_identity': 'lowercase-functional-identifier'}, 'uniqueness_constraints': ['family-construction-identity', 'family-name', 'semantic-domain-and-family-name', 'domain-prefix'], 'conflict_rules': ['included-and-omitted-preimage-fields-must-not-overlap', 'object-kind-requires-null-aggregate', 'aggregate-kind-requires-non-null-aggregate', 'reference-mode-and-verification-mode-must-correspond', 'identity-plus-value-requires-identity-and-value-fields', 'by-identity-requires-identity-field-and-null-value-field', 'none-reference-mode-requires-null-reference-fields-and-empty-family-list', 'unknown-canonicalization-version-fails', 'unknown-digest-algorithm-fails', 'unknown-digest-encoding-fails', 'unknown-or-concrete-later-capability-field-fails'], 'expected_relationships': ['identity model construction boundary', 'canonical JSON construction boundary', 'identity verification construction boundary'], 'unresolved_questions': ['No repository or product identity families are declared by this construction model.', 'Governing revision, manifest bootstrap, sealing, and acceptance behavior remains separately governed.']}
EXPECTED_MODEL_SCHEMA = {'construction_identity': 'identity-model-construction-schema', 'construction_status': 'under-construction', 'responsibility': 'Constrain the exact construction-only shape of the repository-neutral identity model without claiming final normative schema authority.', 'normative': False, 'target_construction_identity': 'identity-model-construction', 'required_fields': ['construction_identity', 'construction_status', 'responsibility', 'normative', 'decision_basis', 'identifier_distinction', 'semantic_identity_representation', 'canonicalization_reference', 'digest_declaration', 'domain_separation', 'object_kinds', 'canonical_preimage_declaration', 'reference_model', 'aggregate_model', 'verification_boundary', 'unavailable_capabilities', 'expected_relationships', 'unresolved_questions'], 'closed': True, 'field_constraints': {'exact_policy': {'construction_identity': 'identity-model-construction', 'construction_status': 'under-construction', 'responsibility': 'Define the repository-neutral semantic identity construction kernel, including explicit own-identity, reference, aggregate, cycle, and verification boundaries without defining repository profiles, manifest bootstrap, sealing, or acceptance behavior.', 'normative': False, 'decision_basis': {'portable_behavior': ['semantic-identity-distinct-from-implementation-identifier', 'family-qualified-identity', 'explicit-canonicalization-version', 'explicit-digest-algorithm-and-encoding', 'domain-separated-canonical-preimage', 'explicit-own-identity-handling', 'family-qualified-reference-verification', 'ordered-and-unordered-aggregate-construction', 'direct-aggregate-closure', 'fail-closed-cycle-and-ambiguity-rejection'], 'repository_generic_decisions': ['closed-family-and-encoded-digest-object-representation', 'object-ordered-aggregate-and-unordered-aggregate-kinds', 'designated-own-identity-field-omission', 'identity-only-and-identity-plus-value-reference-values', 'unordered-members-sorted-by-semantic-identity', 'construction-only-verification-evidence']}, 'identifier_distinction': {'semantic_identity': 'family-qualified-content-derived-identity', 'implementation_identifier': 'implementation-local-locator-or-handle', 'equality_rule': 'implementation-identifiers-do-not-determine-semantic-identity-equality', 'preimage_rule': 'implementation-identifiers-are-excluded-unless-a-family-declaration-explicitly-includes-a-semantic-field'}, 'semantic_identity_representation': {'representation_kind': 'closed-object', 'required_components': ['family', 'encoded_digest'], 'family_qualification_required': True, 'encoded_digest_constraint': 'sixty-four-lowercase-hexadecimal-characters', 'final_string_syntax': 'unresolved'}, 'canonicalization_reference': {'supported_versions': ['canonical-json-v1'], 'selection': 'family-declaration-required'}, 'digest_declaration': {'supported_algorithms': ['sha-256'], 'supported_encodings': ['lowercase-hexadecimal'], 'selection': 'family-declaration-required'}, 'domain_separation': {'ownership': 'identity-family', 'prefix_required': True, 'prefix_character_domain': 'printable-ascii', 'prefix_terminator': 'nul', 'prefix_uniqueness': 'repository-specification-construction-set'}, 'object_kinds': ['object', 'ordered-aggregate', 'unordered-aggregate'], 'canonical_preimage_declaration': {'included_fields': 'non-empty-unique-normalized-field-name-array', 'omitted_fields': 'unique-normalized-field-name-array', 'included_and_omitted_fields': 'disjoint', 'own_identity_rule': 'omit-designated-own-identity-field', 'domain_prefix_application': 'domain-prefix-bytes-followed-by-canonical-value-bytes'}, 'reference_model': {'permitted_modes': ['by-identity', 'identity-plus-value'], 'family_qualification_required': True, 'identity_only_context': 'caller-supplied-verified-identity-set', 'identity_plus_value_context': 'embedded-value-recomputation', 'unsupported_or_ambiguous_reference': 'reject'}, 'aggregate_model': {'ordering_modes': ['ordered', 'unordered'], 'ordered_rule': 'preserve-declared-order', 'unordered_rule': 'sort-ascending-by-member-semantic-identity', 'duplicate_policy': 'reject', 'empty_policy': 'family-declaration-required', 'closure_boundary': 'direct', 'transitive_closure': 'unavailable', 'self_membership': 'reject', 'cycle_policy': 'reject'}, 'verification_boundary': {'supplied_identity_comparison': 'exact-family-and-digest-match', 'reference_verification': 'family-specific-and-fail-closed', 'aggregate_verification': 'all-direct-members-required', 'evidence_scope': 'construction-computation-only'}, 'unavailable_capabilities': ['governing-revision-binding', 'manifest-bootstrap', 'sealing', 'acceptance'], 'expected_relationships': ['canonical JSON construction boundary', 'identity family construction boundary', 'identity verification construction boundary'], 'unresolved_questions': ['Final accepted semantic identity string syntax is not defined.', 'Governing revision, manifest bootstrap, sealing, and acceptance behavior remains separately governed.']}, 'unknown_fields': 'reject', 'missing_fields': 'reject'}, 'forbidden_claim_fields': ['accepted', 'complete', 'completed', 'sealed', 'final', 'digest', 'content_digest', 'revision', 'specification_revision', 'aggregate_revision'], 'expected_relationships': ['identity model construction boundary', 'identity family construction schema', 'identity verification construction schema', 'repository specification construction manifest'], 'unresolved_questions': ['Final normative identity-model schema is not defined.', 'Governing revision, manifest bootstrap, sealing, and acceptance behavior remains separately governed.']}
EXPECTED_FAMILY_SCHEMA = {'construction_identity': 'identity-family-construction-schema', 'construction_status': 'under-construction', 'responsibility': 'Constrain the exact construction-only shape of repository-neutral identity-family declarations without claiming final normative schema authority.', 'normative': False, 'target_construction_identity': 'identity-family-model-construction', 'required_fields': ['construction_identity', 'construction_status', 'responsibility', 'normative', 'decision_basis', 'family_declaration', 'field_constraints', 'uniqueness_constraints', 'conflict_rules', 'expected_relationships', 'unresolved_questions'], 'closed': True, 'field_constraints': {'exact_policy': {'construction_identity': 'identity-family-model-construction', 'construction_status': 'under-construction', 'responsibility': 'Define the closed repository-neutral construction representation and mechanically decidable constraints for identity-family declarations, including own-identity, reference, aggregate, and verification behavior without defining repository profiles, bootstrap, sealing, or acceptance.', 'normative': False, 'decision_basis': {'portable_behavior': ['family-qualified-semantic-identity', 'explicit-canonicalization-binding', 'explicit-digest-binding', 'domain-separated-preimage', 'explicit-own-identity-mode', 'explicit-reference-mode', 'explicit-aggregate-semantics', 'explicit-verification-mode', 'fail-closed-family-selection'], 'repository_generic_decisions': ['functional-family-and-semantic-domain-names', 'closed-object-kind-declaration', 'designated-own-identity-field-omission', 'identity-only-or-identity-plus-value-references', 'unordered-member-semantic-identity-sort', 'fixed-unavailable-later-capabilities']}, 'family_declaration': {'required_fields': ['family_construction_identity', 'family_name', 'semantic_domain', 'object_kind', 'canonicalization_version', 'digest_algorithm', 'digest_encoding', 'domain_prefix', 'included_preimage_fields', 'omitted_preimage_fields', 'own_identity', 'references', 'aggregate', 'verification', 'unavailable_capabilities'], 'closed': True}, 'field_constraints': {'family_name': 'lowercase-functional-identifier', 'semantic_domain': 'lowercase-functional-identifier', 'object_kind': ['object', 'ordered-aggregate', 'unordered-aggregate'], 'canonicalization_version': ['canonical-json-v1'], 'digest_algorithm': ['sha-256'], 'digest_encoding': ['lowercase-hexadecimal'], 'domain_prefix': 'non-empty-printable-ascii-with-implicit-nul-terminator', 'included_preimage_fields': 'non-empty-unique-normalized-field-name-array', 'omitted_preimage_fields': 'unique-normalized-field-name-array', 'included_and_omitted_preimage_fields': 'disjoint', 'own_identity': {'required_fields': ['mode', 'field'], 'closed': True, 'mode': ['omit-own-identity'], 'field': 'normalized-field-name'}, 'references': {'required_fields': ['mode', 'identity_field', 'value_field', 'allowed_family_names'], 'closed': True, 'mode': ['none', 'by-identity', 'identity-plus-value'], 'identity_field': 'normalized-field-name-or-null', 'value_field': 'normalized-field-name-or-null', 'allowed_family_names': 'unique-lowercase-functional-identifier-array'}, 'aggregate': {'required_fields': ['membership_field', 'member_family_names', 'ordering', 'duplicate_policy', 'empty_policy', 'closure_boundary', 'cycle_policy'], 'closed': True, 'non_aggregate_value': None, 'ordering': ['ordered', 'unordered'], 'duplicate_policy': ['reject'], 'empty_policy': ['allow', 'reject'], 'closure_boundary': ['direct'], 'cycle_policy': ['reject']}, 'verification': {'required_fields': ['mode', 'context_source'], 'closed': True, 'mode': ['none', 'verified-identity-set', 'embedded-value-recomputation'], 'context_source': ['none', 'caller-supplied', 'embedded-value']}, 'unavailable_capabilities': ['governing-revision-binding', 'manifest-bootstrap', 'sealing', 'acceptance'], 'family_construction_identity': 'lowercase-functional-identifier'}, 'uniqueness_constraints': ['family-construction-identity', 'family-name', 'semantic-domain-and-family-name', 'domain-prefix'], 'conflict_rules': ['included-and-omitted-preimage-fields-must-not-overlap', 'object-kind-requires-null-aggregate', 'aggregate-kind-requires-non-null-aggregate', 'reference-mode-and-verification-mode-must-correspond', 'identity-plus-value-requires-identity-and-value-fields', 'by-identity-requires-identity-field-and-null-value-field', 'none-reference-mode-requires-null-reference-fields-and-empty-family-list', 'unknown-canonicalization-version-fails', 'unknown-digest-algorithm-fails', 'unknown-digest-encoding-fails', 'unknown-or-concrete-later-capability-field-fails'], 'expected_relationships': ['identity model construction boundary', 'canonical JSON construction boundary', 'identity verification construction boundary'], 'unresolved_questions': ['No repository or product identity families are declared by this construction model.', 'Governing revision, manifest bootstrap, sealing, and acceptance behavior remains separately governed.']}, 'unknown_fields': 'reject', 'missing_fields': 'reject'}, 'forbidden_claim_fields': ['accepted', 'complete', 'completed', 'sealed', 'final', 'digest', 'content_digest', 'revision', 'specification_revision', 'aggregate_revision'], 'expected_relationships': ['identity family construction boundary', 'identity model construction schema', 'identity verification construction schema', 'repository specification construction manifest'], 'unresolved_questions': ['Final normative identity-family schema is not defined.', 'Concrete family instances and later repository lifecycle behavior remain separately governed.']}
EXPECTED_VERIFICATION = {'construction_identity': 'identity-verification-construction', 'construction_status': 'under-construction', 'responsibility': 'Define closed repository-neutral construction behavior for identity derivation, supplied-versus-computed verification, reference verification, direct aggregate verification, deterministic results, and construction-only evidence.', 'normative': False, 'decision_basis': {'portable_behavior': ['family-resolution-before-construction', 'domain-separated-canonical-preimage', 'omit-designated-own-identity-field', 'contradictory-own-identity-rejection', 'by-identity-context-verification', 'identity-plus-value-recomputation', 'ordered-and-unordered-direct-aggregate-verification', 'fail-closed-cycle-and-family-rejection'], 'repository_generic_decisions': ['closed-verification-request-and-result-objects', 'unordered-members-sorted-by-semantic-identity', 'deterministic-construction-only-evidence', 'no-governing-revision-input-for-this-boundary']}, 'verification_request': {'required_fields': ['mode', 'family_name', 'value', 'supplied_identity', 'verification_context'], 'closed': True, 'modes': ['derive', 'verify'], 'derive_supplied_identity': None, 'verify_supplied_identity': 'required-semantic-identity', 'verification_context': 'unique-sequence-of-verified-identity-records-or-empty'}, 'own_identity_verification': {'preimage_treatment': 'omit-designated-field', 'absent_or_null': 'allowed', 'matching_computed_identity': 'allowed', 'contradictory_identity': 'reject'}, 'verification_context': {'record_required_fields': ['identity', 'family_name', 'verified'], 'record_closed': True, 'identity': 'family-qualified-semantic-identity', 'family_name': 'lowercase-functional-identifier', 'verified': [True], 'duplicate_identity_policy': 'reject', 'external_to_canonical_preimage': True}, 'construction_sequence': ['resolve-family', 'validate-family-applicability', 'copy-declared-included-fields', 'capture-and-omit-designated-own-identity-field', 'resolve-and-verify-references', 'validate-direct-aggregate-membership', 'canonicalize-value', 'prepend-domain-prefix-and-nul', 'compute-sha-256', 'encode-lowercase-hexadecimal', 'construct-family-qualified-semantic-identity', 'validate-supplied-own-identity', 'compare-supplied-and-computed-identity'], 'reference_verification': {'by_identity': {'required_context': 'caller-supplied-verified-identity-set', 'canonical_value': 'referenced-semantic-identity', 'missing_unknown_conflicting_or_unverified': 'reject'}, 'identity_plus_value': {'required_context': 'embedded-value', 'canonical_value': 'declared-identity-and-value-reference-object', 'verification': 'recompute-value-identity-and-require-exact-match'}}, 'aggregate_verification': {'closure_boundary': 'direct', 'ordered_members': 'preserve-declared-order', 'unordered_members': 'sort-ascending-by-member-semantic-identity', 'duplicate_members': 'reject', 'empty_members': 'apply-family-declared-policy', 'self_membership': 'reject', 'cycles': 'reject', 'member_family_mismatch': 'reject'}, 'verification_result': {'required_fields': ['status', 'family_name', 'computed_identity', 'supplied_identity', 'evidence', 'diagnostic'], 'closed': True, 'statuses': ['derived', 'verified', 'rejected'], 'success_diagnostic': None, 'rejected_computed_identity': None}, 'construction_evidence': {'required_fields': ['family_name', 'canonicalization_version', 'digest_algorithm', 'domain_prefix', 'own_identity_field_omitted', 'reference_count', 'aggregate_member_count', 'aggregate_ordering', 'canonical_value_sha256', 'computed_identity'], 'closed': True, 'scope': 'construction-computation-only'}, 'rejection_classes': ['malformed-request', 'missing-family', 'unknown-family', 'family-mismatch', 'unsupported-object-kind', 'malformed-own-identity', 'contradictory-own-identity', 'malformed-reference', 'missing-reference-context', 'unverified-reference', 'reference-family-mismatch', 'embedded-reference-identity-mismatch', 'duplicate-aggregate-member', 'empty-aggregate-forbidden', 'self-membership', 'aggregate-cycle', 'supplied-identity-mismatch', 'unsupported-construction-capability'], 'expected_relationships': ['identity model construction boundary', 'canonical JSON construction boundary', 'identity family construction boundary', 'identity verification construction schema'], 'unresolved_questions': ['Governing specification revision selection is not required for this bounded generic construction mechanism.', 'Manifest bootstrap, sealing, acceptance, and product evidence semantics remain separately governed.']}
EXPECTED_VERIFICATION_SCHEMA = {'construction_identity': 'identity-verification-construction-schema', 'construction_status': 'under-construction', 'responsibility': 'Constrain the exact construction-only shape of repository-neutral identity verification behavior without claiming final normative schema authority.', 'normative': False, 'target_construction_identity': 'identity-verification-construction', 'required_fields': ['construction_identity', 'construction_status', 'responsibility', 'normative', 'decision_basis', 'verification_request', 'own_identity_verification', 'verification_context', 'construction_sequence', 'reference_verification', 'aggregate_verification', 'verification_result', 'construction_evidence', 'rejection_classes', 'expected_relationships', 'unresolved_questions'], 'closed': True, 'field_constraints': {'exact_policy': {'construction_identity': 'identity-verification-construction', 'construction_status': 'under-construction', 'responsibility': 'Define closed repository-neutral construction behavior for identity derivation, supplied-versus-computed verification, reference verification, direct aggregate verification, deterministic results, and construction-only evidence.', 'normative': False, 'decision_basis': {'portable_behavior': ['family-resolution-before-construction', 'domain-separated-canonical-preimage', 'omit-designated-own-identity-field', 'contradictory-own-identity-rejection', 'by-identity-context-verification', 'identity-plus-value-recomputation', 'ordered-and-unordered-direct-aggregate-verification', 'fail-closed-cycle-and-family-rejection'], 'repository_generic_decisions': ['closed-verification-request-and-result-objects', 'unordered-members-sorted-by-semantic-identity', 'deterministic-construction-only-evidence', 'no-governing-revision-input-for-this-boundary']}, 'verification_request': {'required_fields': ['mode', 'family_name', 'value', 'supplied_identity', 'verification_context'], 'closed': True, 'modes': ['derive', 'verify'], 'derive_supplied_identity': None, 'verify_supplied_identity': 'required-semantic-identity', 'verification_context': 'unique-sequence-of-verified-identity-records-or-empty'}, 'own_identity_verification': {'preimage_treatment': 'omit-designated-field', 'absent_or_null': 'allowed', 'matching_computed_identity': 'allowed', 'contradictory_identity': 'reject'}, 'verification_context': {'record_required_fields': ['identity', 'family_name', 'verified'], 'record_closed': True, 'identity': 'family-qualified-semantic-identity', 'family_name': 'lowercase-functional-identifier', 'verified': [True], 'duplicate_identity_policy': 'reject', 'external_to_canonical_preimage': True}, 'construction_sequence': ['resolve-family', 'validate-family-applicability', 'copy-declared-included-fields', 'capture-and-omit-designated-own-identity-field', 'resolve-and-verify-references', 'validate-direct-aggregate-membership', 'canonicalize-value', 'prepend-domain-prefix-and-nul', 'compute-sha-256', 'encode-lowercase-hexadecimal', 'construct-family-qualified-semantic-identity', 'validate-supplied-own-identity', 'compare-supplied-and-computed-identity'], 'reference_verification': {'by_identity': {'required_context': 'caller-supplied-verified-identity-set', 'canonical_value': 'referenced-semantic-identity', 'missing_unknown_conflicting_or_unverified': 'reject'}, 'identity_plus_value': {'required_context': 'embedded-value', 'canonical_value': 'declared-identity-and-value-reference-object', 'verification': 'recompute-value-identity-and-require-exact-match'}}, 'aggregate_verification': {'closure_boundary': 'direct', 'ordered_members': 'preserve-declared-order', 'unordered_members': 'sort-ascending-by-member-semantic-identity', 'duplicate_members': 'reject', 'empty_members': 'apply-family-declared-policy', 'self_membership': 'reject', 'cycles': 'reject', 'member_family_mismatch': 'reject'}, 'verification_result': {'required_fields': ['status', 'family_name', 'computed_identity', 'supplied_identity', 'evidence', 'diagnostic'], 'closed': True, 'statuses': ['derived', 'verified', 'rejected'], 'success_diagnostic': None, 'rejected_computed_identity': None}, 'construction_evidence': {'required_fields': ['family_name', 'canonicalization_version', 'digest_algorithm', 'domain_prefix', 'own_identity_field_omitted', 'reference_count', 'aggregate_member_count', 'aggregate_ordering', 'canonical_value_sha256', 'computed_identity'], 'closed': True, 'scope': 'construction-computation-only'}, 'rejection_classes': ['malformed-request', 'missing-family', 'unknown-family', 'family-mismatch', 'unsupported-object-kind', 'malformed-own-identity', 'contradictory-own-identity', 'malformed-reference', 'missing-reference-context', 'unverified-reference', 'reference-family-mismatch', 'embedded-reference-identity-mismatch', 'duplicate-aggregate-member', 'empty-aggregate-forbidden', 'self-membership', 'aggregate-cycle', 'supplied-identity-mismatch', 'unsupported-construction-capability'], 'expected_relationships': ['identity model construction boundary', 'canonical JSON construction boundary', 'identity family construction boundary', 'identity verification construction schema'], 'unresolved_questions': ['Governing specification revision selection is not required for this bounded generic construction mechanism.', 'Manifest bootstrap, sealing, acceptance, and product evidence semantics remain separately governed.']}, 'unknown_fields': 'reject', 'missing_fields': 'reject'}, 'forbidden_claim_fields': ['accepted', 'complete', 'completed', 'sealed', 'final', 'digest', 'content_digest', 'revision', 'specification_revision', 'aggregate_revision'], 'expected_relationships': ['identity verification construction boundary', 'identity model construction boundary', 'identity family construction boundary', 'repository specification construction manifest'], 'unresolved_questions': ['Final normative identity verification schema is not defined.', 'Governing revision, manifest bootstrap, sealing, and acceptance behavior remains separately governed.']}
EXPECTED_BEHAVIOR_FIXTURE_SET = {'construction_identity': 'identity-behavior-fixture-set-construction', 'construction_status': 'under-construction', 'responsibility': 'Provide fixed repository-neutral construction vectors for own-identity omission, reference verification, direct aggregate behavior, deterministic identity derivation, and fail-closed rejection.', 'normative': False, 'family_declarations': [{'family_construction_identity': 'document-family-construction', 'family_name': 'document', 'semantic_domain': 'document-content', 'object_kind': 'object', 'canonicalization_version': 'canonical-json-v1', 'digest_algorithm': 'sha-256', 'digest_encoding': 'lowercase-hexadecimal', 'domain_prefix': 'repo.identity.document.v1', 'included_preimage_fields': ['identity', 'title', 'body'], 'omitted_preimage_fields': ['cache_key'], 'own_identity': {'mode': 'omit-own-identity', 'field': 'identity'}, 'references': {'mode': 'none', 'identity_field': None, 'value_field': None, 'allowed_family_names': []}, 'aggregate': None, 'verification': {'mode': 'none', 'context_source': 'none'}, 'unavailable_capabilities': ['governing-revision-binding', 'manifest-bootstrap', 'sealing', 'acceptance']}, {'family_construction_identity': 'link-family-construction', 'family_name': 'link', 'semantic_domain': 'link-content', 'object_kind': 'object', 'canonicalization_version': 'canonical-json-v1', 'digest_algorithm': 'sha-256', 'digest_encoding': 'lowercase-hexadecimal', 'domain_prefix': 'repo.identity.link.v1', 'included_preimage_fields': ['identity', 'name', 'references'], 'omitted_preimage_fields': ['cache_key'], 'own_identity': {'mode': 'omit-own-identity', 'field': 'identity'}, 'references': {'mode': 'by-identity', 'identity_field': 'identity', 'value_field': None, 'allowed_family_names': ['document']}, 'aggregate': None, 'verification': {'mode': 'verified-identity-set', 'context_source': 'caller-supplied'}, 'unavailable_capabilities': ['governing-revision-binding', 'manifest-bootstrap', 'sealing', 'acceptance']}, {'family_construction_identity': 'envelope-family-construction', 'family_name': 'envelope', 'semantic_domain': 'envelope-content', 'object_kind': 'object', 'canonicalization_version': 'canonical-json-v1', 'digest_algorithm': 'sha-256', 'digest_encoding': 'lowercase-hexadecimal', 'domain_prefix': 'repo.identity.envelope.v1', 'included_preimage_fields': ['identity', 'label', 'references'], 'omitted_preimage_fields': ['cache_key'], 'own_identity': {'mode': 'omit-own-identity', 'field': 'identity'}, 'references': {'mode': 'identity-plus-value', 'identity_field': 'identity', 'value_field': 'value', 'allowed_family_names': ['document']}, 'aggregate': None, 'verification': {'mode': 'embedded-value-recomputation', 'context_source': 'embedded-value'}, 'unavailable_capabilities': ['governing-revision-binding', 'manifest-bootstrap', 'sealing', 'acceptance']}, {'family_construction_identity': 'ordered-bundle-family-construction', 'family_name': 'ordered-bundle', 'semantic_domain': 'ordered-bundle-content', 'object_kind': 'ordered-aggregate', 'canonicalization_version': 'canonical-json-v1', 'digest_algorithm': 'sha-256', 'digest_encoding': 'lowercase-hexadecimal', 'domain_prefix': 'repo.identity.ordered-bundle.v1', 'included_preimage_fields': ['identity', 'members'], 'omitted_preimage_fields': ['cache_key'], 'own_identity': {'mode': 'omit-own-identity', 'field': 'identity'}, 'references': {'mode': 'by-identity', 'identity_field': 'identity', 'value_field': None, 'allowed_family_names': ['document']}, 'aggregate': {'membership_field': 'members', 'member_family_names': ['document'], 'ordering': 'ordered', 'duplicate_policy': 'reject', 'empty_policy': 'reject', 'closure_boundary': 'direct', 'cycle_policy': 'reject'}, 'verification': {'mode': 'verified-identity-set', 'context_source': 'caller-supplied'}, 'unavailable_capabilities': ['governing-revision-binding', 'manifest-bootstrap', 'sealing', 'acceptance']}, {'family_construction_identity': 'unordered-bundle-family-construction', 'family_name': 'unordered-bundle', 'semantic_domain': 'unordered-bundle-content', 'object_kind': 'unordered-aggregate', 'canonicalization_version': 'canonical-json-v1', 'digest_algorithm': 'sha-256', 'digest_encoding': 'lowercase-hexadecimal', 'domain_prefix': 'repo.identity.unordered-bundle.v1', 'included_preimage_fields': ['identity', 'members'], 'omitted_preimage_fields': ['cache_key'], 'own_identity': {'mode': 'omit-own-identity', 'field': 'identity'}, 'references': {'mode': 'by-identity', 'identity_field': 'identity', 'value_field': None, 'allowed_family_names': ['document']}, 'aggregate': {'membership_field': 'members', 'member_family_names': ['document'], 'ordering': 'unordered', 'duplicate_policy': 'reject', 'empty_policy': 'reject', 'closure_boundary': 'direct', 'cycle_policy': 'reject'}, 'verification': {'mode': 'verified-identity-set', 'context_source': 'caller-supplied'}, 'unavailable_capabilities': ['governing-revision-binding', 'manifest-bootstrap', 'sealing', 'acceptance']}, {'family_construction_identity': 'cycle-link-family-construction', 'family_name': 'cycle-link', 'semantic_domain': 'cycle-link-content', 'object_kind': 'object', 'canonicalization_version': 'canonical-json-v1', 'digest_algorithm': 'sha-256', 'digest_encoding': 'lowercase-hexadecimal', 'domain_prefix': 'repo.identity.cycle-link.v1', 'included_preimage_fields': ['identity', 'name', 'references'], 'omitted_preimage_fields': ['cache_key'], 'own_identity': {'mode': 'omit-own-identity', 'field': 'identity'}, 'references': {'mode': 'by-identity', 'identity_field': 'identity', 'value_field': None, 'allowed_family_names': ['cycle-parent']}, 'aggregate': None, 'verification': {'mode': 'verified-identity-set', 'context_source': 'caller-supplied'}, 'unavailable_capabilities': ['governing-revision-binding', 'manifest-bootstrap', 'sealing', 'acceptance']}, {'family_construction_identity': 'cycle-parent-family-construction', 'family_name': 'cycle-parent', 'semantic_domain': 'cycle-parent-content', 'object_kind': 'object', 'canonicalization_version': 'canonical-json-v1', 'digest_algorithm': 'sha-256', 'digest_encoding': 'lowercase-hexadecimal', 'domain_prefix': 'repo.identity.cycle-parent.v1', 'included_preimage_fields': ['identity', 'label', 'references'], 'omitted_preimage_fields': ['cache_key'], 'own_identity': {'mode': 'omit-own-identity', 'field': 'identity'}, 'references': {'mode': 'identity-plus-value', 'identity_field': 'identity', 'value_field': 'value', 'allowed_family_names': ['cycle-link']}, 'aggregate': None, 'verification': {'mode': 'embedded-value-recomputation', 'context_source': 'embedded-value'}, 'unavailable_capabilities': ['governing-revision-binding', 'manifest-bootstrap', 'sealing', 'acceptance']}, {'family_construction_identity': 'empty-bundle-family-construction', 'family_name': 'empty-bundle', 'semantic_domain': 'empty-bundle-content', 'object_kind': 'unordered-aggregate', 'canonicalization_version': 'canonical-json-v1', 'digest_algorithm': 'sha-256', 'digest_encoding': 'lowercase-hexadecimal', 'domain_prefix': 'repo.identity.empty-bundle.v1', 'included_preimage_fields': ['identity', 'members'], 'omitted_preimage_fields': ['cache_key'], 'own_identity': {'mode': 'omit-own-identity', 'field': 'identity'}, 'references': {'mode': 'by-identity', 'identity_field': 'identity', 'value_field': None, 'allowed_family_names': ['document']}, 'aggregate': {'membership_field': 'members', 'member_family_names': ['document'], 'ordering': 'unordered', 'duplicate_policy': 'reject', 'empty_policy': 'allow', 'closure_boundary': 'direct', 'cycle_policy': 'reject'}, 'verification': {'mode': 'verified-identity-set', 'context_source': 'caller-supplied'}, 'unavailable_capabilities': ['governing-revision-binding', 'manifest-bootstrap', 'sealing', 'acceptance']}, {'family_construction_identity': 'direct-cycle-family-construction', 'family_name': 'direct-cycle', 'semantic_domain': 'direct-cycle-content', 'object_kind': 'object', 'canonicalization_version': 'canonical-json-v1', 'digest_algorithm': 'sha-256', 'digest_encoding': 'lowercase-hexadecimal', 'domain_prefix': 'repo.identity.direct-cycle.v1', 'included_preimage_fields': ['identity', 'label', 'references'], 'omitted_preimage_fields': ['cache_key'], 'own_identity': {'mode': 'omit-own-identity', 'field': 'identity'}, 'references': {'mode': 'identity-plus-value', 'identity_field': 'identity', 'value_field': 'value', 'allowed_family_names': ['direct-cycle']}, 'aggregate': None, 'verification': {'mode': 'embedded-value-recomputation', 'context_source': 'embedded-value'}, 'unavailable_capabilities': ['governing-revision-binding', 'manifest-bootstrap', 'sealing', 'acceptance']}], 'cases': [{'name': 'own-identity-omission', 'request': {'mode': 'derive', 'family_name': 'document', 'value': {'title': 'A', 'body': 'alpha'}, 'supplied_identity': None, 'verification_context': []}, 'expected_status': 'derived', 'expected_identity': {'family': 'document', 'encoded_digest': '6e789cfa6d882b7813b9bca2f0b2dd8ec5eb24fe496c2bb4ca83cf5c1194bd95'}, 'expected_diagnostic': None}, {'name': 'matching-own-identity-verifies', 'request': {'mode': 'verify', 'family_name': 'document', 'value': {'identity': {'family': 'document', 'encoded_digest': '6e789cfa6d882b7813b9bca2f0b2dd8ec5eb24fe496c2bb4ca83cf5c1194bd95'}, 'title': 'A', 'body': 'alpha'}, 'supplied_identity': {'family': 'document', 'encoded_digest': '6e789cfa6d882b7813b9bca2f0b2dd8ec5eb24fe496c2bb4ca83cf5c1194bd95'}, 'verification_context': []}, 'expected_status': 'verified', 'expected_identity': {'family': 'document', 'encoded_digest': '6e789cfa6d882b7813b9bca2f0b2dd8ec5eb24fe496c2bb4ca83cf5c1194bd95'}, 'expected_diagnostic': None}, {'name': 'contradictory-own-identity-rejects', 'request': {'mode': 'derive', 'family_name': 'document', 'value': {'title': 'A', 'body': 'alpha', 'identity': {'family': 'document', 'encoded_digest': '9999999999999999999999999999999999999999999999999999999999999999'}}, 'supplied_identity': None, 'verification_context': []}, 'expected_status': 'rejected', 'expected_identity': None, 'expected_diagnostic': 'contradictory-own-identity'}, {'name': 'by-identity-reference-verifies', 'request': {'mode': 'verify', 'family_name': 'link', 'value': {'name': 'link', 'references': [{'identity': {'family': 'document', 'encoded_digest': '6e789cfa6d882b7813b9bca2f0b2dd8ec5eb24fe496c2bb4ca83cf5c1194bd95'}}]}, 'supplied_identity': {'family': 'link', 'encoded_digest': 'd11781e2fcf066ee07a968791f19513afffb6c6009c1a579018b99433c09cc3b'}, 'verification_context': [{'identity': {'family': 'document', 'encoded_digest': '6e789cfa6d882b7813b9bca2f0b2dd8ec5eb24fe496c2bb4ca83cf5c1194bd95'}, 'family_name': 'document', 'verified': True}, {'identity': {'family': 'document', 'encoded_digest': '0d77829c2beb4595331d3820df2b226de3540e3142722f50c5dcbfed4d9f529c'}, 'family_name': 'document', 'verified': True}]}, 'expected_status': 'verified', 'expected_identity': {'family': 'link', 'encoded_digest': 'd11781e2fcf066ee07a968791f19513afffb6c6009c1a579018b99433c09cc3b'}, 'expected_diagnostic': None}, {'name': 'missing-by-identity-context-rejects', 'request': {'mode': 'derive', 'family_name': 'link', 'value': {'name': 'link', 'references': [{'identity': {'family': 'document', 'encoded_digest': '6e789cfa6d882b7813b9bca2f0b2dd8ec5eb24fe496c2bb4ca83cf5c1194bd95'}}]}, 'supplied_identity': None, 'verification_context': []}, 'expected_status': 'rejected', 'expected_identity': None, 'expected_diagnostic': 'missing-reference-context'}, {'name': 'identity-plus-value-recomputes', 'request': {'mode': 'verify', 'family_name': 'envelope', 'value': {'label': 'env', 'references': [{'identity': {'family': 'document', 'encoded_digest': '6e789cfa6d882b7813b9bca2f0b2dd8ec5eb24fe496c2bb4ca83cf5c1194bd95'}, 'value': {'title': 'A', 'body': 'alpha'}}]}, 'supplied_identity': {'family': 'envelope', 'encoded_digest': 'c9bc8601d26b3580d60fd1ffc9ba2331239dce360eb900c38928152ee5a7984b'}, 'verification_context': []}, 'expected_status': 'verified', 'expected_identity': {'family': 'envelope', 'encoded_digest': 'c9bc8601d26b3580d60fd1ffc9ba2331239dce360eb900c38928152ee5a7984b'}, 'expected_diagnostic': None}, {'name': 'identity-plus-value-mismatch-rejects', 'request': {'mode': 'derive', 'family_name': 'envelope', 'value': {'label': 'env', 'references': [{'identity': {'family': 'document', 'encoded_digest': '0000000000000000000000000000000000000000000000000000000000000000'}, 'value': {'title': 'A', 'body': 'alpha'}}]}, 'supplied_identity': None, 'verification_context': []}, 'expected_status': 'rejected', 'expected_identity': None, 'expected_diagnostic': 'embedded-reference-identity-mismatch'}, {'name': 'ordered-aggregate-ab', 'request': {'mode': 'derive', 'family_name': 'ordered-bundle', 'value': {'members': [{'identity': {'family': 'document', 'encoded_digest': '6e789cfa6d882b7813b9bca2f0b2dd8ec5eb24fe496c2bb4ca83cf5c1194bd95'}}, {'identity': {'family': 'document', 'encoded_digest': '0d77829c2beb4595331d3820df2b226de3540e3142722f50c5dcbfed4d9f529c'}}]}, 'supplied_identity': None, 'verification_context': [{'identity': {'family': 'document', 'encoded_digest': '6e789cfa6d882b7813b9bca2f0b2dd8ec5eb24fe496c2bb4ca83cf5c1194bd95'}, 'family_name': 'document', 'verified': True}, {'identity': {'family': 'document', 'encoded_digest': '0d77829c2beb4595331d3820df2b226de3540e3142722f50c5dcbfed4d9f529c'}, 'family_name': 'document', 'verified': True}]}, 'expected_status': 'derived', 'expected_identity': {'family': 'ordered-bundle', 'encoded_digest': 'db3608b8eb9909b4f25eed2148982e89aad484870ff8b7dd5a299763ecc25272'}, 'expected_diagnostic': None}, {'name': 'ordered-aggregate-ba', 'request': {'mode': 'derive', 'family_name': 'ordered-bundle', 'value': {'members': [{'identity': {'family': 'document', 'encoded_digest': '0d77829c2beb4595331d3820df2b226de3540e3142722f50c5dcbfed4d9f529c'}}, {'identity': {'family': 'document', 'encoded_digest': '6e789cfa6d882b7813b9bca2f0b2dd8ec5eb24fe496c2bb4ca83cf5c1194bd95'}}]}, 'supplied_identity': None, 'verification_context': [{'identity': {'family': 'document', 'encoded_digest': '6e789cfa6d882b7813b9bca2f0b2dd8ec5eb24fe496c2bb4ca83cf5c1194bd95'}, 'family_name': 'document', 'verified': True}, {'identity': {'family': 'document', 'encoded_digest': '0d77829c2beb4595331d3820df2b226de3540e3142722f50c5dcbfed4d9f529c'}, 'family_name': 'document', 'verified': True}]}, 'expected_status': 'derived', 'expected_identity': {'family': 'ordered-bundle', 'encoded_digest': 'ee081dad3d6161e388b6192365641184c71f436ce1c1fab78d56258ad45b3384'}, 'expected_diagnostic': None}, {'name': 'unordered-aggregate-ab', 'request': {'mode': 'derive', 'family_name': 'unordered-bundle', 'value': {'members': [{'identity': {'family': 'document', 'encoded_digest': '6e789cfa6d882b7813b9bca2f0b2dd8ec5eb24fe496c2bb4ca83cf5c1194bd95'}}, {'identity': {'family': 'document', 'encoded_digest': '0d77829c2beb4595331d3820df2b226de3540e3142722f50c5dcbfed4d9f529c'}}]}, 'supplied_identity': None, 'verification_context': [{'identity': {'family': 'document', 'encoded_digest': '6e789cfa6d882b7813b9bca2f0b2dd8ec5eb24fe496c2bb4ca83cf5c1194bd95'}, 'family_name': 'document', 'verified': True}, {'identity': {'family': 'document', 'encoded_digest': '0d77829c2beb4595331d3820df2b226de3540e3142722f50c5dcbfed4d9f529c'}, 'family_name': 'document', 'verified': True}]}, 'expected_status': 'derived', 'expected_identity': {'family': 'unordered-bundle', 'encoded_digest': '73b0826c934318d18763aa80fdbeb73ceeb016faddee7f4a65d35c164dceaaf4'}, 'expected_diagnostic': None}, {'name': 'unordered-aggregate-ba', 'request': {'mode': 'derive', 'family_name': 'unordered-bundle', 'value': {'members': [{'identity': {'family': 'document', 'encoded_digest': '0d77829c2beb4595331d3820df2b226de3540e3142722f50c5dcbfed4d9f529c'}}, {'identity': {'family': 'document', 'encoded_digest': '6e789cfa6d882b7813b9bca2f0b2dd8ec5eb24fe496c2bb4ca83cf5c1194bd95'}}]}, 'supplied_identity': None, 'verification_context': [{'identity': {'family': 'document', 'encoded_digest': '6e789cfa6d882b7813b9bca2f0b2dd8ec5eb24fe496c2bb4ca83cf5c1194bd95'}, 'family_name': 'document', 'verified': True}, {'identity': {'family': 'document', 'encoded_digest': '0d77829c2beb4595331d3820df2b226de3540e3142722f50c5dcbfed4d9f529c'}, 'family_name': 'document', 'verified': True}]}, 'expected_status': 'derived', 'expected_identity': {'family': 'unordered-bundle', 'encoded_digest': '73b0826c934318d18763aa80fdbeb73ceeb016faddee7f4a65d35c164dceaaf4'}, 'expected_diagnostic': None}, {'name': 'duplicate-aggregate-member-rejects', 'request': {'mode': 'derive', 'family_name': 'ordered-bundle', 'value': {'members': [{'identity': {'family': 'document', 'encoded_digest': '6e789cfa6d882b7813b9bca2f0b2dd8ec5eb24fe496c2bb4ca83cf5c1194bd95'}}, {'identity': {'family': 'document', 'encoded_digest': '6e789cfa6d882b7813b9bca2f0b2dd8ec5eb24fe496c2bb4ca83cf5c1194bd95'}}]}, 'supplied_identity': None, 'verification_context': [{'identity': {'family': 'document', 'encoded_digest': '6e789cfa6d882b7813b9bca2f0b2dd8ec5eb24fe496c2bb4ca83cf5c1194bd95'}, 'family_name': 'document', 'verified': True}, {'identity': {'family': 'document', 'encoded_digest': '0d77829c2beb4595331d3820df2b226de3540e3142722f50c5dcbfed4d9f529c'}, 'family_name': 'document', 'verified': True}]}, 'expected_status': 'rejected', 'expected_identity': None, 'expected_diagnostic': 'duplicate-aggregate-member'}, {'name': 'empty-aggregate-rejects', 'request': {'mode': 'derive', 'family_name': 'ordered-bundle', 'value': {'members': []}, 'supplied_identity': None, 'verification_context': []}, 'expected_status': 'rejected', 'expected_identity': None, 'expected_diagnostic': 'empty-aggregate-forbidden'}, {'name': 'self-membership-rejects', 'request': {'mode': 'verify', 'family_name': 'ordered-bundle', 'value': {'members': [{'identity': {'family': 'ordered-bundle', 'encoded_digest': 'db3608b8eb9909b4f25eed2148982e89aad484870ff8b7dd5a299763ecc25272'}}]}, 'supplied_identity': {'family': 'ordered-bundle', 'encoded_digest': 'db3608b8eb9909b4f25eed2148982e89aad484870ff8b7dd5a299763ecc25272'}, 'verification_context': [{'identity': {'family': 'ordered-bundle', 'encoded_digest': 'db3608b8eb9909b4f25eed2148982e89aad484870ff8b7dd5a299763ecc25272'}, 'family_name': 'ordered-bundle', 'verified': True}]}, 'expected_status': 'rejected', 'expected_identity': None, 'expected_diagnostic': 'self-membership'}, {'name': 'reference-family-mismatch-rejects', 'request': {'mode': 'derive', 'family_name': 'link', 'value': {'name': 'link', 'references': [{'identity': {'family': 'link', 'encoded_digest': 'd11781e2fcf066ee07a968791f19513afffb6c6009c1a579018b99433c09cc3b'}}]}, 'supplied_identity': None, 'verification_context': [{'identity': {'family': 'link', 'encoded_digest': 'd11781e2fcf066ee07a968791f19513afffb6c6009c1a579018b99433c09cc3b'}, 'family_name': 'link', 'verified': True}]}, 'expected_status': 'rejected', 'expected_identity': None, 'expected_diagnostic': 'reference-family-mismatch'}, {'name': 'supplied-identity-mismatch-rejects', 'request': {'mode': 'verify', 'family_name': 'document', 'value': {'title': 'A', 'body': 'alpha'}, 'supplied_identity': {'family': 'document', 'encoded_digest': '0d77829c2beb4595331d3820df2b226de3540e3142722f50c5dcbfed4d9f529c'}, 'verification_context': []}, 'expected_status': 'rejected', 'expected_identity': None, 'expected_diagnostic': 'supplied-identity-mismatch'}, {'name': 'indirect-cycle-rejects', 'request': {'mode': 'verify', 'family_name': 'cycle-parent', 'value': {'label': 'parent', 'references': [{'identity': {'family': 'cycle-link', 'encoded_digest': '3a466776c3fba6c8334a6fe4561fb78b78f466a2138dc549f323faeb1b989c2a'}, 'value': {'name': 'child', 'references': [{'identity': {'family': 'cycle-parent', 'encoded_digest': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'}}]}}]}, 'supplied_identity': {'family': 'cycle-parent', 'encoded_digest': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'}, 'verification_context': [{'identity': {'family': 'cycle-parent', 'encoded_digest': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'}, 'family_name': 'cycle-parent', 'verified': True}]}, 'expected_status': 'rejected', 'expected_identity': None, 'expected_diagnostic': 'aggregate-cycle'}, {'name': 'empty-aggregate-allowed', 'request': {'mode': 'derive', 'family_name': 'empty-bundle', 'value': {'members': []}, 'supplied_identity': None, 'verification_context': []}, 'expected_status': 'derived', 'expected_identity': {'family': 'empty-bundle', 'encoded_digest': 'de72db850f1569a5645c17bfb2d117c043bb51d413b8915c4565211ed949c107'}, 'expected_diagnostic': None}, {'name': 'direct-cycle-rejects', 'request': {'mode': 'derive', 'family_name': 'direct-cycle', 'value': {'label': 'root', 'references': [{'identity': {'family': 'direct-cycle', 'encoded_digest': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'}, 'value': {'label': 'child', 'references': [{'identity': {'family': 'direct-cycle', 'encoded_digest': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'}, 'value': {'label': 'loop', 'references': []}}]}}]}, 'supplied_identity': None, 'verification_context': []}, 'expected_status': 'rejected', 'expected_identity': None, 'expected_diagnostic': 'aggregate-cycle'}], 'expected_relationships': ['identity verification construction validator', 'identity model construction boundary', 'identity family construction boundary'], 'unresolved_questions': ['These construction vectors are not accepted product conformance vectors.', 'Governing revision, bootstrap, sealing, and acceptance remain separately governed.']}
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


BEHAVIOR_FIXTURE_FIELDS = {
    "construction_identity", "construction_status", "responsibility", "normative",
    "family_declarations", "cases", "expected_relationships", "unresolved_questions",
}
BEHAVIOR_CASE_FIELDS = {
    "name", "request", "expected_status", "expected_identity", "expected_diagnostic",
}
BEHAVIOR_REQUEST_FIELDS = {
    "mode", "family_name", "value", "supplied_identity", "verification_context",
}
BEHAVIOR_FAMILY_FIELDS = {
    "family_construction_identity", "family_name", "semantic_domain", "object_kind",
    "canonicalization_version", "digest_algorithm", "digest_encoding",
    "domain_prefix", "included_preimage_fields", "omitted_preimage_fields",
    "own_identity", "references", "aggregate", "verification",
    "unavailable_capabilities",
}
SEMANTIC_IDENTITY_FIELDS = {"family", "encoded_digest"}
VERIFICATION_RECORD_FIELDS = {"identity", "family_name", "verified"}
LOWER_HEX_64 = re.compile(r"^[0-9a-f]{64}$")


def _behavior_identity(value: Any, label: str) -> dict[str, str]:
    if not isinstance(value, dict):
        fail("REPO-SPEC-IDENTITY-BEHAVIOR-IDENTITY-001", f"{label}: identity must be an object")
    exact_fields(value, SEMANTIC_IDENTITY_FIELDS, label)
    family = value["family"]
    digest = value["encoded_digest"]
    if not isinstance(family, str) or not IDENTITY.fullmatch(family):
        fail("REPO-SPEC-IDENTITY-BEHAVIOR-IDENTITY-001", f"{label}: invalid family")
    if not isinstance(digest, str) or not LOWER_HEX_64.fullmatch(digest):
        fail("REPO-SPEC-IDENTITY-BEHAVIOR-IDENTITY-001", f"{label}: invalid encoded digest")
    return {"family": family, "encoded_digest": digest}


def _behavior_identity_key(value: dict[str, str]) -> tuple[str, str]:
    return value["family"], value["encoded_digest"]


def _behavior_canonical_bytes(value: Any) -> bytes:
    def check(item: Any, label: str) -> None:
        if item is None or isinstance(item, (bool, str)):
            return
        if isinstance(item, int) and not isinstance(item, bool):
            if item < -(2**63) or item > 2**63 - 1:
                fail("REPO-SPEC-IDENTITY-BEHAVIOR-CANONICAL-001", f"{label}: integer outside signed-64-bit range")
            return
        if isinstance(item, list):
            for index, child in enumerate(item):
                check(child, f"{label}[{index}]")
            return
        if isinstance(item, dict):
            for key, child in item.items():
                if not isinstance(key, str):
                    fail("REPO-SPEC-IDENTITY-BEHAVIOR-CANONICAL-001", f"{label}: non-string key")
                check(child, f"{label}.{key}")
            return
        fail("REPO-SPEC-IDENTITY-BEHAVIOR-CANONICAL-001", f"{label}: unsupported JSON value")
    check(value, "canonical-value")
    try:
        encoded = json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        fail("REPO-SPEC-IDENTITY-BEHAVIOR-CANONICAL-001", str(exc))
    return encoded


def _behavior_family_registry(declarations: Any, label: str) -> dict[str, dict[str, Any]]:
    if not isinstance(declarations, list) or not declarations:
        fail("REPO-SPEC-IDENTITY-BEHAVIOR-FAMILY-001", f"{label}: non-empty family declarations required")
    registry: dict[str, dict[str, Any]] = {}
    prefixes: set[str] = set()
    for index, declaration in enumerate(declarations):
        item_label = f"{label}[{index}]"
        if not isinstance(declaration, dict):
            fail("REPO-SPEC-IDENTITY-BEHAVIOR-FAMILY-001", f"{item_label}: declaration must be an object")
        exact_fields(declaration, BEHAVIOR_FAMILY_FIELDS, item_label)
        name = _functional(declaration["family_name"], f"{item_label}.family_name")
        _functional(declaration["family_construction_identity"], f"{item_label}.family_construction_identity")
        _functional(declaration["semantic_domain"], f"{item_label}.semantic_domain")
        if name in registry:
            fail("REPO-SPEC-IDENTITY-BEHAVIOR-FAMILY-001", f"{item_label}: duplicate family name")
        if declaration["object_kind"] not in {"object", "ordered-aggregate", "unordered-aggregate"}:
            fail("REPO-SPEC-IDENTITY-BEHAVIOR-FAMILY-001", f"{item_label}: unsupported object kind")
        if declaration["canonicalization_version"] != "canonical-json-v1":
            fail("REPO-SPEC-IDENTITY-BEHAVIOR-FAMILY-001", f"{item_label}: unsupported canonicalization")
        if declaration["digest_algorithm"] != "sha-256":
            fail("REPO-SPEC-IDENTITY-BEHAVIOR-FAMILY-001", f"{item_label}: unsupported digest")
        if declaration["digest_encoding"] != "lowercase-hexadecimal":
            fail("REPO-SPEC-IDENTITY-BEHAVIOR-FAMILY-001", f"{item_label}: unsupported digest encoding")
        prefix = declaration["domain_prefix"]
        if (
            not isinstance(prefix, str) or not prefix
            or any(ord(character) < 0x20 or ord(character) > 0x7E for character in prefix)
            or prefix in prefixes
        ):
            fail("REPO-SPEC-IDENTITY-BEHAVIOR-FAMILY-001", f"{item_label}: invalid or duplicate domain prefix")
        prefixes.add(prefix)
        included = _preimage_fields(declaration["included_preimage_fields"], f"{item_label}.included_preimage_fields")
        omitted = _preimage_fields(declaration["omitted_preimage_fields"], f"{item_label}.omitted_preimage_fields")
        if set(included) & set(omitted):
            fail("REPO-SPEC-IDENTITY-BEHAVIOR-FAMILY-001", f"{item_label}: included and omitted fields overlap")
        own = declaration["own_identity"]
        if not isinstance(own, dict):
            fail("REPO-SPEC-IDENTITY-BEHAVIOR-FAMILY-001", f"{item_label}.own_identity must be an object")
        exact_fields(own, {"mode", "field"}, f"{item_label}.own_identity")
        if own["mode"] != "omit-own-identity" or not isinstance(own["field"], str) or not FIELD_NAME.fullmatch(own["field"]):
            fail("REPO-SPEC-IDENTITY-BEHAVIOR-FAMILY-001", f"{item_label}: invalid own identity rule")
        references = declaration["references"]
        if not isinstance(references, dict):
            fail("REPO-SPEC-IDENTITY-BEHAVIOR-FAMILY-001", f"{item_label}.references must be an object")
        exact_fields(references, {"mode", "identity_field", "value_field", "allowed_family_names"}, f"{item_label}.references")
        if references["mode"] not in {"none", "by-identity", "identity-plus-value"}:
            fail("REPO-SPEC-IDENTITY-BEHAVIOR-FAMILY-001", f"{item_label}: unsupported reference mode")
        allowed = references["allowed_family_names"]
        if not isinstance(allowed, list) or len(allowed) != len(set(allowed)) or any(
            not isinstance(item, str) or not IDENTITY.fullmatch(item) for item in allowed
        ):
            fail("REPO-SPEC-IDENTITY-BEHAVIOR-FAMILY-001", f"{item_label}: invalid allowed family names")
        identity_field = references["identity_field"]
        value_field = references["value_field"]
        if references["mode"] == "none":
            if identity_field is not None or value_field is not None or allowed:
                fail("REPO-SPEC-IDENTITY-BEHAVIOR-FAMILY-001", f"{item_label}: invalid none reference declaration")
        elif references["mode"] == "by-identity":
            if not isinstance(identity_field, str) or not FIELD_NAME.fullmatch(identity_field) or value_field is not None or not allowed:
                fail("REPO-SPEC-IDENTITY-BEHAVIOR-FAMILY-001", f"{item_label}: invalid by-identity declaration")
        else:
            if (
                not isinstance(identity_field, str) or not FIELD_NAME.fullmatch(identity_field)
                or not isinstance(value_field, str) or not FIELD_NAME.fullmatch(value_field)
                or identity_field == value_field or not allowed
            ):
                fail("REPO-SPEC-IDENTITY-BEHAVIOR-FAMILY-001", f"{item_label}: invalid identity-plus-value declaration")
        aggregate = declaration["aggregate"]
        if declaration["object_kind"] == "object":
            if aggregate is not None:
                fail("REPO-SPEC-IDENTITY-BEHAVIOR-FAMILY-001", f"{item_label}: object family aggregate must be null")
        else:
            if not isinstance(aggregate, dict):
                fail("REPO-SPEC-IDENTITY-BEHAVIOR-FAMILY-001", f"{item_label}: aggregate declaration required")
            exact_fields(
                aggregate,
                {
                    "membership_field", "member_family_names", "ordering",
                    "duplicate_policy", "empty_policy", "closure_boundary", "cycle_policy",
                },
                f"{item_label}.aggregate",
            )
            if aggregate["ordering"] not in {"ordered", "unordered"}:
                fail("REPO-SPEC-IDENTITY-BEHAVIOR-FAMILY-001", f"{item_label}: invalid aggregate ordering")
            expected_ordering = "ordered" if declaration["object_kind"] == "ordered-aggregate" else "unordered"
            if aggregate["ordering"] != expected_ordering:
                fail("REPO-SPEC-IDENTITY-BEHAVIOR-FAMILY-001", f"{item_label}: object kind and ordering conflict")
            membership_field = aggregate["membership_field"]
            member_families = aggregate["member_family_names"]
            if (
                not isinstance(membership_field, str) or not FIELD_NAME.fullmatch(membership_field)
                or not isinstance(member_families, list) or not member_families
                or len(member_families) != len(set(member_families))
                or any(not isinstance(item, str) or not IDENTITY.fullmatch(item) for item in member_families)
                or member_families != allowed
            ):
                fail("REPO-SPEC-IDENTITY-BEHAVIOR-FAMILY-001", f"{item_label}: invalid aggregate membership declaration")
            if aggregate["duplicate_policy"] != "reject" or aggregate["closure_boundary"] != "direct" or aggregate["cycle_policy"] != "reject":
                fail("REPO-SPEC-IDENTITY-BEHAVIOR-FAMILY-001", f"{item_label}: invalid aggregate policy")
            if aggregate["empty_policy"] not in {"allow", "reject"}:
                fail("REPO-SPEC-IDENTITY-BEHAVIOR-FAMILY-001", f"{item_label}: invalid empty policy")
        verification = declaration["verification"]
        if not isinstance(verification, dict):
            fail("REPO-SPEC-IDENTITY-BEHAVIOR-FAMILY-001", f"{item_label}.verification must be an object")
        exact_fields(verification, {"mode", "context_source"}, f"{item_label}.verification")
        expected_verification = {
            "none": ("none", "none"),
            "by-identity": ("verified-identity-set", "caller-supplied"),
            "identity-plus-value": ("embedded-value-recomputation", "embedded-value"),
        }[references["mode"]]
        if (verification["mode"], verification["context_source"]) != expected_verification:
            fail("REPO-SPEC-IDENTITY-BEHAVIOR-FAMILY-001", f"{item_label}: reference and verification modes conflict")
        if declaration["unavailable_capabilities"] != [
            "governing-revision-binding", "manifest-bootstrap", "sealing", "acceptance"
        ]:
            fail("REPO-SPEC-IDENTITY-BEHAVIOR-FAMILY-001", f"{item_label}: unavailable capabilities mismatch")
        registry[name] = declaration
    return registry


def _behavior_context(value: Any, label: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        fail("REPO-SPEC-IDENTITY-BEHAVIOR-CONTEXT-001", f"{label}: context must be an array")
    records: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for index, record in enumerate(value):
        item_label = f"{label}[{index}]"
        if not isinstance(record, dict):
            fail("REPO-SPEC-IDENTITY-BEHAVIOR-CONTEXT-001", f"{item_label}: record must be an object")
        exact_fields(record, VERIFICATION_RECORD_FIELDS, item_label)
        identity = _behavior_identity(record["identity"], f"{item_label}.identity")
        key = _behavior_identity_key(identity)
        if key in seen:
            fail("REPO-SPEC-IDENTITY-BEHAVIOR-CONTEXT-001", f"{item_label}: duplicate identity")
        seen.add(key)
        if record["family_name"] != identity["family"]:
            fail("REPO-SPEC-IDENTITY-BEHAVIOR-CONTEXT-001", f"{item_label}: family conflict")
        if record["verified"] is not True:
            fail("REPO-SPEC-IDENTITY-BEHAVIOR-CONTEXT-001", f"{item_label}: identity is not verified")
        records.append({"identity": identity, "family_name": record["family_name"], "verified": True})
    return records


def derive_behavior_identity(
    family_name: str,
    value: Any,
    registry: dict[str, dict[str, Any]],
    context: list[dict[str, Any]],
    *,
    supplied_identity: dict[str, str] | None = None,
    construction_stack: tuple[tuple[str, str], ...] = (),
) -> tuple[dict[str, str], dict[str, Any]]:
    if family_name not in registry:
        fail("REPO-SPEC-IDENTITY-BEHAVIOR-UNKNOWN-FAMILY", family_name)
    if not isinstance(value, dict):
        fail("REPO-SPEC-IDENTITY-BEHAVIOR-MALFORMED-REQUEST", f"{family_name}: value must be an object")
    family = registry[family_name]
    canonical_value: dict[str, Any] = {}
    own_field = family["own_identity"]["field"]
    raw_own_identity = value.get(own_field)
    provided_own_identity = (
        None
        if raw_own_identity is None
        else _behavior_identity(raw_own_identity, f"{family_name}.{own_field}")
    )
    for field in family["included_preimage_fields"]:
        if field == own_field:
            continue
        if field in value:
            canonical_value[field] = value[field]

    references = family["references"]
    reference_count = 0
    aggregate_member_count = 0
    aggregate_ordering = None
    if references["mode"] != "none":
        collection_field = family["aggregate"]["membership_field"] if family["aggregate"] else "references"
        raw_items = value.get(collection_field, [])
        if not isinstance(raw_items, list):
            fail("REPO-SPEC-IDENTITY-BEHAVIOR-MALFORMED-REFERENCE", f"{family_name}: {collection_field} must be an array")
        processed: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()
        for index, raw_item in enumerate(raw_items):
            if not isinstance(raw_item, dict):
                fail("REPO-SPEC-IDENTITY-BEHAVIOR-MALFORMED-REFERENCE", f"{family_name}[{index}]: reference must be an object")
            reference_fields = {references["identity_field"]}
            if references["value_field"] is not None:
                reference_fields.add(references["value_field"])
            if set(raw_item) != reference_fields:
                fail("REPO-SPEC-IDENTITY-BEHAVIOR-MALFORMED-REFERENCE", f"{family_name}.{collection_field}[{index}]: reference fields mismatch")
            identity = _behavior_identity(
                raw_item.get(references["identity_field"]),
                f"{family_name}.{collection_field}[{index}].{references['identity_field']}",
            )
            key = _behavior_identity_key(identity)
            if supplied_identity is not None and identity == supplied_identity and family["aggregate"] is not None:
                fail("REPO-SPEC-IDENTITY-BEHAVIOR-SELF-MEMBERSHIP", family_name)
            if key in construction_stack:
                fail("REPO-SPEC-IDENTITY-BEHAVIOR-AGGREGATE-CYCLE", family_name)
            if key in seen:
                code = (
                    "REPO-SPEC-IDENTITY-BEHAVIOR-DUPLICATE-AGGREGATE-MEMBER"
                    if family["aggregate"] is not None
                    else "REPO-SPEC-IDENTITY-BEHAVIOR-MALFORMED-REFERENCE"
                )
                fail(code, family_name)
            seen.add(key)
            if identity["family"] not in references["allowed_family_names"]:
                fail("REPO-SPEC-IDENTITY-BEHAVIOR-REFERENCE-FAMILY-MISMATCH", family_name)
            if references["mode"] == "by-identity":
                matches = [record for record in context if record["identity"] == identity]
                if len(matches) != 1:
                    fail("REPO-SPEC-IDENTITY-BEHAVIOR-MISSING-REFERENCE-CONTEXT", family_name)
                processed.append({"identity": identity})
            else:
                embedded = raw_item.get(references["value_field"])
                if not isinstance(embedded, dict):
                    fail("REPO-SPEC-IDENTITY-BEHAVIOR-MALFORMED-REFERENCE", family_name)
                computed, _ = derive_behavior_identity(
                    identity["family"],
                    embedded,
                    registry,
                    context,
                    supplied_identity=None,
                    construction_stack=construction_stack + (key,),
                )
                if computed != identity:
                    fail("REPO-SPEC-IDENTITY-BEHAVIOR-EMBEDDED-REFERENCE-MISMATCH", family_name)
                canonical_embedded = dict(embedded)
                canonical_embedded.pop(registry[identity["family"]]["own_identity"]["field"], None)
                processed.append({"identity": identity, "value": canonical_embedded})
        reference_count = len(processed)
        if family["aggregate"] is not None:
            aggregate_member_count = len(processed)
            aggregate_ordering = family["aggregate"]["ordering"]
            if not processed and family["aggregate"]["empty_policy"] == "reject":
                fail("REPO-SPEC-IDENTITY-BEHAVIOR-EMPTY-AGGREGATE", family_name)
            if aggregate_ordering == "unordered":
                processed.sort(key=lambda item: _behavior_identity_key(item["identity"]))
            canonical_value[collection_field] = processed
        else:
            canonical_value[collection_field] = processed

    canonical_bytes = _behavior_canonical_bytes(canonical_value)
    preimage = family["domain_prefix"].encode("utf-8") + b"\x00" + canonical_bytes
    computed = {
        "family": family_name,
        "encoded_digest": hashlib.sha256(preimage).hexdigest(),
    }
    if provided_own_identity is not None and provided_own_identity != computed:
        fail("REPO-SPEC-IDENTITY-BEHAVIOR-CONTRADICTORY-OWN-IDENTITY", family_name)
    evidence = {
        "family_name": family_name,
        "canonicalization_version": family["canonicalization_version"],
        "digest_algorithm": family["digest_algorithm"],
        "domain_prefix": family["domain_prefix"],
        "own_identity_field_omitted": own_field,
        "reference_count": reference_count,
        "aggregate_member_count": aggregate_member_count,
        "aggregate_ordering": aggregate_ordering,
        "canonical_value_sha256": hashlib.sha256(canonical_bytes).hexdigest(),
        "computed_identity": computed,
    }
    return computed, evidence


def evaluate_behavior_request(
    request: Any,
    registry: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(request, dict):
        fail("REPO-SPEC-IDENTITY-BEHAVIOR-MALFORMED-REQUEST", "request must be an object")
    exact_fields(request, BEHAVIOR_REQUEST_FIELDS, "behavior request")
    mode = request["mode"]
    if mode not in {"derive", "verify"}:
        fail("REPO-SPEC-IDENTITY-BEHAVIOR-MALFORMED-REQUEST", "unsupported mode")
    family_name = request["family_name"]
    if not isinstance(family_name, str) or not IDENTITY.fullmatch(family_name):
        fail("REPO-SPEC-IDENTITY-BEHAVIOR-MALFORMED-REQUEST", "invalid family name")
    supplied = request["supplied_identity"]
    if mode == "derive":
        if supplied is not None:
            fail("REPO-SPEC-IDENTITY-BEHAVIOR-MALFORMED-REQUEST", "derive supplied identity must be null")
        supplied_identity = None
    else:
        supplied_identity = _behavior_identity(supplied, "behavior request.supplied_identity")
        if supplied_identity["family"] != family_name:
            return {
                "status": "rejected", "family_name": family_name,
                "computed_identity": None, "supplied_identity": supplied_identity,
                "evidence": None, "diagnostic": "family-mismatch",
            }
    context = _behavior_context(request["verification_context"], "behavior request.verification_context")
    try:
        computed, evidence = derive_behavior_identity(
            family_name,
            request["value"],
            registry,
            context,
            supplied_identity=supplied_identity,
            construction_stack=(
                (_behavior_identity_key(supplied_identity),)
                if supplied_identity is not None
                else ()
            ),
        )
    except ValidationFailure as exc:
        code = str(exc).split(":", 1)[0]
        diagnostic_map = {
            "REPO-SPEC-IDENTITY-BEHAVIOR-UNKNOWN-FAMILY": "unknown-family",
            "REPO-SPEC-IDENTITY-BEHAVIOR-MALFORMED-REQUEST": "malformed-request",
            "REPO-SPEC-IDENTITY-BEHAVIOR-MALFORMED-REFERENCE": "malformed-reference",
            "REPO-SPEC-IDENTITY-BEHAVIOR-MISSING-REFERENCE-CONTEXT": "missing-reference-context",
            "REPO-SPEC-IDENTITY-BEHAVIOR-REFERENCE-FAMILY-MISMATCH": "reference-family-mismatch",
            "REPO-SPEC-IDENTITY-BEHAVIOR-EMBEDDED-REFERENCE-MISMATCH": "embedded-reference-identity-mismatch",
            "REPO-SPEC-IDENTITY-BEHAVIOR-DUPLICATE-AGGREGATE-MEMBER": "duplicate-aggregate-member",
            "REPO-SPEC-IDENTITY-BEHAVIOR-EMPTY-AGGREGATE": "empty-aggregate-forbidden",
            "REPO-SPEC-IDENTITY-BEHAVIOR-SELF-MEMBERSHIP": "self-membership",
            "REPO-SPEC-IDENTITY-BEHAVIOR-AGGREGATE-CYCLE": "aggregate-cycle",
            "REPO-SPEC-IDENTITY-BEHAVIOR-CONTRADICTORY-OWN-IDENTITY": "contradictory-own-identity",
        }
        if code not in diagnostic_map:
            raise
        return {
            "status": "rejected", "family_name": family_name,
            "computed_identity": None, "supplied_identity": supplied_identity,
            "evidence": None, "diagnostic": diagnostic_map[code],
        }
    if mode == "verify" and computed != supplied_identity:
        return {
            "status": "rejected", "family_name": family_name,
            "computed_identity": None, "supplied_identity": supplied_identity,
            "evidence": evidence, "diagnostic": "supplied-identity-mismatch",
        }
    return {
        "status": "verified" if mode == "verify" else "derived",
        "family_name": family_name,
        "computed_identity": computed,
        "supplied_identity": supplied_identity,
        "evidence": evidence,
        "diagnostic": None,
    }


def validate_behavior_fixture_set(value: dict[str, Any], label: str) -> None:
    exact_fields(value, BEHAVIOR_FIXTURE_FIELDS, label)
    validate_common(value, label)
    if value != EXPECTED_BEHAVIOR_FIXTURE_SET:
        fail("REPO-SPEC-IDENTITY-BEHAVIOR-FIXTURE-001", f"{label}: fixture set does not match governed inventory")
    registry = reusable_build_behavior_registry(
        value["family_declarations"],
        location=f"{label}.family_declarations",
    )
    cases = value["cases"]
    if not isinstance(cases, list) or not cases:
        fail("REPO-SPEC-IDENTITY-BEHAVIOR-FIXTURE-001", f"{label}: non-empty cases required")
    names: set[str] = set()
    for index, case in enumerate(cases):
        case_label = f"{label}.cases[{index}]"
        if not isinstance(case, dict):
            fail("REPO-SPEC-IDENTITY-BEHAVIOR-FIXTURE-001", f"{case_label}: case must be an object")
        exact_fields(case, BEHAVIOR_CASE_FIELDS, case_label)
        name = _functional(case["name"], f"{case_label}.name")
        if name in names:
            fail("REPO-SPEC-IDENTITY-BEHAVIOR-FIXTURE-001", f"{case_label}: duplicate case name")
        names.add(name)
        result = reusable_evaluate_behavior(case["request"], registry)
        if result["status"] != case["expected_status"]:
            fail("REPO-SPEC-IDENTITY-BEHAVIOR-FIXTURE-001", f"{case_label}: unexpected status {result['status']}")
        if result["computed_identity"] != case["expected_identity"]:
            fail("REPO-SPEC-IDENTITY-BEHAVIOR-FIXTURE-001", f"{case_label}: unexpected identity")
        if result["diagnostic"] != case["expected_diagnostic"]:
            fail("REPO-SPEC-IDENTITY-BEHAVIOR-FIXTURE-001", f"{case_label}: unexpected diagnostic {result['diagnostic']}")

def validate_manifest(root: Path) -> None:
    manifest = strict_json(root / MANIFEST_PATH)
    paths = manifest.get("artifact_paths")
    if not isinstance(paths, list) or not paths or len(paths) != len(set(paths)):
        fail("REPO-SPEC-IDENTITY-MANIFEST-002", "manifest paths are malformed or duplicate")
    declared = set(paths)
    for relative in (*ARTIFACTS, SCHEMA_PATH, MODEL_SCHEMA_PATH, FAMILY_SCHEMA_PATH, VERIFICATION_SCHEMA_PATH, FIXTURE_PATH, BEHAVIOR_FIXTURE_PATH):
        if paths.count(relative) != 1:
            fail("REPO-SPEC-IDENTITY-MANIFEST-001", f"{relative}: must participate exactly once")
    for index, relative in enumerate(paths):
        target = contained_path(root, relative, f"manifest.artifact_paths[{index}]")
        if (
            relative.startswith("authoritative/identity/")
            or relative.startswith("authoritative/schemas/identity/")
            or relative in {FIXTURE_PATH, BEHAVIOR_FIXTURE_PATH}
        ) and not target.is_file():
            fail("REPO-SPEC-IDENTITY-MANIFEST-003", f"{relative}: declared identity artifact is missing")
    participating = set()
    for directory in (
        root / "authoritative/identity",
        root / "authoritative/schemas/identity",
        root / "validation/fixtures/identity/identity-family",
        root / "validation/fixtures/identity/identity-behavior",
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
            validate_exact_policy(value, EXPECTED_VERIFICATION, VERIFICATION_FIELDS, relative, "REPO-SPEC-IDENTITY-VERIFICATION-001")
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
    verification_schema = strict_json(root / VERIFICATION_SCHEMA_PATH)
    validate_exact_schema(verification_schema, EXPECTED_VERIFICATION_SCHEMA, VERIFICATION_SCHEMA_PATH)
    observed[VERIFICATION_SCHEMA_PATH] = verification_schema["construction_identity"]
    fixture_set = strict_json(root / FIXTURE_PATH)
    validate_fixture_set(fixture_set, FIXTURE_PATH)
    observed[FIXTURE_PATH] = fixture_set["construction_identity"]
    behavior_fixture_set = strict_json(root / BEHAVIOR_FIXTURE_PATH)
    validate_behavior_fixture_set(behavior_fixture_set, BEHAVIOR_FIXTURE_PATH)
    observed[BEHAVIOR_FIXTURE_PATH] = behavior_fixture_set["construction_identity"]
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
