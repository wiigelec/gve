# Identity construction boundary

This directory is the deterministic human-readable projection of the
repository-neutral identity construction artifacts. The JSON authority remains
controlling.

## Semantic identity

A semantic identity is represented as a closed object containing a functional
family name and a 64-character lowercase hexadecimal SHA-256 digest. An
implementation-local identifier does not determine semantic identity equality.

The digest preimage is:

```text
printable ASCII family domain prefix || NUL || canonical JSON value bytes
```

## Own identity

Each participating family explicitly identifies its own-identity field. The
current repository-neutral construction mode omits that field before
canonicalization. An absent or null field is allowed during derivation, and a
present field must exactly match the computed identity; contradictory values
are rejected.

## References

Two repository-neutral reference modes are constructed:

- `by-identity` includes only the referenced semantic identity and requires one
  matching caller-supplied verified identity record.
- `identity-plus-value` includes the identity and embedded value, recomputes the
  embedded value under its declared family, and rejects any mismatch.

Missing context, ambiguous records, family conflicts, unverified references,
and embedded-value mismatches fail closed.

## Aggregates

Ordered aggregates preserve declared member order. Unordered aggregates sort
direct members by semantic identity before canonicalization. Both use direct
closure; transitive closure is unavailable.

Duplicate members, forbidden empty aggregates, self-membership, family
mismatches, and construction cycles are rejected.

## Verification

A derive request returns the computed identity. A verify request additionally
requires an exact supplied-versus-computed identity match. Construction
evidence records only deterministic computation facts: family,
canonicalization and digest bindings, domain prefix, omitted own-identity
field, direct reference/member counts, aggregate ordering, canonical-value
SHA-256, and computed identity.

Governing-revision binding, manifest bootstrap, sealing, acceptance, and
product-specific evidence semantics remain separately governed.
