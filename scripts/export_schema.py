#!/usr/bin/env python3
"""
Export TaskFrontmatter Pydantic model to JSON Schema for IDE support.

Usage:
    python scripts/export_schema.py
    # Outputs: schemas/task-frontmatter.schema.json

VS Code setup: Add to .vscode/settings.json:
    "yaml.schemas": {
        "./schemas/task-frontmatter.schema.json": ["tasks/*.md"]
    }
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.schemas.task_frontmatter import TaskFrontmatter


def main() -> None:
    schema = TaskFrontmatter.model_json_schema()

    output_dir = Path("schemas")
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / "task-frontmatter.schema.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    print(f"JSON Schema exported to {output_path}")
    print(f"   Fields: {len(TaskFrontmatter.model_fields)}")
    print(f"   Size: {output_path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
