# Backlog — Task Pipeline Core

> **Structure:** Stages ordered by dependency. Each stage maps to a DoD level.  
> **Status legend:** `[ ]` = TODO, `[~]` = IN PROGRESS, `[x]` = DONE

---

## Stage 1: Contract Integrity (DoD Level 0)

> **Gate:** All tasks must be complete before any code is merged to main.
> **Detailed task files:** [`stage-1/`](./stage-1/) — one file per task (ADR-008 format).
> Shared rules (prohibited phrases, mypy, toolchain, paths): [`_conventions.md`](./_conventions.md).

### 1.0 Scaffolding

- [ ] **T1.0.0** Project scaffolding and conventions (package layout, deps, test tree, shared fixtures)

### 1.1 Tool Registry Core

- [ ] **T1.1.1** Define `ToolSpec` Pydantic model (name, input_schema, output_schema, timeout, roles)
- [ ] **T1.1.2** Implement `ToolRegistry` with atomic `register()` / `unregister()`
- [ ] **T1.1.3** Implement role-based `get(tool_name, role)` and `list_for_role(role)`
- [ ] **T1.1.4** Write concurrent register/unregister test (zero race conditions)
- [ ] **T1.1.5** Write role-based filtering integration test (Planner/Executor/Reviewer isolation)

### 1.2 State Schema & Versioning

- [ ] **T1.2.1** Define core State schema as Pydantic model with `version: int` field
- [ ] **T1.2.2** Implement schema migration framework (v1→v2 converter pattern)
- [ ] **T1.2.3** Write migration test: v1→v2 state conversion with 100% backward compatibility
- [ ] **T1.2.4** Implement state serialization/deserialization with corruption detection (JSON checksum)

### 1.3 Event Stream

- [ ] **T1.3.1** Define `Event` Pydantic model (type, payload, timestamp, sequence_number)
- [ ] **T1.3.2** Implement append-only event stream (in-memory for MVP, file-backed for prod)
- [ ] **T1.3.3** Write property test: no mutation after write (10K events, zero violations)
- [ ] **T1.3.4** Implement event stream replay for recovery

### 1.4 Configuration

- [ ] **T1.4.1** Define `CoreConfig` as Pydantic Settings model (all env vars, no YAML paths)
- [ ] **T1.4.2** Implement fail-fast validation at startup (clear error messages for missing/invalid config)
- [ ] **T1.4.3** Write config validation test matrix (missing required, invalid types, defaults)

### 1.5 CI Gate

- [ ] **T1.5.1** Set up CI pipeline that runs all Stage 1 tests as a merge gate
- [ ] **T1.5.2** Add `mypy --strict` check for all tool modules
- [ ] **T1.5.3** Add schema generation test (validate all tools produce valid JSON Schema)

### 1.6 CLI Bootstrap

> **Purpose:** Minimal CLI surface for dogfooding (ADR-009 Phase 0).
> `backlog run` (full orchestration) arrives in Stage 2 — this section covers the
> commands needed to bootstrap the project and validate tasks.

- [ ] **T1.6.0** CLI entry point: Typer app + `console_scripts` in pyproject.toml (`backlog` command)
- [ ] **T1.6.1** `backlog init [DIR]`: detect project root, create `backlog/` + `.backlog/` scaffolding
- [ ] **T1.6.2** `backlog lint [PATH...]`: wrap `scripts/lint_tasks.py` as CLI subcommand (default: `backlog/`)
- [ ] **T1.6.3** `backlog status`: parse `backlog/` frontmatter, display task graph summary (counts by status/priority)

---

## Stage 2: Upper Loop — LangGraph Orchestration (DoD Level 1)

> **Depends on:** Stage 1 (contract integrity)

### 2.1 Graph Structure

- [ ] **T2.1.1** Define `OrchestratorState` Pydantic model (tasks, current_phase, results, version)
- [ ] **T2.1.2** Define `ExecutorState` Pydantic model (code_context, diff, test_results, version)
- [ ] **T2.1.3** Build upper loop graph: Orchestrator → Executor → Reviewer with conditional edges
- [ ] **T2.1.4** Build Executor subgraph: analyze → write_code → run_tests
- [ ] **T2.1.5** Implement `route_after_reviewer()` conditional routing (pass/fail/retry)
- [ ] **T2.1.6** Implement `route_after_write()` and `route_after_tests()` in Executor subgraph

