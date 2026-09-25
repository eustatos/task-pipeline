# Definition of Done — Core

> **Status:** Active  
> **Last Updated:** 2026-09-25  
> **Scope:** Task pipeline core (orchestration + tool execution)

This document defines measurable, automatable readiness criteria for the core. Every criterion references an artifact, has a verification method, and a threshold.

---

## Level 0: Contract Integrity (Gate)

> **All C0.x must pass in CI before any merge to main. No exceptions.**

| # | Criterion | Verification Method | Threshold | Reference |
|---|-----------|-------------------|-----------|-----------|
| C0.1 | All tools have Pydantic schemas with validation | `mypy --strict` + schema generation test | 100% tools typed, 0 mypy errors | ADR-006 |
| C0.2 | Tool Registry registers/removes tools atomically | Unit test: concurrent register/unregister | Zero race conditions, zero partial state | ADR-006 |
| C0.3 | Role-based filtering works correctly | Integration test: Architect sees planning tools, Executor — editing tools | 0 cross-role tool leaks | ADR-001, ADR-006 |
| C0.4 | State schema is versioned and migratable | Migration test: v1→v2 state conversion | 100% backward compatibility | ADR-004 |
| C0.5 | Event stream is append-only and immutable | Property test: no mutation after write | Zero violations across 10K events | F11 |
| C0.6 | Configuration validated at startup | Pydantic Settings validation test | Fail-fast with clear error message | ADR-005 |

---

## Level 1: Upper Loop Functional Correctness

| # | Criterion | Verification Method | Threshold | Reference |
|---|-----------|-------------------|-----------|-----------|
| C1.1 | Graph of N tasks executes in correct topological order | Integration test: DAG with 20 nodes, parallel branches | 100% correct ordering | F1, F6 |
| C1.2 | Conditional routing (pass/fail/retry) works | Parameterized test: all Reviewer branches | 100% coverage of all edges | Upper loop |
| C1.3 | Interrupt/resume preserves and restores state | Kill process → resume → verify state identity | State byte-identical after resume | F7, ADR-004 |
| C1.4 | Checkpoint created after each completed task | Integration test: 10 tasks → 10 git commits + state snapshots | 10/10 checkpoints valid | F5, ADR-004 |
| C1.5 | Recovery from any checkpoint < 5 sec | Benchmark: kill at task N → resume → measure time | p99 < 5s | Benchmarks |
| C1.6 | Explicit context passing sends only dependency artifacts | Token measurement: context size vs full history | Context ≤ 30% of full history tokens | F6, Opt-map |
| C1.7 | Subgraph (Executor) isolated from parent state | Unit test: subgraph state mutations don't leak | Zero leakage | Hybrid arch |
| C1.8 | Human approval gate blocks execution until resume | E2E test: interrupt → verify blocked → resume → verify continued | 100% blocking correctness | F7 |

---

## Level 2: Tool Execution Correctness

| # | Criterion | Verification Method | Threshold | Reference |
|---|-----------|-------------------|-----------|-----------|
| C2.1 | `apply_diff` applies patches correctly | Fuzz test: 500 real LLM outputs → parse → apply | ≥ 95% success rate | ADR-002 |
| C2.2 | `apply_diff` falls back to whole-file on 3 failures | Integration test: malformed diff → retry → fallback | Fallback triggers correctly | ADR-002 |
| C2.3 | `run_tests` auto-detects runner for Java/JS/Python | Test matrix: pom.xml, package.json, pyproject.toml | 100% correct detection | run_tests spec |
| C2.4 | `run_tests` summary ≤ 1000 tokens regardless of suite size | Property test: suites of 10/100/1000 tests | p99 ≤ 1000 tokens | run_tests spec |
| C2.5 | `get_repo_map` covers ≥ 90% of project files | Benchmark: 5 real projects (10K-100K LOC) | Coverage ≥ 90%, size ≤ 10% of codebase | F2 |
| C2.6 | `checkpoint` is atomic: git commit + state save | Chaos test: kill mid-checkpoint → verify no corruption | Zero corrupted states | ADR-004 |
| C2.7 | All tools are idempotent or have undo | Property test: double-call = single-call effect | 100% idempotent or reversible | LangGraph interrupt rules |
| C2.8 | Tool timeout handling: graceful kill + summary | Integration test: hung test → timeout → verify summary | Timeout reported, no zombie processes | run_tests spec |
| C2.9 | Audit log contains every tool call with input/output | Integration test: 50 tool calls → verify event stream | 100% events logged | F11 |
| C2.10 | Rate limiting prevents runaway loops | Stress test: agent in retry loop → verify limit hit | Limit enforced, escalation triggered | Anti-feature AF3 |

