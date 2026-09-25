# ADR-011: Sandbox & Fixture Strategy — Dual Isolation Model

- **Статус:** Принято
- **Дата:** 2026-09-25
- **Связанные документы:**
  - ADR-004 — Checkpoints & recovery
  - [ADR-010](./ADR-010-cli-interface-design.md) — CLI `--sandbox` flag
  - [definition-of-done.md](../definition-of-done.md) — C0-C4 criteria
  - benchmark-планы

## Контекст

Инструмент выполняет код, написанный LLM-агентами. Это создаёт два класса рисков:
1. **Безопасность**: агент может выполнить деструктивные операции
2. **Воспроизводимость**: тесты и отладка требуют детерминированной среды

Попытка использовать одну песочницу для всех целей приводит к компромиссам:
- Docker для unit tests = неприемлемая медлительность (5-10 сек/test)
- tmp_path для отладки = нереалистичная среда, невозможность воспроизведения
- Общий mutable state = flaky tests

Необходимы два ортогональных типа изоляции с чёткими границами применения.

## Решение

### Dual Isolation Model

| Тип | Назначение | Lifecycle | Изоляция | Создание |
|-----|-----------|-----------|----------|----------|
| **Ephemeral Sandbox** | Автоматические тесты, CI, benchmarks | Секунды. Create → test → destroy | Полная (tmp_path / container) | Программно, per-test |
| **Fixture Project** | Отладка, dogfooding, demo, reproduction | Постоянный. Версионируется в git | Логическая (отдельный репо/директория) | `backlog init --from-fixture` |

### Ephemeral Sandbox

**Реализация:** `pytest.tmp_path` для unit/integration. Docker/container только для E2E с реальной изоляцией ОС.

**Требования:**
- Fresh environment per test (no shared mutable state)
- Creation time < 1 sec (unit), < 5 sec (integration with Docker)
- Auto-cleanup after test completion
- Minimal project structure: `tasks/`, `.backlog/`, `src/`, language-specific config
- Seed data через pytest fixtures, не через копирование больших деревьев

**Когда использовать:**
- Unit tests: парсеры, DAG engine, tool registry, schema validation
- Integration tests: полный цикл parse → plan → execute → verify
- Property-based / fuzz testing
- CI pipeline jobs
- Benchmark runs (изоляция от внешних факторов)
- Token measurement

**Когда НЕ использовать:**
- Ручная отладка (слишком эфемерно)
- Dogfooding (нет персистентности)
- Демо (пользователь не может «потрогать»)

### Fixture Projects

**Реализация:** Версионируемые директории в `fixtures/` репозитория инструмента.

**Структура:**
```
fixtures/
├── README.md                    # Usage guide
├── python-webapp/               # Python/NestJS-like, 15 tasks
│   ├── tasks/                   # Ready-to-run backlog
│   ├── src/                     # Realistic source code
│   ├── tests/                   # Existing test suite
│   ├── pyproject.toml
│   └── .backlog.yml
├── java-service/                # Java/Maven, 8 tasks
├── ts-react-app/                # TypeScript/React, 12 tasks
└── broken-state/                # Corrupted state for recovery testing
```

**Требования:**
- Self-contained: no external DB, API keys, network dependencies
- Versioned in git: reproducible at any commit
- Documented: README explains purpose, structure, how to run
- Multi-language: minimum Python, Java, TypeScript
- Mixed complexity: simple (1 file), medium (3-5 files), complex (cross-module)
- Known-good baseline: expected post-execution state captured as snapshot
- Broken variants: intentionally corrupted state for error recovery testing

**Когда использовать:**
- Manual debugging: `cd fixtures/python-webapp && backlog run`
- Dogfooding: agent executes fixture tasks, human reviews
- Bug reproduction: «Bug in TASK-005, here's the fixture»
- Demo & onboarding: clone and try immediately
- Regression testing: run after fix to verify no breakage
- Benchmark calibration: realistic tasks for token measurement

