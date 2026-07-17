from automation_assignment.reporting import markdown_summary, overall_exit_code


def test_overall_exit_code_fails_if_any_gate_fails() -> None:
    assert overall_exit_code(0, 0) == 0
    assert overall_exit_code(0, 1) == 1
    assert overall_exit_code(5, 0) == 1


def test_summary_preserves_individual_gate_results() -> None:
    summary = markdown_summary(quality_exit=0, functional_exit=1, load_exit=0)
    assert "Framework quality gate: PASS" in summary
    assert "Functional/contract release gate: FAIL" in summary
    assert "Load gate: PASS" in summary
    assert "Overall: **FAIL**" in summary
