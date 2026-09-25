# ADR-008: Формат спецификации задач (YAML Frontmatter + Markdown Body)

- **Статус:** Принято
- **Дата:** 2026-09-25
- **Связанные документы:**
  - ADR-001 (Archtect/Executor split)
  - [ADR-006](./ADR-006-tool-registry.md)
  - [ADR-007](./ADR-007-hybrid-orchestration.md)

## Контекст

Инструмент принимает бэклог в виде папки с файлами задач. Формат этих файлов определяет:
1. Способность оркестратора строить DAG зависимостей
2. Качество понимания задачи LLM-агентами (Planner/Executor/Reviewer)
3. Token efficiency подачи контекста разным ролям
4. Human readability и git-friendliness
5. Возможность IDE-валидации и автодополнения

Анализ индустриальных практик (GitHub 2500+ agent configs, Augment Code, Batty, Addy Osmani) показал консенсус: гибридный формат YAML frontmatter + Markdown body является де-факто стандартом для AI-agent task specs.

Чистый JSON/YAML непригоден для описания контекста и инструкций (структурный шум, escaping, нечитаемый diff). Чистый Markdown непригоден для метаданных (нет детерминированного парсинга id/status/depends_on). Гибрид разделяет эти роли.

## Решение

### Формат: YAML Frontmatter + Markdown Body

Каждая задача — один `.md` файл с YAML frontmatter (между `---`) и Markdown-телом.

**Frontmatter** содержит машиночитаемые метаданные для оркестратора:
- `id`, `status`, `priority`, `depends_on`, `tags`, `assigned_role`, `requires_approval`, `estimated_complexity`

**Markdown body** содержит семантическое описание задачи для LLM-агентов, структурированное в 7 секций:
1. Objective + Not Included
2. Context
3. Tech Stack & Constraints
4. Input/Output Contracts
5. Acceptance Criteria (таблица)
6. Boundaries (3-tier: Always / Ask First / Never)
7. Test Plan + Self-Verification

### Валидация

Frontmatter валидируется Pydantic-схемой (`src/schemas/task_frontmatter.py`) при:
- Загрузке бэклога (fail-fast на невалидных задачах)
- CI pipeline (lint tasks)
- Создании задачи через CLI

Markdown body проверяется структурным линтером (наличие обязательных секций) через `scripts/lint_tasks.py`.

### Подача контекста по ролям (ADR-001)

| Роль | Подаваемые секции | Экономия токенов |
|------|------------------|-----------------|
| Planner (Architect) | Frontmatter + Objective + Not Included + depends_on | ~70% vs full task |
| Executor | Полная задача (lazy-loading AC/Contracts по запросу) | Progressive disclosure |
| Reviewer | AC table + Boundaries + Test Plan | ~60% vs full task |

### IDE Support

Pydantic-схема экспортируется в JSON Schema (`schemas/task-frontmatter.schema.json`) для:
- VS Code YAML frontmatter autocomplete
- Cursor/Claude inline validation
- Pre-commit hooks

## Альтернативы

| Альтернатива | Причина отклонения |
|-------------|-------------------|
| Pure JSON | Нечитаемый diff, escaping overhead, wall of brackets |
| Pure YAML | Синтаксический шум для прозы, нет native LLM comprehension |
| Pure Markdown | Нет детерминированного парсинга метаданных, хрупкий regex |
| Gherkin | Variable LLM generation quality, только для AC, не для full spec |
| Custom XML tags | Нет экосистемной поддержки, reinventing wheel |
| Notion/Confluence | Не версионируется, AI не читает, рассинхронизация с кодом |

## Последствия

### Положительные
- ✅ Индустриальный стандарт (GitHub, Augment, Batty)
- ✅ Git-native: читаемый diff, версионность, PR review
- ✅ Dual audience: человек читает MD, оркестратор парсит YAML
- ✅ Token-efficient: role-based section routing
- ✅ IDE support через JSON Schema export
- ✅ Fail-fast валидация через Pydantic

### Отрицательные
- ⚠️ Требует дисциплины: 7 секций, табличные AC, no pseudo-code
- ⚠️ Два парсера (YAML frontmatter + MD section extractor)
- ⚠️ Migration существующих задач (если есть)

### Риски
| Риск | Митигация |
|------|-----------|
| Frontmatter schema drift | Pydantic versioning + migration scripts |
| Секции отсутствуют в задаче | Structural linter в CI + default values |
| AI создаёт задачи без секций | Skill/rules file + golden samples + pre-commit lint |
| Таблицы AC плохо рендерятся | Fallback: bullet list format supported, но table preferred |

## Ссылки

- [The Case for Markdown as Your Agent's Task Format](https://dev.to/battyterm/the-case-for-markdown-as-your-agents-task-format-6mp)
- [How to Write a Good Spec for AI Agents (Addy Osmani)](https://addyosmani.com/blog/good-spec/)
- [AI Spec Template (Augment Code)](https://www.augmentcode.com/guides/ai-spec-template)
- [Spec-driven Development with Markdown (GitHub Blog)](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-using-markdown-as-a-programming-language-when-building-with-ai/)
