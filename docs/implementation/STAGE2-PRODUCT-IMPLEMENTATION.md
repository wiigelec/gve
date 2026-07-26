# Stage 2 Product Implementation

## Purpose

This document defines the Stage 2 product development milestone for the maintained GVE implementation.

Its purpose is to identify the capabilities that exist when Stage 2 is complete and to establish the intended implementation boundary between Stage 2 and later development stages.

This document is **not** a normative specification.

This document does not define:

- Protocol behavior.
- Payload semantics.
- Result semantics.
- Algorithms.
- Validation rules.
- Identity derivation.
- Serialization.
- Conformance requirements.

Those behaviors are defined exclusively by the applicable GVE normative specifications.

---

# Milestone Goal

The goal of Stage 2 is to establish the complete basic maintained core.

When Stage 2 is complete, the maintained product can receive a properly formed normative payload, process every application-independent capability assigned to the maintained core by the normative specifications, intentionally perform no workflow execution when requested by the applicable lifecycle mode, and emit a properly formed authoritative result.

Stage 2 intentionally ends before application-plugin architecture or workflow execution is introduced.

---

# Included Capabilities

Completion of Stage 2 includes implementation of the normative capabilities assigned to the maintained core for:

- Payload ingestion.
- UTF-8 input handling.
- Payload parsing.
- Payload validation.
- Deterministic identity derivation.
- Common payload processing.
- Lifecycle processing.
- Authoritative result generation.
- Diagnostic generation.
- Deterministic serialization.
- Process termination.

The exact behavior of these capabilities is defined by the applicable normative specifications.

---

# Implementation Scope

Stage 2 includes the maintained-core capabilities required to process the normative Stage 2 payload lifecycle defined by the applicable specifications.

The maintained product implements every processing step assigned to the maintained core by those specifications.

The maintained product does not implement behavior assigned to application plugins or later implementation stages.

---

# Explicitly Deferred Capabilities

Completion of Stage 2 does not include implementation of:

- Plugin discovery.
- Plugin loading.
- Plugin registration.
- Plugin resolution.
- Plugin assignment.
- Plugin contracts.
- Plugin-owned instruction interpretation.
- Workflow-plan construction for execution.
- Workflow execution.
- Authorization processing.
- Filesystem mutation.
- Command execution.
- Git operations.
- Network access.
- Remote service interaction.
- Publication.
- Replay.
- Recovery.
- External observation.
- External verification.

These capabilities belong to later development stages.

---

# Processing Boundary

Stage 2 processes every application-independent portion of the normative payload assigned to the maintained core.

The maintained product stops processing at the implementation boundary defined by the applicable specifications.

When the normative payload requests the no-op lifecycle mode defined by those specifications, the maintained product completes all required maintained-core processing while intentionally performing no workflow execution.

The implementation boundary is established by the normative specifications rather than this document.

---

# Completion Outcomes

When Stage 2 is complete, the maintained product:

- Accepts valid Stage 2 normative payloads.
- Rejects invalid payloads.
- Correctly processes the common payload envelope.
- Correctly processes the normative no-op lifecycle mode.
- Produces deterministic authoritative results.
- Produces deterministic diagnostics.
- Produces deterministic identities.
- Produces deterministic serialized output.
- Produces well-defined process exit behavior.

Successful Stage 2 processing does not imply:

- Workflow execution.
- Plugin execution.
- Plugin interpretation.
- External effects.
- External state changes.

---

# Internal Architecture

The internal architecture of the maintained product remains an implementation decision.

One possible decomposition may include responsibilities such as:

- CLI.
- Payload reader.
- Parser.
- Validator.
- Identity.
- Core processor.
- Result builder.
- Diagnostics.
- Serialization.
- Exit handling.

This document does not require any particular internal architecture.

---

# Testing Expectations

Completion of Stage 2 includes testing sufficient to demonstrate:

- Successful processing of valid Stage 2 payloads.
- Correct rejection of invalid payloads.
- Deterministic identities.
- Deterministic authoritative results.
- Deterministic diagnostics.
- Deterministic serialization.
- Stable process termination behavior.

The required conformance fixtures and expected behavior are defined by the applicable normative specifications.

---

# Required Specification Readiness

Stage 2 depends upon normative specifications sufficient to define the maintained-core behavior required for this milestone.

Those specifications must define, at minimum:

- Payload structure.
- Lifecycle controls.
- Validation behavior.
- Identity derivation.
- Authoritative result structure.
- Diagnostic model.
- Serialization rules.
- Conformance fixtures.

Implementation of Stage 2 must not require invention of normative behavior not already defined by those specifications.

---

# Milestone Acceptance

Stage 2 is complete when:

- The maintained product implements every maintained-core capability assigned to Stage 2 by the applicable normative specifications.
- The maintained product passes the Stage 2 conformance tests defined by those specifications.
- The maintained product requires no implementation-defined behavior within the intended Stage 2 scope.

---

# Next Stage

Completion of Stage 2 establishes the maintained basic core.

Stage 3 builds upon that foundation by introducing the application-plugin architecture and the workflow execution capabilities defined by the applicable normative specifications.
