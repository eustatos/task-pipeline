"""
Pydantic schema for task YAML frontmatter validation.

This is the single source of truth for task metadata structure.
Exported to JSON Schema for IDE support via `scripts/export_schema.py`.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in-progress"
    IN_REVIEW = "in-review"
    DONE = "done"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AssignedRole(str, Enum):
    """Agent role this task is primarily assigned to."""

    EXECUTOR = "executor"
    PLANNER = "planner"
    REVIEWER = "reviewer"
    ANY = "any"


class EstimatedComplexity(str, Enum):
    SIMPLE = "simple"  # ≤ 20K tokens expected
    MEDIUM = "medium"  # ≤ 50K tokens expected
    COMPLEX = "complex"  # > 50K tokens expected, may need sub-decomposition


class TaskFrontmatter(BaseModel):
    """
    Machine-readable metadata for a task file.

    Parsed from YAML frontmatter between --- delimiters.
    Used by orchestrator for DAG construction, routing, and scheduling.
    NOT consumed directly by Executor (who reads the Markdown body).
    """

    id: str = Field(
        ...,
        description="Unique task identifier. Format: TASK-NNN or semantic slug.",
        examples=["TASK-042", "auth-jwt-rotation"],
        min_length=1,
        max_length=64,
    )

    status: TaskStatus = Field(
        default=TaskStatus.TODO,
        description="Current task lifecycle state.",
    )

    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM,
        description="Execution priority within the backlog.",
    )

    depends_on: list[str] = Field(
        default_factory=list,
        description=(
            "List of task IDs that must complete before this task starts. "
            "Defines edges in the execution DAG."
        ),
        examples=[["TASK-038", "TASK-039"]],
    )

    tags: list[str] = Field(
        default_factory=list,
        description="Categorization tags for filtering and grouping.",
        examples=[["auth", "api", "security"]],
        max_length=20,
    )

    assigned_role: AssignedRole = Field(
        default=AssignedRole.ANY,
        description="Preferred agent role for this task. 'any' = orchestrator decides.",
    )

    requires_approval: bool = Field(
        default=False,
        description=(
            "If True, orchestrator inserts an interrupt/approval gate "
            "before executing this task. See ADR-004."
        ),
    )

    estimated_complexity: EstimatedComplexity = Field(
        default=EstimatedComplexity.MEDIUM,
        description="Expected token cost tier. Influences model selection (ADR-001).",
    )

    created_at: str | None = Field(
        default=None,
        description="ISO 8601 creation timestamp. Auto-set by CLI if missing.",
        examples=["2026-09-25T10:30:00Z"],
    )

    updated_at: str | None = Field(
        default=None,
        description="ISO 8601 last modification timestamp.",
    )

    @field_validator("id")
    @classmethod
    def validate_id_format(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Task ID cannot be empty or whitespace-only")
        if " " in stripped:
            raise ValueError(f"Task ID must not contain spaces: '{stripped}'")
        return stripped

    @field_validator("depends_on")
    @classmethod
    def validate_dependencies(cls, v: list[str]) -> list[str]:
        seen: set[str] = set()
        for dep in v:
            dep_stripped = dep.strip()
            if not dep_stripped:
                raise ValueError("depends_on entries cannot be empty strings")
            if dep_stripped in seen:
                raise ValueError(f"Duplicate dependency: '{dep_stripped}'")
            seen.add(dep_stripped)
        return [d.strip() for d in v]

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, v: list[str]) -> list[str]:
        normalized: list[str] = []
        seen: set[str] = set()
        for tag in v:
            t = tag.strip().lower().replace(" ", "-")
            if t and t not in seen:
                normalized.append(t)
                seen.add(t)
        return normalized

    model_config = {
        "json_schema_extra": {
            "$id": "https://backlog-tool.dev/schemas/task-frontmatter.json",
            "title": "Task Frontmatter",
            "description": "YAML frontmatter schema for backlog task files.",
        }
    }