### 2.2 Checkpointing & Recovery

- [ ] **T2.2.1** Configure LangGraph checkpointer (SQLite for dev, Postgres for prod)
- [ ] **T2.2.2** Implement checkpoint after each completed task (git commit + state snapshot)
- [ ] **T2.2.3** Write integration test: 10 tasks → 10 valid checkpoints
- [ ] **T2.2.4** Implement recovery: kill at task N → resume → verify state identity
- [ ] **T2.2.5** Benchmark: recovery from any checkpoint p99 < 5s
- [ ] **T2.2.6** Write chaos test: kill mid-checkpoint → verify no state corruption

### 2.3 Human-in-the-Loop

- [ ] **T2.3.1** Implement `interrupt()` before Reviewer decision
- [ ] **T2.3.2** Implement `resume()` with approval/rejection input
- [ ] **T2.3.3** Write E2E test: interrupt → verify blocked → resume → verify continued
- [ ] **T2.3.4** Implement escalation path (3 rejections → halt + notify)

### 2.4 Context Management

- [ ] **T2.4.1** Implement explicit context passing (only dependency artifacts, not full history)
- [ ] **T2.4.2** Measure: context size ≤ 30% of full history tokens
- [ ] **T2.4.3** Implement subgraph state isolation (Executor state mutations don't leak to parent)
- [ ] **T2.4.4** Write unit test: zero state leakage between subgraph and parent

### 2.5 Topological Ordering

- [ ] **T2.5.1** Implement DAG task ordering (topological sort with parallel branches)
- [ ] **T2.5.2** Write integration test: DAG with 20 nodes, parallel branches, 100% correct ordering
- [ ] **T2.5.3** Write parameterized test: all Reviewer branches covered (100% edge coverage)

---

## Stage 3: Tool Execution (DoD Level 2)

> **Depends on:** Stage 1 (registry), Stage 2 (upper loop integration)

### 3.1 apply_diff

- [ ] **T3.1.1** Implement `apply_diff` tool with unified diff parsing
- [ ] **T3.1.2** Implement fallback: 3 failed patches → whole-file replacement
- [ ] **T3.1.3** Write fuzz test: 500 real LLM outputs → parse → apply (≥ 95% success)
- [ ] **T3.1.4** Write integration test: malformed diff → retry → fallback triggers correctly
- [ ] **T3.1.5** Benchmark: 1000 diffs, p99 < 2s

### 3.2 run_tests (Custom Pipeline)

- [ ] **T3.2.1** Define `TestConfig` and `TestSummary` Pydantic models
- [ ] **T3.2.2** Implement `discover_tests(scope, config)` — find test files by scope
- [ ] **T3.2.3** Implement `filter_tests(tests, config)` — apply inclusion/exclusion rules
- [ ] **T3.2.4** Implement `execute_tests(filtered, config)` — subprocess with timeout
- [ ] **T3.2.5** Implement `parse_results(raw_result, runner)` — parse runner-specific output
- [ ] **T3.2.6** Implement `build_summary(parsed, max_failures)` — structured summary ≤ 1000 tokens
- [ ] **T3.2.7** Implement auto-detection: pom.xml → Maven, package.json → npm, pyproject.toml → pytest
- [ ] **T3.2.8** Write test matrix: Java/JS/Python runner detection (100% correct)
- [ ] **T3.2.9** Write property test: suites of 10/100/1000 tests → p99 ≤ 1000 tokens summary
- [ ] **T3.2.10** Write integration test: hung test → timeout → graceful kill + summary (no zombies)

### 3.3 get_repo_map

- [ ] **T3.3.1** Implement `get_repo_map` tool (AST-based file indexing)
- [ ] **T3.3.2** Benchmark: 5 real projects (10K-100K LOC), coverage ≥ 90%, size ≤ 10%
- [ ] **T3.3.3** Benchmark: generation < 10s for 100K LOC (p99)

### 3.4 checkpoint

- [ ] **T3.4.1** Implement `checkpoint` tool: git commit + state save atomically
- [ ] **T3.4.2** Write chaos test: kill mid-checkpoint → zero corrupted states
- [ ] **T3.4.3** Verify idempotency: same state → skip commit (no duplicate)

### 3.5 Cross-cutting

- [ ] **T3.5.1** Implement rate limiting (token bucket per tool) in Tool Registry
- [ ] **T3.5.2** Write stress test: agent in retry loop → limit hit → escalation triggered
- [ ] **T3.5.3** Implement audit logging: every tool call → event stream (input, output, duration)
- [ ] **T3.5.4** Write integration test: 50 tool calls → 100% events in stream
- [ ] **T3.5.5** Property test: all tools double-call = single-call effect (idempotency)

---

## Stage 4: Economics & Performance (DoD Level 3)

> **Depends on:** Stages 2 + 3  
> **Blocking:** All blocking criteria must pass before release.

### 4.1 Token Budget Benchmarks

- [ ] **T4.1.1** Build benchmark harness (token counting, task classification, reporting)
- [ ] **T4.1.2** Benchmark: orchestration overhead (10 tasks, p95 ≤ 25%)
- [ ] **T4.1.3** Benchmark: simple task token count (20 tasks × 3 languages, p95 ≤ 20K)
- [ ] **T4.1.4** Benchmark: complex task token count (10 tasks, p95 ≤ 50K)
- [ ] **T4.1.5** Add token budget checks to CI (fail build on regression > 10%)

### 4.2 Performance Benchmarks

- [ ] **T4.2.1** Benchmark: repo-map generation < 10s for 100K LOC (p99)
- [ ] **T4.2.2** Benchmark: diff apply < 2s (p99, 1000 diffs)
- [ ] **T4.2.3** Benchmark: checkpoint recovery < 5s (p99)
- [ ] **T4.2.4** Add performance regression gates to CI

### 4.3 Monitoring (Non-blocking)

- [ ] **T4.3.1** Implement prompt cache hit rate measurement (target: ≥ 50%)
- [ ] **T4.3.2** Implement test pipeline overhead measurement (target: < 5% of task tokens)
- [ ] **T4.3.3** Add metrics export (Prometheus-compatible) for both monitors

---

## Stage 5: Reliability & Security (DoD Level 4)

> **Depends on:** Stages 2 + 3

### 5.1 Sandbox & Scope

- [ ] **T5.1.1** Implement write-scope enforcement (tools can only write within designated paths)
- [ ] **T5.1.2** Write security test: attempt write outside scope → 100% blocked

### 5.2 Secrets Protection

- [ ] **T5.2.1** Add static analysis check: no secrets in logs or state files
- [ ] **T5.2.2** Add grep-based test on all test outputs (zero secret leaks)
- [ ] **T5.2.3** Implement redaction layer for event stream (API keys, tokens)

### 5.3 Resilience

- [ ] **T5.3.1** Implement retry with exponential backoff for LLM API calls
- [ ] **T5.3.2** Implement fallback: on API 429/500/timeout → structured error → escalate
- [ ] **T5.3.3** Write chaos test: API returns 429/500/timeout → no crash, proper degradation
- [ ] **T5.3.4** Implement state corruption detection (checksum validation on load)
- [ ] **T5.3.5** Write integrity test: corrupt JSON → detection + meaningful error + recovery path

### 5.4 Concurrency & Memory

- [ ] **T5.4.1** Write concurrency test: 2 agents writing same state → zero corruption
- [ ] **T5.4.2** Implement file locking or optimistic concurrency for state writes
- [ ] **T5.4.3** Soak test: 100 sequential tasks, monitor RSS (stable ±10%)
- [ ] **T5.4.4** Add memory leak detection to CI (long-running test with RSS assertions)

---

## Stage 6: Documentation & Handoff

> **Depends on:** All previous stages

- [ ] **T6.1** Update ADR-005/006/007 with verification results and actual decisions
- [ ] **T6.2** Fix all benchmarks in repository with reproducible scripts
- [ ] **T6.3** Ensure core documentation reflects actual architecture (not desired)
- [ ] **T6.4** Write onboarding guide: "How to add a new tool" + "How to add a new graph node"
- [ ] **T6.5** Write operations runbook: recovery, scaling, incident response