---

## Level 3: Economics & Performance (Release-Blocking)

> **All blocking criteria must pass before release.**

| # | Criterion | Verification Method | Threshold | Blocking? | Reference |
|---|-----------|-------------------|-----------|-----------|-----------|
| C3.1 | Orchestration overhead ≤ 25% | Benchmark: 10 tasks, measure orch tokens / total | p95 ≤ 25% | Yes | Benchmarks |
| C3.2 | Simple task ≤ 20K tokens | Benchmark: 20 simple tasks across 3 languages | p95 ≤ 20K | Yes | Benchmarks |
| C3.3 | Complex task ≤ 50K tokens | Benchmark: 10 complex tasks | p95 ≤ 50K | Yes | Benchmarks |
| C3.4 | Repo-map generation < 10 sec (100K LOC) | Benchmark: 5 large projects | p99 < 10s | Yes | Benchmarks |
| C3.5 | Diff apply < 2 sec | Unit benchmark: 1000 diffs | p99 < 2s | Yes | Benchmarks |
| C3.6 | Prompt cache hit rate ≥ 50% | Measurement: 50 sequential tasks | ≥ 50% cached input tokens | No (monitoring) | Opt-map |
| C3.7 | Test pipeline overhead < 5% of task tokens | Measurement: compare with/without structured summary | Overhead < 5% | No (monitoring) | run_tests |

---

## Level 4: Reliability & Security

| # | Criterion | Verification Method | Threshold | Reference |
|---|-----------|-------------------|-----------|-----------|
| C4.1 | Sandbox write-scope enforcement | Security test: attempt write outside scope | 100% blocked | DSH insight |
| C4.2 | No secrets in logs/state | Static analysis + grep on test outputs | Zero secret leaks | Safety |
| C4.3 | Graceful degradation on LLM API failure | Chaos test: API returns 429/500/timeout | Retry → fallback → escalate, no crash | Resilience |
| C4.4 | State file corruption detection | Integrity test: corrupt JSON → verify detection + recovery | Detection + meaningful error | ADR-004 |
| C4.5 | Concurrent safety: 2 agents can't corrupt same state | Concurrency test: parallel writes | Zero corruption | Thread safety |
| C4.6 | Memory bounded: no unbounded growth under load | Soak test: 100 tasks, monitor RSS | RSS stable ±10% | Production readiness |

---

## Summary: Core is Ready When

```
✅ Level 0: ALL criteria pass (gate)
✅ Level 1: ALL criteria pass
✅ Level 2: ALL criteria pass
✅ Level 3: ALL blocking criteria pass
✅ Level 4: ALL criteria pass
✅ CI pipeline automates all checks above
✅ ADR-005/006/007 updated with verification results
✅ Benchmarks fixed in repository and checked in CI
✅ Core documentation reflects actual architecture (not desired)
```

---

## Anti-patterns in Readiness Criteria

| Anti-pattern | Why Dangerous | Instead |
|-------------|--------------|---------|
| "Core works on my laptop" | Not reproducible, not automated | CI pipeline with fixed thresholds |
| "Model usually generates correct code" | Subjective, not measurable | Structured output validation + fuzz testing |
| "Tests pass sometimes" | Flaky tests = false sense of security | Deterministic tests only. Flaky = bug |
| "Overhead is about 20-30%" | No threshold = no guarantee | p95 ≤ 25% with automatic check |
| "We'll add monitoring later" | Without metrics you're blind in production | C3.6/C3.7 as non-blocking but mandatory |
| Criteria without artifact references | Detached from product context | Every criterion → ADR/Feature/Benchmark |

---

## Implementation Recommendations

1. **Start with Level 0 immediately.** This is the contract without which everything else is meaningless. Write tests *before* implementation.
2. **Level 3 (economics) — in CI from day one.** Not "we'll add later." Token budget is a quality criterion just like correctness.
3. **Property-based testing (Hypothesis) for parsers.** Fuzz tests for `apply_diff` and `run_tests` parser — the only guarantee of reliability.
4. **Chaos testing for recovery.** Kill processes, corrupt files, timeout APIs. The core must be *antifragile*.
5. **Version the criteria.** When benchmarks or ADRs change — update DoD. This is a living document.