**Когда НЕ использовать:**
- Unit tests (слишком тяжело, медленно)
- CI per-commit (слишком долго setup)
- Тесты, требующие полной изоляции ОС

### CLI Integration

```bash
# Fixture operations
backlog init --from-fixture python-webapp     # Copy to CWD
backlog init --from-fixture broken-state      # Recovery testing
backlog fixtures list                         # List available

# Run on fixture without copying (read-only inspection)
backlog run --project-dir fixtures/X --sandbox read-only

# Sandbox mode for regular runs
backlog run --sandbox read-only               # Inspect only
backlog run --sandbox workspace-write         # Default: write only within project
backlog run --sandbox full                    # Full access (dangerous)
```

### Sandbox Modes

| Mode | Read | Write Scope | Use Case |
|------|------|-------------|----------|
| `read-only` | Anywhere | None | Inspection, dry-run, fixture exploration |
| `workspace-write` | Anywhere | Only within project root | **Default**. Safe for most tasks |
| `full` | Anywhere | Anywhere | Trusted environments only. Requires explicit flag. |

**Enforcement:** File system middleware intercepts all write operations. Violations logged + blocked (except `full` mode).

## Альтернативы

| Альтернатива | Причина отклонения |
|-------------|-------------------|
| Единая песочница для всего | Tests медленные ИЛИ debugging нереалистичный |
| Docker для всех тестов | 5-10 sec overhead per unit test. CI = hours. |
| No fixtures, only ephemeral | Невозможна ручная отладка, dogfooding, demo |
| Fixtures outside repo (S3/cloud) | Не версионируются, не воспроизводимы, offline не работают |
| Mutable shared test state | Flaky tests, false positives, debugging nightmare |
| Sandbox via prompts only («don't write outside») | Unreliable. Must be enforced at FS level. |
| Fixture generation on-the-fly | Дрейф, несогласованность, нет known-good baseline |

## Последствия

### Положительные
- ✅ Fast tests: tmp_path < 1 sec per unit test
- ✅ Realistic debugging: fixture = real project structure
- ✅ Reproducible: fixtures versioned in git
- ✅ Safe defaults: workspace-write sandbox prevents accidents
- ✅ Multi-language coverage: fixtures for Python, Java, TS
- ✅ Recovery testing: broken-state fixture validates ADR-004
- ✅ Dogfooding infrastructure: ready-to-run backlogs

### Отрицательные
- ⚠️ Two isolation models = cognitive overhead for contributors
- ⚠️ Fixtures require maintenance as tool evolves
- ⚠️ Sandbox enforcement adds runtime overhead (~5-10%)
- ⚠️ Broken-state fixtures must be updated when state schema changes

### Риски
| Риск | Вероятность | Влияние | Митигация |
|------|------------|---------|-----------|
| Fixture drift from actual behavior | Средняя | Высокое | CI job runs all fixtures weekly. Fail = update fixture. |
| Sandbox bypass via symlink/hardlink | Низкая | Критическое | Resolve all paths before check. Test symlinks explicitly. |
| Ephemeral sandbox too minimal | Средняя | Средняя | Richer seed fixtures. Document what's included. |
| Fixture too large (>100MB) | Низкая | Средняя | Size limit in CI. LFS for binary assets if needed. |
| Developer uses `--sandbox full` out of habit | Средняя | Высокое | Warning banner. Audit log. Default = workspace-write always. |

## Эволюция

- **MVP:** Ephemeral (tmp_path) + 1 Python fixture
- **P1:** Java + TS fixtures, broken-state fixture, Docker E2E sandbox
- **P2:** Fixture generator CLI, automated fixture freshness checks, cloud sandbox option

## Ссылки
- [OpenHands sandbox architecture](https://docs.all-hands.dev/modules/usage/architecture)
- [DeepSeek Harness sandbox modes](https://www.deepseek.com/harness/en/)
- [pytest tmp_path documentation](https://docs.pytest.org/en/stable/how-to/tmp_path.html)
- [Test fixtures best practices (Martin Fowler)](https://martinfowler.com/articles/nonDeterminism.html)