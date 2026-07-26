# Stage 2 Product Implementation

## Purpose

This document defines the implementation plan for Stage 2 of the maintained GVE product.

Stage 2 establishes the complete baseline payload-processing pipeline while intentionally performing no external effects. The objective is to prove that the maintained application can receive an instruction payload, process it deterministically, and emit an authoritative result before any plugin execution or external mutation is introduced.

This document is an implementation plan. It does not modify or replace the normative specification set.

---

# Objectives

Stage 2 shall establish the complete lifecycle:

```text
request
    ↓
parse
    ↓
validate
    ↓
evaluate
    ↓
result
```

Upon completion of Stage 2, the maintained product shall be capable of:

- Reading an instruction payload.
- Parsing the payload.
- Performing structural validation.
- Performing schema validation.
- Deriving stable identities.
- Evaluating a baseline core-owned request.
- Producing an authoritative result.
- Producing deterministic diagnostics.
- Returning well-defined exit statuses.

No external effects shall occur.

No plugins shall execute.

---

# Stage 1 Foundation

Stage 2 builds directly upon the completed Stage 1 product.

The following Stage 1 behavior shall remain unchanged:

- Product installation.
- Runtime initialization.
- Stable CLI.
- Version reporting.
- Deterministic diagnostics.
- Defined process exit codes.

Stage 2 shall not weaken or redesign any accepted Stage 1 behavior.

---

# Scope

Stage 2 includes implementation of:

- Payload ingestion.
- UTF-8 input handling.
- JSON parsing.
- Structural validation.
- Schema validation.
- Stable identity derivation.
- Baseline evaluation.
- Result generation.
- Diagnostic generation.
- Deterministic serialization.
- Process exit handling.

The stage is intentionally limited to core processing.

---

# Out of Scope

Stage 2 shall not implement:

- Plugin discovery.
- Plugin loading.
- Plugin registration.
- Plugin execution.
- Plugin contracts.
- Filesystem mutation.
- Command execution.
- Git operations.
- Network access.
- Remote services.
- Workflow execution.
- Publication.
- Replay.
- Recovery.
- External observations.
- Verification of external state.

These capabilities belong to later implementation stages.

---

# Baseline Evaluation

Stage 2 introduces a single core-owned baseline evaluation.

Its purpose is to validate the maintained processing pipeline.

The baseline evaluation shall:

- Require no plugins.
- Produce no external effects.
- Produce deterministic results.
- Produce deterministic diagnostics.
- Exercise the complete request-to-result lifecycle.

The baseline evaluation shall not become a permanent plugin or establish precedent for future plugin behavior.

---

# Payload Processing

The processing sequence shall be:

```text
Read payload
    ↓
Decode UTF-8
    ↓
Parse JSON
    ↓
Structural validation
    ↓
Schema validation
    ↓
Identity derivation
    ↓
Baseline evaluation
    ↓
Authoritative result generation
    ↓
Serialize result
    ↓
Exit
```

Every transition shall be deterministic.

Failures terminate processing immediately using fail-closed behavior.

---

# Validation

Stage 2 shall distinguish at least the following categories:

1. Input acquisition
2. UTF-8 decoding
3. JSON parsing
4. Structural validation
5. Schema validation
6. Baseline semantic validation

Each validation stage shall produce diagnostics that identify the failing stage without requiring later stages to execute.

---

# Identity

Accepted payloads shall receive stable identities.

Identity derivation shall:

- Be deterministic.
- Produce identical identities for identical payloads.
- Avoid environmental information.
- Avoid timestamps.
- Avoid random values.
- Avoid filesystem metadata.
- Avoid process identifiers.

Identity derivation shall be reproducible.

---

# Evaluation

Evaluation shall operate only on validated payloads.

Evaluation shall not:

- Invoke plugins.
- Perform filesystem operations.
- Spawn processes.
- Access the network.
- Modify repositories.
- Produce observable side effects.

Evaluation shall determine only the authoritative processing outcome of the baseline request.

---

# Result Generation

Every accepted payload shall produce exactly one authoritative result.

The result shall distinguish:

- Request acceptance.
- Successful parsing.
- Successful validation.
- Successful evaluation.
- Successful result generation.

Successful ingestion shall not imply successful execution.

The authoritative result shall represent only what the maintained product actually processed.

---

# Diagnostics

Diagnostics shall be:

- Deterministic.
- Stable.
- Machine-readable.
- Human-readable.
- Ordered consistently.

Diagnostics shall never depend upon:

- Memory layout.
- Thread scheduling.
- Object addresses.
- Random values.
- Process identifiers.

---

# Exit Status

Every invocation shall terminate with a defined exit status.

Distinct exit codes shall exist for:

- Success.
- Invalid arguments.
- Input acquisition failure.
- Parse failure.
- Validation failure.
- Evaluation failure.
- Internal failure.

No undefined exit behavior shall exist.

---

# Internal Architecture

Stage 2 should establish reusable core components for later stages.

Recommended module responsibilities include:

- CLI
- Payload reader
- Parser
- Validator
- Identity
- Evaluator
- Result builder
- Diagnostics
- Exit status

Each module should own one responsibility.

Plugin interfaces shall not yet be implemented.

---

# Testing

Tests shall include:

## Successful Processing

- Valid payload accepted.
- Stable identity.
- Stable result.
- Stable diagnostics.

## Parsing Failures

- Invalid UTF-8.
- Invalid JSON.
- Empty input.
- Truncated input.

## Validation Failures

- Missing required members.
- Unknown members.
- Invalid member types.
- Invalid semantic values.

## Determinism

Repeated execution of identical input shall produce identical:

- Results.
- Diagnostics.
- Exit status.
- Identity.

---

# Acceptance Criteria

Stage 2 is complete when the maintained product:

- Accepts valid baseline payloads.
- Rejects invalid payloads.
- Produces deterministic authoritative results.
- Produces deterministic diagnostics.
- Produces deterministic identities.
- Distinguishes successful ingestion from successful evaluation.
- Performs no plugin execution.
- Performs no external mutations.
- Passes all Stage 2 tests.
- Preserves all accepted Stage 1 behavior.

---

# Deferred Work

The following work begins in Stage 3:

- Plugin discovery.
- Plugin resolution.
- Plugin contracts.
- Action validation.
- Authorization processing.
- Filesystem plugin.
- Read-only plugin execution.
- Observations produced by plugin execution.
- Plugin result integration.

Stage 2 intentionally ends before any maintained plugin architecture is exercised.
