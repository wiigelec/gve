---
functional_set: FS-001
artifact: plan
title: Core Governed Repository Execution Plan
design_revision: 6cc46250b8aac3934663be906acd41601791c04f
---

# FS-001 — Plan

## Design binding revision

This Planning revision consumes Product Design at exact Git revision
`6cc46250b8aac3934663be906acd41601791c04f`.

It supersedes the prior Planning baseline bound to
`8ede712d83a3376911dfb561b0173b7b7fd66cfe` specifically because PD-030 now makes native Linux and Cygwin
supported `execute.script` hosts.

## Technical intent

FS-001 implements GVE as a small Python application with a stable engine
boundary and plugin-owned task implementations.

The runtime path is:

```text
JSON document
  -> payload schema validation
  -> workflow model
  -> authority context
  -> task registry
  -> result-reference resolution
  -> plugin.task validation and dispatch
  -> ordered task execution
  -> task result records
  -> workflow result JSON
```

The engine owns orchestration semantics. Plugins own capability semantics.

## Package structure

Build shall use a project-native Python package under `product/src/` with clear
separation between:

- engine/workflow orchestration;
- payload and result models;
- authority representation;
- task registry;
- plugin implementations for `filesystem`, `git`, `execute`, and `github`;
- CLI entry point.

Exact module, function, and class names are Build decisions unless needed to
preserve these boundaries.

## FS-001 payload contract

FS-001 payload schema version is integer `1`.

A payload has exactly this top-level structure:

```json
{
  "schema_version": 1,
  "workflow_id": "example-workflow",
  "tasks": [
    {
      "id": "head",
      "task": "git.head",
      "parameters": {}
    }
  ]
}
```

Top-level fields are:

- `schema_version` — required integer and exactly `1`;
- `workflow_id` — required non-empty string;
- `tasks` — required non-empty array of task invocation objects.

Each task invocation contains exactly:

- `id` — required workflow-local invocation identity;
- `task` — required registered fully-qualified `plugin.task` identity;
- `parameters` — required JSON object interpreted by that task.

Unknown top-level or invocation fields fail payload validation.

Invocation `id` values must be unique within the workflow and match:

```text
[A-Za-z][A-Za-z0-9_-]{0,63}
```

The payload does not carry executable implementation code or an authority grant.

Schema validation of the top-level document and invocation envelope occurs
before any task executes. Task-specific parameter validation occurs after
permitted prior-result references for that invocation have been resolved and
before that task executes.

## Result-reference contract

A result reference is a JSON object containing exactly one key, `$ref`, whose
value is a string:

```json
{
  "$ref": "commit.result.commit"
}
```

The string syntax is:

```text
<prior-invocation-id>.result.<field>[.<field>...]
```

The first component names an earlier invocation in the same workflow.
References address only fields intentionally exposed beneath that task's
`result` object. `observations` and `effects` are evidence surfaces and are not
directly addressable by task-result references.

References may appear recursively anywhere inside task `parameters`.

A reference is resolved immediately before the consuming task's parameter
validation. Resolution substitutes the referenced JSON value into the
consumer's parameter value.

A reference fails closed when:

- the invocation identity is unknown;
- the referenced invocation is not earlier in workflow order;
- the referenced invocation did not complete successfully;
- the selected field path does not exist;
- traversal encounters a non-object before the path is exhausted;
- the substituted value does not satisfy the consuming parameter contract.

References never alter active authority. A referenced string that happens to be
a path, remote, branch, repository, issue, or other resource identifier is still
validated against the consuming task's authority after substitution.

## Workflow execution and failure

Execution is sequential and fail-fast.

For each invocation in payload order, the engine:

1. resolves permitted result references;
2. validates task parameters;
3. intersects requested resources with active authority;
4. executes the registered task;
5. records the task result before considering the next invocation.

If an invocation fails, the engine records its failure, stops dispatching later
tasks, preserves all earlier results, appends `not-executed` records for later
declared invocations, and returns a failed workflow result.

FS-001 exposes no caller-controlled continuation-after-failure mechanism.

## Authority establishment

FS-001 authority is established by the local CLI invocation, outside the
payload.

The command surface is:

```text
gve execute
  --repository PATH
  [--git-remote NAME ...]
  [--github-repository OWNER/NAME]
  [--execute-max-wall-seconds N]
  [--execute-max-concurrent N]
  [--execute-max-total-spawned N]
  [--execute-max-spawns-per-second N]
  PAYLOAD.json
```

`--repository` is required. GVE resolves it to one canonical repository root
before loading the workflow.

