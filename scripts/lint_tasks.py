#!/usr/bin/env python3
"""
Structural linter for task specification files.

Validates:
1. YAML frontmatter parses against the TaskFrontmatter schema
2. All 7 required Markdown sections are present
3. AC section contains a table (not just bullets)
4. No prohibited patterns (pseudo-code, vague attributes)

Usage:
    python scripts/lint_tasks.py tasks/TASK-042.md
    python scripts/lint_tasks.py tasks/          # lint all
"""

import re
import sys
from pathlib import Path

import yaml
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.schemas.task_frontmatter import TaskFrontmatter

REQUIRED_SECTIONS = [
    "objective",
    "context",
    "tech stack",
    "input/output contracts",
    "acceptance criteria",
    "boundaries",
    "test plan",
]

PROHIBITED_PHRASES = [
    "tests should pass",
    "looks correct",
    "follows best practices",
    "seems fine",
    "should work",
    "make it fast",
    "handle errors gracefully",
]


def extract_frontmatter(content: str) -> dict | None:
    """Extract YAML frontmatter from markdown content."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not match:
        return None
    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML frontmatter: {e}")


def validate_frontmatter(fm: dict) -> list[str]:
    """Validate frontmatter against the Pydantic schema."""
    try:
        TaskFrontmatter(**fm)
        return []
    except ValidationError as e:
        return [
            f"Frontmatter validation: {err['msg']} (field: {err['loc']})"
            for err in e.errors()
        ]


def validate_sections(content: str) -> list[str]:
    """Check that all required sections exist."""
    lower = content.lower()
    missing = []
    for section in REQUIRED_SECTIONS:
        if f"## {section}" not in lower and f"# {section}" not in lower:
            missing.append(f"Missing required section: '{section}'")
    return missing


def validate_ac_table(content: str) -> list[str]:
    """Check that the AC section contains a markdown table."""
    ac_match = re.search(
        r"## acceptance criteria.*?(?=## |\Z)",
        content,
        re.IGNORECASE | re.DOTALL,
    )
    if not ac_match:
        return ["Acceptance Criteria section not found"]

    ac_content = ac_match.group(0)
    if "|" not in ac_content or "---" not in ac_content:
        return [
            "Acceptance Criteria must be a table "
            "(| ID | Input | Expected | Verification |)"
        ]
    return []


def _strip_prohibited_section(content: str) -> str:
    """Remove the 'Prohibited Completion Phrases' subsection.

    That subsection lists the forbidden phrases verbatim, so it must be
    excluded from the scan to avoid flagging the task's own definition.
    """
    return re.sub(
        r"###\s*prohibited completion phrases.*?(?=\n##?\s|\Z)",
        "",
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )


def validate_no_prohibited(content: str) -> list[str]:
    """Check for prohibited vague phrases."""
    lower = _strip_prohibited_section(content).lower()
    found = []
    for phrase in PROHIBITED_PHRASES:
        if phrase in lower:
            found.append(f"Prohibited phrase found: '{phrase}'")
    return found


def lint_task(path: Path) -> list[str]:
    """Run all validations on a task file."""
    errors: list[str] = []
    content = path.read_text(encoding="utf-8")

    fm = extract_frontmatter(content)
    if fm is None:
        errors.append("No valid YAML frontmatter found (expected --- delimiters)")
    else:
        errors.extend(validate_frontmatter(fm))

    errors.extend(validate_sections(content))
    errors.extend(validate_ac_table(content))
    errors.extend(validate_no_prohibited(content))

    return errors


def main() -> None:
    targets = sys.argv[1:] if len(sys.argv) > 1 else ["tasks/"]
    all_errors: dict[str, list[str]] = {}

    for target in targets:
        p = Path(target)
        files = sorted(p.glob("*.md")) if p.is_dir() else [p]

        for f in files:
            errors = lint_task(f)
            if errors:
                all_errors[str(f)] = errors

    if all_errors:
        for path, errors in all_errors.items():
            print(f"\n[FAIL] {path}:")
            for err in errors:
                print(f"   - {err}")
        total = sum(len(e) for e in all_errors.values())
        print(f"\n{total} errors in {len(all_errors)} files")
        sys.exit(1)

    print("All task files valid")
    sys.exit(0)


if __name__ == "__main__":
    main()
