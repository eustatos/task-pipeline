# Backlog task conventions (shared by all tasks)

Every task file under `backlog/` follows this convention. Task files do NOT
repeat these rules inline; they reference this document instead.

## Prohibited completion phrases

Do NOT use these phrases in any completion report, commit message, or
self-verification. They signal unverified work.

- "tests should pass"
- "looks correct"
- "follows best practices"
- "implementation seems fine"
- "should work"
- "seems fine"
- "make it fast"
- "handle errors gracefully"

Use specific, observable claims instead: test name + outcome, measured value,
command + exit code.

## Type checking

- All modules pass `mypy --strict`.
- No `# type: ignore` without an adjacent justification comment.
- The CI gate (T1.5.2) fails the build on any type error.

## Toolchain baseline

- Python 3.11
- Pydantic v2.x
- pytest for tests
- mypy --strict for type checks
- hypothesis for property-based tests
- jsonschema (Draft 2020-12) for schema validation

The exact package versions are pinned in `pyproject.toml` (see T1.0.0).

## Path conventions

- Core modules live under `src/core/`
- Tests live under `tests/core/`
- Fixtures live under `tests/fixtures/`

The package layout is established by T1.0.0.
