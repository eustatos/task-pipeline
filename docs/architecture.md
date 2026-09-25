# Hybrid Orchestration Architecture

> **Status:** Approved  
> **Last Updated:** 2026-09-25  
> **Related ADRs:** ADR-004, ADR-005, ADR-006, ADR-007

## Overview

This document describes the core orchestration architecture for the task pipeline. The system uses a **hybrid approach**: LangGraph for stateful orchestration at the upper level, and plain Python pipelines for linear, stateless processing (test execution).

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│              LANGGRAPH (Upper Loop)                  │
│                                                      │
│  Orchestrator ──→ Executor (subgraph) ──→ Reviewer   │
│       ↑               │                     │        │
│       │          ┌────┴────┐                  │        │
│       │          ▼         ▼                  │        │
│       │      Analyze   Write Code             │        │
│       │          │         │                  │        │
│       │          ▼         ▼                  │        │
│       │      [Tools]   [Tools]                │        │
│       │                    │                  │        │
│       │                    ▼                  │        │
│       │          ┌──────────────────┐         │        │
│       │          │  PIPELINE (не    │         │        │
│       │          │  LangGraph!)     │         │        │
│       │          │                  │         │        │
│       │          │ Discover → Filter│         │        │
│       │          │ → Run → Parse →  │         │        │
│       │          │ Summarize        │         │        │
│       │          └──────────────────┘         │        │
│       │                                       │        │
│       └──────── conditional edge ◄────────────┘        │
│                  (pass / fail / retry)                 │
└─────────────────────────────────────────────────────┘
```

## Layer Responsibilities

| Level | Technology | Rationale |
|-------|-----------|-----------|
| **Upper loop** (Orchestrator/Executor/Reviewer) | LangGraph | Stateful, conditional, persistent, observable |
| **Executor sub-steps** (Analyze → Write → Test) | LangGraph subgraph | Natural decomposition, isolation |
| **Test pipeline** (Discover → Filter → Run → Parse → Summarize) | Python pipeline (functions/dataclasses) | Linear process, no branching, minimal overhead |
| **Tool execution** | Tool Registry (custom) | Stateless, deterministic, testable |

## Why Hybrid?

### LangGraph strengths (Upper Loop)

| Requirement | LangGraph Support |
|------------|------------------|
| Stateful orchestration | Checkpointer + State schema |
| Conditional routing (Reviewer → pass/fail/retry) | `add_conditional_edges` |
| Human-in-the-loop (approval gates) | `interrupt()` + resume |
| Persistence & recovery | Postgres/SQLite/Memory checkpointer |
| Streaming & observability | LangSmith integration |
| Subgraph composition | `Command(goto=...)` + subgraphs |

### Why NOT LangGraph for Test Pipeline

| Problem | Impact |
|---------|--------|
| Recursive complexity (graph in graph in graph) | Critical debugging difficulty |
| Checkpoint explosion | High memory/disk growth |
| Token overhead on every transition | Overhead > useful work for small steps |
| Over-abstraction | Test pipeline is a **linear pipeline**, not a graph |
| Vendor lock-in | Tight coupling to LangGraph API |

> **Key insight:** Not every multi-step process is a graph. The test pipeline is a **pipeline** (linear conveyor with stages). Using a graph for a pipeline is over-engineering that kills maintainability.

## Test Pipeline Design

```python
async def run_test_pipeline(scope: str, config: TestConfig) -> TestSummary:
    tests = await discover_tests(scope, config)           # Step 1
    filtered = filter_tests(tests, config)                # Step 2
    raw_result = await execute_tests(filtered, config)    # Step 3
    parsed = parse_results(raw_result, config.runner)     # Step 4
    summary = build_summary(parsed, config.max_failures)  # Step 5
    return summary
```

**Advantages over LangGraph for this use case:**
- Unit-testable without LangGraph mocks
- Zero serialization overhead
- Readable as documentation
- Easy to extend (add step = add function)
- No framework dependency

## Executor Subgraph

```python
executor_graph = StateGraph(ExecutorState)
executor_graph.add_node("analyze", analyze_with_tools)
executor_graph.add_node("write_code", write_with_tools)
executor_graph.add_node("run_tests", run_tests_subdag)
executor_graph.add_edge("analyze", "write_code")
executor_graph.add_conditional_edges("write_code", route_after_write)
executor_graph.add_conditional_edges("run_tests", route_after_tests)
```

## Criteria for Pipeline → Subgraph Promotion

A pipeline should be promoted to a LangGraph subgraph **only** when:

1. **Branching appears** — conditional paths based on intermediate results
2. **Parallel execution needed** — concurrent steps with join points
3. **Conditional retry** — retry logic depends on step-specific state
4. **Persistence required** — individual steps need checkpointing

> **YAGNI:** Do not convert a pipeline to a graph "for the future." Refactor only when the above conditions are met.

## Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| LangGraph breaking changes | High | Pin version, abstraction wrapper over LangGraph API |
| Over-engineering upper loop | Medium | Start with minimal graph (3 nodes). Add complexity only when proven necessary |
| Subgraph testing complexity | Medium | Integration tests with InMemorySaver. Unit-test individual nodes as pure functions |
| State schema drift | Medium | Pydantic models for state. Schema versioning. Migration scripts |
| Pipeline → graph conversion "for future" | High | YAGNI. Refactor only when branching/parallelism actually appears |

## Evaluation Matrix

| Criterion | Upper Loop (LangGraph) | Test Pipeline (Custom) | Hybrid |
|-----------|----------------------|----------------------|--------|
| Extensibility | Excellent — new stage = node + edge | Excellent — new step = function | Best of both |
| Maintainability | Good — visualization, typing, LangSmith | Excellent — simple code, unit tests | Excellent — each level in its abstraction |
| Testability | Requires mocks/checkpointer | Excellent — pure functions | Excellent — isolated levels |
| Overhead | Acceptable for upper loop | Zero | Optimal |
| Debuggability | Good — LangSmith trajectory | Excellent — breakpoints, logs | Good — each level debuggable |
| Vendor lock-in | Moderate — LangGraph API | None | Moderate — locked only at upper loop |
| Onboarding | Requires LangGraph knowledge | Standard Python | Varies by level |
