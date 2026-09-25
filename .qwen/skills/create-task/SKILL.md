---
name: create-task
description: Create or edit a backlog task specification file (YAML frontmatter + 7-section Markdown body) that the orchestrator can parse and that Planner/Executor/Reviewer agents can execute. Use when writing, generating, or fixing any file under tasks/, or when the user asks to break work down into tasks. Also use when validating task format.
---

# Skill: Creating Tasks for the Backlog

> This skill is used by AI agents and developers to produce correct task
> specifications. Follow these rules ALWAYS when creating or editing a task file.

## File format

Each task is a single `.md` file in the `tasks/` directory, named `{id}.md`.

Structure:
```
---
[YAML frontmatter — see schema below]
---

[Markdown body — 7 required sections]
```

## Required frontmatter fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique ID: `TASK-NNN` or a semantic slug |
| `status` | enum | No (=todo) | todo / in-progress / in-review / done / blocked / cancelled |
| `priority` | enum | No (=medium) | critical / high / medium / low |
| `depends_on` | list[string] | No (=[]) | IDs of tasks that must finish BEFORE this one |
| `tags` | list[string] | No (=[]) | Categories: auth, api, db, test, refactor, ... |
| `assigned_role` | enum | No (=any) | executor / planner / reviewer / any |
| `requires_approval` | bool | No (=false) | true = human approval before execution |
| `estimated_complexity` | enum | No (=medium) | simple / medium / complex |

The frontmatter is validated against the Pydantic model in
`src/schemas/task_frontmatter.py` — that model is the single source of truth.

## 7 required Markdown body sections

### 1. Objective + Not Included
- One goal, 1-3 sentences. What we build and WHY.
- `### Not Included` — explicit boundaries. Without it, the agent adds unrequested features.

### 2. Context
- Why this task exists NOW.
- Link to existing files (do NOT copy-paste code).
- Background if relevant.

### 3. Tech Stack & Constraints
- Concrete versions: "NestJS 10.x", NOT "NestJS".
- Constraints: "do NOT upgrade jsonwebtoken".
- Without this, the agent mixes APIs from different versions.

### 4. Input/Output Contracts
- Machine-readable schemas: Zod, JSON Schema, OpenAPI.
- NOT a prose description of fields. The agent cannot infer types from prose.

### 5. Acceptance Criteria (TABLE)
- Format: `| ID | Input | Expected Behavior | Verification |`
- Each row = one verifiable scenario.
- Minimum 3 ACs for any non-trivial task.
- NOT a prose list. A table is an executable spec.

### 6. Boundaries (3-tier)
- `Always` — what the agent MUST do every time
- `Ask First` — what requires confirmation
- `Never` — absolute prohibitions
- Without the "Ask First" tier, the agent treats ambiguity as permission.

### 7. Test Plan + Self-Verification
- Concrete test commands.
- Self-verify instruction: "Run ALL N ACs. Cite specific test names."
- `### Prohibited Completion Phrases`: forbid "tests should pass", "looks correct".

## ANTI-PATTERNS (NEVER do this)

| Do NOT | Instead |
|--------|---------|
| Implementation hints ("Use HashMap") | Outcome spec ("O(1) lookup") |
| Pseudo-code as specification | Behavioral spec + AC table |
| Vague: "make it fast", "handle errors" | Measurable: "P99 < 50ms", "structured error codes" |
| Copy-paste code into the task | Link: `see src/auth/jwt.service.ts` |
| Conflicting instructions | Cross-check all sections |
| Prescriptive architecture | Point to an existing example file |
| Prose AC list | Table with Input → Expected → Verification |
| Monolithic text without sections | 7 sections with headings |

## Golden sample

See the reference example: `tasks/examples/TASK-042-jwt-refresh-rotation.md`

Use it as a template. Copy the structure, replace the content.

## Validation

After creating a task, run:
```bash
python scripts/lint_tasks.py tasks/{id}.md
```

If lint fails — fix it BEFORE committing.

To regenerate the JSON Schema used by IDE tooling:
```bash
python scripts/export_schema.py
```
