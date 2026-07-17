"""Persist the aggregate release-gate result."""

from pathlib import Path

from automation_assignment.reporting import markdown_summary, overall_exit_code


def write_summary(
    *,
    quality_exit: int,
    functional_exit: int,
    load_exit: int,
    output: Path,
) -> int:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        markdown_summary(quality_exit, functional_exit, load_exit),
        encoding="utf-8",
    )
    return overall_exit_code(quality_exit, functional_exit, load_exit)
