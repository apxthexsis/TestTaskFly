"""Pure release-gate result aggregation."""

from __future__ import annotations

from datetime import UTC, datetime


def overall_exit_code(*exit_codes: int) -> int:
    return 0 if all(code == 0 for code in exit_codes) else 1


def _gate_line(name: str, exit_code: int) -> str:
    outcome = "PASS" if exit_code == 0 else "FAIL"
    return f"- {name}: {outcome} (exit {exit_code})"


def markdown_summary(quality_exit: int, functional_exit: int, load_exit: int) -> str:
    overall = overall_exit_code(quality_exit, functional_exit, load_exit)
    outcome = "PASS" if overall == 0 else "FAIL"
    return "\n".join(
        [
            "# Assignment Run Summary",
            "",
            f"- Timestamp (UTC): {datetime.now(UTC).isoformat()}",
            _gate_line("Framework quality gate", quality_exit),
            _gate_line("Functional/contract release gate", functional_exit),
            _gate_line("Load gate", load_exit),
            f"- Overall: **{outcome}**",
            "",
            "Confirmed product defects intentionally fail the functional release gate. "
            "See `BUGS.md` and `pytest-report.html` for evidence.",
            "",
        ]
    )
