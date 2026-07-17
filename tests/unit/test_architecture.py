from __future__ import annotations

import ast
from pathlib import Path

SOURCE_ROOT = Path("src/automation_assignment")

FORBIDDEN_INTERNAL_IMPORTS = {
    "domain": (
        "automation_assignment.api",
        "automation_assignment.commands",
        "automation_assignment.contract",
        "automation_assignment.transport",
        "automation_assignment.workflows",
    ),
    "transport": (
        "automation_assignment.api",
        "automation_assignment.commands",
        "automation_assignment.contract",
        "automation_assignment.workflows",
    ),
    "api": (
        "automation_assignment.commands",
        "automation_assignment.contract",
        "automation_assignment.workflows",
    ),
}


def _imports(source_file: Path) -> set[str]:
    tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    return imported


def test_dependency_direction_is_enforced_by_package_boundary() -> None:
    violations: list[str] = []
    for layer, forbidden_prefixes in FORBIDDEN_INTERNAL_IMPORTS.items():
        for source_file in (SOURCE_ROOT / layer).glob("*.py"):
            for imported in _imports(source_file):
                if imported.startswith(forbidden_prefixes):
                    violations.append(f"{source_file}: forbidden dependency on {imported}")

    assert not violations, "\n".join(violations)
