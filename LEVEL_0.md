# GVE Level 0

GVE is a governed instruction executor.

It:

1. Receives an instruction payload.
2. Executes the requested instructions according to a governed instruction set.
3. Emits an authoritative result.

```text
Instruction Payload
        ↓
Governed Execution
        ↓
Result
```

The payload defines requested work.

The governed instruction set defines what instructions are supported, how they may execute, and how success or failure is determined.

The result records what GVE actually executed and observed.

GVE must not execute unsupported instructions, broaden instruction scope, or report intended effects as completed effects.
