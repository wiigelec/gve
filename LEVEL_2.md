# GVE Level 2

GVE executes instruction payloads through application plugins.

```text
Instruction Payload
        ↓
GVE Core
        ↓
Application Plugin
        ↓
Authoritative Result
```

## GVE Core

The core provides:

* plugin discovery and routing;
* execution lifecycle control;
* shared validation and failure handling;
* cross-plugin sequencing;
* result emission.

## Local Filesystem Modification Plugin

Defines governed instructions for:

* creating files;
* replacing file contents;
* deleting files;
* moving files;
* creating directories;
* applying bounded local changes.

It governs path safety, preconditions, permitted locations, and filesystem-specific results.

## Command Execution Plugin

Defines governed instructions for:

* running tests;
* running linters and formatters;
* building software;
* executing validation scripts;
* running approved project commands.

It governs executable selection, arguments, working directory, environment, timeout, output capture, exit-code handling, redaction, and process termination.

## GitHub Plugin

Defines governed instructions for:

* inspecting repositories;
* creating and updating branches;
* creating commits;
* pushing changes;
* creating and updating issues;
* creating and updating pull requests;
* posting comments and review responses.

It governs repository identity, remote state, credentials, allowed GitHub actions, and GitHub-specific results.

## Plugin Composition

A payload may invoke one plugin or an explicit sequence of plugins.

```text
Filesystem Plugin
    applies local changes
        ↓
Command Execution Plugin
    validates the changes
        ↓
GitHub Plugin
    commits and publishes the result
```

## Invariants

* Every instruction belongs to one plugin.
* Cross-plugin execution must be explicit.
* Plugins may consume only declared outputs from earlier plugins.
* A failed plugin step must be represented before execution continues.
* Later plugin steps may depend on earlier results.
* The final result must identify every plugin invoked and the outcome of each.
* The GVE core remains independent of plugin-specific behavior.
