# ADR-009: CLI-First Architecture & Dogfooding Strategy

- **Статус:** Принято
- **Дата:** 2026-09-25
- **Связанные документы:**
  - ADR-003 — CLI как primary interface
  - [ADR-008](./ADR-008-task-specification-format.md) — Task format
  - [ADR-010](./ADR-010-cli-interface-design.md) — CLI interface design
  - [ADR-011](./ADR-011-sandbox-and-fixtures-strategy.md) — Sandbox & fixtures
  - [definition-of-done.md](../definition-of-done.md) — C0-C4 criteria

## Контекст

Инструмент, автоматизирующий выполнение кода AI-агентами, стоит перед двумя
фундаментальными вопросами:

1. **Интерфейс:** Через что пользователь взаимодействует с инструментом?
2. **Верификация:** Как доказать, что ядро работает корректно?

Ответы взаимосвязаны. CLI является не просто интерфейсом, а архитектурным
фундаментом. Dogfooding (написание инструментом самого себя) — единственный
надёжный способ верификации ядра.

## Решение

### 1. CLI как Primary Interface

CLI — единственный primary interface для MVP. TUI (Textual) допустим как enhancement
поверх CLI, но не как замена.

| Requirement | CLI | Web UI (отклонён) |
|-------------|-----|-------------------|
| CI/CD интеграция | `backlog run tasks/` в pipeline | Невозможно без headless mode |
| Headless execution | Серверы, контейнеры, SSH | Требует браузера |
| Composability | pipe, redirect, xargs, cron | Изолированный процесс |
| Token economy | Нет overhead рендеринга UI | WebSocket + state sync |
| Testability | stdin/stdout/exit code | Selenium/Playwright |
| Dogfooding | `backlog run TASK-NNN` | Невозможно |

### 2. Dogfooding Strategy

Инструмент пишет сам себя. Это не «приятная опция», а обязательное условие
готовности ядра к production.

**Почему это критически необходимо:**
- **Верификация ядра:** Если инструмент не может написать собственный код — он не готов для чужого
- **Обнаружение gaps:** Только работая над собой, находятся недостающие tools, баги в парсерах, проблемы с context passing
- **Доказательство ценности:** «Мы используем свой инструмент для разработки» — сильнейший сигнал доверия
- **Feedback loop:** Каждая задача в собственном бэклоге = тестовый кейс для ядра
- **Экономия:** ROI начинается немедленно
- **Documentation as code:** Задачи в `tasks/` = живая документация возможностей

### 3. Dogfooding Phases

```
Фаза 0: Bootstrap (руками)
├── Ядро: DAG engine, Tool Registry, State management
├── Tools: apply_diff, read_file, checkpoint, run_tests
├── CLI: базовые команды (run, lint, init)
└── Прохождение Level 0 DoD
    ↑ GATE: только после этого → Фаза 1

Фаза 1: Периферия (агент пишет, человек ревьюит)
├── Tasks: lint_tasks.py, export_schema.py
├── Docs: ADR-008, skill create-task.md, golden samples
├── Tests: property-based для парсеров, fuzz для diff
├── CI: benchmark scripts, token measurement
└── Metrics: сбор первых реальных данных

Фаза 2: Расширение инструментов (агент + human-in-the-loop)
├── New tools: search_code, get_coverage, list_files
├── Subgraph: Executor analyze/write/test pipeline
├── TUI: Textual graph visualization
└── Integration: DSH session log pattern

Фаза 3: Ядро (под строгим контролем)
├── Refactoring: optimization, cleanup
├── New features: hybrid orchestration improvements
├── Bug fixes: found during Phase 1-2
└── Self-improvement loop established
```

### 4. Mandatory Policies

**Human review required for every PR**, regardless of whether code was written
by an agent or a human. Code written by an agent is reviewed more strictly,
not more leniently.

**Scope per task:** one file or module. No "rewrite the orchestrator" tasks.
Agents operate at file granularity.

**Metrics tracking:** every dogfooding task records:
- Tokens consumed (input + output)
- Wall-clock time
- Success / failure / retries
- Files modified
- Review time

These are the real benchmarks, not synthetic ones.

### 5. Regression from Dogfooding

Every dogfooding task that completes becomes an E2E test in CI. The task output
(committed delta) is the expected outcome; CI runs the same task and asserts
the same delta.

## Последствия

### Положительные
- ✅ CLI как фундамент композитности, тестируемости и CI-ready
- ✅ Dogfooding как единственный честный тест ядра
- ✅ Органический рост coverage через собственный бэклог
- ✅ Реальные бенчмарки (не синтетические)
- ✅ Раннее обнаружение gaps на периферии, до того как они убьют production

### Отрицательные
- ⚠️ Bootstrap paradox: ядро пишется руками до Level 0 DoD
- ⚠️ Human review обязателен: агент не может быть единственным автором
- ⚠️ Dogfooding-задачи медленнее ручного написания на Фазе 1
- ⚠️ Metrics tracking требует инфраструктуры с первого дня

### Риски

| Риск | Серьёзность | Митигация |
|------|-------------|-----------|
| Bootstrap never completes | 🔴 Высокая | Минимальное ядро (3 узла). Level 0 DoD как gate. |
| Agent produces low-quality code | 🟡 Средняя | Human review + limited scope per task. |
| Dogfooding phases slip | 🟡 Средняя | Phases are guidelines. Pivot if blocked. |
| Metrics not collected from start | 🟡 Средняя | Add `--trace` to CLI. Capture in CI. |
| Team bypasses human review | 🔴 Высокая | Branch protection. PR required. Code owners. |

## Альтернативы

| Альтернатива | Причина отклонения |
|-------------|-------------------|
| Web UI as primary | Противоречит ADR-003. Невозможен headless/CI. |
| No dogfooding (test only) | Не обнаруживает gaps. Нет доказательства ценности. |
| Dogfooding без фаз | Bootstrap paradox. Ядро не готово для себя. |
| Без метрик | Слепое управление. Нет данных для оптимизации. |
| Agent пишет ядро первым | Небезопасно. Ядро — самая сложная часть. |

## Ссылки
- [Aider — dogfooding case study](https://aider.chat/docs/usage/dogfooding.html)
- [DeepSeek Harness — CLI-first design](https://github.com/deepseek-ai/deepseek-harness)
- [Textual — TUI framework for Python](https://textual.textualize.io/)
- [The Bootstrap Paradox in AI-assisted development](https://blog.softwaredesign.engineering/p/ai-assisted-development-bootstrap)