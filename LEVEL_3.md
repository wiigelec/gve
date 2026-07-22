# GVE Level 3

GVE is implemented as a small execution core plus independently registered application plugins.

## Core Runtime

The core is responsible for:

* loading a payload;
* validating common envelope fields;
* selecting plugins;
* sequencing instruction steps;
* passing declared outputs between steps;
* stopping on failure unless continuation is explicitly allowed;
* assembling the final result.

Suggested package layout:

```text
src/gve/
├── core/
│   ├── engine.py
│   ├── lifecycle.py
│   ├── routing.py
│   ├── results.py
│   └── errors.py
├── plugins/
│   ├── filesystem/
│   ├── command/
│   └── github/
└── cli.py
```

## Payload Envelope

The core owns a common payload envelope:

```json
{
  "schema_version": 1,
  "operation_id": "change-0001",
  "steps": [
    {
      "plugin": "filesystem",
      "instruction": "file.replace",
      "inputs": {}
    }
  ],
  "result": {
    "path": "/tmp/change-0001.result.json"
  }
}
```

Each plugin validates its own `inputs`.

## Plugin Interface

Each plugin implements a common interface:

```python
class GVEPlugin:
    name: str

    def validate(self, instruction: str, inputs: dict) -> None:
        ...

    def execute(
        self,
        instruction: str,
        inputs: dict,
        context: ExecutionContext,
    ) -> StepResult:
        ...
```

Plugins register instruction names such as:

```text
filesystem.file.create
filesystem.file.replace
command.run
github.branch.create
github.commit.create
github.pull_request.create
```

Unknown plugins or instructions fail closed.

## Execution Context

The core provides plugins with a controlled context containing:

* operation identity;
* working directory;
* prior declared outputs;
* approved environment values;
* result recorder;
* cancellation and timeout state.

Plugins must not communicate through undeclared global state.

## Filesystem Plugin

Suggested instructions:

```text
file.create
file.replace
file.delete
file.move
directory.create
```

Implementation requirements:

* accept repository-relative paths;
* reject absolute paths and `..` traversal;
* resolve symlinks before containment checks;
* support expected-content hashes;
* record old and new content hashes;
* use atomic replacement where practical;
* return the exact paths changed.

Example:

```json
{
  "plugin": "filesystem",
  "instruction": "file.replace",
  "inputs": {
    "path": "src/parser.py",
    "expected_sha256": "old-hash",
    "content": "new file content"
  }
}
```

## Command Execution Plugin

Primary instruction:

```text
command.run
```

Implementation requirements:

* require argument arrays rather than shell strings;
* use `shell=false`;
* constrain the working directory;
* use an explicit environment allowlist;
* enforce timeouts;
* capture stdout and stderr;
* terminate the full process group on timeout;
* record exit code, duration, and redaction;
* apply output-size limits.

Example:

```json
{
  "plugin": "command",
  "instruction": "command.run",
  "inputs": {
    "argv": ["python", "-m", "pytest"],
    "working_directory": ".",
    "timeout_seconds": 300,
    "success_exit_codes": [0]
  }
}
```

## GitHub Plugin

The GitHub plugin may use local Git commands and GitHub API operations, but must expose them as separate governed instructions.

Suggested instructions:

```text
repository.inspect
branch.create
commit.create
push.execute
issue.create
issue.comment
pull_request.create
pull_request.comment
```

Implementation requirements:

* verify repository identity;
* verify expected branch and HEAD;
* stage only declared paths;
* verify the staged diff before commit;
* push an exact commit to an exact ref;
* keep Git and GitHub API credentials outside payloads;
* record commit IDs, branch refs, issue numbers, and pull-request numbers;
* treat uncertain remote outcomes explicitly.

## Step Results

Every plugin returns a structured result:

```json
{
  "status": "completed",
  "instruction": "command.run",
  "outputs": {
    "exit_code": 0
  },
  "effects": [],
  "evidence": {},
  "error": null
}
```

Supported step states should include:

```text
completed
rejected
failed
partially-completed
uncertain
skipped
```

## Cross-Plugin Sequencing

Later steps may reference declared outputs from earlier steps:

```json
{
  "plugin": "github",
  "instruction": "commit.create",
  "inputs": {
    "paths_from": "steps.filesystem.outputs.changed_paths"
  }
}
```

References must be explicit and validated by the core.

A typical sequence is:

```text
filesystem.file.replace
        ↓
command.run
        ↓
github.branch.create
        ↓
github.commit.create
        ↓
github.push.execute
        ↓
github.pull_request.create
```

## Failure Handling

The core stops execution when a required step returns:

```text
rejected
failed
partially-completed
uncertain
```

A step may declare that it runs only when prior conditions are satisfied.

Example:

```json
{
  "run_if": {
    "step": "validate",
    "status": "completed"
  }
}
```

## Final Result

The final result contains:

* operation identity;
* GVE version;
* ordered step results;
* completed effects;
* failed or uncertain effects;
* final status;
* safest next action.

The result must be written exclusively so an existing result file is never silently overwritten.
