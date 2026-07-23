# GVE

GVE is being rebuilt from governed execution specifications.

The authoritative design documents are:

1. `LEVEL_0.md`
2. `LEVEL_1.md`
3. `LEVEL_2.md`
4. `LEVEL_3.md`

Implement and harden the levels in that order, then implement the maintained
GVE product. The restored historical executor is bootstrap and executable
reference material only. It must not override the level specifications.

## Bootstrap executor

The repository currently includes a restored historical governed executor under
`src/scf_governed_executor` and a repository-local wrapper:

```sh
./scripts/governed-execute /path/to/operation.json
```

Always invoke the wrapper from a clean checkout. It adds `src` to
`PYTHONPATH`, selects an available Python interpreter, and routes the operation
through `scf_governed_executor.launcher`.

The launcher supports two compatibility paths:

- Current restored operations use executor version `0.9.4`.
- Legacy core operations use executor version `0.7.0`.

Do not change an operation's executor version merely to bypass an error. The
operation type and executor version must match a dispatcher that implements that
contract.

## Bootstrap workflow for a fresh chat

A fresh chat should begin by reading:

- this `README.md`;
- `LEVEL_0.md` through `LEVEL_3.md`;
- `scripts/governed-execute`;
- `src/scf_governed_executor/launcher.py`;
- the implementation and tests for the intended operation type.

The chat should treat the tests as examples of payload shape, not as authority
over the level specifications.

Before generating an operation, inspect the repository locally:

```sh
cd ~/git/gve
git status --short
git branch --show-current
git rev-parse HEAD
git remote get-url origin
```

Use those exact values in the operation guards. Do not guess the current commit
ID, branch, repository root, origin, or clean state.

## Operation requirements

A governed operation is a JSON object with a closed top-level contract:

```text
schema_version
operation_id
operation_type
executor_version
operation_digest
repository
guards
authorization
inputs
expected_mutations
validation
publication
result
```

The operation digest is SHA-256 over canonical JSON after removing the
`operation_digest` field:

```python
canonical = json.dumps(
    operation_without_digest,
    sort_keys=True,
    separators=(",", ":"),
    ensure_ascii=False,
).encode("utf-8")
digest = hashlib.sha256(canonical).hexdigest()
```

Each mutation must be explicit, narrowly authorized, guarded, and represented in
`expected_mutations`.

## Local file operations

Legacy executor version `0.7.0` supports `local-file-operations`.

Use only the authorization required for that operation:

```json
{
  "interrogate": true,
  "edit": true,
  "validate": false,
  "stage": false,
  "commit": false,
  "push": false,
  "issue": false,
  "pull_request": false,
  "review": false,
  "merge": false,
  "close_issue": false
}
```

A create item contains:

```json
{
  "action": "create",
  "path": "relative/path",
  "content": "complete UTF-8 file contents",
  "content_sha256": "sha256 of content",
  "mode": "0644"
}
```

A replace item additionally requires `expected_sha256`, which must equal the
SHA-256 hash of the complete existing file. Never use replace without first
reading the current file and hashing its exact bytes.

`expected_mutations.files` must exactly mirror the requested operations using:

```text
action
path
before_sha256
after_sha256
mode
```

For create, `before_sha256` is `null`. For replace, it is the expected hash of
the existing file.

## Current restored operations

Executor version `0.9.4` currently dispatches these operation types through the
restored launcher:

- `development-session-initialize`
- `executor-self-update`
- `git-publication`
- `issue-create`
- `repository-interrogation`

Some additional historical operation types are dispatched through the legacy
`0.7.0` path. Confirm dispatch in `launcher.py` and `__main__.py` before
generating a payload.

## Interaction Model

Actors

Chat
- Reads the specifications.
- Generates governed operation payloads.
- Produces exact local execution instructions.
- Reviews returned result evidence.
- Generates successor operations.

User
- Downloads the generated payload.
- Executes the provided commands in the local environment.
- Returns the result artifact to the chat.
- Never edits generated payloads manually unless explicitly instructed.

Bootstrap Executor
- Executes the operation.
- Produces authoritative execution evidence.
- Never communicates directly with the chat.

Chat
    │
    ├── generates operation.json
    ├── provides execution instructions
    ▼
User
    │
    ├── saves operation.json
    ├── executes governed-execute
    ▼
Bootstrap Executor
    │
    ├── validates
    ├── executes
    ├── writes result.json
    ▼
User
    │
    └── returns result.json
          ▼
Chat
    │
    ├── reviews evidence
    └── generates successor operation if needed

## Chat-to-local execution handoff

The bootstrap executor runs only in the user’s local environment. The chat does not execute the operation against the repository directly.

For each governed change, the chat shall provide:

1. a downloadable JSON operation payload;
2. an execution instruction block containing the exact local commands required to:
    * save or move the payload into the external GVE operations directory;
    * enter the clean local repository checkout;
    * invoke ./scripts/governed-execute with the payload path;
    * inspect the generated result artifact;
3. the expected path of the result artifact that the user should return to the chat for review.

The payload and result evidence shall remain outside the governed repository.

The user executes the supplied instruction block in the local environment. The chat shall not claim that the operation succeeded until it has inspected the resulting execution evidence.

## Executing an operation

Store operations and result evidence outside the repository:

```sh
mkdir -p ~/.local/state/gve/operations
mkdir -p ~/.local/state/gve/results
```

Execute:

```sh
cd ~/git/gve
./scripts/governed-execute   "$HOME/.local/state/gve/operations/<operation>.json"
```

Then inspect the result:

```sh
python3 -m json.tool   "$HOME/.local/state/gve/results/<operation>.result.json"
```

Do not assume success from command output alone. Check:

- `terminal_status`;
- `diagnostics`;
- `mutation.attempted`;
- `mutation.authorized`;
- `mutation.completed`;
- `mutation.observed`;
- read-after-write or publication verification;
- `safest_next_interaction`.

## Guard failures and successor operations

Operations are intentionally bound to repository state.

If the branch, HEAD, origin, root, or clean state no longer matches, do not
weaken the guards. Generate a new operation from the current repository state.

A failed operation may still create a result artifact. Do not reuse its result
filename because result evidence is written without overwrite.

Do not replay a completed mutation operation. Review its evidence and generate a
new successor operation for subsequent work.

## Validation and tests

Run the restored reference test suite with:

```sh
PYTHONPATH=src python3 -m unittest discover   -s src/scf_governed_executor/tests
```

At the time this bootstrap documentation was added, the restored suite contained
86 passing tests. Treat that number as historical evidence, not a permanent
requirement; new implementation work may add tests.

## Development sequence

Work in this order:

1. Harden Level 0.
2. Harden Level 1 without weakening Level 0.
3. Harden Level 2 without weakening Levels 0–1.
4. Harden Level 3 without weakening Levels 0–2.
5. Implement and maintain GVE on the hardened foundation.

The bootstrap executor exists to make those changes governed and reviewable. It
is not the final product specification.
