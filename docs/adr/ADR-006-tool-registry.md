# ADR-006: Tool Registry & Execution Contract

> **Status:** Proposed  
> **Date:** 2026-09-25  
> **Related:** ADR-001, ADR-002, ADR-005, ADR-007

## Context

The core executes a set of tools (apply_diff, run_tests, get_repo_map, checkpoint, etc.) that are:
- Invoked by different agent roles (Architect, Executor, Reviewer)
- Stateless and deterministic
- Subject to strict input/output contracts
- Required to be idempotent or reversible
- Subject to rate limiting and timeout

A centralized registry is needed to manage tool lifecycle, access control, and execution guarantees.

## Decision

### Tool Contract

Every tool MUST:
1. Have a **Pydantic schema** for input and output (validated at call time)
2. Be **idempotent** or provide an explicit undo mechanism
3. Declare a **timeout** (enforced by the registry, not the tool itself)
4. Return a **structured result** (never raw exceptions to the caller)
5. Log every invocation to the **event stream** (input, output, duration)

### Tool Registry API

```python
class ToolRegistry:
    def register(self, tool: ToolSpec) -> None: ...
    def unregister(self, tool_name: str) -> None: ...
    def get(self, tool_name: str, role: AgentRole) -> Tool: ...
    def list_for_role(self, role: AgentRole) -> list[ToolSpec]: ...
```

- `register`/`unregister` are **atomic** (no partial state on failure)
- `get` with role filtering: a role can only access tools assigned to it
- Registry is **in-memory** at runtime, populated from config at startup

### Role-Based Access Control

| Role | Accessible Tools |
|------|----------------|
| Architect | get_repo_map, analyze, plan |
| Executor | apply_diff, run_tests, checkpoint, read_file |
| Reviewer | read_file, run_tests, get_repo_map |

Cross-role access is **denied at the registry level**, not at the graph level.

### Execution Guarantees

| Guarantee | Implementation |
|-----------|---------------|
| Timeout | `asyncio.wait_for` wrapper in registry. On timeout: kill subprocess, return structured error. |
| Idempotency | Tool-specific. `apply_diff`: re-applying same diff = no-op. `checkpoint`: same state = skip commit. |
| Rate limiting | Token bucket per tool. On limit hit: return structured "rate_limited" result. Agent must handle. |
| Audit | Every call appended to event stream: `{tool, input_hash, output_hash, duration_ms, role, timestamp}` |

### Tool Implementation Pattern

```python
class ApplyDiffTool(Tool):
    name = "apply_diff"
    input_schema = ApplyDiffInput    # Pydantic
    output_schema = ApplyDiffOutput  # Pydantic
    timeout = 10.0

    async def execute(self, input: ApplyDiffInput) -> ApplyDiffOutput:
        ...
```

## Consequences

### Positive
- Single point of truth for tool lifecycle
- Role-based access enforced centrally
- Uniform error handling and timeout behavior
- Easy to add/remove tools without touching orchestration
- Audit trail is complete by construction

### Negative
- Registry is a single point of failure (mitigated: in-memory, fast startup)
- Pydantic validation adds small overhead per call (acceptable)
- Tools must conform to contract (enforced at registration, not runtime)

## Verification

- C0.1: All tools have Pydantic schemas, 0 mypy errors
- C0.2: Atomic register/unregister (concurrent test)
- C0.3: Role-based filtering (0 cross-role leaks)
- C2.7: All tools idempotent or reversible
- C2.8: Timeout handling works correctly
- C2.9: Audit log complete
- C2.10: Rate limiting enforced
