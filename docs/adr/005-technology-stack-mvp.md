# ADR-005: Технологический стек MVP

- **Статус:** Принято (условно, до верификации прототипом)
- **Дата:** 2026-09-24
- **Авторы:** [Ваше имя]
- **Связанные документы:**
  - [ADR-001](./001-architect-executor-split.md)
  - [ADR-002](./002-diff-fenced-edit-format.md)
  - [ADR-003](./003-no-chat-primary-ui.md)
  - [ADR-004](./004-file-based-checkpoints.md)
  - [token-optimization-map.md](../competitive-analysis/token-optimization-map.md)
  - [benchmarks.md](../competitive-analysis/benchmarks.md)

## Контекст

Инструмент представляет собой автономный оркестратор выполнения бэклога с графом задач, мультиагентной архитектурой и жёсткими требованиями к экономии токенов. Выбор стека должен удовлетворять следующим ограничениям, вытекающим из артефактов Фазы 1:

1. **Multi-model routing** (ADR-001): поддержка одновременной работы с разными моделями для ролей Planner/Executor/Reviewer
2. **Надёжный парсинг diff-fenced** (ADR-002): обработка SEARCH/REPLACE блоков с устойчивостью к malformed output
3. **File-based state + git** (ADR-004): программные git-операции без внешних БД
4. **AST-based repo-map** (token-optimization-map): эффективное сжатие структуры кода
5. **CLI/TUI first** (ADR-003): богатый терминальный интерфейс с визуализацией графа
6. **Token overhead ≤25%** (benchmarks): минимальный runtime overhead оркестрации
7. **Local-first, no external deps**: работа без Docker/DB/cloud для MVP

Язык программирования должен иметь зрелую экосистему для всех вышеперечисленных требований.

## Решение

### Язык: Python 3.12+

**Обоснование:**
- Зрелая экосистема LLM-инструментов (LiteLLM, tiktoken, tree-sitter bindings)
- Лучшие AST/tree-sitter библиотеки для repo-map
- Textual — единственная production-ready TUI-библиотека с live-updating
- Все проанализированные конкуренты (Aider, OpenHands, LangGraph, CrewAI) написаны на Python → максимальная возможность заимствования паттернов
- Async-native для параллельных LLM-вызовов

**Отклонённые альтернативы:**
- **TypeScript/Node**: Слабая экосистема AST-parsing, нет зрелых TUI-библиотек, меньше LLM-инструментов
- **Rust**: Отличная производительность, но незрелая LLM-экосистема, высокий порог разработки, нет TUI-аналогов Textual
- **Go**: Хорош для CLI, но слабая LLM/AST экосистема, нет TUI с rich rendering

### Компоненты стека

| Компонент | Выбор | Обоснование | Связь с ADR |
|-----------|-------|-------------|-------------|
| **LLM Routing** | LiteLLM | Единый API для 100+ моделей, built-in caching, token counting, fallback chains, streaming | ADR-001, Opt-map |
| **AST Parsing** | tree-sitter + tree-sitter-languages | Инкрементальный парсинг, поддержка 50+ языков, быстрое извлечение сигнатур | F2, Opt-map |
| **Git Operations** | dulwich | Pure Python, нет C-зависимостей, программные commits/diff/status, работает без git binary | ADR-004 |
| **State Serialization** | msgspec + JSON | Быстрая сериализация state graph, schema validation, human-readable fallback | ADR-004 |
| **TUI Framework** | Textual | Live-updating widgets, CSS-like styling, async-native, rich graph visualization | ADR-003, F8 |
| **Task Parsing** | ruamel.yaml + markdown-it-py | YAML с сохранением комментариев, Markdown parsing с extensions | F1 |
| **DAG Engine** | Custom (на основе LangGraph patterns) | Минимальный overhead, полный контроль, нет зависимости от тяжелого фреймворка | Benchmarks (≤25%) |
| **Token Counting** | tiktoken + anthropic-tokenizer | Точный подсчёт для OpenAI/Anthropic, кеширование результатов | Benchmarks |
| **Diff Parser** | Custom (fuzz-tested) | Надёжная обработка SEARCH/REPLACE, tolerance к malformed output | ADR-002 |
| **Config** | Pydantic Settings | Type-safe конфигурация, env vars, .env files, validation | Все ADR |
| **Testing** | pytest + hypothesis | Property-based testing для парсеров, fixture-based для интеграционных | ADR-002, ADR-004 |
| **Linting/Types** | ruff + mypy (strict) | Быстрый lint, строгая типизация как документация | Quality |