If no `--git-remote` option is supplied, Git remote authority is limited to
`origin` when that remote exists; otherwise no remote Git mutation authority is
granted. Repeated `--git-remote` options grant only the named existing remotes.

GitHub authority is absent unless `--github-repository OWNER/NAME` is supplied.
That option grants only the named GitHub repository. Authentication material may
be discovered by the implementation, but credentials do not enlarge the
repository grant.

Filesystem authority is the canonical active repository tree.

Git authority is the active repository plus local branch/ref operations and the
explicitly granted Git remotes. FS-001 does not grant force/history-rewrite
publication.

Execute authority is repository-local script selection and repository-local
working directory plus the finite process limits established below.

Task parameters and resolved result references may select narrower paths,
branches, remotes, or objects inside these grants. They may not expand them.

## Execute resource policy

FS-001 defines these product hard ceilings:

```text
wall-clock runtime:          600 seconds
concurrent governed process: 32
total spawned process count: 1024
spawn rate:                  64 processes/second
```

These values are upper bounds for FS-001 execution, not caller-replaceable
defaults.

Host policy may impose a stricter maximum. The CLI authority options may also
request stricter positive finite integer maxima for the current GVE invocation,
but they may not raise any limit above the applicable FS-001 hard ceiling or a
stricter host-policy ceiling.

For each resource, authority is established as:

```text
authority maximum =
    min(
        FS-001 hard ceiling,
        host-policy ceiling when present,
        CLI-requested maximum when present
    )
```

An omitted CLI value contributes no additional narrowing.

An `execute.script` task may optionally request stricter values through its
`limits` parameter. For each supplied task limit:

```text
effective limit = min(authority maximum, task-requested limit)
```

An omitted task limit uses the authority maximum.

A CLI or task value that is zero, negative, non-integer, above the ceiling it is
allowed to narrow, or otherwise unmonitorable is invalid. It fails rather than
silently enlarging or weakening runaway-process protection.

The OS-specific mechanism for host-policy discovery, process-tree discovery,
accounting, and termination is a Build decision. A host with no separately
discoverable policy still remains bounded by the FS-001 hard ceilings.

FS-001 supports `execute.script` on both native Linux and Cygwin. Build may use
different process-supervision backends for those hosts, but both backends must
provide the same task contract and the same finite process-control guarantees.

For both supported hosts:

- every governed descendant creation must be accountably observable for purposes
  of total-spawn and spawn-rate enforcement, including short-lived descendants;
- concurrent governed process count must remain enforceable for the life of the
  task;
- timeout or any process-limit violation must trigger governed-tree termination;
- inability to establish the required process-control backend must fail before
  the selected repository script is launched;
- script path, argument, executable, and working-directory behavior must retain
  the native semantics expected by that host;
- Cygwin support must preserve Cygwin path and executable semantics even when
  native Windows process-control facilities are used underneath.

A sampling mechanism that can miss short-lived descendants is insufficient for
the total-spawn or spawn-rate limits.

The behavioral contract is not a Build decision: timeout, concurrent-count
excess, total-spawn excess, spawn-rate excess, or inability to perform required
process-tree termination is task failure.

## Task registry

The registry maps each supported fully-qualified task identity to exactly one
implementation for FS-001.

The registry is static and product-owned. Payloads cannot install, load,
replace, alias, or define runtime plugins or tasks.

Unknown task identities fail closed before execution.

## Common task conventions

Unless a task contract below says otherwise:

- unknown parameter fields are invalid;
- repository-relative paths use `/` as the JSON path separator and may not be
  absolute;
- a SHA-256 digest is a lowercase 64-character hexadecimal string;
- a Git commit identity is a lowercase 40-character hexadecimal object ID for
  the FS-001 Git implementation;
- an optional `expected` parameter means observe current state and fail when it
  differs from the supplied expected value;
- mutation tasks return their direct resulting identifiers under `result` and
  describe performed GVE-owned mutation under `effects`;
- state tasks place current state under `observations` and duplicate only values
  intentionally exposed for later task references under `result`;
- only fields beneath `result` are addressable by `$ref`; `observations` and
  `effects` remain non-addressable evidence.

Exact diagnostic wording is a Build decision.

## Filesystem plugin task contracts

### `filesystem.list`

Parameters:

```json
{
  "path": ".",
  "recursive": false
}
```

- `path` is optional and defaults to repository root `.`.
- `recursive` is optional boolean and defaults to `false`.

Result exposes `result.entries`, an ordered array of repository-relative paths.
Each entry observation identifies at least path and kind (`file`, `directory`,
or `symlink`).

