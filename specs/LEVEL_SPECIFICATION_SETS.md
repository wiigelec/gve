# GVE multi-document specification sets

A numeric GVE level may contain one root document and subordinate documents.

## Identity and layout

The root document keeps the canonical identity and path:

```text
specs/levels/level-N/GVE-LEVEL-N.json
```

A subordinate document uses an uppercase stable suffix:

```text
specs/levels/level-N/GVE-LEVEL-N-<DOCUMENT>.json
```

The Markdown projection uses the same basename.

Legacy Level 0 and Level 1 documents omit `document` metadata and are interpreted
as single-document roots. A multi-document level declares:

```json
"document": {
  "role": "root",
  "root": "GVE-LEVEL-N",
  "imports": []
}
```

or:

```json
"document": {
  "role": "subordinate",
  "root": "GVE-LEVEL-N",
  "imports": ["GVE-LEVEL-N", "GVE-LEVEL-N-OTHER"]
}
```

Exactly one document per numeric level has role `root`. Its identity is
`GVE-LEVEL-N`, it names itself as `root`, and it does not import subordinate
documents. Every subordinate names that root and declares the root as its
`specification.parent`.

## Current Level 3 decomposition

The normative Level 3 specification set is decomposed into exactly these
documents:

```text
GVE-LEVEL-3
GVE-LEVEL-3-RUNTIME-OWNERSHIP
GVE-LEVEL-3-PLUGIN-ACTION-CONTRACTS
GVE-LEVEL-3-WORKFLOW-PLANNING-LIFECYCLE
GVE-LEVEL-3-EVIDENCE-RESULT-REALIZATION
```

`GVE-LEVEL-3` is the sole root and has no imports. The four subordinate
documents are separately governed work and must each preserve the
non-overlapping semantic responsibility assigned by the root.

## Resolution and conflicts

Imports are explicit, same-level, acyclic visibility edges. A document can
resolve identifiers declared locally or in its transitive import closure.

Identifiers are unique across the complete governed specification set.
A duplicate identifier in any definition, requirement, or relationship is an
explicit conflict and validation fails. This makes cross-document resolution
deterministic without precedence or shadowing rules.

The repository validator also rejects unresolved roots, unresolved imports,
import cycles, invalid subordinate parentage, unresolved visible references,
and deterministic Markdown projection drift.
