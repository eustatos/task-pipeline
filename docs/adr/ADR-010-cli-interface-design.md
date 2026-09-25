# ADR-010: CLI Interface Design — Convention over Configuration

- **Статус:** Принято
- **Дата:** 2026-09-25
- **Связанные документы:**
  - ADR-003 — CLI как primary interface
  - [ADR-008](./ADR-008-task-specification-format.md) — Task format
  - ADR-009 — Dogfooding strategy
  - benchmark-планы

## Контекст

Инструмент требует командного интерфейса для:
1. Выполнения бэклога (основная функция)
2. Инициализации проектов
3. Валидации задач
4. Инспекции состояния
5. Интеграции в CI/CD и dogfooding

Ключевые требования из ADR-003: CLI-first, no web UI for MVP, git-native workflow.
Ключевые требования из dogfooding: zero-arg start, работа внутри собственного репозитория без указания путей.

Индустриальный стандарт (git, npm, cargo, aider): convention over configuration. Разумные defaults, явные overrides только при необходимости.

## Решение

### Принцип: Zero-Config Start

`backlog run` без аргументов работает, если CWD находится внутри проекта с `backlog/`. Все пути автодетектятся. Все параметры имеют sensible defaults.

### Команды

| Команда | Назначение | Required args |
|---------|-----------|---------------|
| `backlog run [FILTER]` | Выполнение бэклога | Нет |
| `backlog init [DIR]` | Инициализация проекта | Нет (default: CWD) |
| `backlog lint [PATH...]` | Валидация задач | Нет (default: backlog/) |
| `backlog status` | Инспекция графа/прогресса | Нет |
| `backlog resume [TASK_ID]` | Явный resume после прерывания | Нет (auto-resume по умолчанию) |
| `backlog schema export` | Экспорт JSON Schema для IDE | Нет |
| `backlog fixtures list` | Список доступных fixture projects | Нет |

### Автодетект Project Root

Алгоритм: walk up от CWD до первого найденного маркера:
`.backlog/` → `.backlog.yml` → `pyproject.toml` → `package.json` → `pom.xml` → `build.gradle` → `.git/`

Fallback: CWD если ничего не найдено.

### Конвенции путей

| Путь | Default | Override |
|------|---------|----------|
| Project root | Auto-detect | `--project-dir` |
| Tasks directory | `<root>/backlog/` | `--tasks-dir` |
| State file | `<root>/.backlog/state.json` | Не overrideable (by design) |
| Log files | `<root>/.backlog/logs/<ts>.jsonl` | `--log-file` |
| User config | `~/.config/backlog/config.yml` | `BACKLOG_CONFIG` env var |
| Project config | `<root>/.backlog.yml` | Не overrideable (by design) |

### Конфигурация: 3 уровня

Приоритет: CLI flags > Project config (`.backlog.yml`) > User config (`~/.config/backlog/config.yml`) > Defaults

API keys хранятся ТОЛЬКО как env var references. Никогда в файлах.

### Key Flags для `backlog run`

```
Execution:
  --dry-run              Validate only, no execution
  --max-tasks N          Stop after N completed tasks
  --fail-fast            Stop on first failure (default: continue independent branches)
  --parallel N           Max concurrent tasks (default: 1)
  --requires-approval    Force approval on ALL tasks

Model & Cost:
  --planner-model MODEL  Override planner (default: from config)
  --executor-model MODEL Override executor (default: from config)
  --max-cost USD         Hard budget limit

Safety:
  --sandbox MODE         read-only | workspace-write | full (default: workspace-write)
  --no-git               Disable auto-commits
  --yes / -y             Skip approvals (CI only, DANGEROUS)

Output:
  -v / -vv               Verbosity
  -q                     Quiet (errors only)
  --log-file PATH        Custom log path
  --no-log               Disable file logging
  --trace                Enable LangSmith/OTEL tracing
```

### Logging: Dual Output

| Destination | Format | Default | Override |
|-------------|--------|---------|----------|
| stderr | Human-readable, colored | Always (except `-q`) | `-v`, `-q` |
| File | JSONL event stream | `.backlog/logs/<ts>.jsonl` | `--log-file`, `--no-log` |
| stdout | Machine-readable | Only explicit commands | `status --format json` |

### Fixture Integration

```bash
backlog init --from-fixture python-webapp   # Copy fixture to CWD
backlog run --project-dir fixtures/X --sandbox read-only  # Run without copy
backlog fixtures list                       # List available fixtures
```

## Альтернативы

| Альтернатива | Причина отклонения |
|-------------|-------------------|
| Required `--project-dir` and `--tasks-dir` | Убивает zero-config start и dogfooding |
| Interactive wizard при init | Блокирует CI. Non-interactive by default. |
| Web UI as primary interface | Противоречит ADR-003. CLI-first. |
| Single `--model` flag | Нарушает ADR-001 (Planner/Executor split) |
| Global state outside project | Projects must be isolated. All state under `.backlog/` |
| Subcommands per tool | CLI = orchestration, not tool registry |
| Config via env vars only | No project-level committed config. Need `.backlog.yml` |

## Последствия

### Положительные
- ✅ Zero-arg `backlog run` works inside any initialized project
- ✅ Git-like ergonomics: familiar mental model
- ✅ CI-ready: non-interactive, exit codes, structured logs
- ✅ Dogfooding-friendly: no path boilerplate
- ✅ 3-level config: personal prefs + project settings + CLI overrides
- ✅ Safe defaults: workspace-write sandbox, no auto-yes

### Отрицательные
- ⚠️ Auto-detect may surprise users with nested projects
- ⚠️ Convention paths harder to discover than explicit flags
- ⚠️ 3-level config precedence can confuse new users

### Риски
| Риск | Митигация |
|------|-----------|
| Wrong project root detected | `backlog status` shows detected root. `--project-dir` override always available. |
| User commits secrets to `.backlog.yml` | Schema validation rejects API key fields. Docs warn explicitly. Pre-commit hook. |
| `--yes` used interactively by accident | Warning banner + confirmation prompt unless `CI=true` env var set. |
| Log files grow unbounded | Auto-rotation: keep last 10 logs. Documented in `--help`. |

## Ссылки
- [Aider CLI design](https://aider.chat/docs/usage.html)
- [DeepSeek Harness profiles & headless mode](https://github.com/deepseek-ai/deepseek-harness)
- [Git convention-over-configuration philosophy](https://git-scm.com/docs/gitcli)