### `filesystem.file-read`

Parameters:

```json
{
  "path": "README.md",
  "encoding": "utf-8"
}
```

- `path` is required.
- `encoding` is optional; FS-001 supports only `utf-8`.

The task fails if the resolved target is not an existing regular file inside the
authorized repository boundary.

Result exposes `result.content` and `result.sha256`.

### `filesystem.file-stat`

Parameters contain required `path`.

Result exposes at least `result.path`, `result.kind`, `result.size`, and, for an
existing regular file, `result.sha256`. Missing paths are reported as
`result.kind = "missing"` rather than being treated as an execution error.

### `filesystem.file-hash`

Parameters contain required `path`.

The resolved target must be an existing regular file. FS-001 uses SHA-256.
Result exposes `result.sha256`.

### `filesystem.file-create`

Parameters:

```json
{
  "path": "path/to/file",
  "content": "complete UTF-8 content"
}
```

Both fields are required. Parent directories may be created as necessary inside
the authorized repository. The task fails if the target already exists.

Result exposes `result.path` and `result.sha256`.

### `filesystem.file-modify`

Parameters:

```json
{
  "path": "path/to/file",
  "expected_sha256": "lowercase-sha256",
  "content": "complete replacement UTF-8 content"
}
```

All fields are required. The target must be an existing regular file and its
current digest must equal `expected_sha256` immediately before replacement.

Result exposes `result.path`, `result.previous_sha256`, and
`result.sha256`.

### `filesystem.file-delete`

Parameters contain required `path` and required `expected_sha256`.

The target must be an existing regular file whose current digest matches the
expectation. FS-001 does not recursively delete directories.

Result exposes the deleted path and previous digest.

All filesystem paths are canonicalized and checked for containment after
symlink resolution before access or mutation.

## Git plugin task contracts

All Git tasks operate on the active repository. They do not accept a repository
path parameter.

### `git.repository`

Parameters may contain optional `expected_root` and optional
`expected_remotes`.

`expected_remotes`, when supplied, is an object mapping remote names to exact
configured remote URL strings:

```json
{
  "expected_root": "/repo",
  "expected_remotes": {
    "origin": "https://github.com/wiigelec/gve.git"
  }
}
```

The task reports `result.root` and `result.remotes`, where `result.remotes` is
an object mapping every configured remote name to its observed configured URL.

An explicit `expected_root` mismatch fails. For `expected_remotes`, every
supplied remote name must exist and its observed URL must equal the supplied
string exactly; missing or mismatched remotes fail after the observed repository
state is recorded.

`expected_remotes` is an assertion over repository identity. It does not grant
Git remote mutation authority. A remote may therefore be observed or asserted
here while still being unavailable to `git.fetch`, `git.remote-head`, or
`git.push` unless separately granted by the active Git authority.

### `git.branch`

Parameters may contain optional `expected`.

The task reports `result.branch`. Detached HEAD is represented by JSON `null`.
An explicit expectation mismatch fails.

### `git.head`

Parameters may contain optional `expected`.

The task reports `result.commit`. An explicit expectation mismatch fails.

### `git.status`

Parameters may contain optional boolean `expected_clean` and optional boolean
`include_untracked`, which defaults to `true`.

Result exposes `result.clean` and `result.entries`. Each entry retains the exact
two-character porcelain status code separately from its path. Fixed-width Git
status columns are parsed before any trimming of path material.

An explicit `expected_clean` mismatch fails after recording the observation.

### `git.diff`

Parameters:

```json
{
  "cached": false,
  "paths": []
}
```

Both fields are optional. `cached` defaults to `false`; an empty or omitted
`paths` array means all authorized repository paths.

Result exposes the unified diff as `result.diff`.

### `git.diff-check`

Accepts the same `cached` and `paths` selection as `git.diff`.

It performs Git whitespace/error checking for the selected diff and exposes
`result.clean` plus diagnostic text. A detected diff-check error is task failure.

### `git.branch-create`

Parameters contain required `name` and optional `start`.

`start` defaults to current HEAD and may be a commit identity supplied directly
or by result reference. The task fails if the branch already exists.

Result exposes `result.branch` and `result.commit`.

### `git.branch-switch`

Parameters contain required `name`.

The named local branch must already exist. The task fails rather than silently
creating it.

Result exposes the resulting current branch and HEAD.

### `git.add`

Parameters contain required non-empty `paths`.

Each selected path must resolve inside the repository. The task stages exactly
the selected paths and exposes the staged path set under `result.paths`.

