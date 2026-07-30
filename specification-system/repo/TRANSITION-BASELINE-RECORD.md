# Transition Baseline Record

## Status

Transition record for Phase 0 of the repository framework construction plan.

This document is non-normative. It records the completion of the transition
baseline and does not authorize any Phase 1 or later work.

## Overview and plan discoverability

- **Product overview**: `docs/overview/PRODUCT-OVERVIEW.md` — present and
  discoverable. Defines the durable product direction.
- **Active construction plan**: `docs/plans/REPOSITORY-FRAMEWORK-CONSTRUCTION-PLAN.md`
  — present and discoverable. Defines the Phase 0-23 construction sequence.

## Plan supersession

The previous active construction plan,
`docs/implementation/REPOSITORY-SPECIFICATION-IMPLEMENTATION-PLAN.md`, is
explicitly superseded as the active construction plan.

The construction plan at `docs/plans/REPOSITORY-FRAMEWORK-CONSTRUCTION-PLAN.md`
is the active implementation planning authority for the repository framework.

Historical plans under `docs/implementation/staged/` remain available as
non-normative historical evidence. They do not independently authorize
implementation.

## Active dependency order

The revised durable dependency order from the construction plan (lines 339-365)
is the active development sequence:

1. Transition baseline and construction-plan replacement
2. Framework, template, instance, and product boundaries
3. Development artifact roles
4. Repository functional-area model
5. Fixed Level 0-3 specification model
6. Product artifact roles
7. Git repository and revision model
8. AI-session continuity model
9. Generic governed-development model
10. Normative-change and acceptance model
11. Source correspondence and implementation ownership
12. Hosting-platform profile mechanism
13. GitHub hosting profile
14. Framework validation architecture
15. Template initialization and derivation
16. Release and maintenance model
17. Identity-profile reassessment
18. Manifest and revision model
19. Schema and conformance hardening
20. Derived projection hardening
21. Complete repository validation
22. Portable instance validation
23. Framework hardening and acceptance
24. Framework cutover
25. Separate GVE derivation

This sequence is a dependency model, not standing authorization. Each phase
requires its own bounded governed issue.

## Audit gates for successor issues

Before proposing each successor issue, audit (from construction plan lines
1293-1305):

1. Whether every prerequisite boundary is accepted.
2. Whether accepted-main validation is clean.
3. Whether the target boundary is the earliest incomplete dependency.
4. Whether unresolved decisions prevent bounded implementation.
5. Whether one issue can close the boundary without combining independent work.
6. Whether artifact, schema, fixture, validator, manifest, and test updates can
   be atomic.
7. Whether product leakage has been reviewed.
8. Whether the issue can state exact exclusions.

## Baseline classification reference

The artifact classification produced by Phase 0 is recorded in:

specification-system/repo/TRANSITION-BASELINE-CLASSIFICATION.json

That document inventories every construction artifact under
`specification-system/repo/` and classifies each as retained,
retained-and-extended, redesigned-in-place, deferred,
separated-into-future-product, superseded, or removed-only-after-replacement.

## Phase 0 completion evidence

- [x] Product overview present and discoverable
- [x] Construction plan present and discoverable
- [x] Previous plan explicitly superseded
- [x] All construction artifacts inventoried and classified
- [x] Retained generic foundations identified
- [x] Placeholder artifacts requiring redesign identified
- [x] GVE product semantics noted for later separation
- [x] Revised dependency order established
- [x] Audit gates documented
- [x] No normative JSON changed
- [x] No executor behavior changed
- [x] No construction artifact removed
- [x] `./scripts/validate` passes
