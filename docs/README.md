# Документация task-pipeline-tools

## Architecture

| Document | Description |
|----------|-------------|
| [architecture.md](architecture.md) | Hybrid orchestration: LangGraph upper loop + custom test pipeline |
| [definition-of-done.md](definition-of-done.md) | DoD criteria C0–C4, levels, verification methods |

## Backlog

| File | Description |
|------|-------------|
| [backlog.md](../backlog/backlog.md) | Master backlog — stages, tasks, dependencies |
| [stage-1/](../backlog/stage-1/) | Stage 1 detailed task files (one per task) |
| [_conventions.md](../backlog/_conventions.md) | Shared rules for all task files |

## ADRs (Architecture Decision Records)

| # | Title | File |
|---|-------|------|
| 006 | Tool Registry & Execution Contract | [ADR-006](adr/ADR-006-tool-registry.md) |
| 007 | Hybrid Orchestration Architecture | [ADR-007](adr/ADR-007-hybrid-orchestration.md) |
| 008 | Task Specification Format (YAML Frontmatter + Markdown Body) | [ADR-008](adr/ADR-008-task-specification-format.md) |
| 009 | CLI-First Architecture & Dogfooding Strategy | [ADR-009](adr/ADR-009-cli-dogfooding-strategy.md) |
| 010 | CLI Interface Design — Convention over Configuration | [ADR-010](adr/ADR-010-cli-interface-design.md) |
| 011 | Sandbox & Fixture Strategy — Dual Isolation Model | [ADR-011](adr/ADR-011-sandbox-and-fixtures-strategy.md) |