### `git.commit`

Parameters:

```json
{
  "message": "commit message"
}
```

`message` is required and non-empty. FS-001 does not create empty commits.

The task commits the currently staged index and exposes `result.commit` and
`result.parent`.

### `git.fetch`

Parameters contain required `remote` and optional `branches`.

`remote` must be inside active Git remote authority. `branches`, when supplied,
is an array of branch names to fetch. Omission means normal fetch of the
authorized remote using its configured fetch mapping; arbitrary caller-provided
refspec strings are not accepted.

Result reports the remote and observed fetched refs relevant to the request.

### `git.remote-head`

Parameters contain required `remote`, required `branch`, and optional
`expected`.

The remote must be authorized. The task observes exactly
`refs/heads/<branch>`. A missing branch is represented by `result.commit = null`.
An explicit expectation mismatch is task failure.

### `git.push`

Parameters:

```json
{
  "remote": "origin",
  "local_branch": "fs1",
  "remote_branch": "fs1",
  "expected_remote_head": null
}
```

`remote`, `local_branch`, and `remote_branch` are required.
`expected_remote_head` is optional and may be a commit identity or JSON `null`
to assert that the remote branch must not exist.

Immediately before push, when `expected_remote_head` is present, GVE observes
the remote branch and fails on mismatch.

Publication is equivalent to a normal non-force update of the selected local
branch to `refs/heads/<remote_branch>`. Caller-controlled raw Git flags,
refspecs, deletion, tags, force, and history-rewrite modes are not accepted.

Result exposes the local commit selected for publication and the push command's
transport outcome. Remote verification remains an explicit later
`git.remote-head` task.

## Execute plugin task contract

### `execute.script`

Parameters:

```json
{
  "script": "scripts/validate",
  "args": [],
  "working_directory": ".",
  "limits": {
    "wall_seconds": 300,
    "max_concurrent": 16,
    "max_total_spawned": 256,
    "max_spawns_per_second": 32
  }
}
```

- `script` is required repository-relative path to an existing regular file;
- `args` is optional array of strings and defaults to empty;
- `working_directory` is optional repository-relative directory and defaults to
  repository root;
- `limits` is optional and may contain only the four keys shown above.

The script and working directory are canonicalized and must resolve inside the
active repository.

GVE invokes the selected repository-owned script directly according to the
host's executable semantics; the payload does not supply shell source or a raw
shell command string.

Result exposes at least:

- `result.exit_code` when obtained;
- `result.stdout`;
- `result.stderr`;
- `result.effective_limits`;
- `result.timed_out`;
- `result.process_limit`;
- `result.termination`.

A non-zero script exit status is task failure. Timeout, process-limit violation,
or inability to complete required process-tree termination is task failure.

GVE does not interpret the script's filesystem, Git, network, credential, or
other script-internal side effects as GVE-governed effects.

## GitHub plugin task contracts

All GitHub tasks operate only on the repository granted by
`--github-repository`. The tasks fail for absent GitHub authority.

### `github.issue-read`

Parameters contain required positive integer `number`.

Result exposes issue number, URL, title, body, state, and labels.

### `github.issue-create`

Parameters:

```json
{
  "title": "title",
  "body": "body",
  "labels": []
}
```

`title` is required and non-empty. `body` and `labels` are optional.

Result exposes the created issue number, URL, and observed resulting state.

### `github.issue-modify`

Parameters contain required positive integer `number` plus at least one of
`title`, `body`, `labels`, or `state`.

`labels`, when supplied, is the complete desired label-name set.
`state`, when supplied, is `open` or `closed`.

Result exposes issue number, URL, and observed resulting state.

### `github.pull-request-read`

Parameters contain required positive integer `number`.

Result exposes pull-request number, URL, title, body, state, base branch, head
branch, draft state, and merge state when available.

### `github.pull-request-create`

Parameters:

```json
{
  "title": "title",
  "body": "body",
  "base": "main",
  "head": "fs1",
  "draft": false
}
```

`title`, `base`, and `head` are required. `body` is optional and `draft`
defaults to `false`.

Result exposes the created pull-request number, URL, and observed resulting
state.

### `github.pull-request-modify`

Parameters contain required positive integer `number` plus at least one of
`title`, `body`, `base`, or `state`.

`state`, when supplied, is `open` or `closed`. FS-001 does not expose merge as a
generic pull-request modification field.

Result exposes pull-request number, URL, and observed resulting state.

## FS-001 task result envelope

Every declared invocation receives exactly one workflow result record.

A successful task record has this structure:

