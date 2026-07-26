# Stage 2 conformance vectors

This directory contains the normative byte fixtures for Issue 84. The JSON
manifest is the machine-readable authority; this file explains how to consume it
without introducing alternate semantics.

## Running the suite

From the repository root:

```sh
python -m specs.tooling.stage2_vector_runner
./scripts/validate
```

The runner is offline and deterministic. Success is silent with exit status
zero. It compares the reference processor's exit status, stdout bytes, and
stderr bytes against every manifest entry. Result-producing vectors compare
stdout byte-for-byte with the referenced authoritative-result fixture.

## Normative byte rules

JSON fixtures use UTF-8, lexicographically sorted object members, preserved
array order, no insignificant whitespace, finite RFC 8259 numbers, one final LF,
and no trailing bytes. Binary fixtures are consumed as raw bytes. The malformed
UTF-8 and duplicate-member inputs must never be regenerated through a normal
JSON serializer.

Derived identities use SHA-256 over zero-byte-separated preimage components.
The family components are the ASCII strings `request`, `result`, and
`diagnostic`, exactly as recorded in `manifest.json`.

## Coverage matrix

| Requirement | Vector or probe |
|---|---|
| Canonical successful no-op | `canonical-successful-no-op` |
| Malformed UTF-8 | `malformed-utf8` |
| Malformed JSON | `malformed-json` |
| Duplicate object members | `duplicate-object-members` |
| Missing lifecycle | `missing-lifecycle` |
| Unsupported lifecycle | `unsupported-lifecycle` |
| Malformed workflow envelope | `malformed-workflow-envelope` |
| Malformed operation envelope | `malformed-operation-envelope` |
| Forbidden execution field | `forbidden-operation-execution-field` |
| Forbidden plugin field | `unknown-plugin-routing-member` |
| Identity mismatch | `duplicate-operation-identity` |
| Unknown payload member | `unknown-top-level-member` |
| Unknown workflow member | `malformed-workflow-envelope` |
| Unknown operation member | `forbidden-operation-execution-field` |
| Unknown plugin-routing member | `unknown-plugin-routing-member` |
| Opaque plugin content remains open | `opaque-content-unknown-members` |
| Unknown authoritative-result members | `boundary_probes` result entries |
| Unknown diagnostic member | `unknown-diagnostic-member` probe |
| Unknown fatal-failure member | `unknown-fatal-failure-member` probe |

The result-boundary probes mutate a valid stored fixture in memory by inserting
one unknown member at the named JSON Pointer. The accepted Issue 83 schema must
reject every mutation. They are harness-integrity probes rather than process
inputs: implementations emit results and fatal failures; they do not consume
them as Stage 2 request payloads.

## Interpretation rules

Exact fixture bytes and normative schemas override prose. A fatal vector has no
authoritative result, emits no stdout, emits the exact fatal-failure JSON on
stderr, and exits with status four. A result-producing rejection emits the exact
authoritative result on stdout, emits empty stderr, and exits with status two.
A successful no-op emits the exact authoritative result on stdout, emits empty
stderr, and exits with status zero.

Plugin-owned `content` is opaque. Unknown or execution-shaped members inside it
are accepted; equivalent members at governed outer boundaries are rejected.
