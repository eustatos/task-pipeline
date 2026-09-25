# ADR-007: Hybrid Orchestration Architecture

> **Status:** Proposed  
> **Date:** 2026-09-25  
> **Related:** ADR-001, ADR-002, ADR-004, ADR-005, ADR-006

## Context

The task pipeline requires multi-level orchestration:
- An **upper loop** (Orchestrator → Executor → Reviewer) with stateful branching, persistence, and human-in-the-loop gates.
- **Executor sub-steps** (Analyze → Write Code → Run Tests) that form a natural subgraph.
- A **test execution pipeline** (Discover → Filter → Run → Parse → Summarize) that is linear and stateless.
- A **Tool Registry** for stateless, deterministic tool execution.

Using a single orchestration framework for all levels creates a "graph of graphs" anti-pattern with excessive complexity, checkpoint explosion, and vendor lock-in at levels where it is not needed.

## Decision

We adopt a **hybrid architecture** with explicit boundaries between orchestration paradigms:

### 1. LangGraph for Upper Loop

LangGraph is used for:
- Orchestrator → Executor → Reviewer cycle
- Conditional routing (pass/fail/retry)
- Checkpointing and recovery
- Human-in-the-loop approval gates (`interrupt()` / `resume`)
- Executor subgraph (Analyze → Write → Test)

**Justification:** These operations require state persistence, conditional branching, and observability — exactly what LangGraph provides.

### 2. LangGraph Subgraph for Executor

The Executor is composed as a LangGraph subgraph with:
- Own state schema (`ExecutorState`)
- Own checkpointing
- Isolation from parent graph state
- Conditional edges for routing after each step

**Justification:** Natural decomposition, testable in isolation, reuses parent graph's checkpointing infrastructure.

### 3. Custom Python Pipeline for Test Execution

Test execution is a **linear pipeline** implemented as plain async functions:

```
discover → filter → execute → parse → summarize
```

**NOT** a LangGraph subgraph.

**Justification:**
- No branching (linear flow)
- No persistent state between steps
- No need for checkpointing individual steps
- Zero serialization overhead
- Unit-testable without framework mocks
- Easier to debug (breakpoints, logs)

### 4. Tool Registry as Independent Layer

A custom Tool Registry provides:
- Registration/deregistration (atomic)
- Role-based filtering
- Pydantic-validated input/output schemas
- Idempotency guarantees
- Timeout handling
- Audit logging

**Justification:** Stateless, deterministic, testable in isolation. No framework dependency.

## Consequences

### Positive
- Each level uses the right abstraction for its complexity
- Test pipeline remains simple, fast, and framework-independent
- Upper loop benefits from LangGraph's state management and observability
- Clear boundaries reduce coupling and enable independent evolution
- New tools are added to the Registry without touching orchestration

### Negative
- Two orchestration paradigms to understand (onboarding cost)
- LangGraph dependency at upper loop (version pinning required)
- Need to maintain abstraction boundary between LangGraph and pipeline
- Debugging spans two systems (LangSmith + standard Python debugging)

### Risks
| Risk | Mitigation |
|------|-----------|
| LangGraph API breaking changes | Pin version. Abstraction wrapper over LangGraph API calls. |
| Boundary violations (pipeline logic leaks into graph) | Code review checklist. Separate modules. |
| Over-engineering upper loop | Start with 3 nodes. Add complexity only with proven need. |
| State schema drift | Pydantic models + schema versioning + migration scripts. |

## Promotion Criteria

A custom pipeline **may** be promoted to a LangGraph subgraph when **any** of the following conditions are met:

1. **Branching appears** — execution path depends on intermediate results (not just linear flow)
2. **Parallel execution** — concurrent steps with join/synchronization points
3. **Conditional retry** — retry logic depends on step-specific state accumulated across iterations
4. **Per-step persistence** — individual steps require independent checkpointing for recovery

Until these conditions are met, the pipeline remains plain Python. **YAGNI applies.**

## Interface Between Layers

```
LangGraph Upper Loop
    │
    ├── Orchestrator node: routes tasks to Executor
    ├── Executor subgraph:
    │     ├── analyze (uses Tool Registry)
    │     ├── write_code (uses Tool Registry)
    │     └── run_tests (calls custom pipeline)
    │           │
    │           ▼
    │     Custom Test Pipeline (plain async functions)
    │           │
    │           ▼ returns TestSummary
    │
    └── Reviewer node: inspects results, routes pass/fail/retry
```

**Data contract between Executor subgraph and Test Pipeline:**

- **Input:** `scope: str`, `config: TestConfig` (Pydantic model)
- **Output:** `TestSummary` (Pydantic model: passed/failed counts, errors, duration, truncated output)
- **No shared state:** Pipeline is a pure function of its inputs

## Verification

See `docs/definition-of-done.md` for acceptance criteria that validate this architecture.

Key criteria:
- C1.7: Subgraph isolation (zero state leakage)
- C2.3–C2.8: Test pipeline correctness
- C3.7: Test pipeline overhead < 5% of task tokens