```json
{
  "id": "commit",
  "task": "git.commit",
  "status": "success",
  "observations": {},
  "effects": {},
  "result": {},
  "error": null,
  "reason": null
}
```

A failed task uses `status = "failure"` and `error`:

```json
{
  "code": "stable-machine-code",
  "message": "human-readable diagnostic",
  "details": {}
}
```

`details` is a JSON object and may be empty.

A later declared invocation skipped because of fail-fast termination uses
`status = "not-executed"`, empty `observations`, `effects`, and `result`, null
`error`, and `reason = "prior-task-failure"`.

`observations` contains state established by GVE without claiming mutation.
`effects` contains effects directly performed by the GVE task itself.
`result` contains task-specific stable values intentionally exposed to callers
and task-result references.

Task-specific contracts may populate the same observed identifier in both
`observations` and `result` when it is both evidence and an intentionally
addressable value.

## FS-001 workflow result envelope

The authoritative workflow result is:

```json
{
  "schema_version": 1,
  "workflow_id": "example-workflow",
  "status": "success",
  "tasks": []
}
```

`status` is `success` only when every declared task succeeds. It is `failure`
when payload execution cannot complete successfully.

For a structurally invalid payload that cannot establish a trustworthy
invocation list, the CLI emits:

```json
{
  "schema_version": 1,
  "workflow_id": null,
  "status": "failure",
  "tasks": [],
  "error": {
    "code": "invalid-payload",
    "message": "human-readable diagnostic",
    "details": {}
  }
}
```

For a parsed workflow, top-level `error` is omitted and failure is represented
by the failing task record plus `not-executed` successor records.

The task array remains in declared workflow order.

## Error-code stability

FS-001 error codes are machine-readable lowercase kebab-case strings.

Build may refine the complete code vocabulary, but distinct failure classes that
a caller must reason about shall not be collapsed into an undifferentiated
success/failure boolean. At minimum the implementation distinguishes payload
validation, unknown task, result-reference, authority, state/precondition,
task execution, process-limit, process-termination, and remote/API failures.

Human diagnostic wording is not a compatibility surface in FS-001.

## CLI result and exit contract

The local executable command is:

```text
gve execute [authority options] PAYLOAD.json
```

The authoritative workflow result is written as one JSON document to stdout.

Human progress and diagnostics, if any, are written to stderr and must not
contradict the JSON result.

Exit status is:

```text
0  workflow status success
1  validly reported workflow/payload failure
2  CLI invocation failure before a workflow result can be constructed
```

When stdout contains an authoritative workflow result, exit status must agree
with that result.

## Validation strategy

Build owns exact mechanical validation task implementations and exact
requirement-to-validation-task bindings.

Testing shall cover:

- payload envelope validation and rejection of unknown fields;
- result-reference success, rejection of references outside the intentional
  `result` namespace, and every defined failure class;
- ordered execution and fail-fast `not-executed` records;
- authority non-expansion;
- static task registration;
- every plugin task's accepted/rejected parameter boundary;
- filesystem traversal and symlink escape rejection;
- repository-root and exact configured-remote identity observation/assertion;
- Git status fixed-width parsing;
- normal/non-force Git publication and remote-race guards;
- execute hard-ceiling enforcement, CLI/task narrowing, timeout, spawn/count
  limits, process-tree termination, and evidence;
- GitHub repository authority and semantic-field restriction;
- task/workflow result envelopes;
- the reference development workflow expressed only through registered tasks.

Tests may use temporary repositories and controlled fakes where appropriate.

External GitHub mutation tests shall not require destructive operations against
unrelated repositories. Build may use mocked/fake transport for deterministic
mechanical tests while preserving semantic task behavior.

Repository-wide `./scripts/validate` remains the canonical mechanical validation
entry point.

## Build sequencing

A practical Build sequence is:

```text
payload/result/authority models under `product/src/`
  -> registry + engine
  -> filesystem plugin
  -> git plugin
  -> execute plugin
  -> github plugin
  -> CLI
  -> mechanical validation tasks and bindings
  -> end-to-end reference workflow tests
```

This sequence is advisory except where dependencies make the order consequential.

## Build implementation freedom

Build owns ordinary code-level realization choices not fixed by this Plan,
including Python module/class decomposition, library selection, subprocess
mechanics, Git command construction, GitHub transport implementation,
process-tree monitoring mechanism, test-helper organization, and exact
validation-task implementation.

Those choices may not alter the payload/result contracts, task semantics,
authority model, plugin boundaries, failure behavior, or Product Design
established above without returning to Planning or Design as appropriate.