### Архитектурные принципы применения стека

1. **Custom DAG over framework**: Не использовать LangGraph/CrewAI как runtime dependency. Заимствовать *паттерны* (checkpoint, interrupt, store), реализовать минимально необходимую оркестрацию самостоятельно. Цель: overhead ≤25%.
2. **LiteLLM as abstraction layer**: Все вызовы LLM только через LiteLLM. Прямые API-вызовы запрещены. Это обеспечивает hot-swap моделей (ADR-001) и unified caching.
3. **dulwich over subprocess**: Никаких `subprocess.run(["git", ...])`. Только программный API. Это обеспечивает атомарность, тестируемость и отсутствие зависимости от системного git.
4. **tree-sitter over regex**: Repo-map строится исключительно через AST. Regex-парсинг запрещён для структурного анализа кода.
5. **msgspec over dataclasses/json**: State serialization должна быть быстрой и валидируемой. msgspec обеспечивает оба свойства без boilerplate.

## Верификация (обязательна до финального принятия)

Перед началом production-кодинга необходимо написать **верификационный прототип**, покрывающий критические пути:

| Тест | Критерий успеха | Компоненты |
|------|----------------|------------|
| Multi-model call | Planner (Opus) → plan → Executor (Haiku) → edit via LiteLLM | LiteLLM, ADR-001 |
| Diff-fenced parse | 100 реальных outputs → ≥95% корректно распарсены | Custom parser, ADR-002 |
| Repo-map generation | 100K LOC проект → map <10% размера, <10 сек | tree-sitter, F2 |
| Git checkpoint | Commit + state save <3 сек, resume <5 сек | dulwich, msgspec, ADR-004 |
| Orchestration overhead | 10 задач → overhead ≤25% | Custom DAG, benchmarks |
| TUI graph render | Граф из 20 узлов рендерится без лагов | Textual, F8 |

**Если любой тест провален** → пересмотр соответствующего компонента стека и обновление этого ADR.

## Последствия

### Положительные
- ✅ Полный контроль над overhead оркестрации (custom DAG)
- ✅ Единая абстракция для всех LLM-провайдеров (LiteLLM)
- ✅ Максимальная совместимость с экосистемой конкурентов (Python)
- ✅ Production-ready TUI без веб-зависимостей (Textual)
- ✅ Нет внешних runtime-зависимостей (pure Python git, no DB)
- ✅ Строгая типизация как живая документация (mypy strict)

### Отрицательные
- ⚠️ Python GIL может ограничить CPU-bound операции (repo-map). Митигация: tree-sitter написан на C, multiprocessing для больших проектов.
- ⚠️ Custom DAG engine = собственная поддержка. Митигация: минимальная поверхность, заимствование проверенных паттернов LangGraph.
- ⚠️ dulwich медленнее native git для больших репозиториев. Митигация: бенчмарк в верификации; fallback на subprocess при необходимости.
- ⚠️ Textual имеет меньшее сообщество, чем web-фреймворки. Митигация: TUI — не core value, можно заменить на rich/plain output при проблемах.

### Риски
| Риск | Вероятность | Влияние | Митигация |
|------|------------|---------|-----------|
| LiteLLM breaking change | Средняя | Высокое | Pin version, abstraction wrapper, fallback to direct API |
| tree-sitter language gaps | Низкая | Средняя | Fallback на regex для неподдерживаемых языков |
| Custom DAG too complex | Средняя | Высокое | Strict scope: только sequential + conditional. Hierarchical = P1 |
| Textual performance issues | Низкая | Средняя | Degraded mode: static graph output via rich |

## Эволюция стека

Этот ADR фиксирует стек **для MVP**. Пересмотр допускается:
- При переходе к P1/P2 функциональностям (multi-agent crew, web UI)
- При появлении новых библиотек, значительно превосходящих текущие по бенчмаркам
- При доказанной непригодности компонента в production

Любое изменение требует нового ADR или обновления этого с изменением статуса.
