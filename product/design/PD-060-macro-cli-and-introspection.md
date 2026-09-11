---
doc_id: PD-060
title: Macro CLI and Introspection
dependencies:
  - PD-050
---

# Macro CLI and Introspection

## Purpose

This document defines the maintained command-line surface for product macros and
their public introspection.

## Macro execution command

The public macro command is:

```text
gve macro --in REQUEST.json --out RESULT.json [--repo PATH]
```

`REQUEST.json` identifies one registered product macro and supplies its closed
parameter object plus repository expectations defined by this Design and later
Planning.

`RESULT.json` is the authoritative machine-readable macro result.

The macro command does not accept caller-authored task workflows. The existing
FS-001 execute interface remains the separate surface for ordinary caller-owned
workflow payloads.

## Request envelope

The macro request has two conceptual sections:

```json
{
  "header": {
    "repository": {}
  },
  "macro": {
    "name": "modify",
    "parameters": {}
  }
}
```

The exact concrete fields are fixed by Planning.

The request envelope is closed. Unknown fields fail rather than being silently
ignored.

Repository expectations are guards, not authority grants.

## Repository authority establishment

For local repository macro execution, GVE resolves one canonical active
repository root from `--repo` when supplied or from the current working
repository when omitted.

GVE derives candidate Git repository and publication context from that active
repository. Repository expectations in the request are checked against observed
state. Observation of repository configuration is context discovery, not by itself
an authority grant.

Before macro execution, the macro CLI establishes active `Authority` through a
product-defined CLI policy. Derived repository, remote, branch, and GitHub identity
may be intersected with that active authority but may not create or widen authority
merely because the local repository exposes those values.

GitHub repository identity used by `issue` and `pr` is derived from the
repository's configured product-supported remote identity and must match the active
GitHub repository authority. If GitHub repository authority is absent, GitHub macro
execution fails closed.

Caller-supplied strings do not widen authority.

## Introspection

The public introspection commands are:

```text
gve macro-list
gve macro-schema NAME
```

`macro-list` returns the stable registered public macro identities.

`macro-schema NAME` returns the selected macro's public parameter contract in a
machine-readable JSON form suitable for caller preparation and tooling.

Introspection exposes contract data only. It does not expose or serialize macro
implementation code, internal workflow templates, Python source, condition
logic, or transport credentials.

## Output and presentation

Machine-readable result output is authoritative.

Human terminal presentation may show macro identity, stage transitions, governed
task identity, task status, and task-provided streams or concise evidence.

Presentation must remain an observer of execution. It must not become a second
semantic model that has to know the behavior of every plugin task.

Task-specific semantic rendering beyond generic task evidence is optional and
must not be required for execution correctness.

## Result structure

A macro result identifies at least:

```text
macro identity
overall status
ordered stages
ordered governed task results within each stage
failure evidence when present
```

Stage grouping is reconstructed from product-owned macro construction metadata.
Underlying task evidence preserves the FS-001 result meaning.

## Installation

A repository-owned launcher may expose the `gve` command for local use.

Installation or launcher mechanics must not duplicate the macro runtime, alter
authority semantics, or create a separate implementation path.

## Compatibility

FS-002 establishes the first macro CLI/request version.

Compatibility guarantees for future macro request versions require explicit
Product Design. Implementations should fail closed on unsupported versions
rather than guessing intent.
