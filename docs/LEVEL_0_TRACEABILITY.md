# Level 0 structured specification and traceability

`LEVEL_0.md` remains the authoritative prose specification. The machine-readable
representation is `specs/levels/level-0.json`, validated by the reusable contract
in `specs/schemas/level.schema.json`.

Authority is intentionally ordered as follows:

1. `LEVEL_0.md`
2. the structured Level 0 specification
3. implementation
4. tests

Tests provide traceability evidence; they do not replace or override the
specification.

## Repository roles

- `specs/schemas/level.schema.json` defines the closed reusable shape for every
  governed-execution level.
- `specs/levels/level-0.json` assigns stable requirement identifiers and records
  contracts, failure behavior, implementation locations, and test references.
- `src/gve/level0.py` implements the maintained Level 0 description boundary.
- `src/scf_governed_executor/` supplies bootstrap execution mechanics where they
  remain compatible with Level 0.
- `src/gve/tests/test_level_spec.py` checks schema closure, requirement identity,
  and complete traceability.
- `src/gve/tests/test_level0.py` checks the maintained payload contract.

## Stable requirement identifiers

Requirement IDs follow `L<level>-<category>-<sequence>`, for example
`L0-CLOS-001`. IDs are unique within a level and are the durable link between
prose requirements, structured specification entries, implementation, and tests.

## Validation

The governed repository validation entrypoint discovers both executor tests and
maintained product tests:

```sh
python3 -m unittest discover -s tests/governed_executor
git diff --check
```

A Level 0 change is incomplete when a normative requirement lacks either an
implementation reference or test evidence.
